import pytest
from unittest.mock import Mock

from backend.dao import DAOConflictError, MongoDAO, PostgresDAO, field_value
from backend.models.menus import Menu
from backend.models.orders import Order
from backend.models.reservations import Reservation
from backend.models.roles import Role
from backend.models.tables import Table
from backend.models.users import User
from sqlalchemy.exc import IntegrityError


@pytest.mark.integration
def test_mongo_dao_crud_with_real_database(mongo_db, tracker, test_prefix):
    dao = MongoDAO(mongo_db)

    admin_role = dao.get_role_by_name("admin")
    client_role = dao.get_role_by_name("client")
    assert admin_role["role_name"] == "admin"
    assert client_role["role_name"] == "client"

    admin_user = dao.create_user(
        {
            "user_name": f"{test_prefix}-mongo-admin",
            "keycloak_id": f"{test_prefix}-mongo-admin-keycloak",
            "role_id": admin_role["role_id"],
        }
    )
    tracker.track_mongo("users", admin_user["user_id"])

    client_user = dao.create_user(
        {
            "user_name": f"{test_prefix}-mongo-client",
            "keycloak_id": f"{test_prefix}-mongo-client-keycloak",
            "role_id": client_role["role_id"],
        }
    )
    tracker.track_mongo("users", client_user["user_id"])

    assert dao.get_user(admin_user["user_id"])["user_name"].endswith("mongo-admin")
    assert dao.get_user_by_username(client_user["user_name"])["user_id"] == client_user["user_id"]
    assert dao.get_user_by_keycloak_id(client_user["keycloak_id"])["user_id"] == client_user["user_id"]

    restaurant = dao.create_restaurant(
        {
            "restaurant_name": f"{test_prefix}-mongo-restaurant",
            "admin_id": admin_user["user_id"],
            "restaurant_status": 1,
        }
    )
    tracker.track_mongo("restaurants", restaurant["restaurant_id"])
    assert dao.list_restaurants()
    assert dao.get_restaurant(restaurant["restaurant_id"])["admin_id"] == admin_user["user_id"]

    menu = dao.create_menu(
        {
            "dish_name": f"{test_prefix}-mongo-menu",
            "category": "general",
            "description": "direct mongo dao",
            "price": 10.5,
            "restaurant_id": restaurant["restaurant_id"],
        }
    )
    tracker.track_mongo("menus", menu["menu_id"])
    assert dao.list_menus()
    assert dao.get_menu(menu["menu_id"])["dish_name"] == menu["dish_name"]

    table = dao.create_table(
        {
            "table_number": 12,
            "table_status": 1,
            "restaurant_id": restaurant["restaurant_id"],
        }
    )
    tracker.track_mongo("tables", table["table_id"])
    assert dao.list_tables()
    assert dao.get_table(table["table_id"])["table_number"] == 12

    order = dao.create_order(
        {
            "table_id": table["table_id"],
            "client_id": client_user["user_id"],
            "order_type": "pickup",
            "restaurant_id": restaurant["restaurant_id"],
        }
    )
    tracker.track_mongo("orders", order["order_id"])
    assert dao.get_order(order["order_id"])["order_type"] == "pickup"

    reservation = dao.create_reservation(
        {
            "table_id": table["table_id"],
            "client_id": client_user["user_id"],
            "reservation_date": "2026-05-06T18:00:00",
            "reservation_status": 1,
        }
    )
    tracker.track_mongo("reservations", reservation["reservation_id"])
    assert dao.get_reservation(reservation["reservation_id"])["client_id"] == client_user["user_id"]

    updated_menu = dao.update_menu(menu["menu_id"], {"price": 11.0})
    assert updated_menu["price"] == 11.0
    updated_table = dao.update_table(table["table_id"], {"table_status": 2})
    assert updated_table["table_status"] == 2
    updated_user = dao.update_user(client_user["user_id"], {"user_name": f"{test_prefix}-mongo-client-2"})
    assert updated_user["user_name"].endswith("client-2")
    updated_restaurant = dao.update_restaurant(restaurant["restaurant_id"], {"restaurant_status": 2})
    assert updated_restaurant["restaurant_status"] == 2

    assert dao.delete_reservation(reservation["reservation_id"]) is True
    assert dao.delete_table(table["table_id"]) is True
    assert dao.delete_menu(menu["menu_id"]) is True
    assert dao.delete_restaurant(restaurant["restaurant_id"]) is True
    assert dao.delete_user(client_user["user_id"]) is True


@pytest.mark.integration
def test_mongo_dao_conflicts_and_missing_paths(mongo_db, tracker, test_prefix):
    dao = MongoDAO(mongo_db)
    role = dao.get_role_by_name("admin")

    admin_user = dao.create_user(
        {
            "user_name": f"{test_prefix}-mongo-conflict-admin",
            "keycloak_id": f"{test_prefix}-mongo-conflict-admin-keycloak",
            "role_id": role["role_id"],
        }
    )
    tracker.track_mongo("users", admin_user["user_id"])

    restaurant = dao.create_restaurant(
        {
            "restaurant_name": f"{test_prefix}-mongo-conflict-restaurant",
            "admin_id": admin_user["user_id"],
            "restaurant_status": 1,
        }
    )
    tracker.track_mongo("restaurants", restaurant["restaurant_id"])

    menu = dao.create_menu(
        {
            "dish_name": f"{test_prefix}-mongo-conflict-menu",
            "category": "general",
            "description": "dup",
            "price": 5.0,
            "restaurant_id": restaurant["restaurant_id"],
        }
    )
    tracker.track_mongo("menus", menu["menu_id"])

    with pytest.raises(DAOConflictError):
        dao.create_menu(
            {
                "dish_name": menu["dish_name"],
                "category": "general",
                "description": "dup",
                "price": 5.0,
                "restaurant_id": restaurant["restaurant_id"],
            }
        )

    assert dao.update_user(999999, {"user_name": "ghost"}) is None
    assert dao.delete_reservation(999999) is False
    assert dao.get_restaurant(999999) is None


@pytest.mark.integration
def test_postgres_dao_crud_with_real_database(postgres_session_factory, tracker, test_prefix, postgres_direct_status):
    available, reason = postgres_direct_status
    if not available:
        pytest.skip(f"Conexion directa a PostgreSQL no disponible en este host: {reason}")

    session = postgres_session_factory()
    dao = PostgresDAO(session)

    try:
        admin_role = dao.get_role_by_name("admin")
        client_role = dao.get_role_by_name("client")
        assert isinstance(admin_role, Role)
        assert "admin" in repr(admin_role)

        admin_user = dao.create_user(
            {
                "user_name": f"{test_prefix}-pg-admin",
                "keycloak_id": f"{test_prefix}-pg-admin-keycloak",
                "role_id": admin_role.role_id,
            }
        )
        tracker.track_postgres("users", admin_user.user_id)

        client_user = dao.create_user(
            {
                "user_name": f"{test_prefix}-pg-client",
                "keycloak_id": f"{test_prefix}-pg-client-keycloak",
                "role_id": client_role.role_id,
            }
        )
        tracker.track_postgres("users", client_user.user_id)
        assert "pg-client" in repr(client_user)

        restaurant = dao.create_restaurant(
            {
                "restaurant_name": f"{test_prefix}-pg-restaurant",
                "admin_id": admin_user.user_id,
                "restaurant_status": 1,
            }
        )
        tracker.track_postgres("restaurants", restaurant.restaurant_id)
        assert "pg-restaurant" in repr(restaurant)
        assert dao.list_restaurants()
        assert dao.get_restaurant(restaurant.restaurant_id).restaurant_id == restaurant.restaurant_id

        menu = dao.create_menu(
            {
                "dish_name": f"{test_prefix}-pg-menu",
                "category": "general",
                "description": "direct postgres dao",
                "price": 19.5,
                "restaurant_id": restaurant.restaurant_id,
            }
        )
        tracker.track_postgres("menus", menu.menu_id)
        assert "pg-menu" in repr(menu)
        assert dao.list_menus()
        assert dao.get_menu(menu.menu_id).menu_id == menu.menu_id

        table = dao.create_table(
            {
                "table_number": 8,
                "table_status": 1,
                "restaurant_id": restaurant.restaurant_id,
            }
        )
        tracker.track_postgres("tables", table.table_id)
        assert isinstance(table, Table)
        assert dao.list_tables()
        assert dao.get_table(table.table_id).table_number == 8

        order = dao.create_order(
            {
                "table_id": table.table_id,
                "client_id": client_user.user_id,
                "order_type": "delivery",
                "restaurant_id": restaurant.restaurant_id,
            }
        )
        tracker.track_postgres("orders", order.order_id)
        assert dao.get_order(order.order_id).order_type == "delivery"

        reservation = dao.create_reservation(
            {
                "table_id": table.table_id,
                "client_id": client_user.user_id,
                "reservation_date": "2026-05-06 18:00:00",
                "reservation_status": 1,
            }
        )
        tracker.track_postgres("reservations", reservation.reservation_id)
        assert dao.get_reservation(reservation.reservation_id).client_id == client_user.user_id

        updated_restaurant = dao.update_restaurant(restaurant.restaurant_id, {"restaurant_status": 2})
        assert updated_restaurant.restaurant_status == 2
        updated_menu = dao.update_menu(menu.menu_id, {"price": 20.0})
        assert float(updated_menu.price) == 20.0
        updated_table = dao.update_table(table.table_id, {"table_status": 2})
        assert updated_table.table_status == 2
        updated_user = dao.update_user(client_user.user_id, {"user_name": f"{test_prefix}-pg-client-2"})
        assert updated_user.user_name.endswith("client-2")

        assert dao.get_user(client_user.user_id).user_id == client_user.user_id
        assert dao.get_user_by_username(updated_user.user_name).user_id == client_user.user_id
        assert dao.get_user_by_keycloak_id(client_user.keycloak_id).user_id == client_user.user_id
        assert field_value({"role_name": "admin"}, "role_name") == "admin"
        assert field_value(updated_user, "user_name") == updated_user.user_name

        assert dao.delete_reservation(reservation.reservation_id) is True
        session.delete(order)
        session.commit()
        assert dao.delete_table(table.table_id) is True
        assert dao.delete_menu(menu.menu_id) is True
        assert dao.delete_restaurant(restaurant.restaurant_id) is True
        assert dao.delete_user(client_user.user_id) is True
    finally:
        session.close()


@pytest.mark.integration
def test_postgres_dao_conflicts_and_missing_paths(postgres_session_factory, tracker, test_prefix, postgres_direct_status):
    available, reason = postgres_direct_status
    if not available:
        pytest.skip(f"Conexion directa a PostgreSQL no disponible en este host: {reason}")

    session = postgres_session_factory()
    dao = PostgresDAO(session)

    try:
        role = dao.get_role_by_name("admin")
        admin_user = dao.create_user(
            {
                "user_name": f"{test_prefix}-pg-conflict-admin",
                "keycloak_id": f"{test_prefix}-pg-conflict-admin-keycloak",
                "role_id": role.role_id,
            }
        )
        tracker.track_postgres("users", admin_user.user_id)

        restaurant = dao.create_restaurant(
            {
                "restaurant_name": f"{test_prefix}-pg-conflict-restaurant",
                "admin_id": admin_user.user_id,
                "restaurant_status": 1,
            }
        )
        tracker.track_postgres("restaurants", restaurant.restaurant_id)

        menu = dao.create_menu(
            {
                "dish_name": f"{test_prefix}-pg-conflict-menu",
                "category": "general",
                "description": "dup",
                "price": 7.5,
                "restaurant_id": restaurant.restaurant_id,
            }
        )
        tracker.track_postgres("menus", menu.menu_id)

        with pytest.raises(DAOConflictError):
            dao.create_menu(
                {
                    "dish_name": menu.dish_name,
                    "category": "general",
                    "description": "dup",
                    "price": 7.5,
                    "restaurant_id": restaurant.restaurant_id,
                }
            )

        assert dao.update_restaurant(999999, {"restaurant_status": 2}) is None
        assert dao.delete_restaurant(999999) is False
        assert dao.get_user(999999) is None
    finally:
        session.close()


@pytest.mark.integration
def test_postgres_dao_mocked_compatibility_paths(postgres_direct_status):
    available, _ = postgres_direct_status
    if available:
        pytest.skip("La conexion directa a PostgreSQL esta disponible; se usa la integracion real.")

    db = Mock()
    dao = PostgresDAO(db)

    restaurant = dao.create_restaurant(
        {"restaurant_name": "Compat", "admin_id": 1, "restaurant_status": 1}
    )
    menu = dao.create_menu(
        {"dish_name": "Compat menu", "category": "general", "description": "d", "price": 1, "restaurant_id": 1}
    )
    table = dao.create_table({"table_number": 4, "table_status": 1, "restaurant_id": 1})
    order = dao.create_order({"table_id": 1, "client_id": 1, "order_type": "pickup", "restaurant_id": 1})
    reservation = dao.create_reservation(
        {"table_id": 1, "client_id": 1, "reservation_date": "2026-05-06 18:00:00", "reservation_status": 1}
    )
    user = dao.create_user({"user_name": "compat-user", "role_id": 2, "keycloak_id": "compat-keycloak"})

    assert "Compat" in repr(restaurant)
    assert "Compat menu" in repr(menu)
    assert isinstance(table, Table)
    assert isinstance(order, Order)
    assert isinstance(reservation, Reservation)
    assert isinstance(user, User)

    db.query.return_value.filter.return_value.first.side_effect = [
        restaurant,
        restaurant,
        menu,
        menu,
        table,
        table,
        user,
        user,
        user,
        order,
        reservation,
        reservation,
        Role(role_id=1, role_name="admin"),
    ]

    assert dao.list_restaurants() == db.query.return_value.all.return_value
    assert dao.get_restaurant(1) is restaurant
    assert dao.update_restaurant(1, {"restaurant_status": 2}).restaurant_status == 2
    assert dao.delete_restaurant(1) is True

    assert dao.get_menu(1) is menu
    assert float(dao.update_menu(1, {"price": 2}).price) == 2
    assert dao.delete_menu(1) is True

    assert dao.get_table(1) is table
    assert dao.update_table(1, {"table_status": 2}).table_status == 2
    assert dao.delete_table(1) is True

    assert dao.get_user(1) is user
    assert dao.get_user_by_username("compat-user") is user
    assert dao.get_user_by_keycloak_id("compat-keycloak") is user
    assert dao.update_user(1, {"user_name": "compat-user-2"}).user_name == "compat-user-2"
    assert dao.delete_user(1) is True

    assert dao.get_order(1) is order
    assert dao.get_reservation(1) is reservation
    assert dao.delete_reservation(1) is True
    assert dao.get_role_by_name("admin").role_name == "admin"
    assert field_value({"name": "x"}, "name") == "x"
    assert field_value(user, "user_name") == "compat-user-2"


@pytest.mark.integration
def test_postgres_dao_mocked_conflict_paths(postgres_direct_status):
    available, _ = postgres_direct_status
    if available:
        pytest.skip("La conexion directa a PostgreSQL esta disponible; se usa la integracion real.")

    db = Mock()
    dao = PostgresDAO(db)
    row = Menu()
    row.price = 1
    db.query.return_value.filter.return_value.first.return_value = row
    db.commit.side_effect = IntegrityError("", "", "")

    with pytest.raises(DAOConflictError):
        dao.create_menu({"dish_name": "dup", "category": "general", "description": "d", "price": 1, "restaurant_id": 1})

    db.commit.side_effect = IntegrityError("", "", "")
    with pytest.raises(DAOConflictError):
        dao.update_menu(1, {"price": 2})

    db.rollback.assert_called()

    db.commit.side_effect = None
    db.query.return_value.filter.return_value.first.return_value = None
    assert dao.update_restaurant(999, {"restaurant_status": 0}) is None
    assert dao.delete_restaurant(999) is False
