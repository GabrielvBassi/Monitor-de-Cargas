import os

#SFTP_HOST = "10.75.192.92"
#SFTP_PORT = 22
#ERROS_DIRETORIO = "/home/amabr_cargas/shell"
#ERROS_DIRETORIO = r"C:\Users\GBASSI\Documents\Python\arquivos"
#ERROS_DIRETORIO = r"\\VBR006001-002.int.mapfre.net\base$\_ BKP Bases\_BKP Erros"
ERROS_DIRETORIO = os.environ.get(
    "ERROS_DIRETORIO",
    r"\\VBR006001-002.int.mapfre.net\base$\_ BKP Bases\_BKP Erros",
)
ERROS_EXTENSAO = os.environ.get("ERROS_EXTENSAO", ".bad")

# Diretorio com os backups dos arquivos processados com SUCESSO (movidos
# apos a execucao). Usado para validar se cada cliente teve execucao dentro
# da frequencia de verificacao configurada na planilha de clientes.
BACKUP_DIRETORIO = os.environ.get(
    "BACKUP_DIRETORIO",
    r"\\VBR006001-002.int.mapfre.net\base$\_ BKP Bases\_BKP Cargas",
)
BACKUP_EXTENSAO = os.environ.get("BACKUP_EXTENSAO", ".txt")

# Planilha de clientes: basta abrir, editar e salvar para atualizar a lista
# usada pelo app (colunas: Cliente, Sistema, Ambiente, Periodo, Frequencia de
# Verificacao, Email Erro To, Email Erro CC, Ativo). Nao precisa reiniciar o
# app -- a planilha e relida a cada requisicao.

CLIENTES_XLSX_PATH = os.environ.get(
    "CLIENTES_XLSX_PATH",
    os.path.join(os.path.dirname(__file__), "faturados.xlsx"),
)

# Automacao de UI para o envio (botao Enviar da janela de composicao aberta
# via mailto:). Sem API/OAuth/SMTP: precisa da tela ativa e desbloqueada
# durante o processamento, e do Outlook novo configurado como app padrao para
# links mailto. Processo do Outlook novo (Microsoft.OutlookForWindows) e
# "olk.exe" -- o Outlook classico usa "OUTLOOK.EXE". A checagem abaixo aceita
# qualquer um dos dois.
UI_TIMEOUT_ABRIR_JANELA = int(os.environ.get("UI_TIMEOUT_ABRIR_JANELA", "30"))
UI_TIMEOUT_FECHAR_JANELA = int(os.environ.get("UI_TIMEOUT_FECHAR_JANELA", "10"))
UI_PROCESSOS_ESPERADOS = os.environ.get("UI_PROCESSOS_ESPERADOS", "olk,outlook").split(",")

