# 📖 Tutorial: Cómo ejecutar los programas paso a paso

Si prefieres ejecutar todo manualmente desde la terminal para tener más control, sigue estos pasos:

### Paso 1: Abrir la Terminal en la carpeta del proyecto
1. Ve a la carpeta donde tienes el proyecto: `c:\Users\Pedro\Desktop\DEV\audit-automation`
2. En la barra de direcciones del explorador de archivos, escribe `powershell` (o `cmd`) y presiona **Enter**.
   * *Alternativa: Haz clic derecho en un espacio vacío de la carpeta y selecciona "Abrir en terminal".*

### Paso 2: Activar el Entorno Virtual
Para cargar todas las librerías necesarias, debes activar el ambiente aislado:
```powershell
.\.venv\Scripts\activate
```
*(Sabrás que funcionó porque aparecerá `(.venv)` al principio de la línea en verde).*

### Paso 3: Ejecutar el programa deseado

#### A) Para usar el Dashboard Visual (Interfaz de usuario):
Escribe este comando y presiona Enter:
```powershell
streamlit run app.py
```
*Se abrirá automáticamente una pestaña en tu navegador con el panel de control.*

#### B) Para ejecutar solo el Motor de Cálculo (Consola):
Si quieres procesar una empresa y fecha específica rápidamente:
```powershell
python calculo_metricas_video.py -e Nombre_Empresa -f AAAA-MM
```
*(Reemplaza `Nombre_Empresa` por el nombre de la carpeta del cliente y `AAAA-MM` por la fecha).*

---

### 🚀 Opción Rápida (Recomendada)
Si no quieres escribir comandos cada vez, puedes simplemente usar los archivos que creé para ti:
- Haz doble clic en **`RUN_DASHBOARD.bat`** y listo.

---
> [!TIP]
> Si el comando `streamlit` no funciona, asegúrate de haber corrido `pip install -r requirements.txt` la primera vez que configuraste el proyecto.
