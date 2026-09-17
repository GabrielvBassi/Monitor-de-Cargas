from models.cliente_model import ClienteModel
from models.email_model import EmailModel
from services.email_generator import EmailGenerator
from services.email_service import EmailService
from services.error_file_service import ErrorFileService
from services.historico_service import HistoricoService


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
                arquivos = ErrorFileService.buscar_arquivos_cliente(cliente["nome"])

                if not arquivos:
                    falhas.append(f"{cliente['nome']} (nenhum arquivo de erro encontrado)")
                    continue

                for arquivo in arquivos:
                    email = EmailGenerator.gerar(
                        nome_modelo,
                        modelo,
                        cliente,
                        variaveis_extra={
                            "arquivo": arquivo["arquivo"],
                            "quantidade_linhas": arquivo["quantidade_linhas"],
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
