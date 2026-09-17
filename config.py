import os

ERROS_DIRETORIO = r"C:\Users\Gabriel\OneDrive\Área de Trabalho\Diretorio-teste"
ERROS_EXTENSAO = ".txt"

# Automacao de UI para o envio (botao Enviar da janela de composicao aberta
# via mailto:). Sem API/OAuth/SMTP: precisa da tela ativa e desbloqueada
# durante o processamento, e do Outlook novo configurado como app padrao para
# links mailto. Processo do Outlook novo (Microsoft.OutlookForWindows) e
# "olk.exe" -- o Outlook classico usa "OUTLOOK.EXE". A checagem abaixo aceita
# qualquer um dos dois.
UI_TIMEOUT_ABRIR_JANELA = int(os.environ.get("UI_TIMEOUT_ABRIR_JANELA", "30"))
UI_TIMEOUT_FECHAR_JANELA = int(os.environ.get("UI_TIMEOUT_FECHAR_JANELA", "10"))
UI_PROCESSOS_ESPERADOS = os.environ.get("UI_PROCESSOS_ESPERADOS", "olk,outlook").split(",")

