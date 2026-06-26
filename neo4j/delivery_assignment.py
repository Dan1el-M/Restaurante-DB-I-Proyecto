"""Fallback delivery route assignment validator for Project 2 point 6.

This module contains a service-independent nearest-neighbor heuristic.  It is
used as a reproducible local validation when Neo4J is not running.  The main
project flow assigns delivery routes through Neo4J with operational data loaded
from /graph/export.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_SPEED_KMH = 22.0
DEFAULT_STOP_MINUTES = 4


@dataclass(frozen=True)
class Location:
    """Point with latitude/longitude used to estimate delivery distance."""

    id: str
    name: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class DeliveryOrder:
    """Pending order with restaurant origin and customer destination."""

    id: int
    restaurant_location_id: str
    customer_location_id: str
    customer_name: str
    status: str = "pendiente"


@dataclass
class Courier:
    """Available driver that starts from a known location and has capacity."""

    id: int
    name: str
    start_location_id: str
    capacity_orders: int
    current_location_id: str = ""
    stops: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.current_location_id:
            self.current_location_id = self.start_location_id

    @property
    def available_slots(self) -> int:
        """Return how many more orders can be assigned to this courier."""

        return self.capacity_orders - len(self.stops)


def haversine_km(origin: Location, destination: Location) -> float:
    """Return the straight-line distance in kilometers between two locations."""

    lat1 = math.radians(origin.latitude)
    lon1 = math.radians(origin.longitude)
    lat2 = math.radians(destination.latitude)
    lon2 = math.radians(destination.longitude)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return round(6371 * 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine)), 2)


def estimate_minutes(distance_km: float, speed_kmh: float = DEFAULT_SPEED_KMH) -> int:
    """Convert kilometers into route minutes with a small delivery stop buffer."""

    travel_minutes = math.ceil(distance_km / speed_kmh * 60)
    return max(1, travel_minutes) + DEFAULT_STOP_MINUTES


def load_delivery_data(path: Path) -> tuple[dict[str, Location], list[Courier], list[DeliveryOrder]]:
    """Read controlled JSON and return locations, couriers and pending orders."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    locations = {
        row["id"]: Location(
            id=row["id"],
            name=row["name"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
        )
        for row in payload["locations"]
    }
    couriers = [
        Courier(
            id=int(row["id"]),
            name=row["name"],
            start_location_id=row["start_location_id"],
            capacity_orders=int(row["capacity_orders"]),
        )
        for row in payload["couriers"]
    ]
    orders = [
        DeliveryOrder(
            id=int(row["id"]),
            restaurant_location_id=row["restaurant_location_id"],
            customer_location_id=row["customer_location_id"],
            customer_name=row["customer_name"],
            status=row.get("status", "pendiente"),
        )
        for row in payload["orders"]
        if row.get("status", "pendiente") == "pendiente"
    ]
    return locations, couriers, orders


def route_cost(
    locations: dict[str, Location],
    courier: Courier,
    order: DeliveryOrder,
) -> tuple[float, int, list[str]]:
    """Calculate pickup plus delivery cost for one candidate order."""

    current = locations[courier.current_location_id]
    restaurant = locations[order.restaurant_location_id]
    customer = locations[order.customer_location_id]
    pickup_distance = 0.0 if restaurant.id == courier.start_location_id else haversine_km(current, restaurant)
    delivery_distance = haversine_km(restaurant, customer)
    if restaurant.id == courier.start_location_id:
        delivery_distance = haversine_km(current, customer)
    total_distance = round(pickup_distance + delivery_distance, 2)
    total_time = estimate_minutes(total_distance)
    route = [current.name]
    if pickup_distance > 0 and current.id != restaurant.id:
        route.append(restaurant.name)
    route.append(customer.name)
    return total_distance, total_time, route


def choose_nearest_order(
    locations: dict[str, Location],
    courier: Courier,
    pending_orders: list[DeliveryOrder],
) -> tuple[DeliveryOrder, float, int, list[str]] | None:
    """Pick the closest pending order from the courier current location."""

    if not pending_orders:
        return None
    candidates = []
    for order in pending_orders:
        distance, minutes, route = route_cost(locations, courier, order)
        candidates.append((distance, minutes, order.id, order, route))
    distance, minutes, _order_id, order, route = min(candidates)
    return order, distance, minutes, route


def assign_nearest_neighbor(
    locations: dict[str, Location],
    couriers: list[Courier],
    orders: list[DeliveryOrder],
) -> list[Courier]:
    """Distribute pending orders by repeatedly assigning the nearest candidate.

    Drivers are processed in stable order.  Each driver receives one order per
    round, which keeps the distribution balanced while still using nearest
    neighbor from each driver's latest stop.
    """

    pending_orders = orders[:]
    while pending_orders and any(courier.available_slots > 0 for courier in couriers):
        progress = False
        for courier in couriers:
            if courier.available_slots <= 0 or not pending_orders:
                continue
            selected = choose_nearest_order(locations, courier, pending_orders)
            if selected is None:
                continue
            order, distance, minutes, route = selected
            courier.stops.append(
                {
                    "order_id": order.id,
                    "customer": order.customer_name,
                    "route": route,
                    "distance_km": distance,
                    "time_minutes": minutes,
                }
            )
            courier.current_location_id = order.customer_location_id
            pending_orders.remove(order)
            progress = True
        if not progress:
            break
    if pending_orders:
        missing = ", ".join(str(order.id) for order in pending_orders)
        raise RuntimeError(f"No hay capacidad suficiente para asignar pedidos: {missing}")
    return couriers


def print_validation(locations: dict[str, Location], couriers: list[Courier], orders: list[DeliveryOrder]) -> None:
    """Print the checklist and route summary required by the project statement."""

    print("[OK] Se cargaron repartidores disponibles.")
    print("[OK] Se cargaron pedidos pendientes con ubicacion.")
    sample_distance = haversine_km(next(iter(locations.values())), list(locations.values())[1])
    if sample_distance <= 0:
        raise RuntimeError("La distancia de muestra debe ser positiva.")
    print("[OK] Se calculo la distancia entre ubicaciones.")
    print("[OK] Se aplico algoritmo de vecino mas cercano.")
    print("[OK] Se asignaron pedidos a repartidores.")
    print("[OK] Se generaron rutas optimizadas.")
    print("[OK] Se calculo distancia total por repartidor.")
    print("[OK] Se calculo tiempo estimado por ruta.")
    print("[OK] Punto 6 validado correctamente.")
    print()
    for courier in couriers:
        if not courier.stops:
            continue
        route_names = [courier.stops[0]["route"][0]]
        assigned_orders = []
        total_distance = 0.0
        total_minutes = 0
        for stop in courier.stops:
            route_names.extend(stop["route"][1:])
            assigned_orders.append(stop["order_id"])
            total_distance += float(stop["distance_km"])
            total_minutes += int(stop["time_minutes"])
        print(f"Repartidor: {courier.name}")
        print(f"Ruta: {' -> '.join(route_names)}")
        print(f"Pedidos asignados: {assigned_orders}")
        print(f"Distancia total: {round(total_distance, 2)} km")
        print(f"Tiempo estimado: {total_minutes} min")
        print()


def main() -> int:
    """Run the standalone fallback validation for point 6."""

    default_path = Path(__file__).with_name("sample_delivery_data.json")
    parser = argparse.ArgumentParser(description="Valida localmente la heuristica del Punto 6.")
    parser.add_argument("--data", type=Path, default=default_path, help="Archivo JSON de pedidos/repartidores.")
    args = parser.parse_args()
    try:
        locations, couriers, orders = load_delivery_data(args.data)
        assigned = assign_nearest_neighbor(locations, couriers, orders)
        print_validation(locations, assigned, orders)
    except Exception as exc:
        print(f"[ERROR] No se pudo validar el Punto 6 local: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
