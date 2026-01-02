# 🎥 Script para Video de Demostración (2-5 minutos)
## News2Market - Sistema Distribuido en AWS + Kubernetes

---

## 🎬 INTRODUCCIÓN (30 segundos)

### Presentación
**[Pantalla inicial - PowerPoint o texto]**

"Buen día, mi nombre es Iván Ausecha. Este es el proyecto News2Market, un sistema distribuido para análisis de correlación entre noticias económicas y el índice COLCAP, desplegado en AWS con Kubernetes."

**Puntos clave a mencionar:**
- Proyecto para el curso "Infraestructuras Paralelas y Distribuidas"
- Arquitectura de microservicios
- Despliegue en AWS EC2 con Minikube
- Escalado automático con HPA

---

## 🏗️ ARQUITECTURA (30 segundos)

### Diagrama de Componentes
**[Mostrar diagrama o enumerar componentes]**

"El sistema consta de:
- **5 microservicios**: API Gateway, Data Acquisition, Text Processor, Correlation Service, y Frontend
- **2 bases de datos**: PostgreSQL para datos estructurados y Redis para colas de mensajes
- **Kubernetes**: para orquestación y escalado automático
- **AWS EC2**: como infraestructura cloud (t3.medium)"

---

## 💻 PARTE 1: CONEXIÓN Y ESTADO DEL CLUSTER (45 segundos)

### Comando 1: SSH a la instancia
```bash
ssh -i ~/.ssh/news2market-key.pem ubuntu@13.220.67.109
```

**Narración:**
"Me conecto por SSH a la instancia EC2 en AWS. Esta es una instancia t3.medium con 2 vCPUs y 4GB de RAM."

### Comando 2: Ver estado de Minikube
```bash
sudo minikube status
```

**Narración:**
"Verifico que Minikube está activo. Minikube está ejecutando Kubernetes v1.34.0."

### Comando 3: Listar todos los pods
```bash
sudo kubectl get pods -n news2market
```

**Narración:**
"Aquí vemos todos los pods en ejecución:
- API Gateway (1 réplica)
- Data Acquisition (1 réplica)
- Text Processor (2 réplicas - gracias al HPA)
- Correlation Service (1 réplica)
- Frontend (1 réplica)
- PostgreSQL (StatefulSet)
- Redis (StatefulSet)

Todos están en estado READY y Running."

---

## 📊 PARTE 2: MÉTRICAS Y ESCALABILIDAD (60 segundos)

### Comando 4: Ver métricas del cluster
```bash
sudo kubectl top node
```

**Narración:**
"Las métricas del nodo muestran:
- CPU utilizado: ~10-15%
- Memoria: ~40-50%
El cluster tiene recursos disponibles para escalar."

### Comando 5: Ver métricas de pods
```bash
sudo kubectl top pods -n news2market
```

**Narración:**
"Cada pod consume recursos de forma eficiente:
- Text Processor: el más exigente con procesamiento NLP
- API Gateway: punto de entrada, uso moderado
- Frontend: mínimo consumo (solo nginx)
- Bases de datos: uso estable"

### Comando 6: Ver HPA (Horizontal Pod Autoscaler)
```bash
sudo kubectl get hpa -n news2market
```

**Narración:**
"El HPA está configurado para text-processor:
- Mínimo 2 réplicas, máximo 10
- Actualmente 2 réplicas corriendo
- Umbral de escalado: 70% CPU o 80% memoria
- CPU actual: ~4%, memoria ~60%"

### Comando 7: Detalles del HPA
```bash
sudo kubectl describe hpa text-processor-hpa -n news2market
```

**Narración:**
"El HPA monitorea constantemente y está listo para escalar si aumenta la carga."

---

## 🌐 PARTE 3: ACCESO WEB Y FUNCIONALIDAD (45 segundos)

### Acción 1: Abrir navegador - Frontend
**URL:** http://13.220.67.109:8080

**Narración:**
"Accedo al frontend desde el navegador. Esta es una aplicación React que se comunica con el backend mediante nginx como proxy inverso."

**[Mostrar interfaz, navegar brevemente]**

### Acción 2: Abrir navegador - API Health Check  
**URL:** http://13.220.67.109:8000/api/v1/health

**Narración:**
"El API Gateway responde con el health check. Vemos que está healthy aunque los servicios dependientes muestran 'offline' porque no se ha iniciado procesamiento activo."

### Comando 8: Ver logs en tiempo real
```bash
sudo kubectl logs -n news2market deployment/api-gateway -f --tail=20
```

**Narración:**
"Estos son los logs en tiempo real del API Gateway respondiendo peticiones HTTP."

*(Ctrl+C para salir)*

---

## 🚀 PARTE 4: DEMOSTRACIÓN DE ESCALADO (60 segundos)

### Comando 9: Escalar manualmente
```bash
sudo kubectl scale deployment text-processor -n news2market --replicas=5
```

**Narración:**
"Voy a escalar manualmente text-processor de 2 a 5 réplicas para demostrar el escalado horizontal."

### Comando 10: Ver pods escalando
```bash
watch -n 1 'sudo kubectl get pods -n news2market | grep text-processor'
```

**Narración:**
"Observen cómo Kubernetes crea automáticamente 3 nuevas réplicas:
- ContainerCreating → Running
- Load balancing automático
- Sin downtime"

*(Esperar 10-15 segundos, mostrar 5 pods activos)*

*(Ctrl+C para salir del watch)*

### Comando 11: Verificar escalado
```bash
sudo kubectl get deployment text-processor -n news2market
```

**Narración:**
"Ahora tenemos 5/5 réplicas disponibles. Kubernetes distribuye la carga entre ellas automáticamente."

### Comando 12: Volver a estado original
```bash
sudo kubectl scale deployment text-processor -n news2market --replicas=2
```

**Narración:**
"Regreso a 2 réplicas. El HPA seguirá monitoreando y escalará automáticamente si hay carga real."

---

## 💾 PARTE 5: PERSISTENCIA Y VOLÚMENES (30 segundos)

### Comando 13: Ver Persistent Volumes
```bash
sudo kubectl get pv,pvc -n news2market
```

**Narración:**
"Los datos son persistentes gracias a PersistentVolumes:
- PostgreSQL: 20GB para datos estructurados
- Redis: 5GB para colas de mensajes
Los datos sobreviven reinicios y recreaciones de pods."

### Comando 14: Ver servicios
```bash
sudo kubectl get svc -n news2market
```

**Narración:**
"Los servicios exponen los pods:
- NodePort para acceso externo (frontend y API)
- ClusterIP para comunicación interna
- Headless services para StatefulSets"

---

## 📂 PARTE 6: EVIDENCIA Y ESTRUCTURA (20 segundos)

### Comando 15: Ver evidencia recopilada
```bash
ls -lh /home/ubuntu/evidencia/
```

**Narración:**
"Toda la evidencia del sistema funcionando está almacenada aquí:
- Estado de pods y deployments
- Métricas del HPA
- Configuración de servicios
- Health checks
Todo documentado para revisión académica."

---

## 🎓 CONCLUSIÓN (30 segundos)

### Resumen Final
**[Volver a pantalla principal o cerrar terminal]**

**Narración:**
"En resumen, hemos demostrado:

✅ **Arquitectura distribuida** con 5 microservicios independientes
✅ **Orquestación Kubernetes** con Deployments y StatefulSets
✅ **Escalabilidad automática** mediante HPA
✅ **Persistencia de datos** con PersistentVolumes
✅ **Despliegue en la nube** AWS EC2
✅ **Alta disponibilidad** con réplicas y health checks

El sistema cumple todos los requisitos del proyecto académico, demostrando paralelismo, escalabilidad y orquestación de contenedores en un entorno cloud real."

**[Pantalla final con información de contacto o agradecimiento]**

"Gracias por su atención."

---

## 📝 CHECKLIST PRE-GRABACIÓN

### Antes de empezar:
- [ ] Instancia EC2 corriendo (i-0439ceae0363fe4a3)
- [ ] Minikube activo (`sudo minikube status`)
- [ ] Todos los pods en Running (`sudo kubectl get pods -n news2market`)
- [ ] Port-forwarding activo (PIDs 30192, 30193)
- [ ] Navegador con tabs preparadas:
  - Tab 1: http://13.220.67.109:8080
  - Tab 2: http://13.220.67.109:8000/api/v1/health
- [ ] Terminal SSH conectada
- [ ] Grabador de pantalla configurado
- [ ] Audio funcionando correctamente

### Durante la grabación:
- [ ] Hablar claro y pausado
- [ ] Esperar a que los comandos terminen antes de continuar
- [ ] Mostrar resultados completos en pantalla
- [ ] No hacer scroll demasiado rápido
- [ ] Pausar 2-3 segundos después de cada resultado importante

### Comandos de emergencia (si algo falla):
```bash
# Reiniciar port-forwarding
sudo pkill -f "kubectl port-forward"
nohup sudo kubectl port-forward -n news2market --address 0.0.0.0 service/frontend-service 8080:80 > /tmp/pf-frontend.log 2>&1 &
nohup sudo kubectl port-forward -n news2market --address 0.0.0.0 service/api-gateway-service 8000:8000 > /tmp/pf-api.log 2>&1 &

# Reiniciar un pod problemático
sudo kubectl delete pod <POD_NAME> -n news2market

# Ver logs si hay error
sudo kubectl logs -n news2market <POD_NAME> --tail=50
```

---

## ⏱️ TIMING ESTIMADO

| Sección | Duración | Total Acumulado |
|---------|----------|-----------------|
| Introducción | 0:30 | 0:30 |
| Arquitectura | 0:30 | 1:00 |
| Parte 1: Cluster | 0:45 | 1:45 |
| Parte 2: Métricas | 1:00 | 2:45 |
| Parte 3: Web | 0:45 | 3:30 |
| Parte 4: Escalado | 1:00 | 4:30 |
| Parte 5: Persistencia | 0:30 | 5:00 |
| Parte 6: Evidencia | 0:20 | 5:20 |
| Conclusión | 0:30 | 5:50 |

**Duración total**: 5-6 minutos

---

## 💡 TIPS PARA UNA BUENA GRABACIÓN

1. **Practica primero**: Ejecuta todos los comandos una vez antes de grabar
2. **Limpia la terminal**: `clear` antes de empezar
3. **Aumenta el tamaño de fuente**: Para que se vea bien en video
4. **No apresures**: Es mejor un video de 6 minutos claro que uno de 3 minutos confuso
5. **Destaca lo importante**: Pausa cuando muestres resultados clave
6. **Prepara plan B**: Ten comandos de respaldo si algo no responde
7. **Graba en 1080p**: Calidad mínima recomendada
8. **Audio claro**: Usa micrófono externo si es posible

---

## 🎯 JUSTIFICACIÓN ACADÉMICA (Para incluir en informe escrito)

### ¿Por qué EC2 + Minikube en lugar de EKS?

**Restricciones de AWS Learner Lab:**
- No permite crear roles IAM (requerido por EKS)
- No permite usar servicios administrados complejos
- Limitado a $50 USD de crédito

**Ventajas de EC2 + Minikube:**
- Cumple con todos los objetivos de aprendizaje del curso
- Demuestra conocimiento de Kubernetes sin depender de servicios administrados
- Control total sobre el cluster (configuración, troubleshooting)
- Significativamente más económico ($0.04/hora vs $0.10/hora de EKS)
- Instalación y configuración manual = mayor aprendizaje

**Cumplimiento de requisitos académicos:**
✅ Kubernetes funcionando
✅ Orquestación de contenedores
✅ Escalabilidad (HPA)
✅ Persistencia (PV/PVC)
✅ Despliegue en cloud (AWS)
✅ Alta disponibilidad (réplicas)

---

## 📧 INFORMACIÓN DE CONTACTO

**Estudiante**: Iván David Ausecha Salamanca  
**Curso**: Infraestructuras Paralelas y Distribuidas  
**Proyecto**: News2Market - Sistema de Análisis de Correlación Noticias-COLCAP  
**Fecha**: 31 de Diciembre de 2025

---

**¡Éxito en tu presentación! 🚀**
