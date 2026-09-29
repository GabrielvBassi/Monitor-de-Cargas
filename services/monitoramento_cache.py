"""Cache em memoria dos dados de Monitoramento.

A regra de validacao (services/error_file_service.py, execucao_service.py,
arquivo_service.py) NAO muda -- este modulo so evita rodar essa validacao de
novo a cada vez que a pagina e aberta ou que se navega entre as abas. O
calculo so roda na primeira vez, ou quando o usuario clica em "Atualizar"
(forcar=True). Enquanto isso, qualquer acesso devolve o mesmo resultado ja
calculado, instantaneamente."""
from datetime import datetime

from models.cliente_model import ClienteModel
from services.error_file_service import ErrorFileService
from services.execucao_service import ExecucaoService
from services.monitoramento_service import combinar_validacoes, montar_kpis

_cache = {}


def _carregar_clientes():
    try:
        return ClienteModel.todos(), None
    except (FileNotFoundError, ValueError) as exc:
        return {}, str(exc)


def _calcular_principal():
    clientes, erro_clientes = _carregar_clientes()

    resumo = []
    execucoes = []
    erro_diretorio = None
    erro_backup = None

    if not erro_clientes:
        try:
            resumo = ErrorFileService.resumo_por_cliente(clientes)
        except FileNotFoundError as exc:
            erro_diretorio = str(exc)

        try:
            execucoes = ExecucaoService.validar_clientes(clientes)
        except FileNotFoundError as exc:
            erro_backup = str(exc)

    validacoes = combinar_validacoes(resumo, execucoes, clientes)

    return {
        "clientes": clientes,
        "erro_clientes": erro_clientes,
        "erro_diretorio": erro_diretorio,
        "erro_backup": erro_backup,
        "kpis": montar_kpis(validacoes),
        "validacoes": validacoes,
    }


def obter_principal(forcar=False):
    """Retorna (dados, atualizado_em). So recalcula se ainda nao houver
    cache ou se `forcar=True` (botao Atualizar) -- e invalida o
    detalhamento junto, ja que ele depende da mesma leitura de rede."""
    if forcar or "principal" not in _cache:
        _cache["principal"] = _calcular_principal()
        _cache["atualizado_em"] = datetime.now()
        _cache.pop("detalhamento", None)

    return _cache["principal"], _cache["atualizado_em"]


def obter_detalhamento(forcar=False):
    """Detalhamento por arquivo -- mais pesado (le o conteudo de cada
    arquivo), por isso fica em cache separado e so e calculado quando
    realmente pedido (botao "Carregar detalhamento" na tela)."""
    if forcar:
        _cache.pop("detalhamento", None)

    if "detalhamento" not in _cache:
        principal, _ = obter_principal()
        clientes = principal["clientes"]
        erro_clientes = principal["erro_clientes"]
        erro_diretorio = None
        detalhamento = []

        if not erro_clientes:
            try:
                detalhamento = ErrorFileService.detalhamento_por_cliente(clientes)
            except FileNotFoundError as exc:
                erro_diretorio = str(exc)

        _cache["detalhamento"] = {
            "erro_clientes": erro_clientes,
            "erro_diretorio": erro_diretorio,
            "detalhamento": detalhamento,
        }

    return _cache["detalhamento"]
