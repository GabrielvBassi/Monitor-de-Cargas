from datetime import date

# Status do infografico (rotulo, classe CSS) a partir do exec_status do
# Monitoramento. "Vazio" = frequencia nao reconhecida (nao avaliado).
_STATUS = {
    "ok": ("OK", "ok"),
    "sem_arquivo": ("PENDENTE ARQUIVO", "pendente"),
    "atrasado": ("Atrasada", "atrasada"),
    "nao_avaliado": ("Vazio", "vazio"),
}
ORDEM_STATUS = ["OK", "PENDENTE ARQUIVO", "Atrasada", "Vazio"]

_ROTULOS_FREQUENCIA = {
    "DIARIO": "Diária",
    "DIARIA": "Diária",
    "SEMANAL": "Semanal",
    "QUINZENAL": "Quinzenal",
    "MENSAL": "Mensal",
}
_ORDEM_GRUPOS = ["Diária", "Semanal", "Quinzenal", "Mensal"]


def _rotulo_frequencia(frequencia):
    chave = (frequencia or "").strip().upper().replace("Á", "A").replace("Í", "I")

    if chave in ("", "-"):
        return "Sem frequência"

    return _ROTULOS_FREQUENCIA.get(chave, frequencia.strip().capitalize())


def _resumo(itens):
    total = len(itens)
    por_status = {rotulo: 0 for rotulo in ORDEM_STATUS}

    for item in itens:
        por_status[item["status"]] += 1

    ok = por_status["OK"]

    return {
        "total": total,
        "ok": ok,
        "nao_ok": total - ok,
        "percentual": round(ok * 100 / total) if total else 0,
        "por_status": por_status,
    }


def montar_infografico(validacoes, hoje=None):
    """Monta TUDO a partir das validacoes recebidas (nada de historico nem
    contadores anteriores) e valida os numeros antes de devolver. Agrupa por
    frequencia, numerando sequencialmente dentro de cada grupo."""
    hoje = hoje or date.today()
    itens = []

    for v in validacoes:
        if "vayon" in v["cliente"].lower():
            continue

        rotulo, classe = _STATUS.get(v["exec_status"], _STATUS["nao_avaliado"])
        data_arquivo = v.get("exec_data_arquivo")
        item = {
            "cliente": v["cliente"],
            "arquivo": v.get("exec_arquivo"),
            "status": rotulo,
            "classe": classe,
            "ultima_atualizacao": data_arquivo.strftime("%d/%m/%Y") if data_arquivo else "-",
            "frequencia": _rotulo_frequencia(v["frequencia_verificacao"]),
        }
        itens.append(item)

    nomes_grupos = sorted(
        {i["frequencia"] for i in itens},
        key=lambda n: (_ORDEM_GRUPOS.index(n) if n in _ORDEM_GRUPOS else 99, n),
    )
    grupos = []

    for nome in nomes_grupos:
        do_grupo = sorted((i for i in itens if i["frequencia"] == nome), key=lambda i: i["cliente"].lower())

        for numero, item in enumerate(do_grupo, start=1):
            item["numero"] = numero

        grupos.append({"nome": nome, "itens": do_grupo, "resumo": _resumo(do_grupo)})

    geral = _resumo(itens)
    erros = []

    if sum(geral["por_status"].values()) != geral["total"]:
        erros.append("Soma dos status diferente do total.")

    if sum(g["resumo"]["total"] for g in grupos) != geral["total"]:
        erros.append("Soma dos grupos diferente do total.")

    for grupo in grupos:
        if [i["numero"] for i in grupo["itens"]] != list(range(1, len(grupo["itens"]) + 1)):
            erros.append(f"Numeração fora de sequência em {grupo['nome']}.")

    return {
        "data": hoje.strftime("%d/%m"),
        "periodicidade": " + ".join(nomes_grupos) if nomes_grupos else "-",
        "grupos": grupos,
        "geral": geral,
        "ordem_status": ORDEM_STATUS,
        "erros_validacao": erros,
    }
