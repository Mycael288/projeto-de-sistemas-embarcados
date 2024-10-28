import os
import logging
import cv2
import mediapipe as mp
import time
import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF

# Suprimir avisos do TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('tensorflow').setLevel(logging.FATAL)

def enviar_comando_arduino(comando, ser):
    if ser:
        try:
            ser.write(comando.encode())  # Envia o comando como bytes
        except serial.SerialException as e:
            print(f"Erro ao escrever na porta serial: {e}")

def load_exercises(filename='exercicios.txt'):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    exercises = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(';')
                    if len(parts) == 6:
                        nome, repeticoes, series, descanso, offset_verde, offset_vermelho = parts
                        exercises[nome] = {
                            'repeticoes': int(repeticoes),
                            'series': int(series),
                            'descanso': int(descanso),
                            'offset_verde': float(offset_verde),
                            'offset_vermelho': float(offset_vermelho)
                        }
    except FileNotFoundError:
        messagebox.showerror("Erro", f"Arquivo '{file_path}' não encontrado.")
        exit()
    return exercises

def get_exercise_config():
    root = tk.Tk()
    root.title("Configuração do Exercício")

    # Use ttk para widgets mais modernos
    style = ttk.Style()
    style.theme_use('default')

    # Variável para indicar se a configuração foi concluída
    root.config_completed = False

    # Carregar os exercícios do arquivo
    exercises = load_exercises()

    # Função para atualizar os campos quando um exercício é selecionado
    def on_exercise_select(event):
        selected_exercise = exercise_combo.get()
        if selected_exercise in exercises:
            params = exercises[selected_exercise]
            repetitions_entry.delete(0, tk.END)
            repetitions_entry.insert(0, params['repeticoes'])
            series_entry.delete(0, tk.END)
            series_entry.insert(0, params['series'])
            rest_time_entry.delete(0, tk.END)
            rest_time_entry.insert(0, params['descanso'])
            green_line_entry.delete(0, tk.END)
            green_line_entry.insert(0, params['offset_verde'])
            red_line_entry.delete(0, tk.END)
            red_line_entry.insert(0, params['offset_vermelho'])

    # Define labels e campos de entrada usando ttk
    ttk.Label(root, text="Selecione o exercício:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    exercise_combo = ttk.Combobox(root, values=list(exercises.keys()), state='readonly')
    exercise_combo.grid(row=0, column=1, padx=5, pady=5)
    exercise_combo.bind("<<ComboboxSelected>>", on_exercise_select)

    ttk.Label(root, text="Número de repetições:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    repetitions_entry = ttk.Entry(root)
    repetitions_entry.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(root, text="Número de séries:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    series_entry = ttk.Entry(root)
    series_entry.grid(row=2, column=1, padx=5, pady=5)

    ttk.Label(root, text="Tempo de descanso (s):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    rest_time_entry = ttk.Entry(root)
    rest_time_entry.grid(row=3, column=1, padx=5, pady=5)

    ttk.Label(root, text="Altura da linha verde (offset):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
    green_line_entry = ttk.Entry(root)
    green_line_entry.grid(row=4, column=1, padx=5, pady=5)

    ttk.Label(root, text="Altura da linha vermelha (offset):").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
    red_line_entry = ttk.Entry(root)
    red_line_entry.grid(row=5, column=1, padx=5, pady=5)

    # Obter lista de portas seriais disponíveis
    ports = list(serial.tools.list_ports.comports())
    port_list = [port.device for port in ports]

    ttk.Label(root, text="Porta Serial:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
    serial_port_combo = ttk.Combobox(root, values=port_list, state='readonly')
    serial_port_combo.grid(row=6, column=1, padx=5, pady=5)
    if port_list:
        serial_port_combo.current(0)  # Seleciona a primeira porta por padrão
    else:
        serial_port_combo.set('Nenhuma porta encontrada')

    # Valores padrão
    if exercises:
        first_exercise = list(exercises.keys())[0]
        exercise_combo.set(first_exercise)
        on_exercise_select(None)  # Carregar os parâmetros do primeiro exercício

    # Função para obter as entradas e fechar a janela
    def on_ok():
        try:
            root.selected_exercise = exercise_combo.get()
            if root.selected_exercise not in exercises:
                messagebox.showerror("Erro de entrada", "Por favor, selecione um exercício válido.")
                return
            root.repetitions = int(repetitions_entry.get())
            root.series = int(series_entry.get())
            root.rest_time = int(rest_time_entry.get())
            root.green_line = float(green_line_entry.get())
            root.red_line = float(red_line_entry.get())
            root.serial_port = serial_port_combo.get()
            if not root.serial_port or root.serial_port == 'Nenhuma porta encontrada':
                messagebox.showerror("Erro de entrada", "Por favor, selecione uma porta serial válida.")
                return
            root.config_completed = True  # Indica que a configuração foi concluída
            root.destroy()
        except ValueError:
            messagebox.showerror("Erro de entrada", "Por favor, insira valores numéricos válidos.")

    # Função para fechar o programa ao fechar a janela
    def on_close():
        root.config_completed = False
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    ok_button = ttk.Button(root, text="OK", command=on_ok)
    ok_button.grid(row=7, column=0, columnspan=2, pady=10)

    root.mainloop()

    # Verificar se a configuração foi concluída
    if not root.config_completed:
        print("Configuração não foi concluída. Encerrando o programa.")
        exit()

    # Obter as entradas dos atributos do root
    nSerie = root.repetitions
    rSerie = root.series
    timeActive = root.rest_time
    green_line_offset = root.green_line
    red_line_offset = root.red_line
    serial_port = root.serial_port
    selected_exercise = root.selected_exercise

    return nSerie, rSerie, timeActive, green_line_offset, red_line_offset, serial_port, selected_exercise

def run_exercise(nSerie, rSerie, timeActive, green_line_offset, red_line_offset, serial_port, selected_exercise):
    # Configurar a porta serial
    try:
        ser = serial.Serial(serial_port, 9600, timeout=1)
        print(f"Conectado ao Arduino na porta {serial_port}")
    except serial.SerialException as e:
        print(f"Erro ao abrir a porta serial: {e}")
        ser = None
        messagebox.showerror("Erro de conexão", f"Não foi possível conectar à porta serial {serial_port}.\nErro: {e}")

    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose

    cap = cv2.VideoCapture(0)  # Ajuste para o índice correto da câmera

    # Configuração do contador e status do exercício
    contador = 0
    contador_erro = 0
    serie = 1
    estado = 'esperando_levantar'
    erro_ocorrido = False  # Variável para evitar múltiplos incrementos de erro
    acerto_recentemente_contabilizado = False  # Flag para evitar erro imediatamente após acerto
    timer_ativo = False
    start_time_descanso = None
    exercicio_concluido = False
    end_time = None  # Inicializa end_time

    # Variáveis para suavizar a altura dos ombros
    buffer_tamanho = 10  # Número de quadros para a média móvel
    buffer_altura_ombro = []

    # Variáveis para sincronização com tolerância temporal
    tolerancia_tempo = 1.0  # 1 segundo de tolerância
    tempo_regiao_esquerdo = {'acima_verde': None, 'abaixo_vermelha': None}
    tempo_regiao_direito = {'acima_verde': None, 'abaixo_vermelha': None}

    # Adição: Lista para armazenar resultados das repetições (1 = acerto, 0 = erro)
    repetition_results = []

    with mp_pose.Pose(min_detection_confidence=0.3, min_tracking_confidence=0.3) as pose:
        # Loop principal do exercício
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Falha ao capturar imagem da câmera.")
                break

            # Converter a imagem para RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Processar a imagem para encontrar a pose
            results = pose.process(image)

            # Converter a imagem de volta para BGR
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Verificar se os landmarks foram detectados
            if results.pose_landmarks and not timer_ativo and not exercicio_concluido:
                landmarks = results.pose_landmarks.landmark

                # Obter coordenadas dos ombros e cotovelos
                ombro_esquerdo = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                ombro_direito = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
                cotovelo_esquerdo = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
                cotovelo_direito = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]

                # Calcular a altura média dos ombros
                altura_ombro_media = (ombro_esquerdo.y + ombro_direito.y) / 2

                # Adicionar a altura atual dos ombros ao buffer
                buffer_altura_ombro.append(altura_ombro_media)
                if len(buffer_altura_ombro) > buffer_tamanho:
                    buffer_altura_ombro.pop(0)

                # Calcular a média móvel
                altura_ombro_suavizada = np.mean(buffer_altura_ombro)

                # Calcular os limites atualizados
                limite_superior = max(0, altura_ombro_suavizada + green_line_offset)
                limite_inferior = min(1, altura_ombro_suavizada + red_line_offset)

                # Desenhar as linhas limite na imagem
                altura_imagem = image.shape[0]
                cv2.line(image, (0, int(limite_superior * altura_imagem)), (image.shape[1], int(limite_superior * altura_imagem)), (0, 255, 0), 2)
                cv2.line(image, (0, int(limite_inferior * altura_imagem)), (image.shape[1], int(limite_inferior * altura_imagem)), (0, 0, 255), 2)

                # Verificar as posições dos cotovelos
                cotovelo_esquerdo_y = cotovelo_esquerdo.y
                cotovelo_direito_y = cotovelo_direito.y

                # Determinar a região de cada cotovelo
                def get_regiao(cotovelo_y):
                    if cotovelo_y < limite_superior:
                        return 'acima_verde'
                    elif cotovelo_y > limite_inferior:
                        return 'abaixo_vermelha'
                    else:
                        return 'entre_linhas'

                regiao_esquerdo = get_regiao(cotovelo_esquerdo_y)
                regiao_direito = get_regiao(cotovelo_direito_y)

                # Atualizar tempos das regiões
                tempo_atual = time.time()

                # Atualizar tempo de entrada nas regiões para o braço esquerdo
                if regiao_esquerdo in ['acima_verde', 'abaixo_vermelha']:
                    tempo_regiao_esquerdo[regiao_esquerdo] = tempo_atual
                else:
                    tempo_regiao_esquerdo = {'acima_verde': None, 'abaixo_vermelha': None}

                # Atualizar tempo de entrada nas regiões para o braço direito
                if regiao_direito in ['acima_verde', 'abaixo_vermelha']:
                    tempo_regiao_direito[regiao_direito] = tempo_atual
                else:
                    tempo_regiao_direito = {'acima_verde': None, 'abaixo_vermelha': None}

                # Verificar sincronização com tolerância temporal apenas para 'acima_verde'
                def braços_sincronizados(regiao):
                    tempo_esquerdo = tempo_regiao_esquerdo.get(regiao)
                    tempo_direito = tempo_regiao_direito.get(regiao)
                    if tempo_esquerdo and tempo_direito:
                        return abs(tempo_esquerdo - tempo_direito) <= tolerancia_tempo
                    else:
                        return False

                # Logs de depuração aprimorados
                print(f"Estado: {estado}, Regiões - Esquerdo: {regiao_esquerdo}, Direito: {regiao_direito}")
                if regiao_esquerdo == regiao_direito and regiao_esquerdo in ['acima_verde', 'abaixo_vermelha']:
                    print(f"Tempo esquerda {regiao_esquerdo}: {tempo_regiao_esquerdo.get(regiao_esquerdo)}, Tempo direita {tempo_regiao_direito.get(regiao_direito)}")
                    sincronizados = braços_sincronizados(regiao_esquerdo)
                    print(f"Sincronizados: {sincronizados}")
                else:
                    print("Braços entre as linhas ou em regiões não monitoradas.")
                    sincronizados = False
                    print(f"Sincronizados: {sincronizados}")

                # Lógica de transição de estado corrigida
                if regiao_esquerdo == regiao_direito:
                    if regiao_esquerdo == 'abaixo_vermelha':
                        if estado in ['esperando_levantar', 'esperando_baixar', 'erro']:
                            estado = 'braços_abaixados'
                            erro_ocorrido = False  # Resetar o erro
                            acerto_recentemente_contabilizado = False  # Resetar a flag de acerto
                            print("Braços abaixados - Pronto para levantar")
                    elif regiao_esquerdo == 'acima_verde':
                        if estado == 'braços_abaixados' and sincronizados:
                            contador += 1
                            repetition_results.append(1)  # Acerto
                            enviar_comando_arduino('A', ser)
                            estado = 'esperando_baixar'
                            erro_ocorrido = False
                            acerto_recentemente_contabilizado = True  # Indica que um acerto foi contabilizado
                            print("Repetição correta contabilizada")
                        elif estado == 'esperando_baixar' and not erro_ocorrido:
                            contador_erro += 1
                            repetition_results.append(0)  # Erro
                            enviar_comando_arduino('B', ser)
                            erro_ocorrido = True
                            estado = 'esperando_baixar'
                            print("Levantou sem abaixar - Erro contabilizado")
                else:
                    # Verificar se os braços entraram na mesma região dentro da tolerância de tempo
                    if regiao_esquerdo in ['acima_verde', 'abaixo_vermelha'] and regiao_direito in ['acima_verde', 'abaixo_vermelha']:
                        if braços_sincronizados(regiao_esquerdo):
                            sincronizados = True
                        else:
                            sincronizados = False
                    else:
                        sincronizados = False

                    if not sincronizados and estado == 'esperando_baixar' and not erro_ocorrido:
                        contador_erro += 1
                        repetition_results.append(0)  # Erro
                        enviar_comando_arduino('B', ser)
                        erro_ocorrido = True
                        estado = 'esperando_baixar'
                        print("Braços desincronizados - Erro contabilizado")

                # Exibir o contador e o contador de erros na tela
                cv2.putText(image, f'Exercicio: {selected_exercise}', (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(image, f'Serie: {serie} Repeticao: {contador}', (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(image, f'Erros: {contador_erro}', (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                # Checar se a série foi completada
                if contador >= nSerie:
                    timer_ativo = True
                    start_time_descanso = time.time()  # Iniciar o timer de descanso

            # Se o timer estiver ativo, mostrar o tempo restante
            if timer_ativo:
                elapsed_time = time.time() - start_time_descanso
                remaining_time = timeActive - int(elapsed_time)

                if remaining_time > 0:
                    cv2.putText(image, f'Descanso: {remaining_time}s', (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)
                else:
                    # Resetar após o descanso
                    contador = 0
                    serie += 1
                    timer_ativo = False
                    start_time_descanso = None
                    estado = 'esperando_levantar'
                    erro_ocorrido = False
                    acerto_recentemente_contabilizado = False

                    if serie > rSerie:
                        exercicio_concluido = True
                        end_time = time.time()

            # Se o exercício foi concluído, mostrar a mensagem e esperar 5 segundos
            if exercicio_concluido:
                if end_time is None:
                    end_time = time.time()
                elapsed_time_concluido = time.time() - end_time
                if elapsed_time_concluido < 5:
                    cv2.putText(image, 'Exercicio Completo!', (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)
                else:
                    # Finalizar o exercício
                    break

            # Desenhar as landmarks na imagem se disponíveis
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Mostrar o vídeo em uma janela padrão
            cv2.imshow('Exercicio', image)

            # Capturar teclas pressionadas
            key = cv2.waitKey(10) & 0xFF
            if key == ord('t'):  # Pressione 't' para terminar o exercício
                break
            elif key == ord('l'):
                contador = 0
                serie = 1
                contador_erro = 0
                estado = 'esperando_levantar'
                erro_ocorrido = False
                acerto_recentemente_contabilizado = False
                repetition_results.clear()  # Resetar os resultados das repetições
                enviar_comando_arduino('C', ser)  # Enviar comando 'C' ao Arduino para resetar

    cap.release()
    cv2.destroyAllWindows()
    if ser:
        ser.close()  # Fechar a porta serial ao finalizar

    # Adição: Gerar relatório em PDF após o exercício
    gerar_relatorio_pdf(selected_exercise, nSerie, rSerie, timeActive, green_line_offset, red_line_offset, contador, contador_erro, repetition_results)

def gerar_relatorio_pdf(exercicio, nSerie, rSerie, tempo_descanso, offset_verde, offset_vermelho, total_acertos, total_erros, repetition_results):
    # Calcular resultados cumulativos
    acumulado_acertos = []
    acumulado_erros = []
    acertos = 0
    erros = 0
    for resultado in repetition_results:
        if resultado == 1:
            acertos += 1
        else:
            erros += 1
        acumulado_acertos.append(acertos)
        acumulado_erros.append(erros)

    # Plotar o gráfico
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(acumulado_acertos) + 1), acumulado_acertos, label='Acertos', marker='o')
    plt.plot(range(1, len(acumulado_erros) + 1), acumulado_erros, label='Erros', marker='x')
    plt.title('Acertos e Erros por Repetição')
    plt.xlabel('Número de Repetições')
    plt.ylabel('Quantidade')
    plt.legend()
    plt.grid(True)
    plot_filename = 'relatorio_plot.png'
    plt.savefig(plot_filename)
    plt.close()

    # Criar o PDF
    pdf = FPDF()
    pdf.add_page()

    # Título
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Relatório de Exercício", ln=True, align='C')

    pdf.ln(10)

    # Dados do exercício
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Exercício: {exercicio}", ln=True)
    pdf.cell(0, 10, f"Número de Repetições por Série: {nSerie}", ln=True)
    pdf.cell(0, 10, f"Número de Séries: {rSerie}", ln=True)
    pdf.cell(0, 10, f"Tempo de Descanso entre Séries: {tempo_descanso} segundos", ln=True)
    pdf.cell(0, 10, f"Offset da Linha Verde: {offset_verde}", ln=True)
    pdf.cell(0, 10, f"Offset da Linha Vermelha: {offset_vermelho}", ln=True)
    pdf.cell(0, 10, f"Total de Acertos: {total_acertos}", ln=True)
    pdf.cell(0, 10, f"Total de Erros: {total_erros}", ln=True)

    pdf.ln(10)

    # Inserir o gráfico
    if os.path.exists(plot_filename):
        pdf.image(plot_filename, x=10, w=190)
        # Remover o arquivo de plot após a inserção
        os.remove(plot_filename)
    else:
        pdf.cell(0, 10, "Gráfico não disponível.", ln=True)

    # Salvar o PDF
    report_filename = f"Relatorio_{exercicio}_{int(time.time())}.pdf"
    pdf.output(report_filename)
    print(f"Relatório gerado: {report_filename}")

# Loop principal
while True:
    # Obter a configuração do usuário
    nSerie, rSerie, timeActive, green_line_offset, red_line_offset, serial_port, selected_exercise = get_exercise_config()

    # Executar o exercício com a configuração fornecida
    run_exercise(nSerie, rSerie, timeActive, green_line_offset, red_line_offset, serial_port, selected_exercise)
