import re
from datetime import datetime, timedelta

import config
from services.arquivo_service import arquivos_em_pastas, listar_pastas, localizar_pastas_cliente

_PERIODOS_FIXOS = {
    "diaria": timedelta(days=1),
    "diária": timedelta(days=1),
    "semanal": timedelta(weeks=1),
    "quinzenal": timedelta(days=15),
    "mensal": timedelta(days=31),
}

_PADRAO_PERIODO_LIVRE = re.compile(r"(\d+)\s*(hora|dia|semana)", re.IGNORECASE)


def periodo_frequencia(frequencia):
    """Converte o texto de frequencia de verificacao (ex: 'Semanal', 'A cada
    3 dias') na janela de tolerancia (timedelta) dentro da qual deve existir
    pelo menos um arquivo de backup. Retorna None quando o texto nao e
    reconhecido (nesse caso a validacao fica marcada como 'nao avaliada')."""
    texto = (frequencia or "").strip().lower()

    if texto in _PERIODOS_FIXOS:
        return _PERIODOS_FIXOS[texto]

    match = _PADRAO_PERIODO_LIVRE.search(texto)

    if not match:
        return None

    quantidade = int(match.group(1))
    unidade = match.group(2).lower()

    if unidade == "hora":
        return timedelta(hours=quantidade)

    if unidade == "semana":
        return timedelta(weeks=quantidade)

    return timedelta(days=quantidade)


class ExecucaoService:
    """Valida, para cada cliente, se ha um arquivo de backup (execucao com
    sucesso) dentro da janela definida pela frequencia de verificacao."""

    @classmethod
    def validar_clientes(cls, clientes):
        """Le o diretorio de backup UMA UNICA VEZ (nao uma vez por cliente)
        -- essencial em compartilhamentos de rede."""
        pastas = listar_pastas(config.BACKUP_DIRETORIO)
        resultado = []

        for cliente in clientes.values():
            pastas_cliente = localizar_pastas_cliente(pastas, cliente["nome"])
            arquivos = arquivos_em_pastas(pastas_cliente, config.BACKUP_EXTENSAO)
            ultimo = max(arquivos, key=lambda arquivo: arquivo["modificado_em"], default=None)

            frequencia = cliente.get("frequencia_verificacao", "")
            periodo = periodo_frequencia(frequencia)

            if periodo is None:
                status = "nao_avaliado"
            elif ultimo and (datetime.now() - ultimo["modificado_em"]) <= periodo:
                status = "ok"
            else:
                status = "atrasado"

            resultado.append({
                "cliente": cliente["nome"],
                "frequencia_verificacao": frequencia or "-",
                "arquivo": ultimo["arquivo"] if ultimo else None,
                "ultima_execucao": ultimo["modificado_em"] if ultimo else None,
                "status": status,
            })

        return resultado
