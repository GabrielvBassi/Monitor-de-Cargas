import re

from config import ERROS_DIRETORIO, ERROS_EXTENSAO
from services.arquivo_service import (
    arquivo_mais_recente,
    arquivos_em_pastas,
    buscar_arquivos,
    listar_pastas,
    localizar_pastas_cliente,
)

PADRAO_TIPO = re.compile(r"_([FI])\d", re.IGNORECASE)


class ErrorFileService:
    """Localiza arquivos de erro (BAD) de um cliente no diretorio configurado."""

    @staticmethod
    def ler_registros(caminho_arquivo):
        """Retorna (registros, tem_cabecalho). A PRIMEIRA linha nao vazia do
        arquivo e sempre tratada como cabecalho (nao e um erro, so identifica
        o arquivo/formato) e nao entra na contagem -- vale tanto para o
        layout Mawdy (comeca com 'H', ex: H0000001043...) quanto pra layout
        proprio de cada cliente (nome das colunas, ex: 'FHCARGA NUMREGIS...').
        Linhas em branco tambem nao contam como registro. Um arquivo BAD com
        so a linha de cabecalho e um falso positivo (gerado sem nenhum erro
        de verdade) e fica com registros=0."""
        registros = 0
        tem_cabecalho = False
        primeira = True

        with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as arquivo:
            for linha in arquivo:
                linha = linha.lstrip("﻿").strip()

                if not linha:
                    continue

                if primeira:
                    tem_cabecalho = True
                else:
                    registros += 1

                primeira = False

        return registros, tem_cabecalho

    @classmethod
    def contar_linhas(cls, caminho_arquivo):
        """Quantidade de registros do arquivo, sem contar o cabecalho."""
        return cls.ler_registros(caminho_arquivo)[0]

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
    def _completar_arquivos(cls, arquivos):
        for arquivo in arquivos:
            arquivo["quantidade_linhas"] = cls.contar_linhas(arquivo["caminho"])
            arquivo["tipo"] = cls.classificar_tipo(arquivo["arquivo"])

        return arquivos

    @classmethod
    def buscar_arquivos_cliente(cls, nome_cliente):
        """Retorna TODOS os arquivos BAD do cliente (usado no envio de
        e-mail de erro, que gera uma mensagem por arquivo -- nao usar para
        o resumo do Monitoramento, que olha so o mais recente)."""
        arquivos = buscar_arquivos(ERROS_DIRETORIO, ERROS_EXTENSAO, nome_cliente)
        return cls._completar_arquivos(arquivos)

    @classmethod
    def resumo_por_cliente(cls, clientes):
        """Retorna, para TODOS os clientes cadastrados, o status baseado
        APENAS no arquivo BAD mais recente (nome contendo ERROS_EXTENSAO) da
        pasta do cliente -- so a pasta identifica o cliente, o resto do nome
        nao e avaliado. Filtrar pelo marcador aqui e essencial: algumas
        pastas recebem, junto do "_BAD" de verdade, um segundo arquivo por
        execucao com nome diferente (ex: "_ERRO") que NAO e o arquivo de
        erro de monitoramento -- sem o filtro, esse outro arquivo podia ser
        mais recente e ser escolhido no lugar do BAD de verdade. So le o
        conteudo (contar linhas) desse unico arquivo -- os outros so tem a
        data de modificacao consultada, sem abrir o arquivo. Essencial para
        performance em rede."""
        pastas = listar_pastas(ERROS_DIRETORIO)
        resumo = []

        for cliente in clientes.values():
            pastas_cliente = localizar_pastas_cliente(
                pastas, cliente["nome"], cliente.get("pastas_configuradas_bad"), ERROS_DIRETORIO
            )
            ultimo = arquivo_mais_recente(pastas_cliente, ERROS_EXTENSAO)

            if ultimo is None:
                status = "ok"
                quantidade_linhas = 0
                tipo = "-"
            else:
                quantidade_linhas, tem_cabecalho = cls.ler_registros(ultimo["caminho"])
                tipo = cls.classificar_tipo(ultimo["arquivo"])

                if quantidade_linhas > 0:
                    status = "bad"
                elif tem_cabecalho:
                    # So o cabecalho, sem nenhum registro de erro: falso
                    # positivo, nao deve aparecer como BAD no monitor.
                    status = "ok"
                else:
                    status = "aviso"

            resumo.append({
                "cliente": cliente["nome"],
                "frequencia_verificacao": cliente.get("frequencia_verificacao", "-"),
                "arquivo": ultimo["arquivo"] if ultimo else None,
                "modificado_em": ultimo["modificado_em"] if ultimo else None,
                "tipo": tipo,
                "quantidade_linhas": quantidade_linhas,
                "status": status,
                # Pasta(s) de BAD resolvidas de verdade -- ver comentario
                # equivalente em execucao_service.py.
                "pastas": pastas_cliente,
            })

        return resumo

    @classmethod
    def detalhamento_por_cliente(cls, clientes):
        """Lista TODOS os arquivos BAD de TODOS os clientes (mais recente
        primeiro) -- usado só na tabela de detalhamento/drill-down, mais
        pesada pois le o conteudo de cada arquivo encontrado."""
        pastas = listar_pastas(ERROS_DIRETORIO)
        detalhamento = []

        for cliente in clientes.values():
            pastas_cliente = localizar_pastas_cliente(
                pastas, cliente["nome"], cliente.get("pastas_configuradas_bad"), ERROS_DIRETORIO
            )
            arquivos = cls._completar_arquivos(arquivos_em_pastas(pastas_cliente, ERROS_EXTENSAO))

            for arquivo in arquivos:
                detalhamento.append({
                    "cliente": cliente["nome"],
                    "arquivo": arquivo["arquivo"],
                    "tipo": arquivo["tipo"],
                    "quantidade_linhas": arquivo["quantidade_linhas"],
                    "modificado_em": arquivo["modificado_em"],
                    "caminho": arquivo["caminho"],
                })

        detalhamento.sort(key=lambda item: item["modificado_em"], reverse=True)

        return detalhamento
