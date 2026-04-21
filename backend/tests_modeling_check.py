"""Smoke tests para validar relaciones y constraints del modelado ORM.

Uso:
    DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname \
    python backend/tests_modeling_check.py
o
    DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname \
    python -m backend.tests_modeling_check

Notas:
- El script NO se ejecuta solo; se lanza manualmente.
- Por defecto, hace reset del esquema (drop/create) antes de probar.
- Si quieres conservar datos, usa --no-reset.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers

# Permite ejecutar el archivo directo: `python backend/tests_modeling_check.py`
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.database import Base, SessionLocal, engine
from backend.models import Menu, Order, OrderItem, Reservation, Restaurant, Role, Table, User


def _enable_sqlite_foreign_keys(session) -> None:
    """Activa FK enforcement en SQLite para que fallen inserciones inválidas."""
    dialect = session.bind.dialect.name if session.bind is not None else ""
    if dialect == "sqlite":
        session.execute(text("PRAGMA foreign_keys=ON"))


def _expect_integrity_error(action, expected_label: str) -> bool:
    """Ejecuta una acción y confirma que lance IntegrityError."""
    try:
        action()
        print(f"❌ FAIL: no falló la restricción esperada: {expected_label}")
        return False
    except IntegrityError:
        print(f"✅ PASS: restricción detectada correctamente -> {expected_label}")
        return True


def run_checks(reset_schema: bool = True) -> int:
    print("== Validando mappers ==")
    configure_mappers()
    print("✅ PASS: mappers SQLAlchemy configurados")

    if reset_schema:
        print("== Reiniciando esquema (drop/create) ==")
        Base.metadata.drop_all(bind=engine)
    print("== Creando esquema ==")
    Base.metadata.create_all(bind=engine)
    print("✅ PASS: tablas creadas")

    session = SessionLocal()
    passed = True

    try:
        _enable_sqlite_foreign_keys(session)

        # Datos base válidos
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

        table_ok = Table(table_number=1, table_status=1, restaurant_id=restaurant.restaurant_id)
        session.add(table_ok)

        menu_ok = Menu(
            dish_name="Pasta Alfredo",
            price=12.50,
            restaurant_id=restaurant.restaurant_id,
        )
        session.add(menu_ok)
        session.flush()

        order_ok = Order(
            table_id=table_ok.table_id,
            client_id=client.user_id,
            order_type="in_place",
            restaurant_id=restaurant.restaurant_id,
        )
        session.add(order_ok)
        session.flush()

        order_item_ok = OrderItem(
            order_id=order_ok.order_id,
            menu_id=menu_ok.menu_id,
            quantity=2,
            price=25.00,
        )
        session.add(order_item_ok)

        reservation_ok = Reservation(
            table_id=table_ok.table_id,
            client_id=client.user_id,
            reservation_date=datetime(2026, 4, 20, 10, 0, 0),
            reservation_status=1,
        )
        session.add(reservation_ok)
        session.commit()
        print("✅ PASS: inserciones válidas con relaciones correctas")

        # Unique: table_number por restaurante
        def dup_table_same_restaurant():
            s = SessionLocal()
            try:
                _enable_sqlite_foreign_keys(s)
                dup = Table(table_number=1, table_status=1, restaurant_id=restaurant.restaurant_id)
                s.add(dup)
                s.commit()
            finally:
                s.rollback()
                s.close()

        passed = _expect_integrity_error(dup_table_same_restaurant, "unique_table_per_restaurant") and passed

        # Unique: dish_name por restaurante
        def dup_menu_same_restaurant():
            s = SessionLocal()
            try:
                _enable_sqlite_foreign_keys(s)
                dup = Menu(dish_name="Pasta Alfredo", price=13.00, restaurant_id=restaurant.restaurant_id)
                s.add(dup)
                s.commit()
            finally:
                s.rollback()
                s.close()

        passed = _expect_integrity_error(dup_menu_same_restaurant, "unique_dish_per_restaurant") and passed

        # FK inválida: client_id en orders
        def invalid_order_client_fk():
            s = SessionLocal()
            try:
                _enable_sqlite_foreign_keys(s)
                bad = Order(
                    table_id=table_ok.table_id,
                    client_id=999999,
                    order_type="takeaway",
                    restaurant_id=restaurant.restaurant_id,
                )
                s.add(bad)
                s.commit()
            finally:
                s.rollback()
                s.close()

        passed = _expect_integrity_error(invalid_order_client_fk, "FK orders.client_id -> users.user_id") and passed

    finally:
        session.close()

    if passed:
        print("\n🎉 RESULTADO FINAL: TODO OK")
        return 0

    print("\n⚠️ RESULTADO FINAL: HAY FALLOS")
    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida relaciones y constraints del modelado ORM")
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="No hacer drop/create del esquema antes de probar",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    sys.exit(run_checks(reset_schema=not args.no_reset))
