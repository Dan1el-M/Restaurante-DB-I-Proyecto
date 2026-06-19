# Carpeta: storage/

## Función
Define **PersistentVolumeClaims (PVC)** - almacenamiento persistente para bases de datos.

## Archivos

### `elasticsearch-pvc.yaml`
- **Tamaño**: Configurable (default ~20Gi)
- **Tipo**: `ReadWriteOnce` (un pod a la vez)
- Almacena índices de Elasticsearch
- Retiene datos incluso si el pod se reinicia

### `postgres-pvc.yaml`
- **Tamaño**: Configurable (default ~10Gi)
- **Tipo**: `ReadWriteOnce`
- Almacena datos de PostgreSQL
- Persistencia automática

## Cómo funciona
1. El PVC solicita almacenamiento al cluster
2. Kubernetes crea dinámicamente un volumen
3. Se monta en la ruta especificada del pod (ej: `/var/lib/postgresql/data`)
4. Los datos persisten aunque el pod se destruya

## Tipos de acceso
- `ReadWriteOnce`: Un pod puede leer y escribir
- `ReadOnlyMany`: Múltiples pods pueden leer
- `ReadWriteMany`: Múltiples pods pueden leer/escribir

## Storage Class
- Usa el storage class por defecto del cluster
- En minikube: `standard`
- En producción: Configurable (EBS, AzureDisk, NFS, etc.)

## Ver volúmenes
```bash
# PVCs
kubectl -n restaurante get pvc

# Detalles
kubectl -n restaurante describe pvc mongo-pvc
```

## ⚠️ Cuidado
- Eliminar un PVC borra los datos permanentemente
- Hacer backups en producción
