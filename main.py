import win32com.client as win32

# =========================
# CONFIGURAÇÕES DO E-MAIL
# =========================

destinatarios = [
    "gbassi@bbmapfre.com.br",
    "ffava@bbmapfre.com.br"
]

cc = [
    "ffava@bbmapfre.com.br"
]

assunto = "Teste de envio de e-mail automático"

corpo = """
Olá,

Este é um e-mail enviado automaticamente para testes.

Segue a mensagem que será enviada.

Atenciosamente,
Gabriel
"""


# =========================
# ENVIO DO E-MAIL
# =========================

outlook = win32.Dispatch("Outlook.Application")

email = outlook.CreateItem(0)

email.To = "; ".join(destinatarios)
email.CC = "; ".join(cc)
email.Subject = assunto
email.Body = corpo

email.Send()

print("E-mail enviado com sucesso!")