from datetime import datetime

QTD_EVENTOS_GRAFICO = 8


def preparar_grafico_pendentes(pendentes):
    """Adiciona a cada item de `pendentes` o percentual (0-100) do total de
    linhas em relacao ao maior valor, para desenhar a barra horizontal."""
    maior_total = max((item["total_linhas"] for item in pendentes), default=0)

    for item in pendentes:
        item["percentual"] = (item["total_linhas"] / maior_total * 100) if maior_total else 0

    return pendentes


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
