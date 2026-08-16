"""
Testes de contenção de destinos externos de backup (KI-043) --
docs/engineering/plans/PLAN-LGPD-Compliance.md.

EXTERNAL_BACKUP_DESTINATIONS_ENABLED/GOOGLE_DRIVE_BACKUP_DIR/BACKUP_EMAIL_SENHA_APP são decididos no
momento do import do módulo -- mesmo padrão de tests/test_ambiente_preview.py, cada cenário roda
`import fluxoly_config`/`import app` num subprocesso isolado (conftest.py já importa `app` uma vez por
sessão com env fixo, o que não reflete um boot com os destinos externos configurados).
"""

import json
import os
import subprocess
import sys
import tempfile

_RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rodar(codigo, env_extra):
    env = {"PATH": os.environ.get("PATH", "")}
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=_RAIZ_PROJETO,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _eventos_json(stdout):
    eventos = []
    for linha in stdout.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        try:
            eventos.append(json.loads(linha))
        except ValueError:
            continue
    return eventos


class TestDestinosExternosContidos:
    def test_google_drive_fica_vazio_mesmo_configurado(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import fluxoly_config; print(repr(fluxoly_config.GOOGLE_DRIVE_BACKUP_DIR))",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR": "/algum/caminho/configurado",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "''"

    def test_email_senha_fica_vazia_mesmo_configurada(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import fluxoly_config; print(repr(fluxoly_config.BACKUP_EMAIL_SENHA_APP))",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_BACKUP_EMAIL_SENHA": "senha-app-configurada-fake",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "''"

    def test_flag_de_contencao_permanece_falso(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import fluxoly_config; print(fluxoly_config.EXTERNAL_BACKUP_DESTINATIONS_ENABLED)",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR": "/algum/caminho/configurado",
                    "IR_FLOW_BACKUP_EMAIL_SENHA": "senha-app-configurada-fake",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "False"

    def test_valores_configurados_sao_preservados_para_o_log_de_aviso(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import fluxoly_config; "
                "print(repr(fluxoly_config.GOOGLE_DRIVE_BACKUP_DIR_CONFIGURADO)); "
                "print(repr(fluxoly_config.BACKUP_EMAIL_SENHA_APP_CONFIGURADA))",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR": "/algum/caminho/configurado",
                    "IR_FLOW_BACKUP_EMAIL_SENHA": "senha-app-configurada-fake",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        linhas = resultado.stdout.strip().splitlines()
        assert linhas[-2] == "'/algum/caminho/configurado'"
        assert linhas[-1] == "'senha-app-configurada-fake'"


class TestLogDeBootQuandoDestinoExternoConfigurado:
    def _env_base(self, tmp_dir):
        return {
            "IR_FLOW_DATA_DIR": tmp_dir,
            "IR_FLOW_ENABLE_BACKGROUND_JOBS": "0",
            "MERCADO_PHONE_SYNC_ENABLED": "0",
            "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
            "IR_FLOW_ADMIN_PASSWORD": "senha-admin-teste-nao-usar-em-producao",
        }

    def test_log_aparece_quando_destino_externo_configurado(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            env = self._env_base(tmp_dir)
            env["IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR"] = "/algum/caminho/configurado"
            resultado = _rodar("import app", env)
        assert resultado.returncode == 0, resultado.stderr
        eventos = _eventos_json(resultado.stdout)
        evento = next((e for e in eventos if e.get("message") == "backup_destinos_externos_contidos"), None)
        assert evento is not None
        assert evento.get("google_drive_configurado") is True
        assert evento.get("email_configurado") is False

    def test_log_nao_aparece_sem_destino_externo_configurado(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar("import app", self._env_base(tmp_dir))
        assert resultado.returncode == 0, resultado.stderr
        mensagens = {evento.get("message") for evento in _eventos_json(resultado.stdout)}
        assert "backup_destinos_externos_contidos" not in mensagens
