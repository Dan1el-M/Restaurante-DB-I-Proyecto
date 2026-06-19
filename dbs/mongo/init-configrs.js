// Inicializa el Replica Set de Config Servers (cfgReplSet)

//sacamoos la ruta del script replset.js
function tryLoad(path) {
  try {
    load(path);
    return true;
  } catch (e) {
    return false;
  }
}
//si no se pudo cargar desde /scripts, lo intentamos desde la ruta actual
if (!tryLoad("/scripts/_replset.js")) {
  tryLoad("./_replset.js");
}
//si no se pudo cargar el script, lanzamos un error
if (typeof initiateReplicaSet !== "function") {
  throw new Error("No se pudo cargar _replset.js (initiateReplicaSet no existe)");
}

//invocamos la funcion de replset para iniciar el replica set de los config servers
initiateReplicaSet({
  replSetConfig: {      //configuracion del replica set
    _id: "cfgReplSet",//nombre del replica set
    configsvr: true,//indica que este replica set es para los config servers
    members: [
      { _id: 0, host: "cfg1:27019" },
      { _id: 1, host: "cfg2:27019" },
      { _id: 2, host: "cfg3:27019" }
    ]//miembros del replica set, con su id y host
  },
  waitName: "cfgReplSet"// mensaje para los errores relacionados con este replica set
});

