class EmailModel:
    """Modelos (templates) de e-mail disponiveis na aplicacao."""

    MODELOS = {

        "erro": {
            "titulo": "Erro de Processamento",
            "ativo": True,

            "assunto": "Erro no processamento - {cliente}",

            "corpo": """Ola,

Foi identificado um erro no processamento do cliente {cliente}.

Sistema: {sistema}
Ambiente: {ambiente}
Arquivo: {arquivo}
Quantidade de linhas: {quantidade_linhas}

Favor verificar a ocorrencia.

Atenciosamente,
Equipe
""",
        },

        "faturamento": {
            "titulo": "Faturamento",
            "ativo": True,

            "assunto": "Faturamento - {cliente}",

            "corpo": """Ola,

O faturamento do cliente {cliente} foi processado.

Sistema: {sistema}
Periodo: {periodo}

Atenciosamente,
Equipe
""",
        },
    }

    @classmethod
    def modelos_ativos(cls):
        """Retorna apenas os modelos habilitados para uso na interface."""
        return {
            chave: modelo
            for chave, modelo in cls.MODELOS.items()
            if modelo.get("ativo")
        }

    @classmethod
    def obter(cls, nome_modelo):
        return cls.MODELOS.get(nome_modelo)
