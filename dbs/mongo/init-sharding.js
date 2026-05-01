// Inicializa los Replica Sets necesarios para Sharding :
// - Config Server RS: cfgReplSet (cfg1/cfg2/cfg3 en 27019)
// - Shard RS: shard1ReplSet (shard1a/shard1b/shard1c en 27018)

//carga la ruta del script replset.js para usar la funcion initiateReplicaSet
function tryLoad(path) {
  try {
    load(path);
    return true;
  } catch (e) {
    return false;
  }
}

//si la ruta no se pudo cargar desde /scripts, lo intentamos desde la ruta actual
if (!tryLoad("/scripts/_replset.js")) {
  tryLoad("./_replset.js");
}

if (typeof initiateReplicaSet !== "function") {
  throw new Error("No se pudo cargar _replset.js (initiateReplicaSet no existe)");
}

//iniciamos el replica set de los config servers
initiateReplicaSet({
  mongoUri: "mongodb://cfg1:27019",// unsamos mngo db, el host de uno de los config servers y el puerto 27019
  replSetConfig: {
    _id: "cfgReplSet",
    configsvr: true,
    members: [
      { _id: 0, host: "cfg1:27019" },
      { _id: 1, host: "cfg2:27019" },
      { _id: 2, host: "cfg3:27019" }
    ]//lista de miembros del replica set de los config servers, con su id y host
  },
  waitName: "cfgReplSet"
});

initiateReplicaSet({
  mongoUri: "mongodb://shard1a:27018",
  replSetConfig: {
    _id: "shard1ReplSet",
    members: [
      { _id: 0, host: "shard1a:27018" },
      { _id: 1, host: "shard1b:27018" },
      { _id: 2, host: "shard1c:27018" }
    ]//lista de miembros del replica set del shard1, con su id y host
  },
  waitName: "shard1ReplSet"
});



// creo que este archivo ya no se usa, probarlo