"""Executa o envio de e-mails sem a interface web, para uso com o Agendador
de Tarefas do Windows.

Requer a sessao do Windows ativa e DESBLOQUEADA no horario agendado (usa
automacao de UI). No Agendador, configure a tarefa com "Executar somente
quando o usuario estiver conectado" -- a opcao "Executar independente do
usuario ter feito logon ou nao" NAO funciona, pois roda numa sessao sem
area de trabalho interativa.

Os IDs de cliente sao gerados a partir do nome na planilha clientes.xlsx
(ex: "Mapfre" -> "mapfre"). Confira os IDs atuais na pagina Erros nas Cargas
ou Faturamentos (valor de cada checkbox).

Uso:
    python enviar_automatico.py --modelo erro --clientes mapfre,clienteb
    python enviar_automatico.py --modelo faturamento --clientes mapfre,clienteb --acao visualizar
"""
import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    filename=Path(__file__).resolve().parent / "envio_automatico.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

from services.processamento_service import processar_envio


def main():
    parser = argparse.ArgumentParser(description="Envio automatico de e-mails via UI automation.")
    parser.add_argument("--modelo", required=True, help="Chave do modelo de e-mail (ex: erro, faturamento)")
    parser.add_argument(
        "--clientes",
        required=True,
        help="IDs de clientes separados por virgula (ex: mapfre,clienteb)",
    )
    parser.add_argument("--acao", default="enviar", choices=["visualizar", "enviar"])
    args = parser.parse_args()

    ids_clientes = [id_cliente.strip() for id_cliente in args.clientes.split(",") if id_cliente.strip()]

    try:
        sucessos, falhas = processar_envio(args.modelo, ids_clientes, args.acao)
    except ValueError as exc:
        logging.error("Erro de validacao: %s", exc)
        sys.exit(1)

    if sucessos:
        logging.info("Processado com sucesso: %s", ", ".join(sucessos))

    if falhas:
        logging.error("Falha ao processar: %s", ", ".join(falhas))
        sys.exit(1)


if __name__ == "__main__":
    main()
