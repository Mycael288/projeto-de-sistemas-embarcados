import os
import matplotlib.pyplot as plt
from fpdf import FPDF
import time

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