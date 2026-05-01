# Restaurante-DB-I-Proyecto
El objetivo de esta primera entrega es que los estudiantes desarrollen una API REST para la gestión de reservas en restaurantes, implementando autenticación con JWT, contenedorización con Docker y pruebas unitarias. Esta etapa se centra en la creación de una base funcional y bien estructurada para el sistema completo.

## MongoDB: Replicación + Sharding (Docker Compose)
Este proyecto levanta un clúster shardeado de MongoDB con:
- **Config Server Replica Set**: `cfgReplSet` (1 primario + 2 secundarios)
- **Shard 1**: `shard1ReplSet` (1 primario + 2 secundarios)
- **Router**: `mongos` (la API se conecta aquí)

La inicialización es automática con el servicio `mongo-setup`:
- Inicia los replica sets
- Agrega el shard al clúster
- Crea colecciones/índices (ver `dbs/mongo/init-mongo.js`)
- Habilita sharding en `menus` (productos) y `reservations`

### Cómo ejecutar
- `docker compose up -d --build`

### Persistencia
Los datos se persisten en volúmenes Docker (ver `docker-compose.yml`):
- `cfg1_data`, `cfg2_data`, `cfg3_data`
- `shard1a_data`, `shard1b_data`, `shard1c_data`
