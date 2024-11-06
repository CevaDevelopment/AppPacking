import serial
import re
import time

serial_port = 'COM3'
baud_rate = 1200

try:
    ser = serial.Serial(serial_port, baud_rate, bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
    time.sleep(2)  # Esperar a que la conexión se estabilice
    print("Esperando datos de la báscula...")
    
    while True:
        if ser.in_waiting:
            raw_data = ser.read(ser.in_waiting)
            print(f"Datos crudos: {raw_data}")
            try:
                # Decodificar ignorando errores
                raw_string = raw_data.decode('utf-8', errors='ignore').strip()
                print(f"String decodificado: {raw_string}")

                # Buscar números en la cadena
                pesos = re.findall(r'\d+', raw_string)
                
                # Mostrar el peso si se encuentra
                if pesos:
                    # Tomar el último número significativo
                    peso = pesos[-1]
                    
                    # Transformar el peso
                    if len(peso) > 1:  # Asegurarse de que hay suficientes dígitos
                        peso_reversed = peso[::-1]  # Invertir el string
                        peso_correcto_str = peso_reversed[1:3]  # Tomar los dos dígitos
                        if peso_correcto_str:  # Asegurarse de que no está vacío
                            peso_correcto = int(peso_correcto_str)  # Convertir a entero
                            print(f"Peso Leído: {peso_correcto:.2f} kg")
                        else:
                            print("No se encontró peso válido después de la transformación.")
                    else:
                        print("El peso leído no tiene suficientes dígitos.")
                else:
                    print("No se encontró peso válido.")
            except Exception as e:
                print(f"Error de decodificación: {e}")
        time.sleep(1)
except serial.SerialException as e:
    print(f"Error de conexión: {e}")
except Exception as e:
    print(f"Error inesperado: {e}")
