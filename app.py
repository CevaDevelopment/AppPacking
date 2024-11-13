import re
import sys
import os
import serial  # Comunicación serial
from time import sleep
import pyautogui
import pyperclip
import keyboard
import serial.tools.list_ports  # Para detectar puertos COM disponibles
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignalc


def resource_path(relative_path):
    """Obtiene la ruta del recurso, considerando si se ejecuta desde un archivo .exe o no."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class SerialReaderThread(QThread):
    """Hilo para leer datos del puerto serial de forma continua"""
    data_received = pyqtSignal(
        str)  # Señal que se emitirá cuando se reciba un nuevo dato

    def __init__(self, serial_port, baud_rate):
        super().__init__()
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.ser = None
        self.running = True

    def run(self):
        """Inicia el hilo y comienza a leer el puerto serial continuamente"""
        try:
            self.ser = serial.Serial(
                self.serial_port, self.baud_rate, timeout=1)
            print(f"Puerto serial {self.serial_port} abierto correctamente.")
            while self.running:
                if self.ser.in_waiting > 0:  # Si hay datos disponibles
                    raw_data = self.ser.read_until(b'\n').decode(
                        'utf-8', errors='ignore').strip()
                    print(f"Datos leídos de la báscula: '{raw_data}'")
                    # Emite la señal con los datos recibidos
                    self.data_received.emit(raw_data)
        except serial.SerialException as e:
            print(f"Error al abrir el puerto serial: {e}")
            self.data_received.emit("Error de conexión.")
        except Exception as e:
            print(f"Error inesperado: {e}")
            self.data_received.emit("Error inesperado.")

    def stop(self):
        """Detiene el hilo"""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.quit()


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
        pixmap = QPixmap(resource_path('iconos/empresa_logo.png')
                         ).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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

        # Crear una etiqueta para mostrar el puerto detectado
        self.puerto_detectado_label = QLabel("Puerto Detectado: --", self)
        self.puerto_detectado_label.setFont(QFont('Arial', 12))
        self.puerto_detectado_label.setStyleSheet("color: white;")

        # Crear y configurar el layout
        layout = QVBoxLayout()
        layout.addWidget(self.logo_label)
        layout.addWidget(self.app_name_label)
        layout.addWidget(self.peso_label)
        layout.addWidget(self.leer_button)
        layout.addWidget(self.copy_button)

        # Layout para mostrar el puerto detectado
        layout.addWidget(self.puerto_detectado_label)

        container = QWidget()
        container.setLayout(layout)
        container.setStyleSheet(
            "border-radius: 20px; background-color: #003366;")
        self.setCentralWidget(container)

        # Inicializar el puerto serial y la velocidad en baudios
        self.serial_port = self.detectar_puerto_serial()
        self.baud_rate = 9600  # Ajusta esto según la configuración de tu báscula

        # Hilo para la lectura continua de datos
        self.serial_reader_thread = None

        # Iniciar el listener de teclado
        self.iniciar_listener_teclado()

    def iniciar_listener_teclado(self):
        """Inicia un listener para las teclas de acceso rápido"""
        keyboard.add_hotkey('f2', self.copy_and_paste)
        keyboard.add_hotkey('esc', self.cerrar_aplicacion)
        keyboard.add_hotkey('shift+v', self.copy_and_paste)

    def start_reading(self):
        """Inicia la lectura continua de peso en un hilo"""
        self.serial_reader_thread = SerialReaderThread(
            self.serial_port, self.baud_rate)
        self.serial_reader_thread.data_received.connect(self.actualizar_peso)
        self.serial_reader_thread.start()

    def actualizar_peso(self, raw_data):
        """Actualiza el peso en la interfaz cuando se reciben nuevos datos"""
        print(f"Datos leídos: '{raw_data}'")
        match = re.search(r'(\d+\.\d+|\d+)\s*kg', raw_data)
        if match:
            peso = match.group(1)
            self.peso_label.setText(f"Peso: {peso} kg")
        else:
            self.peso_label.setText("Peso: 0 kg")

    def copiar_al_portapapeles(self):
        """Copia solo el valor numérico del peso al portapapeles"""
        texto = self.peso_label.text()
        if "Peso:" in texto:
            valor_numerico = texto.split("Peso:")[1].strip()
            valor_numerico = valor_numerico.split()[0]
            pyperclip.copy(valor_numerico)

    def copy_and_paste(self):
        """Copia el valor al portapapeles y lo pega donde esté el cursor"""
        self.copiar_al_portapapeles()
        sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
        sleep(0.1)
        pyautogui.press('enter')

    def cerrar_aplicacion(self):
        """Cierra la aplicación"""
        if self.serial_reader_thread:
            self.serial_reader_thread.stop()
        self.close()

    def detectar_puerto_serial(self):
        """Detecta el puerto COM disponible para la báscula"""
        puertos = serial.tools.list_ports.comports()
        for puerto in puertos:
            try:
                # Intentamos abrir el puerto para ver si responde la báscula
                with serial.Serial(puerto.device, 9600, timeout=1) as ser:
                    # Aquí puedes probar con un comando que la báscula entienda
                    ser.write(b'READ')
                    sleep(1)  # Esperamos un poco para que la báscula responda
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode(
                            'utf-8', errors='ignore')
                        if "kg" in data:  # Asumimos que los datos de peso incluyen "kg"
                            print(f"Báscula encontrada en {puerto.device}")
                            self.puerto_detectado_label.setText(
                                f"Puerto Detectado: {puerto.device}")
                            return puerto.device
            except (serial.SerialException, ValueError):
                continue
        self.puerto_detectado_label.setText("Puerto Detectado: No encontrado")
        return None  # Si no encontramos un puerto válido


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec_())
