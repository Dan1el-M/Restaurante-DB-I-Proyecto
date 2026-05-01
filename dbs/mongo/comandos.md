comandos:  !!!!!!!!!!!!!!despues la podemos borrar

1. docker compose up -d --build
    1. hasta que salga así 
    
    ![image.png](attachment:6bf8ec11-ad1a-4c39-b986-f382dd1dba7f:image.png)
    
2. docker exec -it restaurant-cfg1 mongosh --port 27019 --quiet --eval "rs.status().members.map(m=>({name:m.name,state:m.stateStr}))”
3. docker exec -it restaurant-shard1a mongosh --port 27018 --quiet --eval "rs.status().members.map(m=>({name:m.name,state:m.stateStr}))”
4. docker compose logs --tail=80 mongo-setup
5. docker compose logs --tail=80 mongo-shard-setup
6. docker compose logs --tail=80 mongo-config-setup
7. docker compose ps -a
    1. los que estan en exited(0) significan que corrieron una vez y luego se cierran
8. docker exec -it restaurant-mongos mongosh --port 27017 --eval "sh.status()”
    1. este imprime la infrmacion

1. Ver quién es PRIMARY.
    1. docker exec -it restaurant-shard1a mongosh --port 27018 --quiet --eval "rs.status().members.map(m=>({name:m.name,state:m.stateStr,health:m.health}))”
2. Insertar un dato por mongos.
    1. docker exec -it restaurant-mongos mongosh --port 27017 --quiet --eval "db.getSiblingDB('restaurant_mongo_db').reservations.insertOne({reservation_id: 10001, client_id: 1, table_id: 1, reservation_date: new Date(), status: 'terminal-test-before-failure'})”
    2. docker exec -it restaurant-mongos mongosh --port 27017 --quiet --eval "db.getSiblingDB('restaurant_mongo_db').reservations.find({reservation_id: 10001}).pretty()”
3. Apagar un nodo. (primeor un secundario)
    1. docker stop restaurant-shard1b
4. Ver si el clúster sigue funcionando.
    1. docker exec -it restaurant-shard1a mongosh --port 27018 --quiet --eval "rs.status().members.map(m=>({name:m.name,state:m.stateStr,health:m.health}))”
5. Probar otra escritura.
    1. docker exec -it restaurant-mongos mongosh --port 27017 --quiet --eval "db.getSiblingDB('restaurant_mongo_db').reservations.insertOne({reservation_id: 10002, client_id: 1, table_id: 1, reservation_date: new Date(), status: 'terminal-test-secondary-down'})”
6. Volver a levantar el nodo caído.
    1. docker start restaurant-shard1b
    2. docker exec -it restaurant-shard1a mongosh --port 27018 --quiet --eval "rs.status().members.map(m=>({name:m.name,state:m.stateStr,health:m.health}))"
7. Apagar el PRIMARY.
    1. docker stop restaurant-shard1a
    2. espere unos 10 a 20 segundos
8. Ver si Mongo elige otro PRIMARY.
    1. docker exec -it restaurant-shard1b mongosh --port 27018 --quiet --eval "rs.status().members.map(m=>({name:m.name,state:m.stateStr,health:m.health}))”
    2. docker exec -it restaurant-mongos mongosh --port 27017 --quiet --eval "db.getSiblingDB('restaurant_mongo_db').reservations.insertOne({reservation_id: 10003, client_id: 1, table_id: 1, reservation_date: new Date(), status: 'terminal-test-primary-down-after-election'})”
9. Levantamos de nuevo al antiguo PRIMARY
    1. docker start restaurant-shard1a
    2. docker exec -it restaurant-shard1b mongosh --port 27018 --quiet --eval "rs.status().members.map(m=>({name:m.name,state:m.stateStr,health:m.health}))”
10. Vemos los datos que hicimos:
    1. docker exec -it restaurant-mongos mongosh --port 27017 --quiet --eval "db.getSiblingDB('restaurant_mongo_db').reservations.find({reservation_id: {`$in: [10001,10002,10003,10005]}}).pretty()”