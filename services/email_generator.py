from models.cliente_model import ClienteModel


class EmailGenerator:
    """Combina um modelo de e-mail com os dados de um cliente."""

    @staticmethod
    def gerar(nome_modelo, modelo, cliente, variaveis_extra=None):
        variaveis = cliente["variaveis"].copy()
        variaveis["cliente"] = cliente["nome"]

        if variaveis_extra:
            variaveis.update(variaveis_extra)

        assunto = modelo["assunto"].format(**variaveis)
        corpo = modelo["corpo"].format(**variaveis)

        if nome_modelo == "faturamento":
            destinatarios = ClienteModel.destinatarios_faturamento()
        else:
            destinatarios = cliente["destinatarios"].get(
                nome_modelo,
                {"to": [], "cc": []},
            )

        return {
            "cliente": cliente["nome"],
            "destinatarios": destinatarios.get("to", []),
            "cc": destinatarios.get("cc", []),
            "assunto": assunto,
            "corpo": corpo,
        }
