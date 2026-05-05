"""Cobertura unitaria para routers funcionales restantes."""

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.routers import menus, orders, reservations, tables
from backend.dao import DAOConflictError
from backend.database import get_dao


def make_app(router, current_user_dependency, mock_dao, token_payload):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_dao] = lambda: mock_dao
    app.dependency_overrides[current_user_dependency] = lambda: token_payload
    return TestClient(app)


def menu_payload():
    return {
        "dish_name": "Pizza",
        "category": "main",
        "description": "Queso",
        "price": 12.5,
        "restaurant_id": 1,
    }


def menu_response():
    return {"menu_id": 1, **menu_payload()}


def table_payload():
    return {"table_number": 1, "table_status": 1, "restaurant_id": 1}


def table_response():
    return {"table_id": 1, **table_payload()}


def test_menus_crud_success_paths(mock_dao, mock_payload_admin):
    mock_dao.list_menus.return_value = [menu_response()]
    mock_dao.get_menu.return_value = menu_response()
    mock_dao.get_restaurant.return_value = {"restaurant_id": 1}
    mock_dao.create_menu.return_value = menu_response()
    mock_dao.update_menu.return_value = {**menu_response(), "price": 13.0}
    mock_dao.delete_menu.return_value = True
    client = make_app(menus.router, menus.get_current_user, mock_dao, mock_payload_admin)

    with patch("backend.app.routers.menus.get_cache", return_value=None), \
            patch("backend.app.routers.menus.set_cache"), \
            patch("backend.app.routers.menus.delete_cache"), \
            patch("backend.app.routers.menus.delete_cache_pattern"):
        assert client.get("/menus/").status_code == 200
        assert client.get("/menus/1").status_code == 200
        assert client.post("/menus/", json=menu_payload()).status_code == 201
        assert client.put("/menus/1", json={"price": 13.0}).status_code == 200
        assert client.delete("/menus/1").status_code == 204


def test_menus_cache_and_error_paths(mock_dao, mock_payload_admin, mock_payload_user):
    client = make_app(menus.router, menus.get_current_user, mock_dao, mock_payload_admin)

    with patch("backend.app.routers.menus.get_cache", return_value=[menu_response()]):
        assert client.get("/menus/").json()[0]["menu_id"] == 1

    with patch("backend.app.routers.menus.get_cache", return_value=None):
        mock_dao.get_menu.return_value = None
        assert client.get("/menus/404").status_code == 404

    mock_dao.get_restaurant.return_value = None
    assert client.post("/menus/", json=menu_payload()).status_code == 404

    mock_dao.get_restaurant.return_value = {"restaurant_id": 1}
    mock_dao.create_menu.side_effect = DAOConflictError()
    assert client.post("/menus/", json=menu_payload()).status_code == 409
    mock_dao.create_menu.side_effect = None

    mock_dao.update_menu.return_value = None
    assert client.put("/menus/404", json={"price": 14.0}).status_code == 404
    assert client.put("/menus/1", json={}).status_code == 400

    user_client = make_app(menus.router, menus.get_current_user, mock_dao, mock_payload_user)
    assert user_client.post("/menus/", json=menu_payload()).status_code == 403
    assert user_client.put("/menus/1", json={"price": 13.0}).status_code == 403
    assert user_client.delete("/menus/1").status_code == 403


def test_tables_crud_success_and_error_paths(mock_dao, mock_payload_admin, mock_payload_user):
    mock_dao.list_tables.return_value = [table_response()]
    mock_dao.get_table.return_value = table_response()
    mock_dao.get_restaurant.return_value = {"restaurant_id": 1}
    mock_dao.create_table.return_value = table_response()
    mock_dao.update_table.return_value = {**table_response(), "table_status": 2}
    mock_dao.delete_table.return_value = True
    client = make_app(tables.router, tables.get_current_user, mock_dao, mock_payload_admin)

    assert client.get("/tables/").status_code == 200
    assert client.get("/tables/1").status_code == 200
    assert client.post("/tables/", json=table_payload()).status_code == 201
    assert client.put("/tables/1", json={"table_status": 2}).status_code == 200
    assert client.delete("/tables/1").status_code == 204

    mock_dao.get_table.return_value = None
    assert client.get("/tables/404").status_code == 404
    mock_dao.get_restaurant.return_value = None
    assert client.post("/tables/", json=table_payload()).status_code == 404
    assert client.put("/tables/1", json={"restaurant_id": 99}).status_code == 404
    assert client.put("/tables/1", json={}).status_code == 400
    mock_dao.delete_table.return_value = False
    assert client.delete("/tables/404").status_code == 404

    user_client = make_app(tables.router, tables.get_current_user, mock_dao, mock_payload_user)
    assert user_client.post("/tables/", json=table_payload()).status_code == 403
    assert user_client.put("/tables/1", json={"table_status": 2}).status_code == 403
    assert user_client.delete("/tables/1").status_code == 403


def test_tables_conflict_paths(mock_dao, mock_payload_admin):
    mock_dao.get_restaurant.return_value = {"restaurant_id": 1}
    mock_dao.create_table.side_effect = DAOConflictError()
    mock_dao.update_table.side_effect = DAOConflictError()
    client = make_app(tables.router, tables.get_current_user, mock_dao, mock_payload_admin)

    assert client.post("/tables/", json=table_payload()).status_code == 409
    assert client.put("/tables/1", json={"table_number": 2}).status_code == 409


def test_orders_success_and_not_found_paths(mock_dao, mock_payload_admin):
    order = {"order_id": 1, "table_id": 1, "client_id": 1, "order_type": "dine-in", "restaurant_id": 1}
    mock_dao.get_table.return_value = {"table_id": 1}
    mock_dao.get_user.return_value = {"user_id": 1}
    mock_dao.get_restaurant.return_value = {"restaurant_id": 1}
    mock_dao.create_order.return_value = order
    mock_dao.get_order.return_value = order
    client = make_app(orders.router, orders.get_current_user, mock_dao, mock_payload_admin)

    payload = {"table_id": 1, "client_id": 1, "order_type": "dine-in", "restaurant_id": 1}
    assert client.post("/orders/", json=payload).status_code == 201
    assert client.get("/orders/1").status_code == 200

    mock_dao.get_table.return_value = None
    assert client.post("/orders/", json=payload).status_code == 404
    mock_dao.get_table.return_value = {"table_id": 1}
    mock_dao.get_user.return_value = None
    assert client.post("/orders/", json=payload).status_code == 404
    mock_dao.get_user.return_value = {"user_id": 1}
    mock_dao.get_restaurant.return_value = None
    assert client.post("/orders/", json=payload).status_code == 404
    mock_dao.get_order.return_value = None
    assert client.get("/orders/404").status_code == 404


def test_reservations_success_and_not_found_paths(mock_dao, mock_payload_admin):
    reservation = {
        "reservation_id": 1,
        "table_id": 1,
        "client_id": 1,
        "reservation_date": "2026-05-05T18:00:00",
        "reservation_status": 1,
    }
    mock_dao.get_table.return_value = {"table_id": 1}
    mock_dao.get_user.return_value = {"user_id": 1}
    mock_dao.create_reservation.return_value = reservation
    mock_dao.delete_reservation.return_value = True
    client = make_app(reservations.router, reservations.get_current_user, mock_dao, mock_payload_admin)

    payload = {k: v for k, v in reservation.items() if k != "reservation_id"}
    assert client.post("/reservations/", json=payload).status_code == 201
    assert client.delete("/reservations/1").status_code == 204

    mock_dao.get_table.return_value = None
    assert client.post("/reservations/", json=payload).status_code == 404
    mock_dao.get_table.return_value = {"table_id": 1}
    mock_dao.get_user.return_value = None
    assert client.post("/reservations/", json=payload).status_code == 404
    mock_dao.delete_reservation.return_value = False
    assert client.delete("/reservations/404").status_code == 404
