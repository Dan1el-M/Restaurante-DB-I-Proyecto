db = db.getSiblingDB("restaurant_mongo_db");

[
  "roles",
  "users",
  "restaurants",
  "menus",
  "tables",
  "orders",
  "order_items",
  "reservations",
  "counters"
].forEach((collectionName) => {
  if (!db.getCollectionNames().includes(collectionName)) {
    db.createCollection(collectionName);
  }
});

db.roles.createIndex({ role_id: 1 }, { unique: true });
db.roles.createIndex({ role_name: 1 }, { unique: true });

db.users.createIndex({ user_id: 1 }, { unique: true });
db.users.createIndex({ user_name: 1 }, { unique: true });
db.users.createIndex({ keycloak_id: 1 }, { unique: true, sparse: true });

db.restaurants.createIndex({ restaurant_id: 1 }, { unique: true });
db.restaurants.createIndex({ restaurant_name: 1 });
db.restaurants.createIndex({ admin_id: 1 });

db.menus.createIndex({ menu_id: 1 }, { unique: true });
db.menus.createIndex({ restaurant_id: 1, dish_name: 1 }, { unique: true });

db.tables.createIndex({ table_id: 1 }, { unique: true });
db.tables.createIndex({ restaurant_id: 1, table_number: 1 }, { unique: true });

db.orders.createIndex({ order_id: 1 }, { unique: true });
db.orders.createIndex({ client_id: 1 });
db.orders.createIndex({ restaurant_id: 1 });
db.orders.createIndex({ table_id: 1 });

db.order_items.createIndex({ order_item_id: 1 }, { unique: true });
db.order_items.createIndex({ order_id: 1 });
db.order_items.createIndex({ menu_id: 1 });

db.reservations.createIndex({ reservation_id: 1 }, { unique: true });
db.reservations.createIndex({ client_id: 1 });
db.reservations.createIndex({ table_id: 1 });
db.reservations.createIndex({ reservation_date: 1 });

db.roles.updateOne(
  { role_id: 1 },
  { $setOnInsert: { role_id: 1, role_name: "admin" } },
  { upsert: true }
);
db.roles.updateOne(
  { role_id: 2 },
  { $setOnInsert: { role_id: 2, role_name: "client" } },
  { upsert: true }
);

[
  ["roles", 2],
  ["users", 0],
  ["restaurants", 0],
  ["menus", 0],
  ["tables", 0],
  ["orders", 0],
  ["order_items", 0],
  ["reservations", 0]
].forEach(([name, seq]) => {
  db.counters.updateOne(
    { _id: name },
    { $setOnInsert: { seq: seq } },
    { upsert: true }
  );
});
