import re
import unicodedata

import openpyxl

import config

_VALORES_VERDADEIROS = {"1", "true", "sim", "x", "yes", "ativo"}
_VALORES_FALSOS = {"0", "false", "nao", "não", "no", "inativo"}


def _normalizar(texto):
    texto = str(texto or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def _slugify(nome):
    slug = _normalizar(nome).replace(" ", "_")
    return slug or "cliente"


def _dividir_lista(valor):
    """Divide um campo com varios valores separados por ; ou , -- e trata
    "-" (convencao usada nas planilhas pra 'sem informacao') como vazio."""
    if not valor:
        return []

    texto = str(valor).strip()

    if not texto or texto == "-":
        return []

    partes = re.split(r"[;,]", texto)
    return [parte.strip() for parte in partes if parte.strip()]


# Alias por clareza de leitura nos pontos onde a lista e de e-mails.
_dividir_emails = _dividir_lista


def _interpretar_ativo(valor):
    if isinstance(valor, bool):
        return valor

    if valor is None or str(valor).strip() == "":
        return True

    texto = _normalizar(valor)

    if texto in _VALORES_FALSOS:
        return False

    return True


def _derivar_frequencia(frequencia_explicita):
    if frequencia_explicita and str(frequencia_explicita).strip() and str(frequencia_explicita).strip() != "-":
        return str(frequencia_explicita).strip()

    return "-"


def _mapear_colunas_monitor(linha_cabecalho):
    """A aba 'Monitor' tem uma coluna 'CLIENTE' duplicada: a primeira (junto
    com FREQUENCIA) NAO fica na mesma linha da segunda (que traz contatos e
    diretorios) -- sao duas tabelas coladas lado a lado, cada uma na sua
    propria ordem. Por decisao do usuario: a 1a coluna 'CLIENTE'+FREQUENCIA
    vira uma tabela de consulta por NOME (nao por posicao de linha); a 2a
    coluna 'CLIENTE' em diante define a lista de clientes de verdade."""
    colunas = {}
    ocorrencias_cliente = []

    for indice, celula in enumerate(linha_cabecalho):
        palavras = set(_normalizar(celula).split())

        if not palavras:
            continue

        if "cliente" in palavras:
            ocorrencias_cliente.append(indice)
        elif "frequencia" in palavras:
            colunas["frequencia_lookup"] = indice
        elif "email" in palavras and "comercial" in palavras:
            colunas["erro_to"] = indice
        elif "email" in palavras and "parceiro" in palavras:
            colunas["erro_cc"] = indice
        elif "diretorios" in palavras and "bads" in palavras:
            colunas["pastas_bad"] = indice
        elif "diretorios" in palavras:
            colunas["pastas_backup"] = indice
        elif "controlm" in palavras:
            colunas["controlm_manual"] = indice
        elif "ativo" in palavras:
            colunas["ativo"] = indice
        elif "sistema" in palavras:
            colunas["sistema"] = indice
        elif "ambiente" in palavras:
            colunas["ambiente"] = indice
        elif "periodo" in palavras:
            colunas["periodo"] = indice

    if len(ocorrencias_cliente) >= 2:
        colunas["cliente_frequencia"] = ocorrencias_cliente[0]
        colunas["nome"] = ocorrencias_cliente[1]
    elif ocorrencias_cliente:
        colunas["cliente_frequencia"] = ocorrencias_cliente[0]
        colunas["nome"] = ocorrencias_cliente[0]

    return colunas


def _valor(linha, colunas, chave):
    indice = colunas.get(chave)

    if indice is None or indice >= len(linha):
        return None

    return linha[indice]


class ClienteModel:
    """Cadastro de clientes, carregado da aba 'Monitor' da planilha
    configurada em config.CLIENTES_XLSX_PATH -- basta editar e salvar o
    arquivo para atualizar a lista, sem precisar mexer no codigo. A aba e
    fixada pelo NOME ("Monitor"), nao pela aba ativa do arquivo -- assim,
    abas diarias novas (ex: "23_09", criadas a cada dia) nunca acabam sendo
    lidas por engano no lugar dela.

    Os destinatarios de faturamento nao variam por cliente, por isso
    continuam com uma unica definicao em FATURAMENTO_DESTINATARIOS.
    """

    ABA_CLIENTES = "Monitor"

    FATURAMENTO_DESTINATARIOS = {
        "to": [
            "financeiro@mawdy.com",
            "AFSILVA@mawdy.com",
            "maolive@mawdy.com",
            "STELL1@mawdy.com",
            "EDRAMOS@mawdy.com",
            "CEDUAR3@mawdy.com",
            "guperei@mawdy.com",
            "patyfer@mawdy.com"],
        "cc": [
            "ffava@mapfre.com.br",
            "Dimiranda@mapfre.com.br",
            "malgarci@mapfre.com.br",
            "Lfigueredo@mapfre.com.br",
            "lbaldino@mapfre.com.br"

],
    }

    @classmethod
    def _carregar(cls):
        try:
            planilha = openpyxl.load_workbook(config.CLIENTES_XLSX_PATH, data_only=True)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Planilha de clientes nao encontrada: {config.CLIENTES_XLSX_PATH}"
            ) from exc

        if cls.ABA_CLIENTES not in planilha.sheetnames:
            raise ValueError(
                f"Planilha de clientes precisa de uma aba chamada '{cls.ABA_CLIENTES}' "
                f"(abas encontradas: {', '.join(planilha.sheetnames)})"
            )

        linhas = list(planilha[cls.ABA_CLIENTES].iter_rows(values_only=True))

        if not linhas:
            raise ValueError(f"Aba '{cls.ABA_CLIENTES}' esta vazia: {config.CLIENTES_XLSX_PATH}")

        colunas = _mapear_colunas_monitor(linhas[0])

        if "nome" not in colunas:
            raise ValueError(
                f"Aba '{cls.ABA_CLIENTES}' precisa de uma coluna 'Cliente' com o nome de cada cliente."
            )

        linhas_dados = linhas[1:]

        # Tabela de consulta de frequencia por NOME (1a coluna Cliente +
        # Frequencia) -- independente da ordem de linha em relacao ao resto
        # dos dados (2a coluna Cliente em diante).
        frequencia_por_nome = {}

        if "cliente_frequencia" in colunas and "frequencia_lookup" in colunas:
            for linha in linhas_dados:
                nome_freq = _valor(linha, colunas, "cliente_frequencia")

                if nome_freq and str(nome_freq).strip():
                    frequencia_por_nome[_normalizar(nome_freq)] = _valor(linha, colunas, "frequencia_lookup")

        clientes = {}
        ids_usados = set()

        for linha in linhas_dados:
            nome = _valor(linha, colunas, "nome")

            if not nome or not str(nome).strip():
                continue

            nome = str(nome).strip()

            if not _interpretar_ativo(_valor(linha, colunas, "ativo")):
                continue

            # Clientes marcados como "API" na coluna CONTROLM/MANUAL nao tem
            # pasta de backup/BAD pra monitorar (integracao e via API, nao
            # arquivo) -- ficam de fora do cadastro, igual aos inativos.
            if _normalizar(_valor(linha, colunas, "controlm_manual")) == "api":
                continue

            id_cliente = _slugify(nome)
            sufixo = 2
            while id_cliente in ids_usados:
                id_cliente = f"{_slugify(nome)}_{sufixo}"
                sufixo += 1
            ids_usados.add(id_cliente)

            frequencia_explicita = frequencia_por_nome.get(_normalizar(nome))

            # O aviso de "atrasado" reaproveita o mesmo contato comercial/
            # parceiro ja cadastrado pra erro -- nao ha coluna separada na
            # planilha pra isso.
            contato_to = _dividir_emails(_valor(linha, colunas, "erro_to"))
            contato_cc = _dividir_emails(_valor(linha, colunas, "erro_cc"))

            clientes[id_cliente] = {
                "nome": nome,
                "frequencia_verificacao": _derivar_frequencia(frequencia_explicita),
                # Diretorios configurados na planilha, um campo por
                # compartilhamento (erros e backup tem pastas diferentes por
                # cliente, entao nao dá pra reaproveitar um so campo pros
                # dois). Vazio ou nao encontrado cai pro casamento padrao por
                # nome (exato, depois "pasta contem o nome do cliente").
                "pastas_configuradas_backup": _dividir_lista(_valor(linha, colunas, "pastas_backup")),
                "pastas_configuradas_bad": _dividir_lista(_valor(linha, colunas, "pastas_bad")),
                "destinatarios": {
                    "erro": {"to": contato_to, "cc": contato_cc},
                    "atrasado": {"to": contato_to, "cc": contato_cc},
                },
                "variaveis": {
                    "sistema": (_valor(linha, colunas, "sistema") or "").strip(),
                    "ambiente": (_valor(linha, colunas, "ambiente") or "").strip(),
                    "periodo": (_valor(linha, colunas, "periodo") or "").strip(),
                },
            }

        return clientes

    @classmethod
    def todos(cls):
        return cls._carregar()

    @classmethod
    def obter(cls, id_cliente):
        return cls._carregar().get(id_cliente)

    @classmethod
    def destinatarios_faturamento(cls):
        return cls.FATURAMENTO_DESTINATARIOS
