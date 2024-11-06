import re
import sys
import os
from time import sleep
import pyautogui
import pyperclip
import keyboard
import serial  # Comunicación serial
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer

def resource_path(relative_path):
    """Obtiene la ruta del recurso, considerando si se ejecuta desde un archivo .exe o no."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setFixedSize(500, 400)

        # Establecer el ícono de la aplicación
        self.setWindowIcon(QIcon(resource_path('iconos/app_icon.png')))

        # Establecer el fondo de color azul oscuro
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 51, 102))
        self.setPalette(palette)

        # Crear widgets
        self.logo_label = QLabel(self)
        pixmap = QPixmap(resource_path('iconos/empresa_logo.png')).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignLeft)

        self.app_name_label = QLabel("App scales", self)
        self.app_name_label.setFont(QFont('Verdana', 16, QFont.Capitalize))
        self.app_name_label.setAlignment(Qt.AlignCenter)
        self.app_name_label.setStyleSheet("color: white;")

        self.peso_label = QLabel("Peso: --", self)
        self.peso_label.setFont(QFont('Arial', 20))
        self.peso_label.setAlignment(Qt.AlignCenter)
        self.peso_label.setStyleSheet("color: white;")

        # Estilo para botones
        button_style = """
            QPushButton {
                padding: 15px;
                border-radius: 15px;
                background-color: #004080;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #0059b3;
            }
        """

        self.leer_button = QPushButton("  Leer Peso", self)
        self.leer_button.setFont(QFont('Arial', 16))
        self.leer_button.setIcon(QIcon(resource_path('iconos/leer.svg')))
        self.leer_button.clicked.connect(self.start_reading)
        self.leer_button.setStyleSheet(button_style)

        self.copy_button = QPushButton("  Copiar al Portapapeles", self)
        self.copy_button.setFont(QFont('Arial', 16))
        self.copy_button.setIcon(QIcon(resource_path('iconos/copiar.svg')))
        self.copy_button.clicked.connect(self.copiar_al_portapapeles)
        self.copy_button.setStyleSheet(button_style)

        # Crear y configurar el layout
        layout = QVBoxLayout()
        layout.addWidget(self.logo_label)
        layout.addWidget(self.app_name_label)
        layout.addWidget(self.peso_label)
        layout.addWidget(self.leer_button)
        layout.addWidget(self.copy_button)

        container = QWidget()
        container.setLayout(layout)
        container.setStyleSheet("border-radius: 20px; background-color: #003366;")
        self.setCentralWidget(container)

        # Puerto serial y parámetros de comunicación
        self.serial_port = 'COM3'  # Cambia esto al puerto adecuado
        self.baud_rate = 1200  # Ajusta esto según la configuración de tu báscula

        # Inicializar el timer para leer datos
        self.timer = QTimer()
        self.timer.timeout.connect(self.leer_peso)

        # Intentar abrir el puerto serial al iniciar
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=2)
            print("Puerto serial abierto correctamente.")
        except serial.SerialException as e:
            print(f"Error al abrir el puerto serial: {e}")
            self.peso_label.setText("Error de conexión.")

        # Iniciar el listener de teclado
        self.iniciar_listener_teclado()

    def iniciar_listener_teclado(self):
        """Inicia un listener para las teclas de acceso rápido"""
        keyboard.add_hotkey('f2', self.copy_and_paste)
        keyboard.add_hotkey('esc', self.cerrar_aplicacion)
        keyboard.add_hotkey('shift+v', self.copy_and_paste)

    def start_reading(self):
        """Inicia la lectura continua de peso"""
        self.timer.start(1000)  # Leer cada segundo

    def leer_peso(self):
            try:
                if self.ser.in_waiting > 0:  # Verifica si hay datos disponibles
                    raw_data = self.ser.read_until(b'\n').decode('utf-8', errors='ignore').strip()  # Leer hasta el salto de línea
                    print(f"Datos leídos de la báscula: '{raw_data}'")  # Imprime los datos leídos
                    
                    # Buscar el peso en el formato esperado
                    match = re.search(r'(\d+)\s*kg', raw_data)
                    if match:
                        peso = match.group(1)  # Extrae solo el número
                        self.peso_label.setText(f"Peso: {peso} kg")
                    else:
                        # Limpiar datos de ceros y formatear
                        cleaned_data = re.sub(r'[^0-9]', '', raw_data)  # Extrae solo los dígitos
                        if cleaned_data:
                            peso = cleaned_data.lstrip('0')  # Elimina ceros a la izquierda
                            if peso:  # Verifica que el peso no esté vacío
                                self.peso_label.setText(f"Peso: {peso} kg")
                            else:
                                self.peso_label.setText("Peso: 0 kg")
                        else:
                            print("No se encontró peso válido.")
                else:
                    print("Esperando datos de la báscula...")  # Mensaje cuando no hay datos
            except serial.SerialException as e:
                self.peso_label.setText("Error de conexión.")
                print(f"Error: {e}")
            except Exception as e: 
                print(f"Error inesperado: {e}")



    def copiar_al_portapapeles(self):
        """Copia solo el valor numérico del peso al portapapeles"""
        texto = self.peso_label.text()
        print(f"Texto extraído: {texto}")

        if "Peso:" in texto:
            valor_numerico = texto.split("Peso:")[1].strip()
            valor_numerico = valor_numerico.split()[0]  # Obtener solo el primer componente numérico
            pyperclip.copy(valor_numerico)
            print(f"Valor copiado al portapapeles: {valor_numerico}")
        else:
            print("Formato de texto no reconocido")

    def copy_and_paste(self):
        """Copia el valor al portapapeles y lo pega donde esté el cursor"""
        self.copiar_al_portapapeles()
        sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
        sleep(0.1)
        pyautogui.press('enter')

    def cerrar_aplicacion(self):
        """Cierra la aplicación"""
        if hasattr(self, 'ser'):
            self.ser.close()  # Cerrar el puerto serial si está abierto
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec_())
