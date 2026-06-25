from datetime import datetime, timedelta, timezone

import pytest

from backend.app.search.search_service import INDEX_NAME


@pytest.mark.integration
def test_api_public_endpoints_and_debug(api_client):
    assert api_client.get("/ping").json() == {"message": "pong"}
    assert api_client.get("/health").json() == {"status": "ok"}
    assert api_client.get("/").json()["version"] == "1.0.0"

    debug_response = api_client.get("/debug/instance")
    assert debug_response.status_code == 200
    assert "service" in debug_response.json()
    assert "container" in debug_response.json()


@pytest.mark.integration
def test_search_service_health_and_debug(search_client):
    assert search_client.get("/health").json() == {"status": "ok"}

    debug_response = search_client.get("/debug/instance")
    assert debug_response.status_code == 200
    assert "service" in debug_response.json()
    assert "container" in debug_response.json()


@pytest.mark.integration
def test_register_login_and_users_me_flow(api_client, user_factory):
    user = user_factory("me")

    response = api_client.get("/users/me", headers=user["headers"])
    assert response.status_code == 200
    assert response.json()["user_id"] == user["user_id"]
    assert response.json()["user_name"] == user["username"]


@pytest.mark.integration
def test_restaurants_crud_and_validation_paths(api_client, admin_headers, admin_user, user_factory, tracker):
    client_user = user_factory("restaurants-client")
    create_payload = {
        "restaurant_name": f"Restaurante {client_user['username']}",
        "admin_id": admin_user["user_id"],
        "restaurant_status": 1,
    }

    forbidden_response = api_client.post("/restaurants/", json=create_payload, headers=client_user["headers"])
    assert forbidden_response.status_code == 403

    create_response = api_client.post("/restaurants/", json=create_payload, headers=admin_headers)
    assert create_response.status_code == 201, create_response.text
    restaurant = create_response.json()
    tracker.track_mongo("restaurants", restaurant["restaurant_id"])

    list_response = api_client.get("/restaurants/", headers=admin_headers)
    assert list_response.status_code == 200
    assert any(item["restaurant_id"] == restaurant["restaurant_id"] for item in list_response.json())

    get_response = api_client.get(f"/restaurants/{restaurant['restaurant_id']}", headers=admin_headers)
    assert get_response.status_code == 200
    assert get_response.json()["restaurant_name"] == create_payload["restaurant_name"]

    empty_update = api_client.put(f"/restaurants/{restaurant['restaurant_id']}", json={}, headers=admin_headers)
    assert empty_update.status_code == 400

    missing_admin = api_client.put(
        f"/restaurants/{restaurant['restaurant_id']}",
        json={"admin_id": 999999},
        headers=admin_headers,
    )
    assert missing_admin.status_code == 404

    update_response = api_client.put(
        f"/restaurants/{restaurant['restaurant_id']}",
        json={"restaurant_name": f"{create_payload['restaurant_name']} Editado"},
        headers=admin_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["restaurant_name"].endswith("Editado")

    not_found_create = api_client.post(
        "/restaurants/",
        json={"restaurant_name": "Sin admin", "admin_id": 999999, "restaurant_status": 1},
        headers=admin_headers,
    )
    assert not_found_create.status_code == 404

    delete_response = api_client.delete(f"/restaurants/{restaurant['restaurant_id']}", headers=admin_headers)
    assert delete_response.status_code == 204

    second_delete = api_client.delete(f"/restaurants/{restaurant['restaurant_id']}", headers=admin_headers)
    assert second_delete.status_code == 404


@pytest.mark.integration
def test_menus_tables_orders_reservations_and_search_integration(
    api_client,
    search_client,
    admin_headers,
    admin_user,
    user_factory,
    tracker,
    redis_cache,
    elasticsearch_client,
):
    customer = user_factory("customer")

    restaurant_response = api_client.post(
        "/restaurants/",
        json={
            "restaurant_name": f"Restaurante menu {customer['username']}",
            "admin_id": admin_user["user_id"],
            "restaurant_status": 1,
        },
        headers=admin_headers,
    )
    assert restaurant_response.status_code == 201, restaurant_response.text
    restaurant = restaurant_response.json()
    tracker.track_mongo("restaurants", restaurant["restaurant_id"])

    menu_payload = {
        "dish_name": f"Pizza {customer['username']}",
        "category": "Pasta",
        "description": "Masa artesanal",
        "price": 12.5,
        "restaurant_id": restaurant["restaurant_id"],
    }
    menu_response = api_client.post("/menus/", json=menu_payload, headers=admin_headers)
    assert menu_response.status_code == 201, menu_response.text
    menu = menu_response.json()
    tracker.track_mongo("menus", menu["menu_id"])

    duplicate_menu = api_client.post("/menus/", json=menu_payload, headers=admin_headers)
    assert duplicate_menu.status_code == 409

    list_response = api_client.get("/menus/", headers=admin_headers)
    assert list_response.status_code == 200
    assert redis_cache.get("menus:all") is not None

    item_response = api_client.get(f"/menus/{menu['menu_id']}", headers=admin_headers)
    assert item_response.status_code == 200
    assert redis_cache.get(f"menus:{menu['menu_id']}") is not None

    missing_restaurant_update = api_client.put(
        f"/menus/{menu['menu_id']}",
        json={"restaurant_id": 999999},
        headers=admin_headers,
    )
    assert missing_restaurant_update.status_code == 404

    conflict_free_update = api_client.put(
        f"/menus/{menu['menu_id']}",
        json={"price": 13.0, "category": "Pasta fresca"},
        headers=admin_headers,
    )
    assert conflict_free_update.status_code == 200
    assert redis_cache.get("menus:all") is None
    assert redis_cache.get(f"menus:{menu['menu_id']}") is None

    missing_menu_update = api_client.put("/menus/999999", json={"price": 99}, headers=admin_headers)
    assert missing_menu_update.status_code == 404

    customer_forbidden = api_client.post("/menus/", json=menu_payload, headers=customer["headers"])
    assert customer_forbidden.status_code == 403

    table_payload = {
        "table_number": 7,
        "table_status": 1,
        "restaurant_id": restaurant["restaurant_id"],
    }
    table_response = api_client.post("/tables/", json=table_payload, headers=admin_headers)
    assert table_response.status_code == 201, table_response.text
    table = table_response.json()
    tracker.track_mongo("tables", table["table_id"])

    duplicate_table = api_client.post("/tables/", json=table_payload, headers=admin_headers)
    assert duplicate_table.status_code == 409

    assert api_client.get("/tables/", headers=admin_headers).status_code == 200
    assert api_client.get(f"/tables/{table['table_id']}", headers=admin_headers).status_code == 200

    empty_table_update = api_client.put(f"/tables/{table['table_id']}", json={}, headers=admin_headers)
    assert empty_table_update.status_code == 400

    missing_table_update = api_client.put(
        f"/tables/{table['table_id']}",
        json={"restaurant_id": 999999},
        headers=admin_headers,
    )
    assert missing_table_update.status_code == 404

    updated_table = api_client.put(
        f"/tables/{table['table_id']}",
        json={"table_status": 2},
        headers=admin_headers,
    )
    assert updated_table.status_code == 200
    assert updated_table.json()["table_status"] == 2

    customer_forbidden_table = api_client.delete(f"/tables/{table['table_id']}", headers=customer["headers"])
    assert customer_forbidden_table.status_code == 403

    reservation_payload = {
        "table_id": table["table_id"],
        "client_id": customer["user_id"],
        "reservation_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "reservation_status": 1,
    }
    reservation_response = api_client.post(
        "/reservations/",
        json=reservation_payload,
        headers=customer["headers"],
    )
    assert reservation_response.status_code == 201, reservation_response.text
    reservation = reservation_response.json()
    tracker.track_mongo("reservations", reservation["reservation_id"])

    missing_table_reservation = api_client.post(
        "/reservations/",
        json={**reservation_payload, "table_id": 999999},
        headers=customer["headers"],
    )
    assert missing_table_reservation.status_code == 404

    missing_user_reservation = api_client.post(
        "/reservations/",
        json={**reservation_payload, "client_id": 999999},
        headers=customer["headers"],
    )
    assert missing_user_reservation.status_code == 404

    order_payload = {
        "table_id": table["table_id"],
        "client_id": customer["user_id"],
        "order_type": "dine-in",
        "restaurant_id": restaurant["restaurant_id"],
    }
    order_response = api_client.post("/orders/", json=order_payload, headers=customer["headers"])
    assert order_response.status_code == 201, order_response.text
    order = order_response.json()
    tracker.track_mongo("orders", order["order_id"])

    get_order = api_client.get(f"/orders/{order['order_id']}", headers=customer["headers"])
    assert get_order.status_code == 200

    missing_table_order = api_client.post(
        "/orders/",
        json={**order_payload, "table_id": 999999},
        headers=customer["headers"],
    )
    assert missing_table_order.status_code == 404

    missing_user_order = api_client.post(
        "/orders/",
        json={**order_payload, "client_id": 999999},
        headers=customer["headers"],
    )
    assert missing_user_order.status_code == 404

    missing_restaurant_order = api_client.post(
        "/orders/",
        json={**order_payload, "restaurant_id": 999999},
        headers=customer["headers"],
    )
    assert missing_restaurant_order.status_code == 404

    cancel_reservation = api_client.delete(
        f"/reservations/{reservation['reservation_id']}",
        headers=customer["headers"],
    )
    assert cancel_reservation.status_code == 204

    second_cancel = api_client.delete(
        f"/reservations/{reservation['reservation_id']}",
        headers=customer["headers"],
    )
    assert second_cancel.status_code == 404

    reindex_response = search_client.post("/reindex", headers=admin_headers)
    assert reindex_response.status_code == 200, reindex_response.text
    assert reindex_response.json()["total"] >= 1
    assert elasticsearch_client.indices.exists(index=INDEX_NAME)

    search_response = search_client.get(
        "/products",
        params={"q": customer["username"]},
        headers=customer["headers"],
    )
    assert search_response.status_code == 200
    assert any(item["menu_id"] == menu["menu_id"] for item in search_response.json())
    assert redis_cache.get(f"search:products:text:{customer['username'].lower()}") is not None

    category_response = search_client.get(
        "/products/category/Pasta fresca",
        headers=customer["headers"],
    )
    assert category_response.status_code == 200
    assert any(item["menu_id"] == menu["menu_id"] for item in category_response.json())

    graph_response = api_client.get("/graph/export")
    assert graph_response.status_code == 200, graph_response.text
    graph_data = graph_response.json()
    assert {"roles", "users", "restaurants", "products", "orders", "order_items"} <= graph_data.keys()
    assert any(item["user_id"] == customer["user_id"] and item["role_name"] for item in graph_data["users"])
    assert any(item["restaurant_id"] == restaurant["restaurant_id"] for item in graph_data["restaurants"])
    assert any(item["menu_id"] == menu["menu_id"] for item in graph_data["products"])
    assert any(item["order_id"] == order["order_id"] and "total" in item for item in graph_data["orders"])

    delete_menu = api_client.delete(f"/menus/{menu['menu_id']}", headers=admin_headers)
    assert delete_menu.status_code == 204

    delete_table = api_client.delete(f"/tables/{table['table_id']}", headers=admin_headers)
    assert delete_table.status_code == 204


@pytest.mark.integration
def test_user_update_delete_permissions_and_not_found(api_client, admin_headers, user_factory):
    owner = user_factory("owner")
    stranger = user_factory("stranger")

    update_response = api_client.put(
        f"/users/{owner['user_id']}",
        json={"user_name": f"{owner['username']}-edit"},
        headers=owner["headers"],
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["user_name"].endswith("-edit")

    duplicate_response = api_client.put(
        f"/users/{owner['user_id']}",
        json={"user_name": stranger["username"]},
        headers=owner["headers"],
    )
    assert duplicate_response.status_code == 400

    forbidden_update = api_client.put(
        f"/users/{owner['user_id']}",
        json={"user_name": "hack-attempt"},
        headers=stranger["headers"],
    )
    assert forbidden_update.status_code == 403

    role_escalation = api_client.put(
        f"/users/{owner['user_id']}",
        json={"role_id": 1},
        headers=owner["headers"],
    )
    assert role_escalation.status_code == 403

    admin_update = api_client.put(
        f"/users/{stranger['user_id']}",
        json={"user_name": f"{stranger['username']}-admin"},
        headers=admin_headers,
    )
    assert admin_update.status_code == 200

    missing_user_update = api_client.put(
        "/users/999999",
        json={"user_name": "ghost"},
        headers=admin_headers,
    )
    assert missing_user_update.status_code == 404

    forbidden_delete = api_client.delete(f"/users/{owner['user_id']}", headers=stranger["headers"])
    assert forbidden_delete.status_code == 403

    missing_user_delete = api_client.delete("/users/999999", headers=admin_headers)
    assert missing_user_delete.status_code == 404

    admin_delete = api_client.delete(f"/users/{stranger['user_id']}", headers=admin_headers)
    assert admin_delete.status_code == 204
