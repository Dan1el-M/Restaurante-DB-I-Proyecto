import os
import socket
import time
import uuid
from dataclasses import dataclass, field
from urllib.parse import urlparse, urlunparse

import pytest
import redis
import requests
import psycopg2
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from fastapi.testclient import TestClient
from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


load_dotenv()


def _is_tcp_reachable(host: str | None, port: int | None, timeout: float = 0.5) -> bool:
    if not host or not port:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _replace_url_host(url: str, new_host: str, new_port: int | None = None) -> str:
    parsed = urlparse(url)
    auth = ""
    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth = f"{auth}:{parsed.password}"
        auth = f"{auth}@"

    port_value = new_port if new_port is not None else parsed.port
    port = f":{port_value}" if port_value else ""
    netloc = f"{auth}{new_host}{port}"
    return urlunparse(parsed._replace(netloc=netloc))


def _prefer_localhost_if_needed(env_key: str, fallback_port: int) -> None:
    raw = os.getenv(env_key)
    if not raw:
        return

    parsed = urlparse(raw)
    if _is_tcp_reachable(parsed.hostname, parsed.port or fallback_port):
        return

    os.environ[env_key] = _replace_url_host(raw, "localhost", fallback_port)


_prefer_localhost_if_needed("KEYCLOAK_URL", 8001)
_prefer_localhost_if_needed("POSTGRES_URL", 5432)
_prefer_localhost_if_needed("MONGO_URL", 27017)
_prefer_localhost_if_needed("REDIS_URL", 6379)
_prefer_localhost_if_needed("ELASTICSEARCH_URL", 9200)


from backend.app.api_main import app as api_app
from backend.app.search_main import app as search_app
from backend.app.autentificador.keycloak_register_admin import get_admin_token
from backend.app.scripts.seed_admin import main as seed_admin_main
from backend.app.search.search_service import INDEX_NAME
from backend.models.menus import Menu
from backend.models.order_items import OrderItem
from backend.models.orders import Order
from backend.models.reservations import Reservation
from backend.models.restaurants import Restaurant
from backend.models.tables import Table
from backend.models.users import User


SERVICE_TIMEOUT_SECONDS = 180


def _wait_until(description: str, check, timeout: int = SERVICE_TIMEOUT_SECONDS) -> None:
    deadline = time.time() + timeout
    last_error = None

    while time.time() < deadline:
        try:
            if check():
                return
        except Exception as exc:
            last_error = exc
        time.sleep(2)

    if last_error is not None:
        raise RuntimeError(f"{description} no estuvo listo: {last_error}") from last_error
    raise RuntimeError(f"{description} no estuvo listo a tiempo")


@dataclass
class ResourceTracker:
    mongo_ids: dict[str, set[int]] = field(
        default_factory=lambda: {
            "users": set(),
            "restaurants": set(),
            "menus": set(),
            "tables": set(),
            "orders": set(),
            "reservations": set(),
        }
    )
    postgres_ids: dict[str, set[int]] = field(
        default_factory=lambda: {
            "users": set(),
            "restaurants": set(),
            "menus": set(),
            "tables": set(),
            "orders": set(),
            "order_items": set(),
            "reservations": set(),
        }
    )
    keycloak_user_ids: set[str] = field(default_factory=set)

    def track_mongo(self, collection: str, value: int | None) -> None:
        if value is not None:
            self.mongo_ids[collection].add(value)

    def track_postgres(self, collection: str, value: int | None) -> None:
        if value is not None:
            self.postgres_ids[collection].add(value)

    def track_keycloak(self, value: str | None) -> None:
        if value:
            self.keycloak_user_ids.add(value)


def _delete_keycloak_user(user_id: str) -> None:
    token = get_admin_token()
    requests.delete(
        f"{os.environ['KEYCLOAK_URL']}/admin/realms/{os.environ['KEYCLOAK_REALM']}/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )


def _check_postgres_direct_connection() -> tuple[bool, str | None]:
    parsed = urlparse(os.environ["POSTGRES_URL"].replace("postgresql+psycopg2://", "postgresql://", 1))
    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            dbname=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
        )
        conn.close()
        return True, None
    except Exception as exc:
        return False, str(exc)


@pytest.fixture(scope="session", autouse=True)
def ensure_live_services_ready():
    keycloak_url = os.environ["KEYCLOAK_URL"]
    postgres_url = urlparse(os.environ["POSTGRES_URL"].replace("postgresql+psycopg2://", "postgresql://", 1))
    mongo_client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=3000)
    redis_client = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    es_client = Elasticsearch(os.environ["ELASTICSEARCH_URL"])

    _wait_until(
        "Keycloak",
        lambda: requests.get(f"{keycloak_url}/realms/master", timeout=5).status_code == 200,
    )
    _wait_until(
        "PostgreSQL",
        lambda: _is_tcp_reachable(postgres_url.hostname, postgres_url.port or 5432),
    )
    _wait_until(
        "MongoDB",
        lambda: mongo_client.admin.command("ping")["ok"] == 1.0,
    )
    _wait_until(
        "Redis",
        lambda: bool(redis_client.ping()),
    )
    _wait_until(
        "Elasticsearch",
        lambda: bool(es_client.ping()),
    )

    seed_admin_main()

    yield

    mongo_client.close()


@pytest.fixture(scope="session")
def mongo_db():
    client = MongoClient(os.environ["MONGO_URL"])
    db = client[os.environ["MONGO_DB"]]
    yield db
    client.close()


@pytest.fixture(scope="session")
def postgres_session_factory():
    engine = create_engine(os.environ["POSTGRES_URL"])
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield factory
    engine.dispose()


@pytest.fixture(scope="session")
def postgres_direct_status():
    return _check_postgres_direct_connection()


@pytest.fixture(scope="session")
def redis_cache():
    return redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


@pytest.fixture(scope="session")
def elasticsearch_client():
    return Elasticsearch(os.environ["ELASTICSEARCH_URL"])


@pytest.fixture
def api_client():
    with TestClient(api_app) as client:
        yield client


@pytest.fixture
def search_client():
    with TestClient(search_app) as client:
        yield client


@pytest.fixture
def tracker(mongo_db, postgres_session_factory, redis_cache, elasticsearch_client):
    state = ResourceTracker()
    yield state

    if elasticsearch_client.indices.exists(index=INDEX_NAME):
        elasticsearch_client.indices.delete(index=INDEX_NAME, ignore_unavailable=True)

    for pattern in ("menus:*", "search:products:*"):
        keys = list(redis_cache.scan_iter(match=pattern))
        if keys:
            redis_cache.delete(*keys)

    for user_id in list(state.keycloak_user_ids):
        try:
            _delete_keycloak_user(user_id)
        except Exception:
            pass

    mongo_id_fields = {
        "users": "user_id",
        "restaurants": "restaurant_id",
        "menus": "menu_id",
        "tables": "table_id",
        "orders": "order_id",
        "reservations": "reservation_id",
    }
    for collection, field_name in mongo_id_fields.items():
        ids = list(state.mongo_ids[collection])
        if ids:
            mongo_db[collection].delete_many({field_name: {"$in": ids}})

    session = postgres_session_factory()
    try:
        if state.postgres_ids["order_items"]:
            session.query(OrderItem).filter(
                OrderItem.order_item_id.in_(list(state.postgres_ids["order_items"]))
            ).delete(synchronize_session=False)
        if state.postgres_ids["reservations"]:
            session.query(Reservation).filter(
                Reservation.reservation_id.in_(list(state.postgres_ids["reservations"]))
            ).delete(synchronize_session=False)
        if state.postgres_ids["orders"]:
            session.query(Order).filter(
                Order.order_id.in_(list(state.postgres_ids["orders"]))
            ).delete(synchronize_session=False)
        if state.postgres_ids["menus"]:
            session.query(Menu).filter(
                Menu.menu_id.in_(list(state.postgres_ids["menus"]))
            ).delete(synchronize_session=False)
        if state.postgres_ids["tables"]:
            session.query(Table).filter(
                Table.table_id.in_(list(state.postgres_ids["tables"]))
            ).delete(synchronize_session=False)
        if state.postgres_ids["restaurants"]:
            session.query(Restaurant).filter(
                Restaurant.restaurant_id.in_(list(state.postgres_ids["restaurants"]))
            ).delete(synchronize_session=False)
        if state.postgres_ids["users"]:
            session.query(User).filter(
                User.user_id.in_(list(state.postgres_ids["users"]))
            ).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


@pytest.fixture(scope="session")
def test_prefix():
    return f"it-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def admin_credentials():
    return {
        "username": os.environ["SEED_ADMIN_USERNAME"],
        "password": os.environ["SEED_ADMIN_PASSWORD"],
    }


@pytest.fixture
def admin_user(mongo_db):
    user = mongo_db.users.find_one({"user_name": os.environ["SEED_ADMIN_USERNAME"]})
    assert user is not None
    return user


@pytest.fixture
def admin_headers(api_client, admin_credentials):
    response = api_client.post("/auth/login", json=admin_credentials)
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_factory(api_client, mongo_db, tracker, test_prefix):
    def _create_user(label: str):
        username = f"{test_prefix}-{label}-{uuid.uuid4().hex[:6]}"
        password = "password123"
        email = f"{username}@example.com"

        register_response = api_client.post(
            "/auth/register",
            json={"username": username, "email": email, "password": password},
        )
        assert register_response.status_code == 201, register_response.text

        user_id = register_response.json()["user_id"]
        login_response = api_client.post(
            "/auth/login",
            json={"username": username, "password": password},
        )
        assert login_response.status_code == 200, login_response.text

        token = login_response.json()["access_token"]
        user = mongo_db.users.find_one({"user_id": user_id})
        assert user is not None

        tracker.track_mongo("users", user_id)
        tracker.track_keycloak(user.get("keycloak_id"))

        return {
            "user_id": user_id,
            "username": username,
            "password": password,
            "headers": {"Authorization": f"Bearer {token}"},
            "keycloak_id": user.get("keycloak_id"),
        }

    return _create_user
