// Inicializa el Replica Set del Shard (shard1ReplSet). Idempotente.

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
//si no se pudo cargar el script, lanzamos un error
if (typeof initiateReplicaSet !== "function") {
  throw new Error("No se pudo cargar _replset.js (initiateReplicaSet no existe)");
}

initiateReplicaSet({//iniciamos el replica set del shard1
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

