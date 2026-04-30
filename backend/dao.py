from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument
from sqlalchemy.exc import IntegrityError

from backend.models.menus import Menu
from backend.models.orders import Order
from backend.models.reservations import Reservation
from backend.models.restaurants import Restaurant
from backend.models.roles import Role
from backend.models.tables import Table
from backend.models.users import User


class DAOConflictError(Exception):
    pass


def field_value(row, field_name: str):
    if isinstance(row, dict):
        return row.get(field_name)
    return getattr(row, field_name)


class BaseDAO:
    def list_restaurants(self):
        raise NotImplementedError

    def get_restaurant(self, restaurant_id: int):
        raise NotImplementedError

    def create_restaurant(self, data: dict):
        raise NotImplementedError

    def update_restaurant(self, restaurant_id: int, data: dict):
        raise NotImplementedError

    def delete_restaurant(self, restaurant_id: int):
        raise NotImplementedError


class PostgresDAO(BaseDAO):
    def __init__(self, db):
        self.db = db

    def _create(self, model, data):
        row = model(**data)
        self.db.add(row)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DAOConflictError() from exc
        self.db.refresh(row)
        return row

    def _update(self, row, data):
        for field, value in data.items():
            setattr(row, field, value)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DAOConflictError() from exc
        self.db.refresh(row)
        return row

    def list_restaurants(self):
        return self.db.query(Restaurant).all()

    def get_restaurant(self, restaurant_id: int):
        return self.db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()

    def create_restaurant(self, data: dict):
        return self._create(Restaurant, data)

    def update_restaurant(self, restaurant_id: int, data: dict):
        row = self.get_restaurant(restaurant_id)
        return self._update(row, data) if row else None

    def delete_restaurant(self, restaurant_id: int):
        row = self.get_restaurant(restaurant_id)
        if not row:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    def list_menus(self):
        return self.db.query(Menu).all()

    def get_menu(self, menu_id: int):
        return self.db.query(Menu).filter(Menu.menu_id == menu_id).first()

    def create_menu(self, data: dict):
        return self._create(Menu, data)

    def update_menu(self, menu_id: int, data: dict):
        row = self.get_menu(menu_id)
        return self._update(row, data) if row else None

    def delete_menu(self, menu_id: int):
        row = self.get_menu(menu_id)
        if not row:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    def list_tables(self):
        return self.db.query(Table).all()

    def get_table(self, table_id: int):
        return self.db.query(Table).filter(Table.table_id == table_id).first()

    def create_table(self, data: dict):
        return self._create(Table, data)

    def update_table(self, table_id: int, data: dict):
        row = self.get_table(table_id)
        return self._update(row, data) if row else None

    def delete_table(self, table_id: int):
        row = self.get_table(table_id)
        if not row:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    def get_order(self, order_id: int):
        return self.db.query(Order).filter(Order.order_id == order_id).first()

    def create_order(self, data: dict):
        return self._create(Order, data)

    def get_reservation(self, reservation_id: int):
        return self.db.query(Reservation).filter(Reservation.reservation_id == reservation_id).first()

    def create_reservation(self, data: dict):
        return self._create(Reservation, data)

    def delete_reservation(self, reservation_id: int):
        row = self.get_reservation(reservation_id)
        if not row:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    def get_user(self, user_id: int):
        return self.db.query(User).filter(User.user_id == user_id).first()

    def get_user_by_username(self, username: str):
        return self.db.query(User).filter(User.user_name == username).first()

    def get_user_by_keycloak_id(self, keycloak_id: str):
        return self.db.query(User).filter(User.keycloak_id == keycloak_id).first()

    def create_user(self, data: dict):
        return self._create(User, data)

    def update_user(self, user_id: int, data: dict):
        row = self.get_user(user_id)
        return self._update(row, data) if row else None

    def delete_user(self, user_id: int):
        row = self.get_user(user_id)
        if not row:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    def get_role_by_name(self, role_name: str):
        return self.db.query(Role).filter(Role.role_name == role_name).first()


class MongoDAO(BaseDAO):
    id_fields = {
        "roles": "role_id",
        "users": "user_id",
        "restaurants": "restaurant_id",
        "menus": "menu_id",
        "tables": "table_id",
        "orders": "order_id",
        "reservations": "reservation_id",
    }

    def __init__(self, db):
        self.db = db

    def _next_id(self, collection_name: str):
        counter = self.db.counters.find_one_and_update(
            {"_id": collection_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return counter["seq"]

    def _clean(self, document):
        if not document:
            return None
        document = dict(document)
        document.pop("_id", None)
        return document

    def _list(self, collection_name: str):
        return [self._clean(doc) for doc in self.db[collection_name].find()]

    def _get(self, collection_name: str, value: int):
        id_field = self.id_fields[collection_name]
        return self._clean(self.db[collection_name].find_one({id_field: value}))

    def _create(self, collection_name: str, data: dict):
        id_field = self.id_fields[collection_name]
        document = dict(data)
        document[id_field] = self._next_id(collection_name)
        try:
            self.db[collection_name].insert_one(document)
        except DuplicateKeyError as exc:
            raise DAOConflictError() from exc
        return self._clean(document)

    def _update(self, collection_name: str, value: int, data: dict):
        id_field = self.id_fields[collection_name]
        try:
            result = self.db[collection_name].update_one({id_field: value}, {"$set": data})
        except DuplicateKeyError as exc:
            raise DAOConflictError() from exc
        if result.matched_count == 0:
            return None
        return self._get(collection_name, value)

    def _delete(self, collection_name: str, value: int):
        id_field = self.id_fields[collection_name]
        return self.db[collection_name].delete_one({id_field: value}).deleted_count > 0

    def list_restaurants(self):
        return self._list("restaurants")

    def get_restaurant(self, restaurant_id: int):
        return self._get("restaurants", restaurant_id)

    def create_restaurant(self, data: dict):
        return self._create("restaurants", data)

    def update_restaurant(self, restaurant_id: int, data: dict):
        return self._update("restaurants", restaurant_id, data)

    def delete_restaurant(self, restaurant_id: int):
        return self._delete("restaurants", restaurant_id)

    def list_menus(self):
        return self._list("menus")

    def get_menu(self, menu_id: int):
        return self._get("menus", menu_id)

    def create_menu(self, data: dict):
        return self._create("menus", data)

    def update_menu(self, menu_id: int, data: dict):
        return self._update("menus", menu_id, data)

    def delete_menu(self, menu_id: int):
        return self._delete("menus", menu_id)

    def list_tables(self):
        return self._list("tables")

    def get_table(self, table_id: int):
        return self._get("tables", table_id)

    def create_table(self, data: dict):
        return self._create("tables", data)

    def update_table(self, table_id: int, data: dict):
        return self._update("tables", table_id, data)

    def delete_table(self, table_id: int):
        return self._delete("tables", table_id)

    def get_order(self, order_id: int):
        return self._get("orders", order_id)

    def create_order(self, data: dict):
        return self._create("orders", data)

    def get_reservation(self, reservation_id: int):
        return self._get("reservations", reservation_id)

    def create_reservation(self, data: dict):
        return self._create("reservations", data)

    def delete_reservation(self, reservation_id: int):
        return self._delete("reservations", reservation_id)

    def get_user(self, user_id: int):
        return self._get("users", user_id)

    def get_user_by_username(self, username: str):
        return self._clean(self.db.users.find_one({"user_name": username}))

    def get_user_by_keycloak_id(self, keycloak_id: str):
        return self._clean(self.db.users.find_one({"keycloak_id": keycloak_id}))

    def create_user(self, data: dict):
        return self._create("users", data)

    def update_user(self, user_id: int, data: dict):
        return self._update("users", user_id, data)

    def delete_user(self, user_id: int):
        return self._delete("users", user_id)

    def get_role_by_name(self, role_name: str):
        return self._clean(self.db.roles.find_one({"role_name": role_name}))
