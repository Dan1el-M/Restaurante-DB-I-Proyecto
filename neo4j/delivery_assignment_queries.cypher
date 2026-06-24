// Proyecto 2 - Punto 6: asignacion de rutas de entrega
// Estas consultas complementan neo4j/queries.cypher y muestran evidencia
// directa de repartidores, pedidos pendientes, rutas optimizadas y relaciones
// ASIGNADO_A generadas por neo4j/assign_routes.py.

// 1. Repartidores disponibles y ubicacion inicial
MATCH (r:Repartidor)-[:UBICADO_EN]->(u:Ubicacion)
RETURN r.id_repartidor AS id_repartidor,
       r.nombre AS repartidor,
       r.zona AS zona,
       r.capacidad_pedidos AS capacidad_pedidos,
       u.nombre AS ubicacion_actual
ORDER BY id_repartidor;

// 2. Pedidos entregables con restaurante de salida y destino del cliente
MATCH (p:Pedido)-[:SALE_DE]->(restaurante:Restaurante)-[:UBICADO_EN]->(origen:Ubicacion)
MATCH (p)-[:ENTREGAR_EN]->(destino:Ubicacion)
WHERE p.estado <> 'Cancelled'
RETURN p.id_pedido AS pedido,
       restaurante.nombre AS restaurante,
       origen.nombre AS punto_salida,
       destino.nombre AS destino_cliente,
       p.total AS total
ORDER BY pedido;

// 3. Ruta de menor tiempo entre dos ubicaciones reales del grafo
// Cambiar estos parametros si el grafo tiene otros id_ubicacion.
:param origen => 'REST_1';
:param destino => 'USER_1';

MATCH (origen:Ubicacion {id_ubicacion: $origen})
MATCH (destino:Ubicacion {id_ubicacion: $destino})
MATCH path = (origen)-[:CONECTA_CON*1..8]->(destino)
WITH path,
     reduce(total = 0.0, rel IN relationships(path) | total + rel.distancia_km) AS distancia_total_km,
     reduce(total = 0, rel IN relationships(path) | total + rel.tiempo_minutos) AS tiempo_total_minutos
RETURN [n IN nodes(path) | n.nombre] AS ruta,
       round(distancia_total_km * 100) / 100 AS distancia_total_km,
       tiempo_total_minutos
ORDER BY tiempo_total_minutos ASC, distancia_total_km ASC
LIMIT 1;

// 4. Resumen por repartidor despues de ejecutar assign_routes.py
MATCH (r:Repartidor)-[a:ASIGNADO_A]->(p:Pedido)
RETURN r.nombre AS repartidor,
       collect(p.id_pedido) AS pedidos_asignados,
       round(sum(a.distancia_total_km) * 100) / 100 AS distancia_total_km,
       sum(a.tiempo_total_minutos) AS tiempo_total_minutos,
       collect(a.heuristica) AS heuristicas
ORDER BY repartidor;

// 5. Detalle de orden de entrega, ruta y destino por pedido
MATCH (r:Repartidor)-[a:ASIGNADO_A]->(p:Pedido)-[:SALE_DE]->(restaurante:Restaurante)
MATCH (p)-[:ENTREGAR_EN]->(destino:Ubicacion)
RETURN r.nombre AS repartidor,
       a.orden_entrega AS orden_entrega,
       p.id_pedido AS pedido,
       restaurante.nombre AS restaurante,
       destino.nombre AS destino,
       a.ruta AS ruta,
       a.distancia_total_km AS distancia_total_km,
       a.tiempo_total_minutos AS tiempo_total_minutos
ORDER BY repartidor, orden_entrega;
