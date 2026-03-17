# 📖 Guía de Instalación y Traspaso - Dashboard Auditoría

Esta guía te ayudará a configurar el proyecto en cualquier otro PC para que puedas continuar trabajando mañana sin problemas.

## 📋 Requisitos Previos
Antes de empezar, asegúrate de que el nuevo PC tenga instalado:
1.  **Python 3.11 o superior**: Puedes descargarlo de [python.org](https://www.python.org/downloads/).
    *   *Importante*: Durante la instalación, marca la casilla que dice **"Add Python to PATH"**.
2.  **Visual Studio Code** (Opcional): Muy recomendado para editar el código.

---

## 🚀 Pasos para la Configuración

### 1. Copiar el Proyecto
Copia toda la carpeta `audit-automation` al nuevo PC (vía USB, Google Drive, Git, etc.).

### 2. Abrir una Terminal
En el nuevo PC, entra en la carpeta del proyecto, haz clic derecho en un espacio vacío y selecciona **"Abrir en Terminal"** (o usa PowerShell/CMD).

### 3. Crear el Entorno Virtual (Limpio)
Para evitar conflictos con otras librerías del PC, crearemos un ambiente aislado:
```powershell
python -m venv .venv
```

### 4. Activar el Entorno
*   **En Windows (PowerShell):**
    ```powershell
    .\.venv\Scripts\activate
    ```
*   **En Windows (CMD):**
    ```cmd
    .venv\Scripts\activate
    ```
*(Sabrás que está activo porque aparecerá `(.venv)` al principio de tu línea de comandos).*

### 5. Instalar Dependencias
Usa el archivo `requirements.txt` que he creado para instalar todo de una vez:
```powershell
pip install -r requirements.txt
```

---

## 📊 Cómo Iniciar el Dashboard
Una vez instalado todo, siempre que quieras trabajar debes seguir estos dos pasos:

1.  **Activar el entorno** (si no lo está):
    ```powershell
    .\.venv\Scripts\activate
    ```
2.  **Lanzar la aplicación**:
    ```powershell
    streamlit run app.py
    ```

---

## 🛠️ Notas de Portabilidad
*   **Plantillas**: Asegúrate de que la carpeta `templates/` se copie con el proyecto, ya que ahí está el archivo de Excel maestro.
*   **Datos**: La carpeta `Auditorias_Clientes/` debe mantener su estructura (Empresa > Sucursal > Fecha) para que el Dashboard encuentre los archivos.

¡Buena suerte mañana en el trabajo! 🚀
