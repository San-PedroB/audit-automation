# Proyecto: Automatización Auditoría (Roadmap)

Este documento detalla el progreso del sistema y los próximos pasos sugeridos para su evolución.

# ✅ Logros Alcanzados
- [x] **Motor de Métricas**: Normalización de fórmulas basada en el Total Auditado (Base 100%).
- [x] **Dashboard Streamlit**: Interfaz profesional con navegación Empresa > Sucursal > Fecha.
- [x] **Visualización Crystal Pro**: Gráficos de doble barra con KPIs de Precisión y Cobertura.
- [x] **Análisis de Unknowns**: Sección dedicada para monitorear fallos de identidad.
- [x] **Tablas de Datos**: Integración de resúmenes detallados con filas de TOTAL dinámicas.
- [x] **Exportación Excel**: Generación de reportes premium con estilos corporativos y gráficos vinculados.
- [x] **Consistencia Estética**: Uso de plantillas centralizadas y limpieza de formatos numéricos.

# 🚀 Próximos Pasos (Evolución)

### 1. Gestión de Datos Históricos
- [ ] **Persistencia en DB**: Crear una base de datos local (SQLite) para guardar el histórico de auditorías sin depender solo de CSVs y carpetas.
- [ ] **Dashboard de Tendencias**: Gráfico de evolución temporal para ver si la precisión mejora mes a mes por tienda.
- [ ] **Ranking de Sucursales**: Comparativa automática de rendimiento entre diferentes ubicaciones.

### 2. Funcionalidades Avanzadas
- [ ] **Generador de PDFs**: Opción de descargar un informe PDF ejecutivo (una página) listo para enviar a gerencia.
- [ ] **Envío Automático**: Botón de "Enviar por Email" para despachar los reportes directamente a los interesados.
- [ ] **Alertas Críticas**: Notificación automática si una cámara cae por debajo del 80% de precisión.

### 3. Seguridad y Despliegue
- [ ] **Login de Usuario**: Implementar una pantalla de acceso para proteger los datos de los clientes.
- [ ] **Optimización**: Manejo eficiente de archivos masivos y limpieza automática de archivos temporales.

---
*Roadmap actualizado - Marzo 2026*
