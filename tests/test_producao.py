"""
Testes das configurações de produção.

Quando o sistema é publicado, duas coisas precisam estar
certas antes de qualquer outra:

1. O modo de depuração do Flask DESLIGADO. A página de erro do
   debug traz um console Python interativo. Quem conseguir
   provocar um erro no site executa comandos no servidor.

2. O servidor web não pode ser iniciado só por importar o
   app.py. Na nuvem é assim que o Flask é carregado, e um
   app.run() solto deixaria o site pendurado.

O terceiro teste cuida de um detalhe menor, mas visível: o
aviso de "sistema desatualizado" do dashboard precisa ter uma
tolerância maior que o intervalo entre as coletas.
"""

import importlib
import io
import re

import pytest

import config

from app import app


# ================================================================
# RECARREGAR O CONFIG
# ================================================================

@pytest.fixture
def config_com_variavel(monkeypatch):
    """
    Permite reler o config.py com a variável de ambiente em um
    valor escolhido pelo teste.

    No fim, a variável volta ao que era e o config é relido,
    para não afetar os outros testes.
    """

    def recarregar(valor):

        if valor is None:
            monkeypatch.delenv(config.VARIAVEL_DEBUG, raising=False)
        else:
            monkeypatch.setenv(config.VARIAVEL_DEBUG, valor)

        return importlib.reload(config)

    yield recarregar

    monkeypatch.undo()

    importlib.reload(config)


# ================================================================
# MODO DE DEPURAÇÃO
# ================================================================

def test_debug_desligado_quando_a_variavel_nao_existe(config_com_variavel):
    """
    Este é o padrão que protege a produção: no servidor ninguém
    precisa fazer nada, basta não definir a variável.
    """

    recarregado = config_com_variavel(None)

    assert recarregado.SERVIDOR_DEBUG is False


@pytest.mark.parametrize("valor", ["1", "true", "TRUE", "sim", "on", " 1 "])
def test_variavel_liga_o_debug(valor, config_com_variavel):
    recarregado = config_com_variavel(valor)

    assert recarregado.SERVIDOR_DEBUG is True


@pytest.mark.parametrize(
    "valor",
    ["0", "false", "nao", "", "   ", "talvez", "2"]
)
def test_valores_que_nao_ligam_o_debug(valor, config_com_variavel):
    """
    Qualquer coisa fora da lista de valores aceitos deixa o
    debug desligado. Errar o valor não pode ligar por acidente.
    """

    recarregado = config_com_variavel(valor)

    assert recarregado.SERVIDOR_DEBUG is False


def test_debug_e_booleano(config_com_variavel):
    """
    O Flask recebe esse valor direto. Um texto como "0" seria
    verdadeiro para ele, porque texto não vazio é verdadeiro.
    """

    recarregado = config_com_variavel("0")

    assert isinstance(recarregado.SERVIDOR_DEBUG, bool)


# ================================================================
# IMPORTAR O APP NÃO SOBE SERVIDOR
# ================================================================

def test_app_run_so_e_chamado_na_execucao_direta():
    """
    Na nuvem o Flask é carregado por importação (WSGI), não por
    "python app.py". Se o app.run() estivesse solto no arquivo,
    o site ficaria pendurado tentando abrir uma porta.
    """

    codigo = io.open(
        config.PASTA_PROJETO / "app.py",
        encoding="utf-8"
    ).read()

    guarda = codigo.find('if __name__ == "__main__":')

    assert guarda != -1, "o app.py não tem a guarda de execução direta"

    for ocorrencia in re.finditer(r"app\.run\(", codigo):
        assert ocorrencia.start() > guarda, (
            "existe um app.run() fora do if __name__ == \"__main__\""
        )


def test_app_e_um_objeto_flask_importavel():
    """O servidor da nuvem importa justamente este objeto."""

    assert app.name == "app"
    assert callable(app.wsgi_app)


# ================================================================
# AVISO DE SISTEMA DESATUALIZADO
# ================================================================

def test_tolerancia_maior_que_o_intervalo_de_coleta():
    """
    Se a tolerância ficar menor que o intervalo entre coletas, o
    dashboard acusa "sistema desatualizado" sozinho, no meio do
    caminho de uma coleta para a outra.

    Ao agendar a coleta no servidor, este teste é o lembrete de
    acertar a tolerância junto.
    """

    tolerancia_em_segundos = config.MINUTOS_TOLERANCIA_DASHBOARD * 60

    assert tolerancia_em_segundos > config.INTERVALO_COLETA


def test_dashboard_envia_a_tolerancia_para_o_javascript(conexao):
    app.config["TESTING"] = True

    pagina = app.test_client().get("/").get_data(as_text=True)

    esperado = (
        f'"minutos_tolerancia": '
        f'{config.MINUTOS_TOLERANCIA_DASHBOARD}'
    )

    assert esperado in pagina


def test_javascript_nao_tem_o_limite_escrito_na_mao():
    """
    O limite ficava escrito como "<= 15" dentro do dashboard.js.
    Agora vem do config.py, e não deve voltar para o código.
    """

    codigo = io.open(
        config.PASTA_PROJETO / "static" / "js" / "dashboard.js",
        encoding="utf-8"
    ).read()

    assert "configuracao.minutos_tolerancia" in codigo

    assert not re.search(r"diferencaMinutos\s*<=\s*\d", codigo)
