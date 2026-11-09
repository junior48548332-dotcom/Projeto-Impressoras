"""
Recursos compartilhados pelos testes.

O arquivo conftest.py é lido automaticamente pelo pytest. As
funções marcadas com @pytest.fixture podem ser pedidas por
qualquer teste, bastando citar o nome delas como parâmetro.

Tudo aqui trabalha em um banco temporário: o pytest cria uma
pasta nova para cada teste (tmp_path) e apaga depois. O banco
de verdade do projeto nunca é tocado.
"""

import json

from datetime import datetime

import pytest

import banco


# ================================================================
# BANCO TEMPORÁRIO
# ================================================================

@pytest.fixture
def banco_vazio(tmp_path, monkeypatch):
    """
    Aponta o sistema para um banco que ainda não existe.

    Serve para testar o que acontece antes de qualquer tabela
    ser criada.
    """

    caminho = tmp_path / "teste.db"

    monkeypatch.setattr(banco, "BANCO_DADOS", caminho)

    return caminho


@pytest.fixture
def conexao(banco_vazio):
    """Banco temporário já com as tabelas criadas."""

    conexao = banco.conectar()

    banco.criar_tabelas(conexao)

    yield conexao

    conexao.close()


# ================================================================
# DADOS DE EXEMPLO
# ================================================================

@pytest.fixture
def impressora_exemplo():
    """Uma impressora no formato que o monitor grava."""

    return {
        "local": "Diretoria",
        "modelo": "CX950",
        "tipo": "COLOR",
        "paper": "A3 / A4",
        "serie": "0123ABCD0123",
        "ip": "192.168.0.2",
        "status_rede": "online",
        "status_geral": "normal",
        "suprimentos": {
            "toner_preto": 60,
            "unidade_imagem": 80
        },
        "status_suprimentos": {
            "toner_preto": "normal",
            "unidade_imagem": "normal"
        }
    }


@pytest.fixture
def cadastro_exemplo():
    """Três impressoras no formato devolvido pela planilha."""

    return [
        {
            "local": "Diretoria",
            "modelo": "CX950",
            "tipo": "COLOR",
            "paper": "A3 / A4",
            "serie": "0123ABCD0123",
            "ip": "192.168.0.2"
        },
        {
            "local": "Almoxarifado",
            "modelo": "MS812",
            "tipo": "MONO",
            "paper": "A4",
            "serie": "0123ABCD0124",
            "ip": "192.168.0.3"
        },
        {
            "local": "Fiscal",
            "modelo": "MX632",
            "tipo": "MONO",
            "paper": "A4",
            "serie": "0123ABCD0125",
            "ip": "192.168.0.4"
        }
    ]


# ================================================================
# CONTROLE DA DATA
# ================================================================

class RelogioFixo:
    """
    Substitui o relógio do sistema nos testes.

    O banco grava a data da medição com datetime.now(). Para
    testar consultas por dia, precisamos escolher essa data.
    """

    def __init__(self, texto):
        self.texto = texto

    def now(self, fuso=None):
        # O banco chama datetime.now(FUSO_HORARIO). O fuso é
        # recebido e ignorado: o teste já escolheu a hora exata
        # que quer ver gravada.
        return datetime.strptime(
            self.texto,
            "%Y-%m-%d %H:%M:%S"
        )


@pytest.fixture
def relogio(monkeypatch):
    """Permite gravar medições com a data que o teste quiser."""

    def ajustar(texto):
        monkeypatch.setattr(
            banco,
            "datetime",
            RelogioFixo(texto)
        )

    return ajustar


# ================================================================
# ATALHOS
# ================================================================

@pytest.fixture
def gravar_medicao(conexao, impressora_exemplo, relogio):
    """
    Grava uma medição informando data, IP e status.

    Deixa os testes de consulta curtos e legíveis.
    """

    def gravar(
        data_hora,
        ip="192.168.0.2",
        local="Diretoria",
        status_rede="online",
        status_geral="normal",
        suprimentos=None
    ):
        relogio(data_hora)

        impressora = dict(impressora_exemplo)

        impressora["ip"] = ip
        impressora["local"] = local
        impressora["status_rede"] = status_rede
        impressora["status_geral"] = status_geral

        if suprimentos is not None:
            impressora["suprimentos"] = suprimentos

        banco.salvar_medicao(conexao, impressora)

        return impressora

    return gravar


@pytest.fixture
def consolidacao_exemplo():
    """Um registro de consolidação diária."""

    return {
        "data": "2026-10-01",
        "local": "Diretoria",
        "ip": "192.168.0.2",
        "modelo": "CX950",
        "total_medicoes": 10,
        "online": 9,
        "offline": 1,
        "criticas": 2,
        "atencoes": 3,
        "normais": 5,
        "consumo_medio": 2.5,
        "ultima_medicao": "2026-10-01 18:00:00"
    }
