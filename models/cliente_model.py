class ClienteModel:
    """Cadastro de clientes: destinatarios de erro por cliente e variaveis por tipo de e-mail.

    Os destinatarios de faturamento nao variam por cliente, por isso possuem
    uma unica definicao em FATURAMENTO_DESTINATARIOS.
    """

    FATURAMENTO_DESTINATARIOS = {
        "to": ["faturamento@empresa.com"],
        "cc": [],
    }

    CLIENTES = {

        "mafri": {

            "nome": "Mapfre",

            "destinatarios": {

                "erro": {
                    "to": ["gabrielvbassi@hotmail.com"],
                    "cc": ["gabrielvb477@gmail.com"],
                },
            },

            "variaveis": {
                "sistema": "Sistema Mapfre",
                "ambiente": "Producao",
                "periodo": "Julho/2026",
            },
        },

        "cliente_b": {

            "nome": "ClienteB",

            "destinatarios": {

                "erro": {
                    "to": ["suporte@clienteb.com"],
                    "cc": [],
                },
            },

            "variaveis": {
                "sistema": "Sistema Cliente B",
                "ambiente": "Producao",
                "periodo": "Julho/2026",
            },
        },
    }

    @classmethod
    def todos(cls):
        return cls.CLIENTES

    @classmethod
    def obter(cls, id_cliente):
        return cls.CLIENTES.get(id_cliente)

    @classmethod
    def destinatarios_faturamento(cls):
        return cls.FATURAMENTO_DESTINATARIOS
