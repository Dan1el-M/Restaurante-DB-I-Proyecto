from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument
from sqlalchemy.exc import IntegrityError

from backend.models.menus import Menu
from backend.models.order_items import OrderItem
from backend.models.orders import Order
from backend.models.reservations import Reservation
from backend.models.restaurants import Restaurant
from backend.models.roles import Role
from backend.models.tables import Table
from backend.models.users import User

'''
A este archivo no se le podria aplicar SOLID?
o ya lo tiene?
'''

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
        self._restaurant_cache: dict[int, Restaurant | None] = {}
        self._menu_cache: dict[int, Menu | None] = {}
        self._table_cache: dict[int, Table | None] = {}
        self._user_cache: dict[int, User] = {}

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
        restaurant = self.db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
        self._restaurant_cache[restaurant_id] = restaurant
        return restaurant

    def create_restaurant(self, data: dict):
        return self._create(Restaurant, data)

    def update_restaurant(self, restaurant_id: int, data: dict):
        row = self.get_restaurant(restaurant_id)
        return self._update(row, data) if row else None

    def delete_restaurant(self, restaurant_id: int):
        if restaurant_id in self._restaurant_cache:
            cached = self._restaurant_cache.pop(restaurant_id)
            if cached is None:
                return False
            self.db.delete(cached)
            self.db.commit()
            return True

        deleted = (
            self.db.query(Restaurant)
            .filter(Restaurant.restaurant_id == restaurant_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        if isinstance(deleted, int):
            return deleted > 0
        return bool(deleted)

    def list_menus(self):
        return self.db.query(Menu).all()

    def get_menu(self, menu_id: int):
        menu = self.db.query(Menu).filter(Menu.menu_id == menu_id).first()
        self._menu_cache[menu_id] = menu
        return menu

    def create_menu(self, data: dict):
        return self._create(Menu, data)

    def update_menu(self, menu_id: int, data: dict):
        row = self.get_menu(menu_id)
        return self._update(row, data) if row else None

    def delete_menu(self, menu_id: int):
        if menu_id in self._menu_cache:
            cached = self._menu_cache.pop(menu_id)
        else:
            cached = self.get_menu(menu_id)
            self._menu_cache.pop(menu_id, None)

        if cached is None:
            return False
        self.db.delete(cached)
        self.db.commit()
        return True

    def list_tables(self):
        return self.db.query(Table).all()

    def get_table(self, table_id: int):
        table = self.db.query(Table).filter(Table.table_id == table_id).first()
        self._table_cache[table_id] = table
        return table

    def create_table(self, data: dict):
        return self._create(Table, data)

    def update_table(self, table_id: int, data: dict):
        row = self.get_table(table_id)
        return self._update(row, data) if row else None

    def delete_table(self, table_id: int):
        if table_id in self._table_cache:
            cached = self._table_cache.pop(table_id)
        else:
            cached = self.get_table(table_id)
            self._table_cache.pop(table_id, None)

        if cached is None:
            return False
        self.db.delete(cached)
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
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if user is not None:
            self._user_cache[user_id] = user
        return user

    def get_user_by_username(self, username: str):
        return self.db.query(User).filter(User.user_name == username).first()

    def get_user_by_keycloak_id(self, keycloak_id: str):
        return self.db.query(User).filter(User.keycloak_id == keycloak_id).first()

    def create_user(self, data: dict):
        return self._create(User, data)

    def update_user(self, user_id: int, data: dict):
        row = self._user_cache.get(user_id)
        if row is None:
            row = self.get_user(user_id)
        return self._update(row, data) if row else None

    def delete_user(self, user_id: int):
        deleted = (
            self.db.query(User)
            .filter(User.user_id == user_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        self._user_cache.pop(user_id, None)
        if isinstance(deleted, int):
            return deleted > 0
        return bool(deleted)

    def get_role_by_name(self, role_name: str):
        return self.db.query(Role).filter(Role.role_name == role_name).first()

    def list_roles(self):
        return self.db.query(Role).all()

    def list_users(self):
        return self.db.query(User).all()

    def list_orders(self):
        return self.db.query(Order).all()

    def list_order_items(self):
        return self.db.query(OrderItem).all()


class MongoDAO(BaseDAO):
    id_fields = {
        "roles": "role_id",
        "users": "user_id",
        "restaurants": "restaurant_id",
        "menus": "menu_id",
        "tables": "table_id",
        "orders": "order_id",
        "order_items": "order_item_id",
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

    def list_roles(self):
        return self._list("roles")

    def list_users(self):
        return self._list("users")

    def list_orders(self):
        return self._list("orders")

    def list_order_items(self):
        return self._list("order_items")
