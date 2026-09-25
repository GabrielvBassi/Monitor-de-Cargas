# Monitor de Cargas

Painel web (Flask) para acompanhar o processamento de arquivos de clientes (backups e erros/BAD), sinalizar pendências e disparar e-mails de notificação e faturamento direto pelo Outlook.

## Requisitos

- Windows, com **Outlook novo** instalado e configurado como aplicativo padrão para links `mailto:` (o envio de e-mail usa automação de UI, não API/SMTP).
- Python 3.10+
- Acesso de rede aos compartilhamentos de backup/erros (UNC), configurados em `config.py`.
- Arquivo `AcompanhamentoFaturados.xlsx` com a aba **"Monitor"** preenchida (cadastro de clientes, frequências, diretórios e contatos).

## Instalação

```bash
pip install -r requirements.txt
```

Pacotes principais: `Flask`, `openpyxl` (leitura da planilha), `pywinauto` + `psutil` (automação de UI para envio de e-mail).

## Executar

```bash
python app.py
```

Acesse `http://127.0.0.1:5000` (ou a porta configurada) no navegador. Mantenha a tela desbloqueada ao usar as ações de envio de e-mail, já que elas controlam a janela do Outlook.

### Configuração (opcional, via variáveis de ambiente)

Todas têm um valor padrão em `config.py`; sobrescreva só se precisar apontar para outro caminho:

| Variável | Uso |
|---|---|
| `ERROS_DIRETORIO` | Pasta de rede com os arquivos de erro (BAD) |
| `BACKUP_DIRETORIO` | Pasta de rede com os backups processados com sucesso |
| `CLIENTES_XLSX_PATH` | Caminho da planilha de clientes |
| `UI_TIMEOUT_ABRIR_JANELA` / `UI_TIMEOUT_FECHAR_JANELA` | Timeouts (segundos) da automação de envio |

### Envio automático (sem abrir o navegador)

`enviar_automatico.py` roda o mesmo envio de e-mail via linha de comando, pensado para o Agendador de Tarefas do Windows (a sessão precisa estar logada e desbloqueada no horário agendado):

```bash
python enviar_automatico.py --modelo erro --clientes mapfre,clienteb
python enviar_automatico.py --modelo atrasado --clientes mapfre --acao visualizar
```

## Funcionalidades

- **Monitoramento** — dashboard principal: KPIs (clientes OK, com BAD, pendentes, atrasados), tabela/cards com status de processamento e BAD por cliente, filtros avançados (processamento, status BAD, período, cliente, frequência, arquivo, ordenação incluindo "prioridade"), filtros salvos, exportação para CSV e histórico de envios.
- **Notificações** — lista clientes com arquivo BAD e/ou processamento atrasado; permite escolher o modelo de e-mail (Erro ou Atrasado) e visualizar ou enviar automaticamente, um e-mail por cliente, com os dados da última checagem.
- **Faturamentos** — envio de e-mail de faturamento por cliente.
- **Envio de e-mail** — feito por automação de UI (abre o Outlook via `mailto:` e aciona o botão Enviar), já que a conta não pode usar a API do Graph nem SMTP com senha de app (bloqueio de TI).
- Clientes com o campo "CONTROLM / MANUAL" marcado como `API` são desconsiderados do monitoramento (integração não é por arquivo).
