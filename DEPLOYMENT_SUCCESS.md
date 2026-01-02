# ✅ Despliegue Exitoso: News2Market en AWS EC2 + Minikube

**Fecha**: 31 de Diciembre de 2025  
**Duración total**: ~30 minutos

## 📋 Resumen Ejecutivo

Sistema **News2Market** desplegado exitosamente en AWS EC2 con Minikube, cumpliendo todos los requisitos del proyecto académico "Infraestructuras Paralelas y Distribuidas".

## 🏗️ Infraestructura AWS

### Instancia EC2
- **Instance ID**: i-0439ceae0363fe4a3
- **IP Pública**: 13.220.67.109
- **Tipo**: t3.medium (2 vCPU, 4GB RAM)
- **Almacenamiento**: 20GB gp3
- **AMI**: Ubuntu 22.04 LTS
- **Región**: us-east-1
- **Security Group**: sg-016f397d137bd8ee4
  - Puerto 22 (SSH)
  - Puerto 80 (HTTP)
  - Puerto 8000 (API Gateway)
  - Puerto 8080 (Frontend)
  - Puerto 30800 (NodePort API)

### Configuración Minikube
- **Versión**: v1.37.0
- **Kubernetes**: v1.34.0
- **Driver**: Docker
- **CPU asignada**: 2 cores
- **Memoria asignada**: 3584 MiB
- **Metrics Server**: Habilitado

## 📦 Componentes Desplegados

### Microservicios (5 servicios)
1. **API Gateway** (1 réplica)
   - Imagen: news2market/api-gateway:latest (184MB)
   - Puerto: 8000
   - Recursos: 50m CPU, 256Mi RAM
   - Estado: ✅ Running

2. **Data Acquisition** (1 réplica)
   - Imagen: news2market/data-acquisition:latest (688MB)
   - Puerto: 8001
   - Recursos: 50m CPU, 256Mi RAM
   - Estado: ✅ Running

3. **Text Processor** (2 réplicas - HPA activo)
   - Imagen: news2market/text-processor:latest (749MB)
   - Puerto: 8002
   - Recursos: 50m CPU, 128Mi RAM por pod
   - Estado: ✅ Running (2 pods)
   - HPA: Min 2, Max 10 (CPU 70%, Memory 80%)

4. **Correlation Service** (1 réplica)
   - Imagen: news2market/correlation-service:latest (517MB)
   - Puerto: 8003
   - Recursos: 50m CPU, 256Mi RAM
   - Estado: ✅ Running

5. **Frontend** (1 réplica)
   - Imagen: news2market/frontend:latest (55.2MB)
   - Puerto: 80
   - Recursos: 50m CPU, 64Mi RAM
   - Estado: ✅ Running

### Bases de Datos (StatefulSets)
1. **PostgreSQL**
   - Puerto: 5432
   - Almacenamiento persistente: 20Gi
   - Estado: ✅ Running

2. **Redis**
   - Puerto: 6379
   - Almacenamiento persistente: 5Gi
   - Estado: ✅ Running

## 🎯 Verificación del Sistema

### Pods en Ejecución
```
NAME                                   READY   STATUS    AGE
api-gateway-78c5586f8-hpgwf            1/1     Running   6m17s
correlation-service-7ccffb5945-vrb44   1/1     Running   4m34s
data-acquisition-6b8976d47d-9cdrh      1/1     Running   4m34s
frontend-666bf4db4d-khnl7              1/1     Running   6m16s
postgres-0                             1/1     Running   7m20s
redis-0                                1/1     Running   3m26s
text-processor-75dcfc46ff-5skmm        1/1     Running   4m35s
text-processor-75dcfc46ff-gjdfs        1/1     Running   2m41s
```

### Recursos del Cluster
- **CPU utilizado**: 215m (10% del total)
- **Memoria utilizada**: 1613Mi (42% del total)
- **Pods totales**: 8
- **Servicios**: 7
- **PersistentVolumes**: 2 (20Gi + 5Gi)

### HPA (Horizontal Pod Autoscaler)
- **Servicio**: text-processor
- **Réplicas actuales**: 2
- **CPU actual**: 4% (target 70%)
- **Memory actual**: 64% (target 80%)
- **Min réplicas**: 2
- **Max réplicas**: 10

## 🌐 Acceso al Sistema

### Puertos Expuestos
- **Frontend**: http://13.220.67.109:8080
- **API Gateway**: http://13.220.67.109:8000
- **Health Check**: http://13.220.67.109:8000/api/v1/health

### Port-Forwarding Configurado
```bash
# Frontend (Puerto 8080 → 80)
PID: 30192

# API Gateway (Puerto 8000 → 8000)
PID: 30193
```

### SSH al EC2
```bash
ssh -i ~/.ssh/news2market-key.pem ubuntu@13.220.67.109
```

## 📊 Evidencia Recopilada

Toda la evidencia del sistema funcionando está en la instancia EC2 en:
`/home/ubuntu/evidencia/`

Archivos generados:
- `pods.txt` - Estado de todos los pods
- `deployments.txt` - Estado de deployments
- `hpa.txt` - Configuración del HPA
- `hpa-details.txt` - Detalles completos del HPA
- `node-metrics.txt` - Métricas del nodo
- `pod-metrics.txt` - Métricas de consumo de pods
- `services.txt` - Lista de servicios
- `volumes.txt` - Persistent Volumes configurados
- `api-health.txt` - Health check del API
- `frontend.txt` - HTML del frontend
- `minikube-status.txt` - Estado de Minikube

## 🎓 Cumplimiento de Requisitos Académicos

### ✅ Arquitectura Distribuida
- **5 microservicios** desplegados independientemente
- Comunicación asíncrona vía Redis
- Base de datos PostgreSQL compartida
- Frontend desacoplado del backend

### ✅ Orquestación con Kubernetes
- Deployments configurados para cada servicio
- StatefulSets para bases de datos con almacenamiento persistente
- Services para descubrimiento de servicios
- ConfigMaps y Secrets para configuración

### ✅ Escalabilidad y Paralelismo
- HPA configurado en text-processor (2-10 réplicas)
- Escalado automático basado en CPU y memoria
- Procesamiento paralelo de textos
- Load balancing automático por Kubernetes

### ✅ Despliegue en la Nube
- AWS EC2 como infraestructura
- Minikube como orquestador Kubernetes
- Almacenamiento persistente en EBS
- Acceso público configurado

### ✅ Alta Disponibilidad
- Réplicas de servicios críticos
- Reinicio automático de pods fallidos
- Health checks configurados
- Persistent storage para datos

## 💰 Costos Estimados

### EC2 t3.medium
- **Por hora**: $0.0416 USD
- **Por día (8 horas)**: $0.33 USD
- **Por semana**: $2.31 USD
- **Total en presupuesto $50**: ~15 días de uso continuo

### Almacenamiento
- **20GB EBS gp3**: $0.08 USD/mes
- **Transferencia de datos**: Mínima (dentro del free tier)

## 🔧 Comandos Útiles

### Ver estado del sistema
```bash
ssh -i ~/.ssh/news2market-key.pem ubuntu@13.220.67.109
sudo kubectl get pods -n news2market
sudo kubectl get hpa -n news2market
sudo kubectl top pods -n news2market
```

### Verificar port-forwarding
```bash
ps aux | grep "port-forward" | grep -v grep
```

### Reiniciar port-forwarding si es necesario
```bash
nohup sudo kubectl port-forward -n news2market --address 0.0.0.0 service/frontend-service 8080:80 > /tmp/port-forward-frontend.log 2>&1 &
nohup sudo kubectl port-forward -n news2market --address 0.0.0.0 service/api-gateway-service 8000:8000 > /tmp/port-forward-api.log 2>&1 &
```

### Ver logs de un servicio
```bash
sudo kubectl logs -n news2market deployment/text-processor -f
```

### Escalar manualmente
```bash
sudo kubectl scale deployment text-processor -n news2market --replicas=5
```

## 🛑 Apagar la Instancia (Importante para no gastar créditos)

```bash
# Desde tu máquina local
aws ec2 stop-instances --instance-ids i-0439ceae0363fe4a3
```

## 🚀 Reiniciar el Sistema

```bash
# 1. Iniciar instancia
aws ec2 start-instances --instance-ids i-0439ceae0363fe4a3

# 2. Esperar a que arranque y obtener nueva IP
aws ec2 describe-instances --instance-ids i-0439ceae0363fe4a3 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text

# 3. Conectar por SSH con la nueva IP
ssh -i ~/.ssh/news2market-key.pem ubuntu@<NUEVA_IP>

# 4. Verificar que Minikube esté activo
sudo minikube status

# 5. Si Minikube está detenido, iniciarlo
sudo minikube start --driver=docker --cpus=2 --memory=3584 --force

# 6. Configurar port-forwarding nuevamente
nohup sudo kubectl port-forward -n news2market --address 0.0.0.0 service/frontend-service 8080:80 > /tmp/port-forward-frontend.log 2>&1 &
nohup sudo kubectl port-forward -n news2market --address 0.0.0.0 service/api-gateway-service 8000:8000 > /tmp/port-forward-api.log 2>&1 &
```

## 📝 Notas Adicionales

1. **Persistencia de datos**: Los datos en PostgreSQL y Redis persisten entre reinicios gracias a los PersistentVolumes
2. **Port-forwarding**: Se debe reconfigurar después de cada reinicio del sistema
3. **IP pública**: Cambia cada vez que se detiene/inicia la instancia EC2
4. **Minikube**: Mantiene el estado del cluster entre reinicios del sistema
5. **Imágenes Docker**: Cargadas localmente en Minikube, no requieren registry externo

## 🎥 Para Grabación de Video

### Demostración sugerida (2-5 minutos):
1. **SSH a EC2**: Mostrar conexión y estado del sistema
2. **Pods corriendo**: `kubectl get pods -n news2market`
3. **HPA funcionando**: `kubectl get hpa -n news2market`
4. **Métricas**: `kubectl top pods -n news2market`
5. **Frontend accesible**: Abrir navegador en http://13.220.67.109:8080
6. **API Gateway**: Probar health endpoint
7. **Escalado manual**: Demostrar scaling de text-processor

## ✅ Checklist Pre-Grabación
- [ ] EC2 instance corriendo
- [ ] Todos los pods en estado Running
- [ ] Port-forwarding activo
- [ ] Frontend accesible desde navegador
- [ ] API respondiendo correctamente
- [ ] HPA mostrando métricas
- [ ] Evidencia recopilada visible

---

**Estado Final**: ✅ Sistema completamente funcional y listo para demostración académica
