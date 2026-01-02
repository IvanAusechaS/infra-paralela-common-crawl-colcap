# 🖥️ Setup de Terminales para Presentación
## Configuración Visual Óptima

---

## 📐 LAYOUT DE PANTALLA RECOMENDADO

```
┌────────────────────────────────────────────────────────┐
│                    DIAPOSITIVAS                        │
│                   (Presentación)                       │
└────────────────────────────────────────────────────────┘

Durante las demos técnicas:

┌─────────────────────────┬──────────────────────────────┐
│                         │                              │
│      VS CODE            │     TERMINAL 1               │
│   (archivos k8s/)       │   (comandos principales)     │
│                         │                              │
│                         │                              │
├─────────────────────────┼──────────────────────────────┤
│                         │                              │
│   NAVEGADOR             │     TERMINAL 2               │
│ (Frontend + API)        │  (watch metrics)             │
│                         │                              │
└─────────────────────────┴──────────────────────────────┘
```

---

## 🎨 CONFIGURACIÓN DE TERMINALES

### Terminal 1: Comandos Principales (SSH EC2)

**Tamaño de fuente:** 16-18pt  
**Color scheme:** Dark background con texto verde/blanco  
**Posición:** Superior derecha o centro  

**Preparación inicial:**
```bash
# Conectar y limpiar
ssh -i ~/.ssh/news2market-key.pem ubuntu@13.220.67.109
clear

# Prompt limpio (opcional)
export PS1='\[\e[1;32m\]k8s@news2market\[\e[0m\]:\[\e[1;34m\]\w\[\e[0m\]\$ '
```

**Mantener listo para:**
- `sudo kubectl get pods -n news2market`
- `sudo kubectl scale deployment text-processor --replicas=5 -n news2market`
- `sudo kubectl logs -f deployment/text-processor -n news2market`

---

### Terminal 2: Métricas en Tiempo Real

**Tamaño de fuente:** 14-16pt  
**Color scheme:** Dark background  
**Posición:** Inferior derecha o panel lateral  

**Comando permanente:**
```bash
ssh -i ~/.ssh/news2market-key.pem ubuntu@13.220.67.109
watch -n 2 'sudo kubectl top pods -n news2market'
```

**Este terminal debe estar SIEMPRE VISIBLE durante las demos**

---

### Terminal 3 (Opcional): Logs en Tiempo Real

**Tamaño de fuente:** 12-14pt  
**Posición:** Tab adicional o segundo monitor  

**Para mostrar durante procesamiento:**
```bash
ssh -i ~/.ssh/news2market-key.pem ubuntu@13.220.67.109
sudo kubectl logs -f deployment/text-processor -n news2market
```

---

## 🎨 CONFIGURACIÓN DE COLORES (GNOME Terminal)

### Preferencias → Perfiles → Editar

```bash
# Abrir configuración de perfil
gnome-terminal --preferences

# O desde terminal:
dconf-editor /org/gnome/terminal/legacy/profiles:/
```

**Configuración recomendada:**
- **Background:** #1E1E1E (gris oscuro)
- **Foreground:** #D4D4D4 (blanco suave)
- **Palette:** Monokai o Solarized Dark
- **Font:** Monospace 16 o JetBrains Mono 16
- **Transparency:** 95% (ligeramente transparente)

---

## 📏 TAMAÑOS DE FUENTE POR USO

```
Proyector/Pantalla grande:
- Comandos principales: 18-20pt
- Watch metrics: 16-18pt
- VS Code: 16-18pt
- Navegador: Zoom 125-150%

Monitor normal (demo local):
- Comandos principales: 14-16pt
- Watch metrics: 12-14pt
- VS Code: 14-16pt
- Navegador: Zoom 100-110%
```

---

## ⌨️ SHORTCUTS ÚTILES PARA LA DEMO

### Terminal
```bash
Ctrl + L          # Limpiar pantalla (mantiene historial)
Ctrl + Shift + +  # Aumentar fuente
Ctrl + Shift + -  # Disminuir fuente
Ctrl + Shift + T  # Nueva pestaña
Ctrl + Shift + W  # Cerrar pestaña
Ctrl + PageUp     # Pestaña anterior
Ctrl + PageDown   # Pestaña siguiente
```

### VS Code
```bash
Ctrl + B          # Toggle sidebar
Ctrl + J          # Toggle terminal integrado
Ctrl + +          # Zoom in
Ctrl + -          # Zoom out
Ctrl + P          # Quick file open
Ctrl + Shift + E  # Explorer
F11               # Fullscreen
```

### Navegador
```bash
Ctrl + T          # Nueva pestaña
Ctrl + Tab        # Cambiar pestaña
Ctrl + Shift + T  # Reabrir pestaña cerrada
Ctrl + +          # Zoom in
Ctrl + -          # Zoom out
F5                # Refresh
F11               # Fullscreen
F12               # DevTools
```

---

## 🎬 SCRIPT DE PREPARACIÓN DE VENTANAS

### Script Bash para posicionar ventanas (Linux)

```bash
#!/bin/bash
# prepare-windows.sh

# Instalar wmctrl si no existe
# sudo apt install wmctrl

# Abrir VS Code
code ~/Documentos/infra-paralela-common-crawl-colcap &
sleep 2

# Abrir Terminal 1 (comandos)
gnome-terminal --title="K8s Commands" --geometry=120x30+1920+0 -- \
    ssh -i ~/.ssh/news2market-key.pem ubuntu@13.220.67.109 &
sleep 1

# Abrir Terminal 2 (metrics)
gnome-terminal --title="K8s Metrics" --geometry=120x15+1920+600 -- \
    bash -c "ssh -i ~/.ssh/news2market-key.pem ubuntu@13.220.67.109 \
    'watch -n 2 \"sudo kubectl top pods -n news2market\"'" &
sleep 1

# Abrir navegador
firefox "http://13.220.67.109:8080" &
sleep 2

# Posicionar ventanas con wmctrl
wmctrl -r "Visual Studio Code" -e 0,0,0,960,1080
wmctrl -r "K8s Commands" -e 0,960,0,960,720
wmctrl -r "K8s Metrics" -e 0,960,720,960,360
wmctrl -r "Mozilla Firefox" -e 0,0,720,960,360

echo "✅ Ventanas configuradas para presentación"
```

---

## 📝 PLANTILLA DE COMANDOS PRE-PREPARADOS

### Crear archivo con comandos copiables

**Archivo:** `~/demo-commands.txt`

```bash
# ========================================
# COMANDOS PARA COPIAR DURANTE LA DEMO
# ========================================

# ESTADO INICIAL
sudo kubectl get pods -n news2market
sudo kubectl get hpa -n news2market
sudo kubectl top pods -n news2market

# ESCALAR A 5 REPLICAS
sudo kubectl scale deployment text-processor --replicas=5 -n news2market
sudo kubectl get pods -n news2market -w

# VER LOGS
sudo kubectl logs -f deployment/text-processor -n news2market
sudo kubectl logs -f deployment/api-gateway -n news2market

# DESCRIBIR HPA
sudo kubectl describe hpa text-processor-hpa -n news2market

# METRICAS CONTINUAS
watch -n 2 'sudo kubectl top pods -n news2market'

# VOLVER A 2 REPLICAS
sudo kubectl scale deployment text-processor --replicas=2 -n news2market

# RESUMEN COMPLETO
sudo kubectl get all -n news2market

# VERIFICAR DATOS EN POSTGRES
sudo kubectl exec -n news2market postgres-0 -- psql -U news2market -d news2market -c "SELECT COUNT(*) FROM commoncrawl.news_articles;"

# EVENTOS RECIENTES
sudo kubectl get events -n news2market --sort-by='.lastTimestamp' | tail -20
```

**Mantener este archivo abierto en VS Code para copiar-pegar rápido**

---

## 🎥 SETUP PARA GRABACIÓN (Opcional)

### Si vas a grabar la demo:

```bash
# Instalar SimpleScreenRecorder
sudo apt install simplescreenrecorder

# O usar ffmpeg
ffmpeg -f x11grab -framerate 30 -video_size 1920x1080 -i :0.0 \
       -f pulse -ac 2 -i default \
       -c:v libx264 -crf 23 -preset medium \
       -c:a aac -b:a 192k \
       demo-news2market.mp4

# Detener con Ctrl+C
```

**Configuración recomendada:**
- Resolution: 1920x1080
- FPS: 30
- Audio: Micrófono + Audio del sistema
- Duración: Grabar toda la sección de demo (12:30 - 14:00)

---

## 🖱️ SETTINGS DE VS CODE PARA PRESENTACIÓN

### Archivo: `.vscode/settings.json`

```json
{
  "editor.fontSize": 16,
  "terminal.integrated.fontSize": 14,
  "editor.lineHeight": 24,
  "editor.minimap.enabled": false,
  "workbench.colorTheme": "Monokai Dimmed",
  "editor.renderWhitespace": "none",
  "breadcrumbs.enabled": true,
  "explorer.compactFolders": false,
  "files.exclude": {
    "**/.git": true,
    "**/node_modules": true,
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### Extensiones útiles:
- Kubernetes (ms-kubernetes-tools.vscode-kubernetes-tools)
- YAML (redhat.vscode-yaml)
- Python (ms-python.python)
- Docker (ms-azuretools.vscode-docker)

---

## 🎯 CHECKLIST DE CONFIGURACIÓN VISUAL

### Antes de la presentación:

**VS Code:**
- [ ] Zoom al 125-150%
- [ ] Sidebar abierto mostrando estructura k8s/
- [ ] Terminal integrado cerrado (usar externos)
- [ ] Tema oscuro configurado
- [ ] Minimap deshabilitado

**Terminal 1 (Comandos):**
- [ ] Fuente 16-18pt
- [ ] SSH conectado a EC2
- [ ] Prompt limpio
- [ ] Clear ejecutado
- [ ] demo-commands.txt abierto para referencia

**Terminal 2 (Metrics):**
- [ ] Fuente 14-16pt
- [ ] watch corriendo
- [ ] Posicionado visible todo el tiempo
- [ ] No se cierra durante toda la demo

**Navegador:**
- [ ] Frontend en tab 1: http://13.220.67.109:8080
- [ ] API health en tab 2: http://13.220.67.109:8000/api/v1/health
- [ ] Zoom 110-125%
- [ ] DevTools cerrado (abrir solo si necesario)
- [ ] Pestañas innecesarias cerradas

**Sistema:**
- [ ] Notificaciones silenciadas
- [ ] WiFi conectado y estable
- [ ] Batería cargada (si es laptop)
- [ ] Aplicaciones innecesarias cerradas
- [ ] Volumen del sistema apropiado

---

## 🎨 TEMAS RECOMENDADOS

### Terminal (GNOME Terminal)
- **Solarized Dark** - Professional, fácil de leer
- **Monokai** - Popular, buenos contrastes
- **Gruvbox Dark** - Cálido, agradable a la vista
- **Dracula** - Moderno, colores vivos

### VS Code
- **Monokai Dimmed** - Oscuro pero no cansa
- **GitHub Dark** - Familiar, profesional
- **One Dark Pro** - Popular, bien balanceado
- **Night Owl** - Diseñado para presentaciones

---

## 📊 DISPOSICIÓN RECOMENDADA POR SECCIÓN

### 10:00 - 11:00 | Kubernetes (Diapositivas + VS Code)
```
50% Diapositivas | 50% VS Code mostrando:
- k8s/namespace.yaml
- k8s/text-processor-deployment.yaml
- k8s/text-processor-hpa.yaml
- k8s/postgres-statefulset.yaml
```

### 11:00 - 12:30 | AWS Deployment (Diapositivas + Terminal)
```
30% Diapositivas | 70% Terminal mostrando:
- kubectl get nodes
- kubectl get pods
- kubectl describe
- kubectl top
```

### 12:30 - 14:00 | Demo en Vivo (4 ventanas)
```
┌──────────────┬──────────────┐
│  Navegador   │  Terminal 1  │
│  (Frontend)  │  (Comandos)  │
├──────────────┼──────────────┤
│   VS Code    │  Terminal 2  │
│   (Código)   │  (Metrics)   │
└──────────────┴──────────────┘
```

### 14:00 - 15:00 | Conclusiones (Diapositivas)
```
100% Diapositivas
(Terminales en background mostrando sistema estable)
```

---

## 🚀 SCRIPT DE INICIO RÁPIDO

```bash
#!/bin/bash
# start-demo-env.sh

echo "🚀 Iniciando entorno de presentación..."

# 1. Verificar sistema
./scripts/prepare-presentation.sh

# 2. Aumentar fuente de terminales
gsettings set org.gnome.desktop.interface text-scaling-factor 1.25

# 3. Abrir VS Code
code ~/Documentos/infra-paralela-common-crawl-colcap &

# 4. Esperar y abrir documentos clave
sleep 3
code ~/Documentos/infra-paralela-common-crawl-colcap/GUION_PRESENTACION.md &
code ~/Documentos/infra-paralela-common-crawl-colcap/DEMO_COMMANDS.md &

# 5. Abrir terminales
gnome-terminal --title="K8s-Commands" --geometry=120x30 &
gnome-terminal --title="K8s-Metrics" --geometry=120x15 &

# 6. Abrir frontend en navegador
firefox "http://13.220.67.109:8080" &

echo "✅ Entorno listo para presentación"
echo "🎯 Conecta SSH manualmente en las terminales"
echo "📝 Revisa GUION_PRESENTACION.md para la secuencia"
```

---

**¡Todo configurado para una presentación visual impecable! 🎬✨**
