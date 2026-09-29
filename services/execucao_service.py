import re
from datetime import datetime, timedelta

import config
from services.arquivo_service import arquivo_mais_recente, listar_pastas, localizar_pastas_cliente

_PERIODOS_FIXOS = {
    "diaria": timedelta(days=1),
    "diária": timedelta(days=1),
    "diario": timedelta(days=1),
    "diário": timedelta(days=1),
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
        -- essencial em compartilhamentos de rede. So a pasta identifica o
        cliente; dentro dela, o arquivo considerado e sempre o de data de
        modificacao mais recente, independente do nome/extensao."""
        pastas = listar_pastas(config.BACKUP_DIRETORIO)
        resultado = []

        for cliente in clientes.values():
            pastas_cliente = localizar_pastas_cliente(
                pastas, cliente["nome"], cliente.get("pastas_configuradas_backup"), config.BACKUP_DIRETORIO
            )
            ultimo = arquivo_mais_recente(pastas_cliente)

            frequencia = cliente.get("frequencia_verificacao", "")
            periodo = periodo_frequencia(frequencia)

            if periodo is None:
                status = "nao_avaliado"
            elif ultimo is None:
                # Nunca houve backup para este cliente -- processamento
                # ainda nao ocorreu (diferente de "atrasado", que pressupoe
                # que ja ocorreu antes e agora esta fora do prazo).
                status = "sem_arquivo"
            elif (datetime.now() - ultimo["modificado_em"]) <= periodo:
                status = "ok"
            else:
                status = "atrasado"

            resultado.append({
                "cliente": cliente["nome"],
                "frequencia_verificacao": frequencia or "-",
                "arquivo": ultimo["arquivo"] if ultimo else None,
                "modificado_em": ultimo["modificado_em"] if ultimo else None,
                "status": status,
                # Pasta(s) de backup resolvidas de verdade (config ou
                # casamento por nome) -- usado na exportacao da planilha de
                # controle, que precisa mostrar o caminho real, nao so o
                # texto configurado (que pode estar vazio).
                "pastas": pastas_cliente,
            })

        return resultado
