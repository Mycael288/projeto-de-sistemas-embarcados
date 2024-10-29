import cv2
import mediapipe as mp
import time
import serial
from tkinter import messagebox
import numpy as np

from Comunica import enviar_comando_arduino
from GeraRelatorio import gerar_relatorio_pdf

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