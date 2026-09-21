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


def _dividir_emails(valor):
    if not valor:
        return []

    partes = re.split(r"[;,]", str(valor))
    return [parte.strip() for parte in partes if parte.strip()]


def _interpretar_ativo(valor):
    if isinstance(valor, bool):
        return valor

    if valor is None or str(valor).strip() == "":
        return True

    texto = _normalizar(valor)

    if texto in _VALORES_FALSOS:
        return False

    return True


def _marcado_sim(valor):
    return _normalizar(valor) == "sim"


def _derivar_frequencia(frequencia_explicita, diario, semanal, mensal):
    """Usa a coluna 'Frequencia de Verificacao' quando existir; senao deriva
    das colunas 'Acompanhamento Diario/Semanal/Mensal' (formato da planilha
    de controle de faturamento), priorizando a mais frequente quando mais de
    uma estiver marcada 'SIM'."""
    if frequencia_explicita and str(frequencia_explicita).strip():
        return str(frequencia_explicita).strip()

    if _marcado_sim(diario):
        return "Diaria"

    if _marcado_sim(semanal):
        return "Semanal"

    if _marcado_sim(mensal):
        return "Mensal"

    return "-"


def _mapear_colunas(linha_cabecalho):
    """Identifica, pela palavra-chave no titulo de cada coluna, qual campo
    ela representa. Tolerante a acentos, maiusculas/minusculas e pequenas
    variacoes de redacao no cabecalho da planilha."""
    colunas = {}

    for indice, celula in enumerate(linha_cabecalho):
        palavras = set(_normalizar(celula).split())

        if not palavras:
            continue

        if "cliente" in palavras:
            colunas["nome"] = indice
        elif "sistema" in palavras:
            colunas["sistema"] = indice
        elif "ambiente" in palavras:
            colunas["ambiente"] = indice
        elif "periodo" in palavras:
            colunas["periodo"] = indice
        elif "frequencia" in palavras:
            colunas["frequencia_verificacao"] = indice
        elif "acompanhamento" in palavras and "semanal" in palavras:
            colunas["acompanhamento_semanal"] = indice
        elif "acompanhamento" in palavras and "mensal" in palavras:
            colunas["acompanhamento_mensal"] = indice
        elif "acompanhamento" in palavras:
            colunas["acompanhamento_diario"] = indice
        elif "ativo" in palavras:
            colunas["ativo"] = indice
        elif "erro" in palavras and "to" in palavras:
            colunas["erro_to"] = indice
        elif "erro" in palavras and "cc" in palavras:
            colunas["erro_cc"] = indice

    return colunas


class ClienteModel:
    """Cadastro de clientes, carregado a partir da planilha configurada em
    config.CLIENTES_XLSX_PATH -- basta editar e salvar o arquivo para
    atualizar a lista, sem precisar mexer no codigo.

    Os destinatarios de faturamento nao variam por cliente, por isso
    continuam com uma unica definicao em FATURAMENTO_DESTINATARIOS.
    """

    FATURAMENTO_DESTINATARIOS = {
        "to": ["faturamento@empresa.com"],
        "cc": [],
    }

    @classmethod
    def _carregar(cls):
        try:
            planilha = openpyxl.load_workbook(config.CLIENTES_XLSX_PATH, data_only=True)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Planilha de clientes nao encontrada: {config.CLIENTES_XLSX_PATH}"
            ) from exc

        aba = planilha.active
        linhas = aba.iter_rows(values_only=True)

        try:
            cabecalho = next(linhas)
        except StopIteration:
            raise ValueError(f"Planilha de clientes esta vazia: {config.CLIENTES_XLSX_PATH}")

        colunas = _mapear_colunas(cabecalho)

        if "nome" not in colunas:
            raise ValueError(
                "Planilha de clientes precisa de uma coluna 'Cliente' com o nome de cada cliente."
            )

        clientes = {}
        ids_usados = set()

        for linha in linhas:
            nome = linha[colunas["nome"]] if colunas["nome"] < len(linha) else None

            if not nome or not str(nome).strip():
                continue

            nome = str(nome).strip()

            def valor(chave):
                indice = colunas.get(chave)
                if indice is None or indice >= len(linha):
                    return None
                return linha[indice]

            if not _interpretar_ativo(valor("ativo")):
                continue

            id_cliente = _slugify(nome)
            sufixo = 2
            while id_cliente in ids_usados:
                id_cliente = f"{_slugify(nome)}_{sufixo}"
                sufixo += 1
            ids_usados.add(id_cliente)

            clientes[id_cliente] = {
                "nome": nome,
                "frequencia_verificacao": _derivar_frequencia(
                    valor("frequencia_verificacao"),
                    valor("acompanhamento_diario"),
                    valor("acompanhamento_semanal"),
                    valor("acompanhamento_mensal"),
                ),
                "destinatarios": {
                    "erro": {
                        "to": _dividir_emails(valor("erro_to")),
                        "cc": _dividir_emails(valor("erro_cc")),
                    },
                },
                "variaveis": {
                    "sistema": (valor("sistema") or "").strip(),
                    "ambiente": (valor("ambiente") or "").strip(),
                    "periodo": (valor("periodo") or "").strip(),
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
