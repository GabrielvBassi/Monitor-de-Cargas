import os
from datetime import datetime

from config import ERROS_DIRETORIO, ERROS_EXTENSAO


class ErrorFileService:
    """Localiza arquivos de erro de um cliente no diretorio configurado e conta suas linhas."""

    @staticmethod
    def contar_linhas(caminho_arquivo):
        with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as arquivo:
            return sum(1 for _ in arquivo)

    @classmethod
    def buscar_arquivos_cliente(cls, nome_cliente):
        if not os.path.isdir(ERROS_DIRETORIO):
            raise FileNotFoundError(f"Diretorio de erros nao encontrado: {ERROS_DIRETORIO}")

        arquivos_encontrados = []

        for nome_arquivo in os.listdir(ERROS_DIRETORIO):
            caminho_completo = os.path.join(ERROS_DIRETORIO, nome_arquivo)

            if not os.path.isfile(caminho_completo):
                continue

            if not nome_arquivo.lower().endswith(ERROS_EXTENSAO.lower()):
                continue

            if nome_cliente.lower() not in nome_arquivo.lower():
                continue

            arquivos_encontrados.append({
                "arquivo": nome_arquivo,
                "caminho": caminho_completo,
                "quantidade_linhas": cls.contar_linhas(caminho_completo),
                "modificado_em": datetime.fromtimestamp(os.path.getmtime(caminho_completo)),
            })

        return arquivos_encontrados

    @classmethod
    def pendentes_por_cliente(cls, clientes):
        """Retorna, para cada cliente com arquivos de erro pendentes, o nome
        do cliente, os arquivos encontrados (com data de modificacao) e o
        total de linhas somado."""
        pendentes = []

        for cliente in clientes.values():
            arquivos = cls.buscar_arquivos_cliente(cliente["nome"])

            if arquivos:
                pendentes.append({
                    "cliente": cliente["nome"],
                    "arquivos": arquivos,
                    "total_linhas": sum(arquivo["quantidade_linhas"] for arquivo in arquivos),
                })

        return pendentes
