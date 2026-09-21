import os
from datetime import datetime


def _localizar_pastas_cliente(diretorio, nome_cliente):
    """Encontra, dentro de `diretorio`, a(s) subpasta(s) cujo nome bate com
    `nome_cliente` (comparacao tolerante a maiusculas/minusculas e a nomes
    parciais, ex: cliente 'C6Bank' casa com a pasta 'C6Bank' ou 'c6bank_bad')."""
    pastas = []

    for nome_entrada in os.listdir(diretorio):
        caminho_entrada = os.path.join(diretorio, nome_entrada)

        if not os.path.isdir(caminho_entrada):
            continue

        if nome_cliente.lower() not in nome_entrada.lower():
            continue

        pastas.append(caminho_entrada)

    return pastas


def buscar_arquivos(diretorio, extensao, nome_cliente):
    """Lista os arquivos com `extensao` dentro da subpasta do cliente
    (diretorio/<pasta do cliente>/*), usada tanto para os arquivos de erro
    (BAD) quanto para os arquivos de backup (execucoes com sucesso).

    Retorna lista vazia quando o cliente nao tem pasta (ainda sem
    ocorrencias) -- so levanta erro quando o diretorio base nao existe."""
    if not os.path.isdir(diretorio):
        raise FileNotFoundError(f"Diretorio nao encontrado: {diretorio}")

    encontrados = []

    for pasta_cliente in _localizar_pastas_cliente(diretorio, nome_cliente):
        for nome_arquivo in os.listdir(pasta_cliente):
            caminho_completo = os.path.join(pasta_cliente, nome_arquivo)

            if not os.path.isfile(caminho_completo):
                continue

            if not nome_arquivo.lower().endswith(extensao.lower()):
                continue

            encontrados.append({
                "arquivo": nome_arquivo,
                "caminho": caminho_completo,
                "modificado_em": datetime.fromtimestamp(os.path.getmtime(caminho_completo)),
            })

    return encontrados
