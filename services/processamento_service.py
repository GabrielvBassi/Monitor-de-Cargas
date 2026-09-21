from models.cliente_model import ClienteModel
from models.email_model import EmailModel
from services.email_generator import EmailGenerator
from services.email_service import EmailService
from services.historico_service import HistoricoService
from services.monitoramento_cache import obter_principal


def processar_envio(nome_modelo, ids_clientes, acao):
    """Gera e processa (visualiza ou envia) e-mails para os clientes informados.

    Levanta ValueError para entradas invalidas. Retorna (sucessos, falhas),
    onde cada item de falha ja descreve o motivo.
    """
    modelo = EmailModel.obter(nome_modelo)

    if not modelo or not modelo.get("ativo"):
        raise ValueError("Modelo de e-mail invalido ou inativo.")

    if not ids_clientes:
        raise ValueError("Selecione ao menos um cliente.")

    if acao not in ("visualizar", "enviar"):
        raise ValueError("Acao invalida.")

    validacoes_por_cliente = {}

    if nome_modelo == "erro":
        # Reaproveita a ultima varredura do Monitoramento (cache) em vez de
        # escanear o diretorio de novo -- o e-mail usa sempre o ultimo
        # registro BAD encontrado naquela varredura, nao uma busca nova.
        dados, _ = obter_principal()

        if dados.get("erro_clientes"):
            raise ValueError(dados["erro_clientes"])

        if dados.get("erro_diretorio"):
            raise ValueError(dados["erro_diretorio"])

        validacoes_por_cliente = {item["cliente"]: item for item in dados["validacoes"]}

    email_service = EmailService()

    sucessos = []
    falhas = []

    for id_cliente in ids_clientes:
        cliente = ClienteModel.obter(id_cliente)

        if not cliente:
            falhas.append(f"{id_cliente} (cliente nao encontrado)")
            continue

        try:
            if nome_modelo == "erro":
                validacao = validacoes_por_cliente.get(cliente["nome"])

                if not validacao or not validacao["bad_arquivo"]:
                    falhas.append(
                        f"{cliente['nome']} (nenhum arquivo BAD na ultima varredura do Monitoramento)"
                    )
                    continue

                email = EmailGenerator.gerar(
                    nome_modelo,
                    modelo,
                    cliente,
                    variaveis_extra={
                        "arquivo": validacao["bad_arquivo"],
                        "quantidade_linhas": validacao["bad_registros"],
                    },
                )

                if acao == "visualizar":
                    email_service.visualizar(email)
                else:
                    email_service.enviar(email)
            else:
                email = EmailGenerator.gerar(nome_modelo, modelo, cliente)

                if acao == "visualizar":
                    email_service.visualizar(email)
                else:
                    email_service.enviar(email)

            sucessos.append(cliente["nome"])
        except Exception as exc:
            falhas.append(f"{cliente['nome']} ({exc})")

    HistoricoService.registrar(nome_modelo, acao, sucessos, falhas)

    return sucessos, falhas
