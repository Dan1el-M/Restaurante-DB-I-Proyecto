SHOW VIEWS;

SELECT 'cubo_ingresos_mes_categoria' AS vista, COUNT(*) AS total
FROM cubo_ingresos_mes_categoria;

SELECT 'cubo_actividad_clientes_zona' AS vista, COUNT(*) AS total
FROM cubo_actividad_clientes_zona;

SELECT 'cubo_ordenes_completadas_canceladas' AS vista, COUNT(*) AS total
FROM cubo_ordenes_completadas_canceladas;
