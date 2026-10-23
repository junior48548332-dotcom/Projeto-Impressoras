"""
Testes das rotas do servidor web.

Diferente dos outros testes, que verificam funções isoladas,
estes passam pelo sistema inteiro: rota, banco de dados e
template. É o teste mais próximo do que o usuário vê.

O Flask oferece um "cliente de teste" que faz as requisições
sem precisar subir o servidor de verdade.
"""

import re

import pytest

import banco

from app import app


# ================================================================
# PREPARAÇÃO
# ================================================================

@pytest.fixture
def cliente(conexao):
    """Cliente de teste do Flask, ligado ao banco temporário."""

    app.config["TESTING"] = True

    return app.test_client()


@pytest.fixture
def sistema_com_dados(cliente, conexao, cadastro_exemplo, gravar_medicao):
    """Cadastro importado e uma medição de cada impressora."""

    banco.substituir_impressoras(conexao, cadastro_exemplo)

    gravar_medicao(
        "2026-10-01 08:00:00",
        ip="192.168.0.2",
        status_rede="online",
        status_geral="normal"
    )

    gravar_medicao(
        "2026-10-01 08:00:05",
        ip="192.168.0.3",
        status_rede="offline",
        status_geral="atencao"
    )

    gravar_medicao(
        "2026-10-01 08:00:10",
        ip="192.168.0.4",
        status_rede="online",
        status_geral="critico"
    )

    return cliente


def numero_do_contador(html, identificador):
    """Lê o valor de um contador dentro do HTML."""

    busca = re.search(
        r'id="' + identificador + r'"[^>]*>\s*([\d.,]+)',
        html
    )

    return busca.group(1) if busca else None


# ================================================================
# PÁGINA DO DASHBOARD
# ================================================================

def test_pagina_abre(sistema_com_dados):
    resposta = sistema_com_dados.get("/")

    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["Content-Type"]


def test_pagina_tem_o_titulo_do_sistema(sistema_com_dados):
    html = sistema_com_dados.get("/").get_data(as_text=True)

    assert "<title>Monitoramento de Impressoras</title>" in html


def test_pagina_mostra_um_card_por_impressora(sistema_com_dados):
    html = sistema_com_dados.get("/").get_data(as_text=True)

    assert html.count('class="impressora ') == 3


def test_pagina_mostra_o_nome_dos_setores(sistema_com_dados):
    html = sistema_com_dados.get("/").get_data(as_text=True)

    for local in ("Diretoria", "Almoxarifado", "Fiscal"):
        assert local in html


def test_contadores_da_pagina_batem_com_os_dados(sistema_com_dados):
    html = sistema_com_dados.get("/").get_data(as_text=True)

    assert numero_do_contador(html, "contadorTotal") == "3"
    assert numero_do_contador(html, "contadorOnline") == "2"
    assert numero_do_contador(html, "contadorOffline") == "1"
    assert numero_do_contador(html, "contadorAtencao") == "1"
    assert numero_do_contador(html, "contadorCritico") == "1"


def test_pagina_mostra_a_data_da_ultima_medicao(sistema_com_dados):
    html = sistema_com_dados.get("/").get_data(as_text=True)

    assert "2026-10-01 08:00:10" in html


def test_pagina_informa_os_enderecos_da_api(sistema_com_dados):
    """O JavaScript lê estes endereços para buscar os dados."""

    html = sistema_com_dados.get("/").get_data(as_text=True)

    assert '"api_impressoras": "/api/impressoras"' in html
    assert '"api_analise": "/api/analise"' in html


def test_pagina_nao_embute_mais_os_dados(sistema_com_dados):
    """Os dados vêm da API, não dentro do HTML."""

    html = sistema_com_dados.get("/").get_data(as_text=True)

    assert "dados-impressoras" not in html


def test_pagina_abre_sem_nenhum_cadastro(cliente):
    """Antes da primeira importação a tela ainda precisa abrir."""

    resposta = cliente.get("/")

    assert resposta.status_code == 200
    assert numero_do_contador(resposta.get_data(as_text=True), "contadorTotal") == "0"


def test_pagina_abre_com_banco_sem_tabelas(banco_vazio):
    """Nem o banco existe ainda; a página não pode quebrar."""

    resposta = app.test_client().get("/")

    assert resposta.status_code == 200


# ================================================================
# ARQUIVOS DE CSS E JAVASCRIPT
# ================================================================

@pytest.mark.parametrize("caminho,tipo", [
    ("/static/css/dashboard.css", "text/css"),
    ("/static/js/dashboard.js", "javascript"),
])
def test_arquivos_da_pagina_sao_entregues(cliente, caminho, tipo):
    resposta = cliente.get(caminho)

    assert resposta.status_code == 200
    assert tipo in resposta.headers["Content-Type"]
    assert len(resposta.get_data()) > 0


# ================================================================
# ROTA /api/impressoras
# ================================================================

def test_api_impressoras_responde_json(sistema_com_dados):
    resposta = sistema_com_dados.get("/api/impressoras")

    assert resposta.status_code == 200
    assert "application/json" in resposta.headers["Content-Type"]


def test_api_impressoras_tem_as_tres_partes(sistema_com_dados):
    dados = sistema_com_dados.get("/api/impressoras").get_json()

    assert set(dados) == {"atualizado_em", "resumo", "impressoras"}


def test_api_impressoras_traz_todo_o_cadastro(sistema_com_dados):
    dados = sistema_com_dados.get("/api/impressoras").get_json()

    locais = [i["local"] for i in dados["impressoras"]]

    assert locais == ["Diretoria", "Almoxarifado", "Fiscal"]


def test_api_impressoras_traz_os_campos_esperados(sistema_com_dados):
    dados = sistema_com_dados.get("/api/impressoras").get_json()

    primeira = dados["impressoras"][0]

    for campo in (
        "local", "modelo", "tipo", "paper", "serie", "ip",
        "status_rede", "status_geral", "suprimentos",
        "status_suprimentos", "data_hora"
    ):
        assert campo in primeira


def test_api_impressoras_resumo_confere(sistema_com_dados):
    dados = sistema_com_dados.get("/api/impressoras").get_json()

    assert dados["resumo"] == {
        "total": 3,
        "online": 2,
        "offline": 1,
        "atencao": 1,
        "criticas": 1
    }


def test_api_impressoras_informa_a_ultima_medicao(sistema_com_dados):
    dados = sistema_com_dados.get("/api/impressoras").get_json()

    assert dados["atualizado_em"] == "2026-10-01 08:00:10"


def test_api_e_pagina_mostram_os_mesmos_numeros(sistema_com_dados):
    """A tela e a API não podem divergir."""

    html = sistema_com_dados.get("/").get_data(as_text=True)
    resumo = sistema_com_dados.get("/api/impressoras").get_json()["resumo"]

    assert numero_do_contador(html, "contadorTotal") == str(resumo["total"])
    assert numero_do_contador(html, "contadorOnline") == str(resumo["online"])
    assert numero_do_contador(html, "contadorCritico") == str(resumo["criticas"])


def test_soma_dos_status_fecha_com_o_total(sistema_com_dados):
    """
    Nenhuma impressora pode ficar de fora nem ser contada duas vezes.

    Verificação que antes era feita à mão pelo teste_contagem.py.
    """

    dados = sistema_com_dados.get("/api/impressoras").get_json()

    resumo = dados["resumo"]

    assert resumo["online"] + resumo["offline"] == resumo["total"]

    normais = sum(
        1
        for impressora in dados["impressoras"]
        if impressora["status_geral"] == "normal"
    )

    assert (
        normais + resumo["atencao"] + resumo["criticas"]
        == resumo["total"]
    )

    assert len(dados["impressoras"]) == resumo["total"]


def test_impressora_sem_medicao_aparece_como_desconhecida(cliente, conexao, cadastro_exemplo):
    """Cadastrada mas ainda não medida: precisa aparecer na lista."""

    banco.substituir_impressoras(conexao, cadastro_exemplo)

    dados = cliente.get("/api/impressoras").get_json()

    assert len(dados["impressoras"]) == 3
    assert dados["atualizado_em"] is None

    for impressora in dados["impressoras"]:
        assert impressora["status_rede"] == "desconhecido"
        assert impressora["suprimentos"] == {}


def test_api_impressoras_sem_cadastro(cliente):
    dados = cliente.get("/api/impressoras").get_json()

    assert dados["impressoras"] == []
    assert dados["resumo"]["total"] == 0


# ================================================================
# ROTA /api/analise
# ================================================================

def test_api_analise_responde_json(cliente):
    resposta = cliente.get("/api/analise")

    assert resposta.status_code == 200
    assert "application/json" in resposta.headers["Content-Type"]


def test_api_analise_tem_todos_os_campos(cliente):
    dados = cliente.get("/api/analise").get_json()

    for campo in (
        "total_registros", "consumo_medio",
        "total_criticas", "total_atencoes", "total_normais",
        "total_online", "total_offline",
        "setores", "top_impressoras", "evolucao"
    ):
        assert campo in dados


def test_api_analise_zerada_sem_consolidacao(cliente):
    dados = cliente.get("/api/analise").get_json()

    assert dados["total_registros"] == 0
    assert dados["consumo_medio"] == 0
    assert dados["setores"] == []
    assert dados["evolucao"] == []


def test_api_analise_com_dados_consolidados(cliente, conexao, consolidacao_exemplo):
    banco.salvar_consolidacao(conexao, consolidacao_exemplo)

    outra = dict(consolidacao_exemplo)
    outra.update({"ip": "192.168.0.3", "local": "Fiscal", "consumo_medio": 6.5})

    banco.salvar_consolidacao(conexao, outra)

    dados = cliente.get("/api/analise").get_json()

    assert dados["total_registros"] == 2
    assert dados["consumo_medio"] == pytest.approx(4.5)   # média de 2.5 e 6.5
    assert dados["setores"][0]["local"] == "Fiscal"
    assert len(dados["evolucao"]) == 1


def test_numeros_da_analise_aparecem_na_pagina(cliente, conexao, consolidacao_exemplo):
    banco.salvar_consolidacao(conexao, consolidacao_exemplo)

    html = cliente.get("/").get_data(as_text=True)

    assert numero_do_contador(html, "analiseRegistros") == "1"
    assert numero_do_contador(html, "analiseCriticas") == "2"
    assert numero_do_contador(html, "analiseAtencoes") == "3"


# ================================================================
# ENDEREÇOS INVÁLIDOS
# ================================================================

@pytest.mark.parametrize("caminho", [
    "/api",
    "/api/impressora",
    "/pagina-que-nao-existe",
])
def test_endereco_inexistente_devolve_404(cliente, caminho):
    assert cliente.get(caminho).status_code == 404


def test_api_aceita_apenas_leitura(cliente):
    """As rotas são de consulta; gravar não é permitido."""

    assert cliente.post("/api/impressoras").status_code == 405
    assert cliente.delete("/api/analise").status_code == 405
