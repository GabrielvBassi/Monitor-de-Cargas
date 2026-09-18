from flask import Flask, render_template, request, redirect, url_for, flash

from models.cliente_model import ClienteModel
from services.error_file_service import ErrorFileService
from services.historico_service import HistoricoService
from services.monitoramento_service import (
    montar_detalhamento,
    montar_kpis,
    preparar_grafico_historico,
    preparar_grafico_resumo,
)
from services.processamento_service import processar_envio

app = Flask(__name__)
app.secret_key = "chave-local-dev"


@app.route("/")
def index():
    return redirect(url_for("monitoramento"))


@app.route("/monitoramento")
def monitoramento():
    erro_diretorio = None

    try:
        resumo = ErrorFileService.resumo_por_cliente(ClienteModel.todos())
    except FileNotFoundError as exc:
        resumo = []
        erro_diretorio = str(exc)

    historico = HistoricoService.listar()

    return render_template(
        "monitoramento.html",
        pagina_ativa="monitoramento",
        erro_diretorio=erro_diretorio,
        kpis=montar_kpis(resumo),
        resumo=preparar_grafico_resumo(resumo),
        detalhamento=montar_detalhamento(resumo),
        historico=historico,
        grafico_historico=preparar_grafico_historico(historico),
    )


@app.route("/erros")
def erros():
    return render_template("erros.html", pagina_ativa="erros", clientes=ClienteModel.todos())


@app.route("/faturamentos")
def faturamentos():
    return render_template("faturamentos.html", pagina_ativa="faturamentos", clientes=ClienteModel.todos())


@app.route("/processar", methods=["POST"])
def processar():
    nome_modelo = request.form.get("modelo")
    ids_clientes = request.form.getlist("clientes")
    acao = request.form.get("acao")

    destino = "erros" if nome_modelo == "erro" else "faturamentos"

    try:
        sucessos, falhas = processar_envio(nome_modelo, ids_clientes, acao)
    except ValueError as exc:
        flash(str(exc), "erro")
        return redirect(url_for(destino))

    if sucessos:
        acao_label = "aberto(s) para visualizacao" if acao == "visualizar" else "enviado(s) automaticamente"
        flash(f"E-mail(s) {acao_label} para: {', '.join(sucessos)}.", "sucesso")

    if falhas:
        flash(f"Falha ao processar: {', '.join(falhas)}.", "erro")

    return redirect(url_for(destino))


if __name__ == "__main__":
    app.run(debug=True)
