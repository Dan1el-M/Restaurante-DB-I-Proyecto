# Carpeta: databases/mongo/

## Función
Manifiestos para **MongoDB** - base de datos NoSQL principal del proyecto.

## Archivos

### `mongo-statefulset.yaml`
- Define MongoDB usando **StatefulSet** (mejor para datos persistentes)
- Configura:
  - Imagen: `mongo:latest`
  - Puerto: 27017 (puerto estándar MongoDB)
  - Volumen persistente para datos
  - ReplicaSet: Configurado para una replica única (RS0)

### `mongo-service.yaml`
- Expone MongoDB como servicio interno
- DNS: `mongo.restaurante.svc.cluster.local:27017`
- Acceso: Solo desde dentro del namespace `restaurante`

## Almacenamiento
- **Documentos**: usuarios, órdenes, reservaciones, mesas, menús
- **Volumen**: `mongo-pvc` (20Gi) en `storage/`

## Configuración ReplicaSet
- El initContainer ejecuta `rs.initiate()` al iniciar
- Permite transacciones ACID multi-documento
- Replica única (escalable a múltiples replicas si es necesario)

## Conexión desde la API
- URL: `mongodb://mongo:27017`
- Usuario/contraseña: Definidos en `secrets/restaurante-secret.yaml`
