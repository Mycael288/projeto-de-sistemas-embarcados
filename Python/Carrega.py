import os

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import serial.tools.list_ports

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