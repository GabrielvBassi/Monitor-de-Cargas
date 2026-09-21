import re

from config import ERROS_DIRETORIO, ERROS_EXTENSAO
from services.arquivo_service import buscar_arquivos

PADRAO_TIPO = re.compile(r"_([FI])\d", re.IGNORECASE)


class ErrorFileService:
    """Localiza arquivos de erro (BAD) de um cliente no diretorio configurado."""

    @staticmethod
    def contar_linhas(caminho_arquivo):
        with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as arquivo:
            return sum(1 for _ in arquivo)

    @staticmethod
    def classificar_tipo(nome_arquivo):
        """Classifica o arquivo como FULL ou INCREMENTAL pela letra que segue
        o nome do cliente (ex: CLIENTE_F202601011_BAD.TXT / CLIENTE_I202601011_BAD.TXT).
        Retorna 'Nao identificado' quando o padrao nao e encontrado."""
        match = PADRAO_TIPO.search(nome_arquivo)

        if not match:
            return "Nao identificado"

        return "FULL" if match.group(1).upper() == "F" else "INCREMENTAL"

    @classmethod
    def buscar_arquivos_cliente(cls, nome_cliente):
        arquivos = buscar_arquivos(ERROS_DIRETORIO, ERROS_EXTENSAO, nome_cliente)

        for arquivo in arquivos:
            arquivo["quantidade_linhas"] = cls.contar_linhas(arquivo["caminho"])
            arquivo["tipo"] = cls.classificar_tipo(arquivo["arquivo"])

        return arquivos

    @classmethod
    def resumo_por_cliente(cls, clientes):
        """Retorna, para TODOS os clientes cadastrados, um resumo dos
        arquivos BAD: contagens, tipos encontrados, ultima ocorrencia e
        status (ok / aviso / bad)."""
        resumo = []

        for cliente in clientes.values():
            arquivos = cls.buscar_arquivos_cliente(cliente["nome"])
            arquivos_com_registros = [a for a in arquivos if a["quantidade_linhas"] > 0]
            registros_bad = sum(a["quantidade_linhas"] for a in arquivos)
            tipos = sorted({a["tipo"] for a in arquivos})

            if not arquivos:
                status = "ok"
            elif not arquivos_com_registros:
                status = "aviso"
            else:
                status = "bad"

            resumo.append({
                "cliente": cliente["nome"],
                "frequencia_verificacao": cliente.get("frequencia_verificacao", "-"),
                "tipo": ", ".join(tipos) if tipos else "-",
                "arquivos_bad": len(arquivos),
                "arquivos_com_registros": len(arquivos_com_registros),
                "registros_bad": registros_bad,
                "ultima_ocorrencia": max((a["modificado_em"] for a in arquivos), default=None),
                "status": status,
                "arquivos": arquivos,
            })

        return resumo
