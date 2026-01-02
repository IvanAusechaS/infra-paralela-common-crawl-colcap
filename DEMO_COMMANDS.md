# 🎬 Comandos para Demostración en Vivo
## News2Market - Presentación

---

## 🔌 CONEXIÓN INICIAL

```bash
# Conectar a EC2 (mantener esta terminal abierta)
ssh -i ~/.ssh/news2market-key.pem ubuntu@13.220.67.109
```

---

## 📊 DEMO 1: Estado Inicial del Sistema

### Terminal 1: Estado General

```bash
# Ver todos los pods
sudo kubectl get pods -n news2market

# Ver servicios
sudo kubectl get services -n news2market

# Ver HPA
sudo kubectl get hpa -n news2market
```

**Explicar:**
- 8 pods corriendo
- 2 réplicas de text-processor (mínimo del HPA)
- Uso de recursos bajo

---

## 📈 DEMO 2: Métricas en Tiempo Real

### Terminal 1: Métricas Continuas

```bash
# Monitoreo continuo (se actualiza cada 2 segundos)
watch -n 2 'sudo kubectl top pods -n news2market'
```

**Mantener esta terminal visible durante toda la demo**

### Terminal 2: Métricas del Nodo

```bash
# Recursos totales del nodo
sudo kubectl top node

# Descripción detallada del nodo
sudo kubectl describe node minikube | grep -A 10 "Allocated resources"
```

**Explicar:**
- CPU: ~215m/2000m (10% utilizado)
- Memoria: ~1613Mi/3834Mi (42% utilizado)
- Todavía hay capacidad para escalar

---

## 🚀 DEMO 3: Escalado Manual

### Paso 1: Ver estado actual

```bash
# Contar pods de text-processor
sudo kubectl get pods -n news2market | grep text-processor | wc -l
# Output esperado: 2
```

### Paso 2: Escalar a 5 réplicas

```bash
# Comando de escalado
sudo kubectl scale deployment text-processor --replicas=5 -n news2market
```

### Paso 3: Ver creación en tiempo real

```bash
# Ver pods creándose en vivo
sudo kubectl get pods -n news2market -w
```

**Presionar Ctrl+C cuando todos estén Running (1-2 minutos)**

### Paso 4: Verificar resultado

```bash
# Contar nuevas réplicas
sudo kubectl get pods -n news2market | grep text-processor

# Ver métricas de todas las réplicas
sudo kubectl top pods -n news2market | grep text-processor
```

**Explicar:**
- Ahora hay 5 pods de text-processor
- Kubernetes distribuye la carga automáticamente
- Cada pod consume ~2m CPU y ~65-70MB RAM

---

## 📝 DEMO 4: Logs en Tiempo Real

### Terminal 1: Logs del Text Processor

```bash
# Ver logs de todos los text-processor
sudo kubectl logs -f deployment/text-processor -n news2market
```

### Terminal 2: Logs del API Gateway

```bash
# Ver logs del API Gateway
sudo kubectl logs -f deployment/api-gateway -n news2market --tail=20
```

**Mantener ambas terminales visibles mientras se ejecutan requests**

---

## 🧪 DEMO 5: Prueba de Procesamiento

### En el Navegador:
1. Abrir: http://13.220.67.109:8080
2. Ir a "Text Processing"
3. Pegar texto de prueba
4. Click en "Process Text"

### En Terminal (simultáneamente):

```bash
# Ver logs reaccionando en tiempo real
sudo kubectl logs -f deployment/text-processor -n news2market
```

**Explicar:**
- El request llega al API Gateway
- Se enruta al text-processor
- Kubernetes balancea entre las 5 réplicas
- Redis maneja la cola de trabajos

---

## 📊 DEMO 6: Análisis de Correlación

### En el Navegador:
1. Ir a "Correlation Analysis"
2. Configurar:
   - Start Date: `2024-01-01`
   - End Date: `2024-12-31`
   - Lag Days: `1`
3. Click en "Analyze Correlation"

### En Terminal:

```bash
# Ver logs del correlation-service
sudo kubectl logs -f deployment/correlation-service -n news2market
```

**Explicar:**
- Sistema genera datos mock de COLCAP
- Genera métricas de noticias
- Calcula correlaciones de Pearson
- Genera insights estadísticos

---

## 🔄 DEMO 7: HPA (Horizontal Pod Autoscaler)

### Ver configuración del HPA

```bash
# Descripción completa del HPA
sudo kubectl describe hpa text-processor-hpa -n news2market
```

**Explicar configuración:**
- Min replicas: 2
- Max replicas: 10
- Target CPU: 70%
- Target Memory: 80%
- Actualmente: 2 réplicas (porque no hay carga)

### Ver métricas actuales del HPA

```bash
# Ver HPA en modo watch
sudo kubectl get hpa -n news2market -w
```

**Explicar:**
- TARGETS muestra: cpu: 4%/70%, memory: 52%/80%
- Si CPU > 70% o Memory > 80%, escala automáticamente
- Descala después de 5 minutos de bajo uso

---

## 💾 DEMO 8: Persistencia de Datos

### Ver volúmenes persistentes

```bash
# Ver PVCs
sudo kubectl get pvc -n news2market

# Describir PVC de PostgreSQL
sudo kubectl describe pvc postgres-storage-postgres-0 -n news2market

# Describir PVC de Redis
sudo kubectl describe pvc redis-storage-redis-0 -n news2market
```

### Verificar datos en PostgreSQL

```bash
# Conectar a PostgreSQL
sudo kubectl exec -n news2market postgres-0 -- psql -U news2market -d news2market -c "\dt *.*"

# Contar artículos
sudo kubectl exec -n news2market postgres-0 -- psql -U news2market -d news2market -c "SELECT COUNT(*) FROM commoncrawl.news_articles;"

# Ver últimos artículos
sudo kubectl exec -n news2market postgres-0 -- psql -U news2market -d news2market -c "SELECT id, title, date FROM commoncrawl.news_articles LIMIT 5;"
```

**Explicar:**
- PostgreSQL: 20GB de almacenamiento persistente
- Redis: 5GB de almacenamiento persistente
- Los datos sobreviven a reinicios de pods

---

## 🔍 DEMO 9: Debugging y Troubleshooting

### Ver eventos del cluster

```bash
# Eventos recientes
sudo kubectl get events -n news2market --sort-by='.lastTimestamp' | tail -20
```

### Describir un pod específico

```bash
# Obtener nombre de un pod
POD=$(sudo kubectl get pods -n news2market -l app=text-processor -o jsonpath='{.items[0].metadata.name}')

# Describir el pod
sudo kubectl describe pod $POD -n news2market
```

### Ver recursos de un pod

```bash
# Métricas detalladas
sudo kubectl top pod $POD -n news2market
```

---

## ⚡ DEMO 10: Rollback y Recovery

### Reiniciar un deployment

```bash
# Reiniciar text-processor (rolling update)
sudo kubectl rollout restart deployment/text-processor -n news2market

# Ver progreso del rollout
sudo kubectl rollout status deployment/text-processor -n news2market
```

**Explicar:**
- Rolling update: no hay downtime
- Kubernetes crea nuevos pods antes de eliminar los viejos
- El servicio permanece disponible todo el tiempo

---

## 🔙 DEMO 11: Volver a Estado Original

### Escalar de vuelta a 2 réplicas

```bash
# Reducir a 2 réplicas
sudo kubectl scale deployment text-processor --replicas=2 -n news2market

# Ver pods terminando
sudo kubectl get pods -n news2market -w
```

**Presionar Ctrl+C cuando queden solo 2**

### Verificar estado final

```bash
# Confirmar 2 réplicas
sudo kubectl get pods -n news2market | grep text-processor

# Ver HPA volviendo a normal
sudo kubectl get hpa -n news2market
```

---

## 📸 COMANDOS PARA CAPTURAS DE PANTALLA

### Dashboard completo

```bash
# Un solo comando con todo el estado
clear && echo "=== NODES ===" && \
sudo kubectl get nodes && \
echo -e "\n=== PODS ===" && \
sudo kubectl get pods -n news2market && \
echo -e "\n=== SERVICES ===" && \
sudo kubectl get services -n news2market && \
echo -e "\n=== HPA ===" && \
sudo kubectl get hpa -n news2market && \
echo -e "\n=== METRICS ===" && \
sudo kubectl top pods -n news2market
```

### Estado compacto

```bash
# Resumen en una línea por recurso
sudo kubectl get all -n news2market
```

---

## 🎯 SECUENCIA RECOMENDADA PARA LA DEMO

1. **Terminal 1:** `watch -n 2 'sudo kubectl top pods -n news2market'` (dejar corriendo)
2. **Navegador:** Abrir http://13.220.67.109:8080
3. **Terminal 2:** Mostrar estado inicial
4. **Terminal 2:** Escalar a 5 réplicas
5. **Terminal 1:** Ver aumento de recursos (automático)
6. **Navegador:** Probar procesamiento de texto
7. **Terminal 3:** Ver logs en tiempo real
8. **Navegador:** Probar correlación
9. **Terminal 2:** Mostrar HPA
10. **Terminal 2:** Volver a 2 réplicas

---

## ⌨️ ATAJOS DE TECLADO ÚTILES

- `Ctrl+C` - Detener watch o logs en tiempo real
- `Ctrl+Z` - Suspender proceso (luego `bg` para background)
- `Ctrl+L` - Limpiar pantalla
- `↑` / `↓` - Navegar historial de comandos
- `Tab` - Autocompletar

---

## 🚨 COMANDOS DE EMERGENCIA

### Si algo falla:

```bash
# Ver pods con problemas
sudo kubectl get pods -n news2market | grep -v Running

# Logs de un pod con error
sudo kubectl logs POD_NAME -n news2market --previous

# Reiniciar todo el namespace (ÚLTIMO RECURSO)
sudo kubectl delete pods --all -n news2market
# Los deployments recrearán los pods automáticamente
```

### Si port-forwards fallan:

```bash
# Reiniciar port-forwards
pkill -f "kubectl.*port-forward" 2>/dev/null || true
sudo kubectl port-forward -n news2market svc/api-gateway-service 8000:8000 --address 0.0.0.0 > /tmp/pf-api.log 2>&1 &
sudo kubectl port-forward -n news2market svc/frontend-service 8080:80 --address 0.0.0.0 > /tmp/pf-frontend.log 2>&1 &
```

---

## 📋 CHECKLIST DE DEMOS

- [ ] Demo 1: Estado inicial ✓
- [ ] Demo 2: Métricas en tiempo real ✓
- [ ] Demo 3: Escalado manual ✓
- [ ] Demo 4: Logs en tiempo real ✓
- [ ] Demo 5: Procesamiento de texto ✓
- [ ] Demo 6: Análisis de correlación ✓
- [ ] Demo 7: HPA explicado ✓
- [ ] Demo 8: Persistencia de datos ✓
- [ ] Demo 9: Debugging ✓
- [ ] Demo 10: Rollback ✓
- [ ] Demo 11: Volver a estado original ✓

---

**¡Todo listo para una demo exitosa! 🚀**
