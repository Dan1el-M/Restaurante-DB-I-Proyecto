/**
1. Conectarse a mongos.
2. Revisar si el shard ya fue agregado.
3. Si no fue agregado, agregar shard1ReplSet.
4. Habilitar sharding en la base restaurant_mongo_db.
 */

const DB_NAME = "restaurant_mongo_db"; // nombre ifual que en ./init-mongo.js 

const mongos = new Mongo("mongodb://mongos:27017");//conectarse a mongos
const admin = mongos.getDB("admin");//obtenemos la db admin para ejecutar comandos en los shards

const list = admin.runCommand({ listShards: 1 }); //para sacar la lista de los shards
const alreadyAdded = (list.shards || []).some((s) => s._id === "shard1ReplSet"); //revisar si el shard ya fue agregado el shard1ReplSet

if (!alreadyAdded) { //si no fue agregado, agregar shard1ReplSet
  admin.runCommand({
    addShard: "shard1ReplSet/shard1a:27018,shard1b:27018,shard1c:27018"
  });
}

admin.runCommand({ enableSharding: DB_NAME }); //habiulitar sharding en la base restaurant_mongo_db

