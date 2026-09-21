import os
from datetime import datetime


def listar_pastas(diretorio):
    """Lista, uma UNICA vez, as subpastas de primeiro nivel de `diretorio`.

    Chamado uma vez por diretorio (nao uma vez por cliente) -- em
    compartilhamentos de rede, listar o diretorio repetidamente para cada
    cliente e o que deixa a pagina lenta/parada esperando resposta."""
    if not os.path.isdir(diretorio):
        raise FileNotFoundError(f"Diretorio nao encontrado: {diretorio}")

    pastas = []

    for nome_entrada in os.listdir(diretorio):
        caminho_entrada = os.path.join(diretorio, nome_entrada)

        if os.path.isdir(caminho_entrada):
            pastas.append((nome_entrada, caminho_entrada))

    return pastas


def localizar_pastas_cliente(pastas, nome_cliente):
    """Filtra, dentre as pastas ja listadas (via listar_pastas), as que
    pertencem a `nome_cliente` -- nao acessa o disco/rede, so filtra em
    memoria a lista recebida.

    Prioriza nome EXATO da pasta (sem diferenciar maiusculas/minusculas ou
    espacos nas pontas). Isso evita que um cliente cujo nome e prefixo de
    outro (ex: "STARR COMPANIES" vs "STARR COMPANIES 01"/"02", que sao
    clientes DIFERENTES) acabe casando com a pasta errada. So cai para
    "pasta contem o nome do cliente" quando nenhuma pasta exata e encontrada,
    como reserva para pastas com nomenclatura levemente diferente."""
    nome_cliente_normalizado = nome_cliente.strip().lower()

    exatas = [
        caminho for nome, caminho in pastas
        if nome.strip().lower() == nome_cliente_normalizado
    ]

    if exatas:
        return exatas

    return [caminho for nome, caminho in pastas if nome_cliente_normalizado in nome.strip().lower()]


def arquivos_em_pastas(pastas_cliente, extensao=None):
    """Lista os arquivos dentro das pastas ja resolvidas de um cliente (uma
    por cliente, normalmente). Se `extensao` for informada, filtra por ela;
    se for None, lista TODOS os arquivos da pasta, sem avaliar o nome --
    usado quando so a pasta importa e o criterio de escolha e a data de
    modificacao mais recente, nao o nome do arquivo."""
    encontrados = []

    for pasta in pastas_cliente:
        for nome_arquivo in os.listdir(pasta):
            caminho_completo = os.path.join(pasta, nome_arquivo)

            if not os.path.isfile(caminho_completo):
                continue

            if extensao and not nome_arquivo.lower().endswith(extensao.lower()):
                continue

            encontrados.append({
                "arquivo": nome_arquivo,
                "caminho": caminho_completo,
                "modificado_em": datetime.fromtimestamp(os.path.getmtime(caminho_completo)),
            })

    return encontrados


def arquivo_mais_recente(pastas_cliente):
    """Retorna o arquivo com data de modificacao mais recente dentre TODOS
    os arquivos das pastas informadas, independente do nome/extensao."""
    arquivos = arquivos_em_pastas(pastas_cliente)
    return max(arquivos, key=lambda arquivo: arquivo["modificado_em"], default=None)


def buscar_arquivos(diretorio, extensao, nome_cliente):
    """Busca de um unico cliente (le o diretorio base + a(s) pasta(s) do
    cliente). Para varrer TODOS os clientes de uma vez, use listar_pastas()
    uma vez e depois localizar_pastas_cliente()/arquivos_em_pastas() por
    cliente, para nao relistar o diretorio base repetidamente."""
    pastas = listar_pastas(diretorio)
    pastas_cliente = localizar_pastas_cliente(pastas, nome_cliente)

    return arquivos_em_pastas(pastas_cliente, extensao)
