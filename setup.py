import sys
from cx_Freeze import setup, Executable

# Si estás utilizando algún archivo adicional (como iconos o imágenes), añádelos aquí
includefiles = ['iconos/empresa_logo.png', 'iconos/empresa_logo.png']

# Configuración de las opciones de construcción del ejecutable
build_exe_options = {
    "packages": ["pyserial", "re", "os", "time", "pyautogui", "keyboard", "pyperclip", "PyQt5"],
    "include_files": includefiles,  # Si tienes archivos adicionales, agrégales aquí
    "optimize": 2,  # Optimiza el tamaño del ejecutable
}

# Configura el "base" dependiendo del sistema operativo (esto es para Windows)
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="App Scales",
    version="1.0",
    description="Aplicación para leer el peso de una báscula",
    options={"build_exe": build_exe_options},
    # Nombre de tu script Python
    executables=[Executable("tu_script.py", base=base,
                            icon="iconos/empresa_logo.png")]
)
