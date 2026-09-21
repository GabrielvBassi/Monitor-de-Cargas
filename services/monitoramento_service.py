from datetime import datetime

QTD_EVENTOS_GRAFICO = 8


def preparar_grafico_resumo(resumo):
    """Adiciona a cada item do resumo o percentual (0-100) de registros do
    arquivo BAD mais recente em relacao ao maior valor, para a barra
    horizontal."""
    maior_total = max((item["quantidade_linhas"] for item in resumo), default=0)

    for item in resumo:
        item["percentual"] = (item["quantidade_linhas"] / maior_total * 100) if maior_total else 0

    return resumo


def montar_kpis(validacoes):
    """Calcula os KPIs a partir das validacoes ja combinadas (BAD +
    execucao) -- mesma fonte de dados da tabela, para nunca divergir dela."""
    total = len(validacoes)

    def percentual(quantidade):
        return round(quantidade / total * 100) if total else 0

    clientes_ok = sum(1 for item in validacoes if item["bad_status"] == "ok" and item["exec_status"] == "ok")
    clientes_bad = sum(1 for item in validacoes if item["bad_status"] == "bad")
    clientes_aviso = sum(1 for item in validacoes if item["bad_status"] == "aviso")
    clientes_atrasados = sum(1 for item in validacoes if item["exec_status"] == "atrasado")

    return {
        "total_clientes": total,
        "clientes_ok": clientes_ok,
        "percentual_ok": percentual(clientes_ok),
        "clientes_bad": clientes_bad,
        "percentual_bad": percentual(clientes_bad),
        "clientes_aviso": clientes_aviso,
        "percentual_aviso": percentual(clientes_aviso),
        "clientes_atrasados": clientes_atrasados,
        "percentual_atrasados": percentual(clientes_atrasados),
    }


def combinar_validacoes(resumo, execucoes):
    """Junta, por cliente, o status do arquivo BAD mais recente com o status
    da execucao (backup) mais recente, numa unica linha para o painel."""
    execucoes_por_cliente = {item["cliente"]: item for item in execucoes}
    combinado = []

    for item in resumo:
        execucao = execucoes_por_cliente.get(item["cliente"], {})

        combinado.append({
            "cliente": item["cliente"],
            "frequencia_verificacao": item["frequencia_verificacao"],
            "bad_arquivo": item["arquivo"],
            "bad_modificado_em": item["modificado_em"],
            "bad_tipo": item["tipo"],
            "bad_status": item["status"],
            "exec_arquivo": execucao.get("arquivo"),
            "exec_modificado_em": execucao.get("modificado_em"),
            "exec_status": execucao.get("status", "nao_avaliado"),
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
