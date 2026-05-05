"""Cobertura unitaria adicional para DAOs sin servicios externos."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pymongo.errors import DuplicateKeyError
from sqlalchemy.exc import IntegrityError

from backend.dao import DAOConflictError, MongoDAO, PostgresDAO
from backend.models.menus import Menu
from backend.models.order_items import OrderItem
from backend.models.orders import Order
from backend.models.reservations import Reservation
from backend.models.roles import Role
from backend.models.tables import Table
from backend.models.users import User


@pytest.mark.parametrize(
    ("model", "create_method", "update_method", "delete_method", "get_method", "id_value"),
    [
        (Menu, "create_menu", "update_menu", "delete_menu", "get_menu", 10),
        (Table, "create_table", "update_table", "delete_table", "get_table", 20),
        (User, "create_user", "update_user", "delete_user", "get_user", 30),
    ],
)
def test_postgres_crud_helpers_for_common_models(model, create_method, update_method, delete_method, get_method, id_value):
    db = Mock()
    dao = PostgresDAO(db)
    row = model()
    db.query.return_value.filter.return_value.first.return_value = row

    created = getattr(dao, create_method)({})
    updated = getattr(dao, update_method)(id_value, {"marker": "updated"})
    deleted = getattr(dao, delete_method)(id_value)
    found = getattr(dao, get_method)(id_value)

    assert isinstance(created, model)
    assert updated.marker == "updated"
    assert deleted is True
    assert found is row
    assert db.commit.call_count >= 3


def test_postgres_delete_returns_false_when_row_missing():
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = None
    dao = PostgresDAO(db)

    assert dao.delete_menu(999) is False
    assert dao.update_menu(999, {"dish_name": "Nada"}) is None


def test_postgres_order_and_reservation_methods():
    db = Mock()
    dao = PostgresDAO(db)
    order = Order()
    reservation = Reservation()
    db.query.return_value.filter.return_value.first.side_effect = [order, reservation, reservation]

    assert isinstance(dao.create_order({}), Order)
    assert dao.get_order(1) is order
    assert isinstance(dao.create_reservation({}), Reservation)
    assert dao.get_reservation(1) is reservation
    assert dao.delete_reservation(1) is True


def test_postgres_role_and_username_lookup_methods():
    db = Mock()
    dao = PostgresDAO(db)
    role = Role()
    user = User()
    db.query.return_value.filter.return_value.first.side_effect = [role, user, user]

    assert dao.get_role_by_name("admin") is role
    assert dao.get_user_by_username("ana") is user
    assert dao.get_user_by_keycloak_id("kc-1") is user


def test_postgres_update_conflict_rolls_back():
    db = Mock()
    row = Menu()
    db.query.return_value.filter.return_value.first.return_value = row
    db.commit.side_effect = IntegrityError("", "", "")
    dao = PostgresDAO(db)

    with pytest.raises(DAOConflictError):
        dao.update_menu(1, {"dish_name": "Duplicado"})

    db.rollback.assert_called_once()


class FakeInsertResult:
    inserted_id = "mongo-id"


class FakeDeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class FakeUpdateResult:
    def __init__(self, matched_count):
        self.matched_count = matched_count


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = list(documents or [])
        self.insert_should_fail = False
        self.update_should_fail = False
        self.matched_count = 1
        self.deleted_count = 1

    def find(self):
        return list(self.documents)

    def find_one(self, query):
        id_field, value = next(iter(query.items()))
        for document in self.documents:
            if document.get(id_field) == value:
                return dict(document)
        return None

    def insert_one(self, document):
        if self.insert_should_fail:
            raise DuplicateKeyError("duplicate")
        self.documents.append(dict(document))
        return FakeInsertResult()

    def update_one(self, query, update):
        if self.update_should_fail:
            raise DuplicateKeyError("duplicate")
        document = self.find_one(query)
        if document:
            document.update(update["$set"])
        return FakeUpdateResult(self.matched_count)

    def delete_one(self, query):
        return FakeDeleteResult(self.deleted_count)


class FakeMongoDB:
    def __init__(self):
        self.collections = {
            "counters": Mock(),
            "restaurants": FakeCollection([{"_id": "x", "restaurant_id": 1, "restaurant_name": "R"}]),
            "menus": FakeCollection([{"menu_id": 1, "dish_name": "Pizza"}]),
            "tables": FakeCollection([{"table_id": 1, "table_number": 1}]),
            "orders": FakeCollection([{"order_id": 1}]),
            "reservations": FakeCollection([{"reservation_id": 1}]),
            "users": FakeCollection([{"user_id": 1, "user_name": "ana", "keycloak_id": "kc-1"}]),
            "roles": FakeCollection([{"role_id": 1, "role_name": "admin"}]),
        }
        self.collections["counters"].find_one_and_update.return_value = {"seq": 99}
        self.counters = self.collections["counters"]
        self.users = self.collections["users"]
        self.roles = self.collections["roles"]

    def __getitem__(self, name):
        return self.collections[name]


def test_mongo_restaurant_crud_and_cleaning():
    db = FakeMongoDB()
    dao = MongoDAO(db)

    assert dao.list_restaurants() == [{"restaurant_id": 1, "restaurant_name": "R"}]
    assert dao.get_restaurant(1) == {"restaurant_id": 1, "restaurant_name": "R"}
    assert dao.create_restaurant({"restaurant_name": "Nuevo"}) == {
        "restaurant_id": 99,
        "restaurant_name": "Nuevo",
    }
    assert dao.update_restaurant(1, {"restaurant_name": "Editado"}) == {
        "restaurant_id": 1,
        "restaurant_name": "R",
    }
    assert dao.delete_restaurant(1) is True
    assert dao.get_restaurant(404) is None


@pytest.mark.parametrize(
    ("list_method", "get_method", "create_method", "update_method", "delete_method", "id_value"),
    [
        ("list_menus", "get_menu", "create_menu", "update_menu", "delete_menu", 1),
        ("list_tables", "get_table", "create_table", "update_table", "delete_table", 1),
    ],
)
def test_mongo_common_collection_methods(list_method, get_method, create_method, update_method, delete_method, id_value):
    dao = MongoDAO(FakeMongoDB())

    assert getattr(dao, list_method)()
    assert getattr(dao, get_method)(id_value)
    assert getattr(dao, create_method)({})
    assert getattr(dao, update_method)(id_value, {"value": "x"})
    assert getattr(dao, delete_method)(id_value) is True


def test_mongo_order_reservation_user_and_role_methods():
    dao = MongoDAO(FakeMongoDB())

    assert dao.get_order(1) == {"order_id": 1}
    assert dao.create_order({}) == {"order_id": 99}
    assert dao.get_reservation(1) == {"reservation_id": 1}
    assert dao.create_reservation({}) == {"reservation_id": 99}
    assert dao.delete_reservation(1) is True
    assert dao.get_user(1)["user_name"] == "ana"
    assert dao.get_user_by_username("ana")["keycloak_id"] == "kc-1"
    assert dao.get_user_by_keycloak_id("kc-1")["user_id"] == 1
    assert dao.create_user({"user_name": "new"}) == {"user_id": 99, "user_name": "new"}
    assert dao.update_user(1, {"user_name": "edit"})
    assert dao.delete_user(1) is True
    assert dao.get_role_by_name("admin")["role_id"] == 1


def test_mongo_conflict_and_not_found_paths():
    db = FakeMongoDB()
    dao = MongoDAO(db)
    db["menus"].insert_should_fail = True
    db["tables"].update_should_fail = True
    db["users"].matched_count = 0
    db["reservations"].deleted_count = 0

    with pytest.raises(DAOConflictError):
        dao.create_menu({})
    with pytest.raises(DAOConflictError):
        dao.update_table(1, {})

    assert dao.update_user(1, {}) is None
    assert dao.delete_reservation(1) is False
