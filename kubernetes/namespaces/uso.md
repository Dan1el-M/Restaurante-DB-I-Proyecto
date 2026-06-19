# Carpeta: namespaces/

## Función
Define **Namespaces** - aislamientos lógicos dentro del cluster de Kubernetes.

## Archivos

### `restaurante-namespace.yaml`
- Crea el namespace `restaurante`
- Propósito: Aislar todos los recursos de la aplicación

## Beneficios de los Namespaces
- **Organización**: Agrupa recursos relacionados
- **Control de acceso**: Diferentes permisos por namespace
- **Aislamiento**: Evita conflictos entre aplicaciones
- **Límites de recursos**: Cuotas por namespace (CPU, memoria)

## Aplicación en tu proyecto
- Todos los pods (API, Search, Keycloak, BDs) se crean en `restaurante`
- Los ConfigMaps y Secrets también están en este namespace
- Servicios internos: `{servicio}.restaurante.svc.cluster.local`

## Comandos útiles
```bash
# Ver recursos en el namespace
kubectl -n restaurante get all

# Ver ConfigMaps
kubectl -n restaurante get configmaps

# Eliminar todo el namespace (y sus recursos)
kubectl delete namespace restaurante
```

## Alternativa
- Podrías crear múltiples namespaces (prod, dev, test) para diferentes entornos
