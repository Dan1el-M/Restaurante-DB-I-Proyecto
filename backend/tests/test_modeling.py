import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_modeling_pytest.db")
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.database import Base, SessionLocal, engine  # noqa: E402
from backend.models import Menu, Order, OrderItem, Reservation, Restaurant, Role, Table, User  # noqa: E402


def enable_sqlite_foreign_keys(session) -> None:
    if session.bind is not None and session.bind.dialect.name == "sqlite":
        session.execute(text("PRAGMA foreign_keys=ON"))


@pytest.fixture(autouse=True)
def reset_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def seeded_data():
    session = SessionLocal()
    enable_sqlite_foreign_keys(session)

    role_admin = Role(role_name="admin")
    role_client = Role(role_name="cliente")
    session.add_all([role_admin, role_client])
    session.flush()

    admin = User(user_name="admin_1", role_id=role_admin.role_id)
    client = User(user_name="cliente_1", role_id=role_client.role_id)
    session.add_all([admin, client])
    session.flush()

    restaurant = Restaurant(
        restaurant_name="Resto Demo",
        admin_id=admin.user_id,
        restaurant_status=1,
    )
    session.add(restaurant)
    session.flush()

    table = Table(table_number=1, table_status=1, restaurant_id=restaurant.restaurant_id)
    menu = Menu(dish_name="Pasta Alfredo", price=12.50, restaurant_id=restaurant.restaurant_id)
    session.add_all([table, menu])
    session.flush()

    session.commit()

    return {
        "restaurant_id": restaurant.restaurant_id,
        "table_id": table.table_id,
        "menu_id": menu.menu_id,
        "client_id": client.user_id,
    }


def test_mappers_configure_without_errors():
    configure_mappers()


def test_valid_relationship_inserts(seeded_data):
    session = SessionLocal()
    enable_sqlite_foreign_keys(session)

    order = Order(
        table_id=seeded_data["table_id"],
        client_id=seeded_data["client_id"],
        order_type="in_place",
        restaurant_id=seeded_data["restaurant_id"],
    )
    session.add(order)
    session.flush()

    item = OrderItem(
        order_id=order.order_id,
        menu_id=seeded_data["menu_id"],
        quantity=2,
        price=25.00,
    )
    reservation = Reservation(
        table_id=seeded_data["table_id"],
        client_id=seeded_data["client_id"],
        reservation_date=datetime(2026, 4, 21, 12, 0, 0),
        reservation_status=1,
    )

    session.add_all([item, reservation])
    session.commit()

    assert order.order_id is not None


def test_unique_table_per_restaurant(seeded_data):
    session = SessionLocal()
    enable_sqlite_foreign_keys(session)

    duplicate = Table(
        table_number=1,
        table_status=1,
        restaurant_id=seeded_data["restaurant_id"],
    )
    session.add(duplicate)

    with pytest.raises(IntegrityError):
        session.commit()


def test_unique_dish_per_restaurant(seeded_data):
    session = SessionLocal()
    enable_sqlite_foreign_keys(session)

    duplicate = Menu(
        dish_name="Pasta Alfredo",
        price=15.00,
        restaurant_id=seeded_data["restaurant_id"],
    )
    session.add(duplicate)

    with pytest.raises(IntegrityError):
        session.commit()


def test_invalid_client_fk_in_order(seeded_data):
    session = SessionLocal()
    enable_sqlite_foreign_keys(session)

    bad_order = Order(
        table_id=seeded_data["table_id"],
        client_id=999999,
        order_type="takeaway",
        restaurant_id=seeded_data["restaurant_id"],
    )
    session.add(bad_order)

    with pytest.raises(IntegrityError):
        session.commit()
