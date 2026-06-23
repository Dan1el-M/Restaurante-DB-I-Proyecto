// Proyecto 2 - Punto 5: Uso de Neo4J para analisis de grafos y rutas
// Ejecutar estas consultas en Neo4J Browser: http://localhost:7474

// A. Los 5 productos mas comprados juntos
MATCH (pedido:Pedido)-[:CONTIENE]->(p1:Producto)
MATCH (pedido)-[:CONTIENE]->(p2:Producto)
WHERE p1.id_producto < p2.id_producto
RETURN p1.nombre AS producto_1,
       p2.nombre AS producto_2,
       count(*) AS veces_comprados_juntos
ORDER BY veces_comprados_juntos DESC, producto_1, producto_2
LIMIT 5;

// B. Usuarios que recomiendan a otros
MATCH (usuario:Usuario)-[rel:RECOMIENDA_A]->(recomendado:Usuario)
RETURN usuario.nombre AS usuario_recomendador,
       recomendado.nombre AS usuario_recomendado,
       rel.fecha AS fecha,
       rel.canal AS canal
ORDER BY usuario_recomendador, usuario_recomendado;

// C. Usuarios influyentes por recomendaciones salientes o entrantes
MATCH (usuario:Usuario)
OPTIONAL MATCH (usuario)-[:RECOMIENDA_A]->(saliente:Usuario)
WITH usuario, count(saliente) AS recomendaciones_salientes
OPTIONAL MATCH (entrante:Usuario)-[:RECOMIENDA_A]->(usuario)
WITH usuario, recomendaciones_salientes, count(entrante) AS recomendaciones_entrantes
WITH usuario,
     recomendaciones_salientes,
     recomendaciones_entrantes,
     recomendaciones_salientes + recomendaciones_entrantes AS total_recomendaciones
WHERE total_recomendaciones > 0
RETURN usuario.nombre AS usuario,
       recomendaciones_salientes,
       recomendaciones_entrantes,
       total_recomendaciones,
       CASE
         WHEN recomendaciones_salientes >= recomendaciones_entrantes THEN 'recomendador'
         ELSE 'referenciado'
       END AS tipo_influencia
ORDER BY total_recomendaciones DESC, usuario;

// D. Camino minimo entre ubicaciones para reparto eficiente
// Cambiar los parametros segun la ruta que se quiera demostrar.
:param origen => 'U_REST_CENTRAL';
:param destino => 'U_OESTE';

MATCH (origen:Ubicacion {id_ubicacion: $origen})
MATCH (destino:Ubicacion {id_ubicacion: $destino})
MATCH path = shortestPath((origen)-[:CONECTA_CON*..8]->(destino))
RETURN origen.nombre AS origen,
       destino.nombre AS destino,
       [n IN nodes(path) | n.nombre] AS ruta,
       reduce(total = 0.0, r IN relationships(path) | total + r.distancia_km) AS distancia_total,
       reduce(total = 0, r IN relationships(path) | total + r.tiempo_minutos) AS tiempo_estimado_total;

// D2. Ruta mas eficiente por menor tiempo usando Cypher puro y limite de saltos
MATCH (origen:Ubicacion {id_ubicacion: $origen})
MATCH (destino:Ubicacion {id_ubicacion: $destino})
MATCH path = (origen)-[:CONECTA_CON*1..8]->(destino)
WITH path,
     reduce(total = 0.0, r IN relationships(path) | total + r.distancia_km) AS distancia_total,
     reduce(total = 0, r IN relationships(path) | total + r.tiempo_minutos) AS tiempo_estimado_total
RETURN [n IN nodes(path) | n.nombre] AS ruta,
       distancia_total,
       tiempo_estimado_total
ORDER BY tiempo_estimado_total ASC, distancia_total ASC
LIMIT 1;

// E. Productos mas comprados por zona
MATCH (usuario:Usuario)-[:VIVE_EN]->(ubicacion:Ubicacion)
MATCH (usuario)-[:REALIZO]->(:Pedido)-[rel:CONTIENE]->(producto:Producto)
RETURN usuario.zona AS zona,
       producto.nombre AS producto,
       producto.categoria AS categoria,
       sum(rel.cantidad) AS cantidad_total
ORDER BY zona, cantidad_total DESC, producto;

// F. Recomendaciones de productos por co-compra
:param producto => 'Hamburguesa Clasica';

MATCH (pedido:Pedido)-[:CONTIENE]->(base:Producto {nombre: $producto})
MATCH (pedido)-[rel:CONTIENE]->(sugerido:Producto)
WHERE sugerido <> base
RETURN base.nombre AS producto_base,
       sugerido.nombre AS producto_recomendado,
       count(*) AS veces_juntos,
       sum(rel.cantidad) AS cantidad_observada
ORDER BY veces_juntos DESC, cantidad_observada DESC
LIMIT 5;

// Vista general del grafo para capturas
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 80;

// Punto 6. Resumen de asignaciones por repartidor
MATCH (r:Repartidor)-[a:ASIGNADO_A]->(p:Pedido)
RETURN r.nombre AS repartidor,
       collect(p.id_pedido) AS pedidos_asignados,
       round(sum(a.distancia_total_km) * 100) / 100 AS distancia_total_km,
       sum(a.tiempo_total_minutos) AS tiempo_total_minutos
ORDER BY repartidor;

// Punto 6. Detalle de rutas optimizadas y asignaciones por repartidor
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
