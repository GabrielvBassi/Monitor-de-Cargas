from datetime import datetime

QTD_EVENTOS_GRAFICO = 8


def montar_kpis(validacoes):
    """Calcula os KPIs a partir das validacoes ja combinadas (BAD +
    execucao) -- mesma fonte de dados da tabela, para nunca divergir dela.
    Alinhado com os grupos de filtro (bad_grupo/exec_grupo): 'OK' aqui
    significa 'nao gerou BAD' + 'processamento OK'."""
    total = len(validacoes)

    def percentual(quantidade):
        return round(quantidade / total * 100) if total else 0

    clientes_ok = sum(1 for item in validacoes if item["bad_grupo"] == "nao_bad" and item["exec_grupo"] == "ok")
    clientes_bad = sum(1 for item in validacoes if item["bad_grupo"] == "bad")
    clientes_pendentes = sum(1 for item in validacoes if item["exec_grupo"] == "pendente")

    return {
        "total_clientes": total,
        "clientes_ok": clientes_ok,
        "percentual_ok": percentual(clientes_ok),
        "clientes_bad": clientes_bad,
        "percentual_bad": percentual(clientes_bad),
        "clientes_pendentes": clientes_pendentes,
        "percentual_pendentes": percentual(clientes_pendentes),
    }


def combinar_validacoes(resumo, execucoes):
    """Junta, por cliente, o status do arquivo BAD mais recente com o status
    da execucao (backup) mais recente, numa unica linha para o painel.

    bad_grupo / exec_grupo sao os agrupamentos binarios usados nos filtros
    compostos da tela: "geraram BAD" x "nao geraram BAD", e "processamento
    pendente" (atrasado ou frequencia nao reconhecida) x "processamento OK"."""
    execucoes_por_cliente = {item["cliente"]: item for item in execucoes}
    combinado = []

    for item in resumo:
        execucao = execucoes_por_cliente.get(item["cliente"], {})
        exec_status = execucao.get("status", "nao_avaliado")

        combinado.append({
            "cliente": item["cliente"],
            "frequencia_verificacao": item["frequencia_verificacao"],
            "bad_arquivo": item["arquivo"],
            "bad_modificado_em": item["modificado_em"],
            "bad_registros": item["quantidade_linhas"],
            "bad_tipo": item["tipo"],
            "bad_status": item["status"],
            "bad_grupo": "bad" if item["status"] == "bad" else "nao_bad",
            "exec_arquivo": execucao.get("arquivo"),
            "exec_modificado_em": execucao.get("modificado_em"),
            "exec_status": exec_status,
            "exec_grupo": "ok" if exec_status == "ok" else "pendente",
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
