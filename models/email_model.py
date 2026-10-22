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

        "atrasado": {
            "titulo": "Atrasado",
            "ativo": True,

            "assunto": "Arquivo pendente - {cliente}",

            "corpo": """Prezado(a) cliente {cliente},

Verificamos que, ate o momento ({data_hoje}), nao recebemos o arquivo de processamento referente ao periodo esperado.

Sistema: {sistema}
Frequencia esperada: {frequencia_verificacao}
Ultimo arquivo recebido: {arquivo} (data do arquivo: {data_arquivo})
Dias sem recebimento: {dias_atraso}

Solicitamos, por gentileza, que verifique o envio e nos encaminhe o arquivo o quanto antes. Caso ja tenha enviado, desconsidere esta mensagem e nos avise para que possamos conferir.

Ficamos a disposicao.

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
