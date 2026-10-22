import calendar
from datetime import date

from flask import Flask, render_template, request, redirect, url_for, flash, send_file

MESES_PT = [
    "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

from models.cliente_model import ClienteModel
from models.email_model import EmailModel
from services.historico_service import HistoricoService
from services.exportacao_service import gerar_planilha_controle, nome_arquivo_exportacao
from services.infografico_service import montar_infografico
from services.monitoramento_cache import obter_detalhamento, obter_principal
from services.monitoramento_service import preparar_grafico_historico
from services.planilha_diaria_service import atualizar_aba_diaria
from services.processamento_service import processar_envio

app = Flask(__name__)
app.secret_key = "chave-local-dev"


@app.route("/")
def index():
    return redirect(url_for("monitoramento"))


@app.route("/monitoramento")
def monitoramento():
    """Le do cache (services/monitoramento_cache.py): a validacao dos
    diretorios so roda de verdade na primeira vez, ou quando o botao
    "Atualizar" manda ?atualizar=1 -- trocar de aba e voltar nao recalcula."""
    forcar = request.args.get("atualizar") == "1"
    dados, atualizado_em = obter_principal(forcar=forcar)

    historico = HistoricoService.listar()

    return render_template(
        "monitoramento.html",
        pagina_ativa="monitoramento",
        erro_diretorio=dados["erro_diretorio"],
        erro_clientes=dados["erro_clientes"],
        erro_backup=dados["erro_backup"],
        kpis=dados["kpis"],
        validacoes=dados["validacoes"],
        atualizado_em=atualizado_em,
        # Previa visual do seletor de "dia base" -- ainda nao afeta o calculo
        # de status; so desenha o calendario com o mes atual e hoje marcado.
        calendario_semanas=calendar.Calendar(firstweekday=6).monthdayscalendar(
            date.today().year, date.today().month
        ),
        data_base_dia=date.today().day,
        data_base_label=date.today().strftime("%d/%m/%Y"),
        hoje_dia=date.today().day,
        mes_ano_label=f"{MESES_PT[date.today().month - 1]} {date.today().year}",
        historico=historico,
        grafico_historico=preparar_grafico_historico(historico),
    )


@app.route("/monitoramento/exportar")
def monitoramento_exportar():
    """Exporta a planilha de controle (.xlsx), no mesmo formato das abas
    diarias da planilha de clientes -- ver services/exportacao_service.py.

    Filtros via querystring (combinaveis):
    ?clientes=Nome1,Nome2  -- so esses clientes (selecao manual na tela).
    ?frequencias=diario,semanal -- so essas frequencias (comparacao
    sem diferenciar maiusculas/minusculas).
    Sem nenhum filtro, exporta todos os clientes cadastrados. Usa o mesmo
    cache do Monitoramento (nao revarre a rede)."""
    dados, _ = obter_principal()

    if dados.get("erro_clientes"):
        flash(dados["erro_clientes"], "erro")
        return redirect(url_for("monitoramento"))

    if dados.get("erro_diretorio"):
        flash(dados["erro_diretorio"], "erro")
        return redirect(url_for("monitoramento"))

    validacoes = dados["validacoes"]

    nomes_selecionados = request.args.get("clientes")

    if nomes_selecionados:
        nomes = {nome.strip() for nome in nomes_selecionados.split(",") if nome.strip()}
        validacoes = [item for item in validacoes if item["cliente"] in nomes]

    frequencias_selecionadas = request.args.get("frequencias")

    if frequencias_selecionadas:
        frequencias = {freq.strip().lower() for freq in frequencias_selecionadas.split(",") if freq.strip()}
        validacoes = [
            item for item in validacoes
            if item["frequencia_verificacao"].strip().lower() in frequencias
        ]

    if not validacoes:
        flash("Nenhum cliente encontrado para exportar com esses filtros.", "erro")
        return redirect(url_for("monitoramento"))

    planilha = gerar_planilha_controle(validacoes, dados["clientes"])

    return send_file(
        planilha,
        as_attachment=True,
        download_name=nome_arquivo_exportacao(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/monitoramento/infografico")
def monitoramento_infografico():
    """Infografico executivo do dia, montado do zero a partir da varredura
    atual (cache do Monitoramento) -- ver services/infografico_service.py.
    Mesmos filtros do exportar: ?clientes=Nome1,Nome2 e/ou
    ?frequencias=diario,semanal. A periodicidade no cabecalho vem dos
    clientes que sobraram depois do filtro."""
    dados, _ = obter_principal()

    if dados.get("erro_clientes") or dados.get("erro_diretorio"):
        flash(dados.get("erro_clientes") or dados["erro_diretorio"], "erro")
        return redirect(url_for("monitoramento"))

    validacoes = dados["validacoes"]

    nomes_selecionados = request.args.get("clientes")

    if nomes_selecionados:
        nomes = {nome.strip() for nome in nomes_selecionados.split(",") if nome.strip()}
        validacoes = [item for item in validacoes if item["cliente"] in nomes]

    frequencias_selecionadas = request.args.get("frequencias")

    if frequencias_selecionadas:
        frequencias = {freq.strip().lower() for freq in frequencias_selecionadas.split(",") if freq.strip()}
        validacoes = [
            item for item in validacoes
            if item["frequencia_verificacao"].strip().lower() in frequencias
        ]

    if not validacoes:
        flash("Nenhum cliente encontrado para o infográfico com esses filtros.", "erro")
        return redirect(url_for("monitoramento"))

    return render_template("infografico.html", info=montar_infografico(validacoes))


@app.route("/monitoramento/gerar-aba-diaria", methods=["POST"])
def monitoramento_gerar_aba_diaria():
    """Grava, na aba do dia (criando se ainda nao existir) da planilha
    configurada em config.CLIENTES_XLSX_PATH, so os clientes informados em
    ?clientes=Nome1,Nome2 -- pensado pra preencher aos poucos ao longo do
    dia, por leva de horario de processamento (o botao na tela manda a
    selecao/filtro atual, igual o "Exportar planilha"). Linhas de levas
    anteriores no mesmo dia ficam intactas; cliente repetido tem a linha
    atualizada, nunca duplicada -- ver services/planilha_diaria_service.py."""
    dados, _ = obter_principal()

    if dados.get("erro_clientes"):
        flash(dados["erro_clientes"], "erro")
        return redirect(url_for("monitoramento"))

    validacoes = dados["validacoes"]

    nomes_selecionados = request.args.get("clientes")

    if nomes_selecionados:
        nomes = {nome.strip() for nome in nomes_selecionados.split(",") if nome.strip()}
        validacoes = [item for item in validacoes if item["cliente"] in nomes]

    if not validacoes:
        flash("Nenhum cliente encontrado para gravar com esses filtros.", "erro")
        return redirect(url_for("monitoramento"))

    try:
        nome_aba, criados, atualizados = atualizar_aba_diaria(validacoes, dados["clientes"])
    except PermissionError as exc:
        flash(str(exc), "erro")
        return redirect(url_for("monitoramento"))

    flash(
        f"Aba '{nome_aba}': {criados} cliente(s) novo(s) gravado(s), {atualizados} atualizado(s).",
        "sucesso",
    )
    return redirect(url_for("monitoramento"))


@app.route("/monitoramento/detalhamento")
def monitoramento_detalhamento():
    """Detalhamento por arquivo (le o conteudo de cada arquivo BAD para
    contar linhas) -- carregado sob demanda via fetch(), e tambem cacheado:
    so recalcula na primeira vez ou quando o Atualizar geral invalida o
    cache principal."""
    dados = obter_detalhamento()

    return render_template(
        "_detalhamento.html",
        erro_clientes=dados["erro_clientes"],
        erro_diretorio=dados["erro_diretorio"],
        detalhamento=dados["detalhamento"],
    )


@app.route("/monitoramento/cobrar-atrasados", methods=["POST"])
def monitoramento_cobrar_atrasados():
    nomes = set(request.form.getlist("clientes"))
    acao = request.form.get("acao")

    try:
        ids = [id_cliente for id_cliente, c in ClienteModel.todos().items() if c["nome"] in nomes]
        sucessos, falhas = processar_envio("atrasado", ids, acao)
    except (FileNotFoundError, ValueError) as exc:
        flash(str(exc), "erro")
        return redirect(url_for("monitoramento"))

    if sucessos:
        acao_label = "aberto(s) para visualizacao" if acao == "visualizar" else "enviado(s) automaticamente"
        flash(f"E-mail(s) de arquivo pendente {acao_label} para: {', '.join(sucessos)}.", "sucesso")

    if falhas:
        flash(f"Falha ao processar: {', '.join(falhas)}.", "erro")

    return redirect(url_for("monitoramento"))


@app.route("/erros")
def erros():
    try:
        clientes = ClienteModel.todos()
    except (FileNotFoundError, ValueError) as exc:
        flash(str(exc), "erro")
        clientes = {}

    # O envio de e-mail (erro ou atrasado) usa a varredura cacheada
    # (services/monitoramento_cache.py) para saber o ultimo arquivo BAD/
    # execucao de cada cliente -- aqui so exibimos quando foi a ultima
    # checagem e permitimos forcar uma nova (?atualizar=1) sem precisar ir
    # ate o Monitoramento.
    forcar = request.args.get("atualizar") == "1"
    dados, atualizado_em = obter_principal(forcar=forcar)

    # Pre-marca (e sinaliza) quem tem BAD/esta atrasado na ultima varredura
    # -- o usuario ainda pode desmarcar livremente, isso so agiliza o caso
    # comum.
    clientes_com_bad = {
        item["cliente"] for item in dados["validacoes"] if item["bad_status"] == "bad"
    }
    clientes_atrasados = {
        item["cliente"] for item in dados["validacoes"] if item["exec_status"] == "atrasado"
    }

    modelos = {
        chave: EmailModel.obter(chave)
        for chave in ("erro", "atrasado")
    }

    return render_template(
        "erros.html",
        pagina_ativa="erros",
        clientes=clientes,
        atualizado_em=atualizado_em,
        clientes_com_bad=clientes_com_bad,
        clientes_atrasados=clientes_atrasados,
        modelos=modelos,
    )


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

    destino = "erros" if nome_modelo in ("erro", "atrasado") else "faturamentos"

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
