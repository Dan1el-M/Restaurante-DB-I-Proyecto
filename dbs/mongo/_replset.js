// funciones que pueden ser usadas tanto en el init como en el test de replset

//funcion de sleep, recibe milisegundos y bloquea el hilo actual durante este tiempo
function sleep(ms) {
  const start = Date.now(); 
  while (Date.now() - start < ms) {} //mienmtyras no pasen los ms, sigue bloqueando el hilo
}

//funcion para obtener la base de datos de administracion
function getAdminDb(mongoUri) {
  if (mongoUri) return new Mongo(mongoUri).getDB("admin");
  //admin se usa para comandos administrativos como: replSetInitiate, addShard, enableSharding, etc. No requiere autenticación.
  return db.getSiblingDB("admin");
}

//paraa saber si un replica set ya fue uniciado
//recibe la DB admin
function isReplicaSetInitiated(adminDb) {
  try {
    const status = adminDb.runCommand({ replSetGetStatus: 1 }); // esta ok? si no esta iniciado amnda false
    return status?.ok === 1;
  } catch (e) {
    return false;
  }
}

// espera hasta que el replica ser tenga un Primary
function waitForPrimary(adminDb, timeoutMs, nameForErrors) { //recibe la DB admin, el tiempo maximo de espera y un nombre para los errores
  const start = Date.now();
  while (Date.now() - start < timeoutMs) { //mientras no se alcance el tiempo maximo de espera
    try {
      const status = adminDb.runCommand({ replSetGetStatus: 1 }); //si el comando es exitoso, busca el miembro que sea PRIMARY y devuelve su nombre
      if (status?.ok === 1) {
        const primary = (status.members || []).find((m) => m.stateStr === "PRIMARY");
        if (primary) return primary.name;
      }
    } catch (e) {}
    sleep(1000); //sino espera 1 segundo antes de volver a intentar
  }
  throw new Error(`Timeout esperando PRIMARY en ${nameForErrors}`); //si se alcanza el tiempo maximo de espera, lanza un error
}

// si ya fue iniciado, no hace nada. Si no, inicia el replica set con la config dada y espera a que haya un PRIMARY (o timeout).
function initiateReplicaSet({ mongoUri, replSetConfig, waitName, timeoutMs = 300000 }) {
  const adminDb = getAdminDb(mongoUri);

  const alreadyInitiated = isReplicaSetInitiated(adminDb); //si el replica set ya fue iniciado, no hace nada
  if (!alreadyInitiated) {
    const res = adminDb.runCommand({ replSetInitiate: replSetConfig }); //si no fue iniciado, lo inicia con la config dada
    if (res?.ok !== 1) {
      throw new Error(`replSetInitiate falló (${waitName}): ${tojson(res)}`); //si el comando falla, lanza un error con el resultado del comando
    }
  }

  waitForPrimary(adminDb, timeoutMs, waitName); //espera a que haya un PRIMARY
}
