import os
import re
from datetime import datetime


def resolver_pasta_configurada(diretorio_base, caminho_configurado):
    """Tenta resolver um caminho configurado na planilha (pode vir de outra
    maquina/drive, ex: "Z:\\_BKP Cargas\\Auto_+_Casa\\Mapfre") contra o
    `diretorio_base` real usado por este app.

    A logica: acha, dentro do caminho configurado, o segmento cujo nome
    bate com o nome final de `diretorio_base` (que deve ser o mesmo nos
    dois ambientes, ja que e a mesma pasta de rede vista por mapeamentos
    diferentes) -- e junta o que vier DEPOIS disso (podendo ser mais de um
    nivel, ex: "Auto_+_Casa\\Mapfre") no `diretorio_base` real.

    Retorna o caminho absoluto resolvido (o chamador deve confirmar com
    os.path.isdir antes de usar), ou None se nao for possivel relacionar
    os dois caminhos."""
    if not caminho_configurado or not diretorio_base:
        return None

    nome_base = os.path.basename(os.path.normpath(diretorio_base)).strip().lower()
    segmentos = [segmento for segmento in re.split(r"[\\/]+", caminho_configurado.strip()) if segmento]

    for indice, segmento in enumerate(segmentos):
        if segmento.strip().lower() == nome_base:
            resto = segmentos[indice + 1:]

            if not resto:
                return None

            return os.path.join(diretorio_base, *resto)

    return None


def listar_pastas(diretorio):
    """Lista, uma UNICA vez, as subpastas de primeiro nivel de `diretorio`.

    Chamado uma vez por diretorio (nao uma vez por cliente) -- em
    compartilhamentos de rede, listar o diretorio repetidamente para cada
    cliente e o que deixa a pagina lenta/parada esperando resposta. Usa
    os.scandir (nao os.listdir) para reaproveitar os metadados que o
    Windows ja retorna junto da listagem, evitando uma chamada de rede
    extra por entrada."""
    if not os.path.isdir(diretorio):
        raise FileNotFoundError(f"Diretorio nao encontrado: {diretorio}")

    pastas = []

    with os.scandir(diretorio) as entradas:
        for entrada in entradas:
            if entrada.is_dir():
                pastas.append((entrada.name, entrada.path))

    return pastas


def localizar_pastas_cliente(pastas, nome_cliente, pastas_configuradas=None, diretorio_base=None):
    """Filtra, dentre as pastas ja listadas (via listar_pastas), as que
    pertencem a `nome_cliente` -- nao acessa o disco/rede, so filtra em
    memoria a lista recebida (exceto o passo 1, que faz um os.path.isdir
    pontual so quando ha caminho configurado pra resolver).

    Ordem de prioridade:
    1. `pastas_configuradas` como CAMINHO (pode vir de outra maquina/drive,
       ex: "Z:\\_BKP Cargas\\Auto_+_Casa\\Mapfre", inclusive aninhado em
       mais de um nivel) -- resolvido contra `diretorio_base` via
       resolver_pasta_configurada(). So confirma pastas que realmente
       existem no disco.
    2. `pastas_configuradas` como NOME simples de pasta de primeiro nivel
       (ex: "MAPFRE - PSICOLOGICA") -- match exato contra as pastas ja
       listadas, sem tocar o disco de novo.
       Se nada dos passos 1/2 encontrar nada, cai pro comportamento padrao
       abaixo -- nao para de buscar.
    3. Nome EXATO da pasta = nome do cliente (sem diferenciar maiusculas/
       minusculas ou espacos nas pontas). Evita que um cliente cujo nome e
       prefixo de outro (ex: "STARR COMPANIES" vs "STARR COMPANIES 01"/"02",
       que sao clientes DIFERENTES) acabe casando com a pasta errada.
    4. "pasta contem o nome do cliente" -- reserva final para pastas com
       nomenclatura levemente diferente."""
    if pastas_configuradas:
        resolvidas = []

        for caminho_configurado in pastas_configuradas:
            resolvido = resolver_pasta_configurada(diretorio_base, caminho_configurado)

            if resolvido and os.path.isdir(resolvido):
                resolvidas.append(resolvido)

        if resolvidas:
            return resolvidas

        configuradas_normalizadas = {
            pasta.strip().lower() for pasta in pastas_configuradas if pasta and pasta.strip()
        }

        encontradas = [
            caminho for nome, caminho in pastas
            if nome.strip().lower() in configuradas_normalizadas
        ]

        if encontradas:
            return encontradas

    nome_cliente_normalizado = nome_cliente.strip().lower()

    exatas = [
        caminho for nome, caminho in pastas
        if nome.strip().lower() == nome_cliente_normalizado
    ]

    if exatas:
        return exatas

    return [caminho for nome, caminho in pastas if nome_cliente_normalizado in nome.strip().lower()]


def arquivos_em_pastas(pastas_cliente, marcador=None):
    """Lista os arquivos dentro das pastas ja resolvidas de um cliente (uma
    por cliente, normalmente).

    `marcador`, quando informado, e um texto que precisa aparecer em
    QUALQUER parte do nome do arquivo (nao so no final/extensao) -- ex:
    "BAD" casa com "CLIENTE_I202411011_BAD.TXT", cuja extensao real e
    ".TXT" e "BAD" fica no meio do nome. Se `marcador` for None, lista
    TODOS os arquivos da pasta, sem avaliar o nome -- usado quando so a
    pasta importa e o criterio de escolha e a data de modificacao mais
    recente (Monitoramento).

    Usa os.scandir: em compartilhamentos de rede (Windows/SMB), a data de
    modificacao ja vem junto da listagem da pasta, entao entrada.stat() nao
    dispara uma chamada de rede adicional por arquivo como os.path.getmtime
    dispararia -- essencial quando a pasta tem muitos arquivos."""
    encontrados = []

    for pasta in pastas_cliente:
        with os.scandir(pasta) as entradas:
            for entrada in entradas:
                if not entrada.is_file():
                    continue

                if marcador and marcador.lower() not in entrada.name.lower():
                    continue

                encontrados.append({
                    "arquivo": entrada.name,
                    "caminho": entrada.path,
                    "modificado_em": datetime.fromtimestamp(entrada.stat().st_mtime),
                })

    return encontrados


def arquivo_mais_recente(pastas_cliente):
    """Retorna o arquivo com data de modificacao mais recente dentre TODOS
    os arquivos das pastas informadas, independente do nome/extensao."""
    arquivos = arquivos_em_pastas(pastas_cliente)
    return max(arquivos, key=lambda arquivo: arquivo["modificado_em"], default=None)


def buscar_arquivos(diretorio, marcador, nome_cliente):
    """Busca de um unico cliente (le o diretorio base + a(s) pasta(s) do
    cliente). Para varrer TODOS os clientes de uma vez, use listar_pastas()
    uma vez e depois localizar_pastas_cliente()/arquivos_em_pastas() por
    cliente, para nao relistar o diretorio base repetidamente."""
    pastas = listar_pastas(diretorio)
    pastas_cliente = localizar_pastas_cliente(pastas, nome_cliente)

    return arquivos_em_pastas(pastas_cliente, marcador)
