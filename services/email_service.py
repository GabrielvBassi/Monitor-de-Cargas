import time
import webbrowser
from urllib.parse import quote

import psutil
from pywinauto import Desktop

import config


class EmailServiceError(Exception):
    """Falha ao automatizar o envio via UI (janela nao encontrada/nao confirmada)."""


class EmailService:
    """Abre o e-mail via mailto: e automatiza o envio invocando o botao
    "Enviar" da janela de composicao via UI Automation (Invoke Pattern).
    Nao rouba o foco do mouse/teclado, mas ainda depende da sessao do
    Windows estar ativa e desbloqueada (nao funciona com tela travada)."""

    def _link_mailto(self, email):
        destinatarios = ",".join(email["destinatarios"])
        parametros = [f"subject={quote(email['assunto'])}", f"body={quote(email['corpo'])}"]

        if email.get("cc"):
            parametros.append(f"cc={quote(','.join(email['cc']))}")

        return f"mailto:{destinatarios}?{'&'.join(parametros)}"

    def visualizar(self, email):
        webbrowser.open(self._link_mailto(email))

    def enviar(self, email):
        webbrowser.open(self._link_mailto(email))

        janela = self._aguardar_janela(email["assunto"])
        botao_enviar = self._localizar_botao_enviar(janela, email["assunto"])

        try:
            botao_enviar.invoke()
        except Exception as exc:
            raise EmailServiceError(
                f"Nao foi possivel acionar o botao Enviar para o assunto "
                f"'{email['assunto']}': {exc}"
            ) from exc

        self._aguardar_fechar(janela, email["assunto"])

    def _localizar_botao_enviar(self, janela, assunto):
        for botao in janela.descendants(control_type="Button"):
            try:
                texto = botao.window_text()
            except Exception:
                continue

            if texto and "enviar" in texto.lower():
                return botao

        raise EmailServiceError(
            f"Botao 'Enviar' nao encontrado na janela de composicao do "
            f"assunto '{assunto}'. O e-mail NAO foi enviado."
        )

    def _processo_e_confiavel(self, janela):
        try:
            nome_processo = psutil.Process(janela.process_id()).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

        nome_processo = nome_processo.lower()
        return any(esperado.strip().lower() in nome_processo for esperado in config.UI_PROCESSOS_ESPERADOS)

    def _aguardar_janela(self, assunto):
        limite = time.time() + config.UI_TIMEOUT_ABRIR_JANELA

        while time.time() < limite:
            for janela in Desktop(backend="uia").windows():
                try:
                    titulo = janela.window_text()
                except Exception:
                    continue

                if titulo and assunto.lower() in titulo.lower() and self._processo_e_confiavel(janela):
                    return janela

            time.sleep(0.5)

        raise EmailServiceError(
            f"Janela de composicao do Outlook nao encontrada para o assunto "
            f"'{assunto}' em {config.UI_TIMEOUT_ABRIR_JANELA}s. O e-mail NAO foi enviado."
        )

    def _aguardar_fechar(self, janela, assunto):
        limite = time.time() + config.UI_TIMEOUT_FECHAR_JANELA

        while time.time() < limite:
            if not janela.exists():
                return
            time.sleep(0.5)

        raise EmailServiceError(
            f"A janela de composicao do assunto '{assunto}' nao fechou apos "
            "acionar o botao Enviar -- o envio pode nao ter sido concluido. Verifique manualmente."
        )
