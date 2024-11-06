import serial


def leer_peso(puerto):
    try:
        with serial.Serial(puerto, 1200, timeout=1) as ser:
            while True:
                if ser.in_waiting:
                    peso = ser.readline().decode().strip()
                    return peso
    except Exception as e:
        print(f"Error al leer el peso: {e}")
        return None
