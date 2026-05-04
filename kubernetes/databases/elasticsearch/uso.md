# Carpeta: databases/elasticsearch/

## Función
Manifiestos para **Elasticsearch** - motor de búsqueda y análisis de datos.

## Archivos

### `elasticsearch-deployment.yaml`
- Define el pod que ejecuta Elasticsearch
- Configura:
  - Imagen: `docker.elastic.co/elasticsearch/elasticsearch:8.x`
  - Puerto: 9200 (API REST)
  - Memoria: 1Gi (configurado en variables de entorno)
  - Volumen persistente para índices

### `elasticsearch-service.yaml`
- Expone Elasticsearch como servicio interno en el cluster
- DNS: `elasticsearch.restaurante.svc.cluster.local:9200`
- Acceso: Solo desde dentro del namespace `restaurante`

## Usado por
- **search**: Servicio de búsqueda que indexa menús, restaurantes y platos
- **API**: Para consultas de búsqueda en tiempo real

## Variables de entorno importantes
- `discovery.type=single-node`: Para un nodo único (sin clustering)
- `xpack.security.enabled=true`: Seguridad habilitada (requiere autenticación)
