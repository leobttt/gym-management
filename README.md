# Power Gym App

Una aplicación de escritorio moderna diseñada para la gestión integral de gimnasios. Construida con Python y CustomTkinter, ofrece una interfaz premium y herramientas eficientes para la administración de socios, membresías y finanzas.

## Características principales

- **Dashboard Interactivo:** Visualización en tiempo real de métricas clave (socios activos, ingresos, gastos).
- **Gestión de Socios:** Control total de altas, vencimientos y recordatorios.
- **Punto de Venta:** Gestión de ventas de productos y servicios.
- **Finanzas:** Registro de gastos y cálculo de ingresos netos.
- **Notificaciones:** Sistema de alertas para membresías próximas a vencer.
- **Notificaciones:** Sistema de notificación al usuario mediante whatsapp.

## Tecnologías

- **Lenguaje:** Python 3.x
- **GUI:** CustomTkinter (basado en Tkinter)
- **Base de Datos:** SQLite3
- **Gráficos:** Canvas personalizados y lógica matemática para visualización de datos.

## Instalación y Ejecución

### Windows

1. Clonar el repositorio.
2. Crear un entorno virtual:
   `py -m venv venv`
3. Activar el entorno virtual:
   `venv\Scripts\activate`
4. Instalar dependencias:
   `pip install -r requirements.txt`
5. Ejecutar la aplicación:
   `py main.py`

Notas para Windows:
- `pywin32` se instala automáticamente desde `requirements.txt` y se usa para copiar recibos al portapapeles.
- `opencv-python` habilita la cámara para tomar fotos de socios.
- Los PDFs y recibos ya tienen fallback de fuentes para Windows.
- Los datos de la app se guardan en `%LOCALAPPDATA%\Power Gym`.

### Descargar `.exe` desde GitHub

- El repositorio ya puede generar `PowerGym.exe` con GitHub Actions.
- Si publicas un Release en GitHub, el workflow de [`build-windows.yml`](/Users/leobtt/Documents/gimnasio-app/.github/workflows/build-windows.yml) compila la app en Windows y adjunta dos archivos al Release:
  - `PowerGym.exe`
  - `PowerGym-Setup.exe`
- `PowerGym-Setup.exe` es el recomendado para usuarios finales porque instala la app, crea accesos directos y deja desinstalador.
- También puedes lanzarlo manualmente desde la pestaña `Actions` con `Build Windows App`.

### Build local para Windows

1. Instalar dependencias:
   `pip install -r requirements.txt`
2. Instalar PyInstaller:
   `pip install pyinstaller`
3. Generar el ejecutable:
   `pyinstaller --noconfirm PowerGym.spec`
4. El archivo final queda en:
   `dist\PowerGym.exe`

### Crear instalador para Windows

1. Instalar Inno Setup en Windows.
2. Compilar el ejecutable:
   `pyinstaller --noconfirm PowerGym.spec`
3. Abrir [`PowerGym.iss`](/Users/leobtt/Documents/gimnasio-app/installer/PowerGym.iss) en Inno Setup y compilar.
4. El instalador final queda en:
   `dist_installer\PowerGym-Setup.exe`

### macOS / Linux

1. Clonar el repositorio.
2. Crear un entorno virtual:
   `python3 -m venv venv`
3. Activar el entorno virtual e instalar dependencias:
   `source venv/bin/activate`
   `pip install -r requirements.txt`
4. Ejecutar la aplicación:
   `python3 main.py`

---
*Desarrollado con enfoque en estética premium y facilidad de uso.*
