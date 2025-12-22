# Diseño del Frontend - News2Market

## Visión General

El frontend de News2Market es una aplicación web moderna construida con React y Vite, diseñada para proporcionar una experiencia de usuario fluida y profesional en el análisis de correlación entre noticias y mercados financieros.

## Stack Tecnológico

- **Framework**: React 19.2.0
- **Build Tool**: Vite 7.2.4
- **Lenguaje**: TypeScript 5.x
- **Estilos**: SASS/SCSS con módulos
- **Enrutamiento**: React Router DOM 7.1.1
- **Notificaciones**: react-toastify 11.0.3
- **Cliente HTTP**: axios 1.7.9
- **Gráficos**: Chart.js + react-chartjs-2
- **Exportación PDF**: jsPDF 2.x

## Estructura de Archivos

```
frontend/
├── public/                      # Archivos estáticos
├── src/
│   ├── assets/                  # SVGs, imágenes, iconos
│   │   ├── logo.svg            # Logo principal (News2Market)
│   │   └── icons/              # Iconos del sistema (8 iconos)
│   ├── components/             # Componentes reutilizables
│   │   ├── Navbar.tsx          # Barra de navegación fija
│   │   ├── Navbar.scss
│   │   ├── Footer.tsx          # Pie de página con sitemap
│   │   ├── Footer.scss
│   │   ├── CorrelationChart.tsx # Gráfico de correlaciones
│   │   └── CorrelationChart.scss
│   ├── pages/                  # Páginas de la aplicación
│   │   ├── HomePage.tsx        # Landing page
│   │   ├── HomePage.scss
│   │   ├── AnalysisPage.tsx    # Configuración de análisis
│   │   ├── AnalysisPage.scss
│   │   ├── ResultsPage.tsx     # Resultados históricos
│   │   └── ResultsPage.scss
│   ├── services/               # Lógica de negocio
│   │   └── api.ts              # Cliente API con axios
│   ├── styles/                 # Estilos globales
│   │   └── global.scss         # Design system completo
│   ├── App.tsx                 # Componente raíz
│   ├── App.css                 # Estilos de layout
│   ├── main.tsx                # Entry point
│   └── index.css               # Reset CSS
├── index.html                  # HTML principal
├── package.json                # Dependencias
├── tsconfig.json               # Configuración TypeScript
├── vite.config.ts              # Configuración Vite
└── Dockerfile                  # Imagen Docker

```

## Design System

### Tipografía

**Fuentes**:

- **Headings**: Days One (Google Fonts) - Profesional y distintiva
- **Body**: Rubik (Google Fonts) - Legible y moderna

**Tamaños**:

```scss
$font-size-xs: 0.75rem; // 12px
$font-size-sm: 0.875rem; // 14px
$font-size-base: 1rem; // 16px
$font-size-lg: 1.125rem; // 18px
$font-size-xl: 1.25rem; // 20px
$font-size-2xl: 1.5rem; // 24px
$font-size-3xl: 1.875rem; // 30px
$font-size-4xl: 2.25rem; // 36px
$font-size-5xl: 3rem; // 48px
```

**Pesos**:

```scss
$font-weight-light: 300;
$font-weight-normal: 400;
$font-weight-medium: 500;
$font-weight-semibold: 600;
$font-weight-bold: 700;
```

### Paleta de Colores

**Colores primarios**:

```scss
$primary-color: #1e40af; // Deep Blue - marca principal
$primary-light: #3b82f6; // Hover states
$primary-dark: #1e3a8a; // Active states

$secondary-color: #059669; // Emerald - énfasis
$secondary-light: #10b981;
$secondary-dark: #047857;
```

**Colores de estado**:

```scss
$success-color: #059669; // Verde - éxito
$danger-color: #dc2626; // Rojo - errores
$warning-color: #f59e0b; // Ámbar - advertencias
$info-color: #0ea5e9; // Cyan - información
```

**Colores de texto**:

```scss
$text-primary: #111827; // Negro - texto principal
$text-secondary: #6b7280; // Gris - texto secundario
$text-tertiary: #9ca3af; // Gris claro - metadata
$text-inverse: #ffffff; // Blanco - texto sobre oscuro
```

**Colores de fondo**:

```scss
$bg-primary: #ffffff; // Blanco - fondo principal
$bg-secondary: #f9fafb; // Gris muy claro
$bg-tertiary: #f3f4f6; // Gris claro
$bg-dark: #111827; // Negro - fondos oscuros (CTA)
```

### Espaciado

Sistema de espaciado consistente basado en múltiplos de 4px:

```scss
$spacing-xs: 0.25rem; // 4px
$spacing-sm: 0.5rem; // 8px
$spacing-md: 1rem; // 16px
$spacing-lg: 1.5rem; // 24px
$spacing-xl: 2rem; // 32px
$spacing-2xl: 3rem; // 48px
$spacing-3xl: 4rem; // 64px
```

### Border Radius

```scss
$radius-sm: 0.25rem; // 4px
$radius-md: 0.5rem; // 8px
$radius-lg: 0.75rem; // 12px
$radius-xl: 1rem; // 16px
$radius-2xl: 1.5rem; // 24px
$radius-full: 9999px; // Círculo
```

### Sombras

```scss
$shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
$shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
$shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
$shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
$shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
```

### Transiciones

```scss
$transition-fast: 150ms ease;
$transition-base: 250ms ease;
$transition-slow: 350ms ease;
$transition-all: all 250ms ease;
```

## Componentes

### 1. Navbar

**Ubicación**: `src/components/Navbar.tsx`

**Características**:

- Fijo en la parte superior (`position: fixed`)
- Altura: 70px
- Logo clickable (navegación a Home)
- Enlaces de navegación: Inicio, Análisis, Resultados
- Responsive con menú hamburguesa en móvil
- Active state para página actual

**Propiedades**:

```typescript
// Sin props - navegación global
```

**Estilos**: `Navbar.scss`

- Background: `$bg-primary` con `backdrop-filter: blur(10px)`
- Shadow: `$shadow-md`
- Z-index: 1000

---

### 2. Footer

**Ubicación**: `src/components/Footer.tsx`

**Características**:

- Pie de página con sitemap
- Información de copyright
- Enlaces externos (GitHub, documentación)
- Logo y descripción breve

**Estructura**:

```
┌─────────────────────────────────────┐
│ Logo          Navegación    Recursos│
│ Descripción   - Inicio      - Docs  │
│               - Análisis    - GitHub│
│               - Resultados           │
│                                      │
│ © 2025 News2Market                   │
└─────────────────────────────────────┘
```

---

### 3. CorrelationChart

**Ubicación**: `src/components/CorrelationChart.tsx`

**Características**:

- Visualización de correlaciones con Chart.js
- Barras horizontales para cada métrica
- Colores: verde (correlación positiva), rojo (negativa)
- Tooltips con p-values

**Props**:

```typescript
interface CorrelationChartProps {
  correlations: Record<string, number>;
  pValues: Record<string, number>;
}
```

**Ejemplo**:

```tsx
<CorrelationChart
  correlations={{ volume: 0.75, keywords: 0.82, sentiment: -0.23 }}
  pValues={{ volume: 0.001, keywords: 0.0003, sentiment: 0.15 }}
/>
```

---

## Páginas

### 1. HomePage (Landing Page)

**Ruta**: `/`  
**Archivo**: `src/pages/HomePage.tsx`

**Secciones**:

1. **Hero**
   - Título principal: "Análisis de Correlación Noticias-Mercado"
   - Descripción del sistema
   - CTA button: "Iniciar análisis"
2. **Features Grid** (3 columnas)

   - Adquisición de datos
   - Procesamiento inteligente
   - Análisis estadístico

3. **System Status**

   - Estado de servicios (health check)
   - Indicadores visuales (verde/rojo)
   - Última actualización

4. **CTA Section** (fondo oscuro)
   - Call-to-action final
   - Button: "Comenzar ahora"
   - Separado visualmente con `$bg-dark`

**Características**:

- Animaciones CSS (fadeIn, slideUp)
- Carga de estado del sistema en useEffect
- Notificaciones no duplicadas (flag de control)

---

### 2. AnalysisPage

**Ruta**: `/analysis`  
**Archivo**: `src/pages/AnalysisPage.tsx`

**Funcionalidad**:

- Configuración de parámetros de análisis
- Cálculo de correlación en tiempo real
- Visualización de resultados

**Formulario**:

```typescript
interface FormState {
  startDate: string; // YYYY-MM-DD
  endDate: string; // YYYY-MM-DD
  lagDays: number; // 0-30
  selectedMetrics: string[]; // ['volume', 'keywords', 'sentiment']
}
```

**Campos**:

- **Fecha de inicio**: `<input type="date">`
- **Fecha de fin**: `<input type="date">`
- **Días de lag**: `<input type="number" min="0" max="30">`
- **Métricas**: Checkboxes múltiples

**Validaciones**:

- Fechas requeridas
- Fecha inicio < Fecha fin
- Al menos 1 métrica seleccionada

**Flujo**:

1. Usuario completa formulario
2. Click en "Calcular correlación"
3. Loading state (botón deshabilitado)
4. Llamada a API: `POST /api/v1/correlation/correlate`
5. Notificación de éxito
6. Renderizado de resultados con gráfico

**Resultados mostrados**:

- Job ID
- Tamaño de muestra
- Gráfico de correlaciones
- Lista de insights

---

### 3. ResultsPage

**Ruta**: `/results`  
**Archivo**: `src/pages/ResultsPage.tsx`

**Funcionalidad**:

- Listado de análisis históricos
- Visualización de resultados previos
- Exportación a PDF

**Carga de datos**:

```typescript
useEffect(() => {
  // GET /api/v1/correlation/results
  fetchResults();
}, []);
```

**Estructura de resultado**:

```
┌──────────────────────────────┐
│ Análisis #1          [PDF ↓] │
│ Job ID: a3f2b8c1             │
├──────────────────────────────┤
│ Muestra: 30 días             │
├──────────────────────────────┤
│ Correlaciones:               │
│ volume    [████████] 0.750   │
│ keywords  [█████████] 0.820  │
│ sentiment [███] -0.230       │
├──────────────────────────────┤
│ Insights principales:        │
│ • Correlación fuerte...      │
│ • Significancia estadística..│
└──────────────────────────────┘
```

**Funcionalidad PDF**:

- Botón "Descargar PDF" en cada card
- Generación con jsPDF
- Contenido: job_id, fechas, correlaciones, p-values, insights
- Nombre: `analisis-correlacion-{job_id}.pdf`

**Empty state**:

- Mensaje cuando no hay resultados
- Icono ilustrativo
- CTA para realizar primer análisis

---

## Servicios

### API Client

**Archivo**: `src/services/api.ts`

**Configuración**:

```typescript
const apiClient = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});
```

**Interceptores**:

- Request: Logging de peticiones
- Response: Manejo global de errores
- Error: Notificaciones toast automáticas

**Métodos**:

```typescript
// Health check del sistema
export const checkSystemHealth = async (): Promise<SystemHealth>

// Calcular correlación
export const calculateCorrelation = async (
  request: CorrelationRequest
): Promise<CorrelationResponse>

// Obtener resultados históricos
export const getCorrelationResults = async (): Promise<CorrelationResponse[]>
```

**Tipos**:

```typescript
interface CorrelationRequest {
  start_date: string;
  end_date: string;
  metrics: string[];
  lag_days?: number;
}

interface CorrelationResponse {
  job_id: string;
  start_date: string;
  end_date: string;
  correlations: Record<string, number>;
  p_values: Record<string, number>;
  sample_size: number;
  insights: string[];
  colcap_data?: any[];
  news_metrics?: any[];
}
```

**Notificaciones**:

```typescript
export const notify = {
  success: (message: string) => toast.success(message),
  error: (message: string) => toast.error(message),
  info: (message: string) => toast.info(message),
  warning: (message: string) => toast.warn(message),
};
```

---

## Routing

**Configuración**: `src/App.tsx`

```typescript
<BrowserRouter>
  <Routes>
    <Route path="/" element={<HomePage />} />
    <Route path="/analysis" element={<AnalysisPage />} />
    <Route path="/results" element={<ResultsPage />} />
  </Routes>
</BrowserRouter>
```

**Navegación**:

- Declarativa con `<Link to="/path">`
- Programática con `useNavigate()`

---

## Responsive Design

### Breakpoints

```scss
$breakpoint-sm: 640px; // Móvil grande
$breakpoint-md: 768px; // Tablet
$breakpoint-lg: 1024px; // Desktop pequeño
$breakpoint-xl: 1280px; // Desktop grande
$breakpoint-2xl: 1536px; // Desktop XL
```

### Mixin Helper

```scss
@mixin responsive($breakpoint) {
  @if $breakpoint == "md" {
    @media (min-width: $breakpoint-md) {
      @content;
    }
  }
}
```

### Estrategia Mobile-First

- Estilos base para móvil
- Media queries para pantallas mayores
- Grids con `auto-fill` y `minmax()`
- Flex con `flex-wrap`

**Ejemplo**:

```scss
.features-grid {
  display: grid;
  grid-template-columns: 1fr; // Móvil: 1 columna
  gap: $spacing-lg;

  @media (min-width: $breakpoint-md) {
    grid-template-columns: repeat(3, 1fr); // Desktop: 3 columnas
  }
}
```

---

## Accesibilidad

### Características implementadas

1. **Semántica HTML**

   - Tags apropiados (`<header>`, `<main>`, `<nav>`, `<footer>`)
   - Jerarquía de headings correcta (h1 → h2 → h3)

2. **Navegación por teclado**

   - Focus visible en todos los elementos interactivos
   - Tab order lógico
   - Skip links (futuro)

3. **Screen readers**

   - `aria-label` en iconos
   - `alt` text en imágenes
   - `sr-only` class para texto oculto visualmente

4. **Contraste de colores**

   - Ratio mínimo WCAG AA (4.5:1 para texto)
   - Verificado con herramientas de contraste

5. **Estados de formularios**
   - Labels asociados con `htmlFor`
   - Mensajes de error descriptivos
   - Required fields indicados

---

## Heurísticas de Usabilidad (Nielsen)

### 1. Visibilidad del estado del sistema

✅ Implementado:

- Loading spinners durante peticiones
- Notificaciones toast de éxito/error
- System status en HomePage
- Botones disabled durante procesamiento

### 2. Relación sistema-mundo real

✅ Implementado:

- Lenguaje claro y no técnico
- Iconos representativos
- Fechas en formato comprensible

### 3. Control y libertad del usuario

✅ Implementado:

- Navegación clara con navbar
- Botón de "volver" en páginas
- Cancelación de formularios

### 4. Consistencia y estándares

✅ Implementado:

- Design system unificado
- Botones con mismos estilos
- Patrones de interacción consistentes

### 5. Prevención de errores

✅ Implementado:

- Validación de formularios antes de submit
- Input types apropiados (date, number)
- Min/max en campos numéricos

### 6. Reconocimiento vs. recuerdo

✅ Implementado:

- Labels descriptivos en formularios
- Placeholder text informativos
- Tooltips en iconos

### 7. Flexibilidad y eficiencia de uso

✅ Implementado:

- Valores por defecto razonables
- Checkboxes pre-seleccionados
- Atajos de teclado (futuro)

### 8. Diseño estético y minimalista

✅ Implementado:

- Sin elementos superfluos
- Espaciado generoso
- Jerarquía visual clara

### 9. Ayuda para errores

✅ Implementado:

- Mensajes de error descriptivos
- Notificaciones con contexto
- Sugerencias de corrección

### 10. Ayuda y documentación

🚧 Parcialmente implementado:

- Placeholder text como guías
- Tooltips (futuro)
- Documentación externa (este archivo)

---

## Performance

### Optimizaciones

1. **Code splitting**

   - Lazy loading de rutas (futuro)
   - Dynamic imports

2. **Memoización**

   - `useMemo` para cálculos costosos
   - `useCallback` para callbacks

3. **Reducción de re-renders**

   - State local vs. global
   - Componentes puros donde posible

4. **Assets**
   - SVGs en lugar de PNGs
   - Iconos inline (no icon fonts)

---

## Build y Deploy

### Desarrollo

```bash
npm install
npm run dev
# Servidor en http://localhost:5173
```

### Producción

```bash
npm run build
# Output en dist/
```

### Docker

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## Testing (Futuro)

### Unit Tests

- Jest + React Testing Library
- Tests de componentes
- Tests de utilidades

### E2E Tests

- Playwright o Cypress
- Flujos críticos
- Responsive testing

---

## Roadmap

- [ ] Dark mode
- [ ] Internacionalización (i18n)
- [ ] PWA (Progressive Web App)
- [ ] Tests automatizados
- [ ] Lazy loading de rutas
- [ ] Virtualized lists para resultados largos
- [ ] WebSocket para updates en tiempo real
- [ ] Drag & drop para reordenar gráficos

---

## Sitemap

```
Home (/)
├── Análisis (/analysis)
│   ├── Configurar parámetros
│   ├── Calcular correlación
│   └── Ver resultados
└── Resultados (/results)
    ├── Listar históricos
    └── Exportar a PDF
```

---

## Contacto

Para preguntas sobre el diseño del frontend, contactar al equipo de desarrollo.

**Última actualización**: Enero 2025
