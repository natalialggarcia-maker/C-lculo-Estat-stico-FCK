import gradio as gr
import statistics
import tempfile

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from xml.sax.saxutils import escape


def calcular_fck(lote, idade, dados, fck_projeto):
    try:
        linhas = dados.strip().split("\n")
        exemplares = []

        for linha in linhas:
            valores = linha.replace(",", ".").split()

            if len(valores) != 2:
                return "Erro: informe dois resultados por linha.", None

            cp1, cp2 = map(float, valores)

            if cp1 <= 0 or cp2 <= 0:
                return "As resistências devem ser positivas.", None

            exemplares.append(max(cp1, cp2))

        if not exemplares:
            return "Informe pelo menos uma betonada.", None

        media = statistics.mean(exemplares)

        if len(exemplares) >= 2:
            variancia = statistics.variance(exemplares)
            desvio = statistics.stdev(exemplares)
            cv = desvio / media * 100
        else:
            variancia = desvio = cv = 0

        linhas_relatorio = [
            "RELATORIO DE CALCULO ESTATISTICO DO FCK",
            "",
            f"Lote: {lote}",
            f"Idade dos ensaios: {idade} dias",
            f"Quantidade de betonadas: {len(exemplares)}",
            "",
            "RESULTADOS POR BETONADA"
        ]

        relatorio = f"""
# RELATÓRIO DE CÁLCULO ESTATÍSTICO DO FCK

*Lote:* {lote}

*Idade dos ensaios:* {idade} dias

*Quantidade de betonadas:* {len(exemplares)}

## Resultados por betonada
"""

        for i, resistencia in enumerate(exemplares):
            texto = f"Betonada {i+1}: {resistencia:.2f} MPa"
            linhas_relatorio.append(texto)
            relatorio += f"\n- {texto}"

        relatorio += f"""

## Tratamento estatístico descritivo

- Média: {media:.2f} MPa
- Variância: {variancia:.2f} MPa²
- Desvio padrão: {desvio:.2f} MPa
- Coeficiente de variação: {cv:.2f}%

## Avaliação
"""

        linhas_relatorio.extend([
            "",
            "TRATAMENTO ESTATISTICO DESCRITIVO",
            f"Media: {media:.2f} MPa",
            f"Variancia: {variancia:.2f} MPa²",
            f"Desvio padrao: {desvio:.2f} MPa",
            f"Coeficiente de variacao: {cv:.2f}%"
        ])

        if fck_projeto is not None and fck_projeto > 0:
            linhas_relatorio.append("")
            linhas_relatorio.append("VERIFICACAO DE CONFORMIDADE")

            for i, resistencia in enumerate(exemplares):
                situacao = "ATENDE" if resistencia >= fck_projeto else "NAO ATENDE"
                texto = f"Betonada {i+1}: {situacao}"
                linhas_relatorio.append(texto)
                relatorio += f"\n- {texto}"
        else:
            texto = "Fck de projeto nao informado. Conformidade nao avaliada."
            linhas_relatorio.append(texto)
            relatorio += f"\n{texto}"

        linhas_relatorio.extend([
            "",
            "Metodo: Amostragem total (100%).",
            "Cada betonada e avaliada individualmente.",
            "A media apresentada e apenas estatistica descritiva."
        ])

        relatorio += """

*Método:* Amostragem total (100%).

Observação: cada betonada é avaliada individualmente.
A média apresentada é apenas estatística descritiva.
"""

        # Criar o arquivo PDF
        arquivo_temporario = tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        )
        caminho_pdf = arquivo_temporario.name
        arquivo_temporario.close()

        documento = SimpleDocTemplate(
            caminho_pdf,
            pagesize=A4,
            rightMargin=45,
            leftMargin=45,
            topMargin=45,
            bottomMargin=45
        )

        estilos = getSampleStyleSheet()
        conteudo = []

        for linha in linhas_relatorio:
            if linha == "":
                conteudo.append(Spacer(1, 10))
            elif linha in [
                "RELATORIO DE CALCULO ESTATISTICO DO FCK",
                "RESULTADOS POR BETONADA",
                "TRATAMENTO ESTATISTICO DESCRITIVO",
                "VERIFICACAO DE CONFORMIDADE"
            ]:
                conteudo.append(
                    Paragraph(f"<b>{escape(linha)}</b>", estilos["Heading2"])
                )
            else:
                conteudo.append(
                    Paragraph(escape(linha), estilos["BodyText"])
                )

        documento.build(conteudo)

        return relatorio, caminho_pdf

    except Exception as erro:
        return f"Erro ao processar os dados: {erro}", None


with gr.Blocks(title="Sistema de Cálculo do FCK") as sistema:

    gr.Markdown("""
    # SISTEMA COMPUTACIONAL DE CÁLCULO ESTATÍSTICO DO FCK

    ### Controle tecnológico do concreto — Amostragem total (100%)

    *Projeto acadêmico*

    Sistema para entrada de resultados dos corpos de prova,
    tratamento estatístico e avaliação por betonada.

    ---
    """)

    lote = gr.Textbox(label="Identificação do lote", value="Lote 1")

    idade = gr.Number(label="Idade dos ensaios (dias)", value=28)

    dados = gr.Textbox(
        label="Resistências dos corpos de prova (MPa)",
        placeholder="Dois valores por linha:\n27.5 28.0\n29.0 29.5",
        lines=8
    )

    fck_projeto = gr.Number(
        label="Fck especificado no projeto (MPa) — opcional",
        value=None
    )

    botao = gr.Button("CALCULAR FCK", variant="primary")

    resultado = gr.Markdown()

    arquivo_pdf = gr.File(label="BAIXAR RELATÓRIO EM PDF")

    botao.click(
        fn=calcular_fck,
        inputs=[lote, idade, dados, fck_projeto],
        outputs=[resultado, arquivo_pdf]
    )


import os

sistema.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 10000))
)
