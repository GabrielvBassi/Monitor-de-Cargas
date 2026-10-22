r"""Gera pastas FAKE de backup/erros (uma por cliente da planilha) pra testar o
app sem acesso aos diretorios de rede.

Uso (PowerShell, na raiz do projeto):
    py dev/gerar_dados_teste.py
    $env:BACKUP_DIRETORIO = "$PWD\dev\dados_teste\cargas"
    $env:ERROS_DIRETORIO  = "$PWD\dev\dados_teste\erros"
    $env:EMAIL_TESTE_DESTINO = "seu.email@exemplo.com"   # NUNCA pule isso
    py app.py

Distribui os clientes em: OK (arquivo de hoje), ATRASADO (arquivo antigo),
SEM ARQUIVO (sem pasta) e alguns com BAD de hoje.
"""
import os
import re
import sys
from datetime import datetime, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from models.cliente_model import ClienteModel  # noqa: E402

DESTINO = os.path.join(RAIZ, "dev", "dados_teste")
CARGAS = os.path.join(DESTINO, "cargas")
ERROS = os.path.join(DESTINO, "erros")


def _pasta(nome):
    return re.sub(r'[<>:"/\|?*]', "_", nome).strip()


def _arquivo(pasta, nome, dias_atras, conteudo="registro\n"):
    quando = datetime.now() - timedelta(days=dias_atras)
    caminho = os.path.join(pasta, nome)
    os.makedirs(pasta, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    ts = quando.timestamp()
    os.utime(caminho, (ts, ts))


def main():
    os.makedirs(CARGAS, exist_ok=True)
    os.makedirs(ERROS, exist_ok=True)
    clientes = [c["nome"] for c in ClienteModel.todos().values()]

    for i, nome in enumerate(clientes):
        base = _pasta(nome).replace(" ", "_")
        papel = i % 5  # 0,1,2 = OK | 3 = atrasado | 4 = sem arquivo
        if papel == 4:
            continue
        dias = 0 if papel < 3 else 5
        data = (datetime.now() - timedelta(days=dias)).strftime("%Y%m%d")
        _arquivo(os.path.join(CARGAS, _pasta(nome)), f"{base}_F{data}1.TXT", dias)
        if papel == 1 and i % 2 == 0:
            _arquivo(os.path.join(ERROS, _pasta(nome)), f"{base}_I{data}1_BAD.TXT", 0, "cab\nlinha1\nlinha2\n")

    print(f"{len(clientes)} clientes -> {DESTINO}")


if __name__ == "__main__":
    main()

