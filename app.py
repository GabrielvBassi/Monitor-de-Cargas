from flask import Flask, render_template, request, redirect, url_for, flash

from models.cliente_model import ClienteModel
from services.error_file_service import ErrorFileService
from services.execucao_service import ExecucaoService
from services.historico_service import HistoricoService
from services.monitoramento_service import combinar_validacoes, montar_kpis, preparar_grafico_historico
from services.processamento_service import processar_envio

app = Flask(__name__)
app.secret_key = "chave-local-dev"


@app.route("/")
def index():
    return redirect(url_for("monitoramento"))


@app.route("/monitoramento")
def monitoramento():
    erro_diretorio = None
    erro_clientes = None

    try:
        clientes = ClienteModel.todos()
    except (FileNotFoundError, ValueError) as exc:
        clientes = {}
        erro_clientes = str(exc)

    resumo = []
    erro_backup = None
    execucoes = []
    detalhamento = []

    if not erro_clientes:
        try:
            resumo = ErrorFileService.resumo_por_cliente(clientes)
            detalhamento = ErrorFileService.detalhamento_por_cliente(clientes)
        except FileNotFoundError as exc:
            erro_diretorio = str(exc)

        try:
            execucoes = ExecucaoService.validar_clientes(clientes)
        except FileNotFoundError as exc:
            erro_backup = str(exc)

    historico = HistoricoService.listar()
    validacoes = combinar_validacoes(resumo, execucoes)

    return render_template(
        "monitoramento.html",
        pagina_ativa="monitoramento",
        erro_diretorio=erro_diretorio,
        erro_clientes=erro_clientes,
        erro_backup=erro_backup,
        kpis=montar_kpis(validacoes),
        validacoes=validacoes,
        detalhamento=detalhamento,
        historico=historico,
        grafico_historico=preparar_grafico_historico(historico),
    )


@app.route("/erros")
def erros():
    try:
        clientes = ClienteModel.todos()
    except (FileNotFoundError, ValueError) as exc:
        flash(str(exc), "erro")
        clientes = {}

    return render_template("erros.html", pagina_ativa="erros", clientes=clientes)


@app.route("/faturamentos")
def faturamentos():
    try:
        clientes = ClienteModel.todos()
    except (FileNotFoundError, ValueError) as exc:
        flash(str(exc), "erro")
        clientes = {}

    return render_template("faturamentos.html", pagina_ativa="faturamentos", clientes=clientes)


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
