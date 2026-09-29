from datetime import datetime, time

QTD_EVENTOS_GRAFICO = 8


def _formatar_horario_execucao(valor):
    """Normaliza o campo HORARIO EXECUCAO da planilha (pode vir como
    datetime.time, texto como 'DESCONTINUADO'/'N/A', ou vazio) pro filtro e
    pra coluna da tabela."""
    if isinstance(valor, time):
        return valor.strftime("%H:%M")

    if valor is None:
        return "-"

    texto = str(valor).strip()
    return texto or "-"


def montar_kpis(validacoes):
    """Calcula os KPIs a partir das validacoes ja combinadas (BAD +
    execucao) -- mesma fonte de dados da tabela, para nunca divergir dela.

    Cada card reflete uma unica dimensao/status, sem combinar BAD com
    execucao:
    - Cliente OK: processamento (execucao) OK.
    - Clientes com BAD: arquivo BAD mais recente com registros.
    - Sem Arquivo: processamento que ainda nao ocorreu nenhuma vez.
    - Atrasados: processamento que ja ocorreu antes, mas esta fora do prazo."""
    total = len(validacoes)

    def percentual(quantidade):
        return round(quantidade / total * 100) if total else 0

    clientes_ok = sum(1 for item in validacoes if item["exec_status"] == "ok")
    clientes_bad = sum(1 for item in validacoes if item["bad_status"] == "bad")
    clientes_sem_arquivo = sum(1 for item in validacoes if item["exec_status"] == "sem_arquivo")
    clientes_atrasados = sum(1 for item in validacoes if item["exec_status"] == "atrasado")

    return {
        "total_clientes": total,
        "clientes_ok": clientes_ok,
        "percentual_ok": percentual(clientes_ok),
        "clientes_bad": clientes_bad,
        "percentual_bad": percentual(clientes_bad),
        "clientes_sem_arquivo": clientes_sem_arquivo,
        "percentual_sem_arquivo": percentual(clientes_sem_arquivo),
        "clientes_atrasados": clientes_atrasados,
        "percentual_atrasados": percentual(clientes_atrasados),
    }


def combinar_validacoes(resumo, execucoes, clientes=None):
    """Junta, por cliente, o status do arquivo BAD mais recente com o status
    da execucao (backup) mais recente, numa unica linha para o painel. Os
    filtros da tela comparam direto contra bad_status/exec_status (ok /
    aviso / bad, e ok / sem_arquivo / atrasado / nao_avaliado).

    `clientes` (dict id->cadastro, opcional) traz o horario de execucao
    configurado na planilha -- usado no filtro/coluna "Horario Execucao"."""
    execucoes_por_cliente = {item["cliente"]: item for item in execucoes}
    horarios_por_nome = {
        cadastro["nome"]: cadastro.get("horario_execucao")
        for cadastro in (clientes or {}).values()
    }
    combinado = []

    for item in resumo:
        execucao = execucoes_por_cliente.get(item["cliente"], {})

        combinado.append({
            "cliente": item["cliente"],
            "frequencia_verificacao": item["frequencia_verificacao"],
            "horario_execucao": _formatar_horario_execucao(horarios_por_nome.get(item["cliente"])),
            "bad_arquivo": item["arquivo"],
            "bad_modificado_em": item["modificado_em"],
            "bad_registros": item["quantidade_linhas"],
            "bad_tipo": item["tipo"],
            "bad_status": item["status"],
            "bad_pastas": item.get("pastas") or [],
            "exec_arquivo": execucao.get("arquivo"),
            "exec_modificado_em": execucao.get("modificado_em"),
            "exec_status": execucao.get("status", "nao_avaliado"),
            "exec_pastas": execucao.get("pastas") or [],
        })

    return combinado


def preparar_grafico_historico(historico):
    """Retorna os ultimos eventos (ordem cronologica) com contagem de
    sucessos/falhas e percentuais para a barra empilhada."""
    eventos = list(reversed(historico))[-QTD_EVENTOS_GRAFICO:]

    for evento in eventos:
        evento["qtd_sucessos"] = len(evento.get("sucessos") or [])
        evento["qtd_falhas"] = len(evento.get("falhas") or [])
        try:
            evento["label"] = datetime.fromisoformat(evento["timestamp"]).strftime("%d/%m %H:%M")
        except (KeyError, ValueError):
            evento["label"] = "?"

    maior_total = max(
        (evento["qtd_sucessos"] + evento["qtd_falhas"] for evento in eventos),
        default=0,
    )

    for evento in eventos:
        evento["percentual_sucessos"] = (evento["qtd_sucessos"] / maior_total * 100) if maior_total else 0
        evento["percentual_falhas"] = (evento["qtd_falhas"] / maior_total * 100) if maior_total else 0

    return eventos
