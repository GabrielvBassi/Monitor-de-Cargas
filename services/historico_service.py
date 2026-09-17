import json
from datetime import datetime
from pathlib import Path

HISTORICO_PATH = Path(__file__).resolve().parent.parent / "historico.jsonl"
LIMITE_PADRAO = 30


class HistoricoService:
    """Registra e le o historico de processamentos (visualizar/enviar) em um
    arquivo JSON Lines local, usado pela aba de Monitoramento."""

    @staticmethod
    def registrar(nome_modelo, acao, sucessos, falhas):
        evento = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "modelo": nome_modelo,
            "acao": acao,
            "sucessos": sucessos,
            "falhas": falhas,
        }

        with open(HISTORICO_PATH, "a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(evento, ensure_ascii=False) + "\n")

    @staticmethod
    def listar(limite=LIMITE_PADRAO):
        if not HISTORICO_PATH.exists():
            return []

        with open(HISTORICO_PATH, "r", encoding="utf-8") as arquivo:
            linhas = [linha for linha in arquivo if linha.strip()]

        eventos = [json.loads(linha) for linha in linhas]
        eventos.reverse()

        return eventos[:limite]
