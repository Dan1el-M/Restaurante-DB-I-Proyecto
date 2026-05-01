//solo shardea platillos (menus) y reservaciones
const DB_NAME = "restaurant_mongo_db";

const mongos = new Mongo("mongodb://mongos:27017"); //conectarse a mongos
const admin = mongos.getDB("admin");//obtenemos la db admin para ejecutar comandos en los shards
const config = mongos.getDB("config");//sacamos la db de config para revisar si las colecciones ya estan shardeadas


function isAlreadySharded(namespace) {
  const doc = config.collections.findOne({ _id: namespace });
  return !!doc && !!doc.key;
}

// `menus` tiene un índice UNIQUE en { restaurant_id: 1, dish_name: 1 }.
// Para poder mantener unicidad en un clúster shardeado, el shard key debe ser
// prefijo de cualquier índice unique. Por eso se usa ese mismo prefijo.
const menusNs = `${DB_NAME}.menus`;
if (!isAlreadySharded(menusNs)) {
  admin.runCommand({
    shardCollection: menusNs,
    key: { restaurant_id: 1, dish_name: 1 }
  });
}

const reservationsNs = `${DB_NAME}.reservations`;
if (!isAlreadySharded(reservationsNs)) {
  admin.runCommand({
    shardCollection: reservationsNs,
    key: { reservation_id: "hashed" }
  });
}

