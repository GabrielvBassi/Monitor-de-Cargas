from datetime import datetime

QTD_EVENTOS_GRAFICO = 8


def preparar_grafico_resumo(resumo):
    """Adiciona a cada item do resumo o percentual (0-100) de registros BAD
    em relacao ao maior valor, para a barra horizontal."""
    maior_total = max((item["registros_bad"] for item in resumo), default=0)

    for item in resumo:
        item["percentual"] = (item["registros_bad"] / maior_total * 100) if maior_total else 0

    return resumo


def montar_detalhamento(resumo):
    """Achata os arquivos de cada cliente numa lista unica (mais recente
    primeiro) para a tabela de detalhamento por arquivo."""
    detalhamento = []

    for item in resumo:
        for arquivo in item["arquivos"]:
            detalhamento.append({
                "cliente": item["cliente"],
                "arquivo": arquivo["arquivo"],
                "tipo": arquivo["tipo"],
                "quantidade_linhas": arquivo["quantidade_linhas"],
                "modificado_em": arquivo["modificado_em"],
                "caminho": arquivo["caminho"],
            })

    detalhamento.sort(key=lambda item: item["modificado_em"], reverse=True)

    return detalhamento


def montar_kpis(resumo):
    return {
        "total_clientes": len(resumo),
        "clientes_bad": sum(1 for item in resumo if item["status"] == "bad"),
        "arquivos_bad": sum(item["arquivos_bad"] for item in resumo),
        "registros_bad": sum(item["registros_bad"] for item in resumo),
    }


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
