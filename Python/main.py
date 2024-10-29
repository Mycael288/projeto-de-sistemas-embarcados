import os
import logging

from Carrega import get_exercise_config
from ExecutarExercicio import run_exercise

# Suprimir avisos do TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('tensorflow').setLevel(logging.FATAL)

# Loop principal
while True:
    # Obter a configuração do usuário
    nSerie, rSerie, timeActive, green_line_offset, red_line_offset, serial_port, selected_exercise = get_exercise_config()

    # Executar o exercício com a configuração fornecida
    run_exercise(nSerie, rSerie, timeActive, green_line_offset, red_line_offset, serial_port, selected_exercise)
