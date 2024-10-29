import serial

def enviar_comando_arduino(comando, ser):
    if ser:
        try:
            ser.write(comando.encode())  # Envia o comando como bytes
        except serial.SerialException as e:
            print(f"Erro ao escrever na porta serial: {e}")