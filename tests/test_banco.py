"""
Testes do banco.py, o arquivo que concentra o acesso ao SQLite.

Todos usam um banco temporário criado pelo pytest (ver
conftest.py). O banco do projeto não é alterado.
"""

import json

import pytest

import banco


# ================================================================
# CRIAÇÃO DAS TABELAS
# ================================================================

def test_criar_tabelas_cria_as_tres_tabelas(conexao):
    for tabela in ("impressoras", "historico_impressoras", "consolidacao_diaria"):
        assert banco.tabela_existe(conexao, tabela)


def test_criar_tabelas_pode_rodar_varias_vezes(conexao, impressora_exemplo):
    """Rodar de novo não pode apagar o que já está gravado."""

    banco.salvar_medicao(conexao, impressora_exemplo)

    banco.criar_tabelas(conexao)
    banco.criar_tabelas(conexao)

    assert banco.contar_registros(conexao, "historico_impressoras") == 1


def test_tabela_inexistente(conexao):
    assert banco.tabela_existe(conexao, "tabela_que_nao_existe") is False


def test_banco_e_criado_no_caminho_configurado(banco_vazio):
    assert not banco_vazio.exists()

    conexao = banco.conectar()
    banco.criar_tabelas(conexao)
    conexao.close()

    assert banco_vazio.exists()


# ================================================================
# PROTEÇÃO CONTRA NOME DE TABELA INVÁLIDO
# ================================================================

@pytest.mark.parametrize("nome", [
    "usuarios",
    "historico_impressoras; DROP TABLE impressoras",
    "",
])
def test_nome_de_tabela_desconhecido_e_recusado(conexao, nome):
    """
    O nome da tabela entra direto no texto do SQL, então só os
    nomes conhecidos são aceitos (proteção contra SQL injection).
    """

    with pytest.raises(ValueError):
        banco.contar_registros(conexao, nome)

    with pytest.raises(ValueError):
        banco.estrutura_tabela(conexao, nome)


def test_tentativa_de_injecao_nao_apaga_tabela(conexao, cadastro_exemplo):
    banco.substituir_impressoras(conexao, cadastro_exemplo)

    with pytest.raises(ValueError):
        banco.contar_registros(
            conexao,
            "impressoras; DROP TABLE impressoras"
        )

    assert banco.tabela_existe(conexao, "impressoras")
    assert banco.contar_registros(conexao, "impressoras") == 3


# ================================================================
# ESTRUTURA E CONTAGEM
# ================================================================

def test_estrutura_da_tabela_traz_as_colunas(conexao):
    colunas = [
        coluna[1]
        for coluna in banco.estrutura_tabela(conexao, "consolidacao_diaria")
    ]

    assert "data" in colunas
    assert "consumo_medio" in colunas
    assert "total_medicoes" in colunas


def test_contagem_comeca_em_zero(conexao):
    assert banco.contar_registros(conexao, "historico_impressoras") == 0
    assert banco.contar_registros(conexao, "impressoras") == 0


# ================================================================
# CADASTRO DAS IMPRESSORAS
# ================================================================

def test_gravar_e_ler_o_cadastro(conexao, cadastro_exemplo):
    banco.substituir_impressoras(conexao, cadastro_exemplo)

    cadastro = banco.buscar_impressoras(conexao)

    assert cadastro == cadastro_exemplo


def test_cadastro_mantem_a_ordem_da_planilha(conexao, cadastro_exemplo):
    banco.substituir_impressoras(conexao, cadastro_exemplo)

    locais = [
        impressora["local"]
        for impressora in banco.buscar_impressoras(conexao)
    ]

    assert locais == ["Diretoria", "Almoxarifado", "Fiscal"]


def test_importar_de_novo_substitui_em_vez_de_duplicar(conexao, cadastro_exemplo):
    banco.substituir_impressoras(conexao, cadastro_exemplo)
    banco.substituir_impressoras(conexao, cadastro_exemplo)

    assert banco.contar_registros(conexao, "impressoras") == 3


def test_impressora_removida_da_planilha_sai_do_cadastro(conexao, cadastro_exemplo):
    banco.substituir_impressoras(conexao, cadastro_exemplo)

    banco.substituir_impressoras(conexao, cadastro_exemplo[:1])

    cadastro = banco.buscar_impressoras(conexao)

    assert len(cadastro) == 1
    assert cadastro[0]["local"] == "Diretoria"


def test_ip_repetido_e_recusado_pelo_banco(conexao, cadastro_exemplo):
    repetido = cadastro_exemplo + [cadastro_exemplo[0]]

    with pytest.raises(Exception):
        banco.substituir_impressoras(conexao, repetido)


def test_erro_na_gravacao_preserva_o_cadastro_anterior(conexao, cadastro_exemplo):
    """Se a nova lista falhar no meio, o cadastro antigo continua."""

    banco.substituir_impressoras(conexao, cadastro_exemplo)

    repetido = [cadastro_exemplo[1], cadastro_exemplo[1]]

    with pytest.raises(Exception):
        banco.substituir_impressoras(conexao, repetido)

    assert banco.contar_registros(conexao, "impressoras") == 3


def test_cadastro_vazio_quando_a_tabela_nao_existe(banco_vazio):
    """O dashboard precisa abrir mesmo antes da primeira importação."""

    conexao = banco.conectar()

    assert banco.buscar_impressoras(conexao) == []

    conexao.close()


# ================================================================
# HISTÓRICO DE MEDIÇÕES
# ================================================================

def test_salvar_medicao_grava_todos_os_campos(conexao, impressora_exemplo):
    banco.salvar_medicao(conexao, impressora_exemplo)

    registro = banco.buscar_ultima_medicao_completa(conexao)

    local, ip, suprimentos, status_suprimentos = registro

    assert local == "Diretoria"
    assert ip == "192.168.0.2"
    assert json.loads(suprimentos) == impressora_exemplo["suprimentos"]
    assert json.loads(status_suprimentos) == impressora_exemplo["status_suprimentos"]


def test_data_da_medicao_fica_no_formato_do_banco(conexao, gravar_medicao):
    gravar_medicao("2026-10-01 08:30:00")

    assert banco.buscar_data_ultima_medicao(conexao) == "2026-10-01 08:30:00"


def test_ultima_medicao_de_cada_impressora(conexao, gravar_medicao):
    """A consulta deve trazer uma linha por IP, sempre a mais recente."""

    gravar_medicao("2026-10-01 08:00:00", ip="192.168.0.2", status_geral="normal")
    gravar_medicao("2026-10-01 09:00:00", ip="192.168.0.2", status_geral="critico")
    gravar_medicao("2026-10-01 09:00:00", ip="192.168.0.3", status_geral="atencao")

    registros = banco.buscar_ultimas_medicoes(conexao)

    assert len(registros) == 2

    por_ip = {registro[5]: registro for registro in registros}

    # posição 7 = status_geral
    assert por_ip["192.168.0.2"][7] == "critico"
    assert por_ip["192.168.0.3"][7] == "atencao"


def test_contagem_de_impressoras_com_medicao(conexao, gravar_medicao):
    gravar_medicao("2026-10-01 08:00:00", ip="192.168.0.2")
    gravar_medicao("2026-10-01 08:05:00", ip="192.168.0.2")
    gravar_medicao("2026-10-01 08:10:00", ip="192.168.0.3")

    assert banco.contar_registros(conexao, "historico_impressoras") == 3
    assert banco.contar_impressoras_registradas(conexao) == 2


def test_medicoes_recentes_vem_da_mais_nova_para_a_mais_antiga(conexao, gravar_medicao):
    gravar_medicao("2026-10-01 08:00:00", local="Primeira")
    gravar_medicao("2026-10-01 09:00:00", local="Segunda")
    gravar_medicao("2026-10-01 10:00:00", local="Terceira")

    recentes = banco.buscar_medicoes_recentes(conexao, limite=2)

    assert [registro[1] for registro in recentes] == ["Terceira", "Segunda"]


def test_dias_presentes_no_historico(conexao, gravar_medicao):
    gravar_medicao("2026-10-01 08:00:00")
    gravar_medicao("2026-10-01 20:00:00")
    gravar_medicao("2026-10-02 08:00:00")

    assert banco.buscar_dias_historico(conexao) == ["2026-10-01", "2026-10-02"]


def test_impressoras_medidas_em_um_dia(conexao, gravar_medicao):
    gravar_medicao("2026-10-01 08:00:00", ip="192.168.0.2", local="Diretoria")
    gravar_medicao("2026-10-02 08:00:00", ip="192.168.0.3", local="Fiscal")

    do_dia = banco.buscar_impressoras_do_dia(conexao, "2026-10-01")

    assert len(do_dia) == 1
    assert do_dia[0][0] == "Diretoria"


def test_medicoes_de_um_dia_vem_em_ordem_crescente(conexao, gravar_medicao):
    gravar_medicao("2026-10-01 10:00:00", suprimentos={"toner_preto": 50})
    gravar_medicao("2026-10-01 08:00:00", suprimentos={"toner_preto": 60})
    gravar_medicao("2026-10-02 08:00:00", suprimentos={"toner_preto": 40})

    medicoes = banco.buscar_medicoes_do_dia(conexao, "2026-10-01", "192.168.0.2")

    # a ordem importa: o consumo é calculado comparando uma medição com a seguinte
    assert [m[1] for m in medicoes] == [
        "2026-10-01 08:00:00",
        "2026-10-01 10:00:00"
    ]


# ================================================================
# CONSOLIDAÇÃO DIÁRIA
# ================================================================

def test_salvar_consolidacao_cria_o_registro(conexao, consolidacao_exemplo):
    banco.salvar_consolidacao(conexao, consolidacao_exemplo)

    registros = banco.buscar_consolidacoes(conexao)

    assert len(registros) == 1
    assert registros[0][0] == "2026-10-01"
    assert registros[0][4] == 10


def test_consolidar_o_mesmo_dia_atualiza_em_vez_de_duplicar(conexao, consolidacao_exemplo):
    banco.salvar_consolidacao(conexao, consolidacao_exemplo)

    atualizado = dict(consolidacao_exemplo)
    atualizado["total_medicoes"] = 20
    atualizado["consumo_medio"] = 4.0

    banco.salvar_consolidacao(conexao, atualizado)

    registros = banco.buscar_consolidacoes(conexao)

    assert len(registros) == 1
    assert registros[0][4] == 20
    assert registros[0][10] == 4.0


def test_dias_diferentes_geram_registros_diferentes(conexao, consolidacao_exemplo):
    banco.salvar_consolidacao(conexao, consolidacao_exemplo)

    outro_dia = dict(consolidacao_exemplo)
    outro_dia["data"] = "2026-10-02"

    banco.salvar_consolidacao(conexao, outro_dia)

    assert banco.contar_registros(conexao, "consolidacao_diaria") == 2


def test_impressoras_diferentes_no_mesmo_dia(conexao, consolidacao_exemplo):
    banco.salvar_consolidacao(conexao, consolidacao_exemplo)

    outra = dict(consolidacao_exemplo)
    outra["ip"] = "192.168.0.3"
    outra["local"] = "Fiscal"

    banco.salvar_consolidacao(conexao, outra)

    assert banco.contar_registros(conexao, "consolidacao_diaria") == 2


# ================================================================
# CONSULTAS DA ABA ANÁLISE
# ================================================================

@pytest.fixture
def consolidacoes(conexao, consolidacao_exemplo):
    """Dois dias de consolidação para duas impressoras."""

    registros = [
        {"data": "2026-10-01", "local": "Diretoria", "ip": "192.168.0.2",
         "consumo_medio": 2.0, "online": 9, "offline": 1,
         "criticas": 2, "atencoes": 3, "normais": 5},

        {"data": "2026-10-01", "local": "Fiscal", "ip": "192.168.0.3",
         "consumo_medio": 6.0, "online": 10, "offline": 0,
         "criticas": 0, "atencoes": 1, "normais": 9},

        {"data": "2026-10-02", "local": "Diretoria", "ip": "192.168.0.2",
         "consumo_medio": 4.0, "online": 8, "offline": 2,
         "criticas": 1, "atencoes": 1, "normais": 8},
    ]

    for registro in registros:
        dados = dict(consolidacao_exemplo)
        dados.update(registro)
        banco.salvar_consolidacao(conexao, dados)

    return conexao


def test_indicadores_somam_o_periodo_inteiro(consolidacoes):
    consumo, criticas, atencoes, normais, online, offline = (
        banco.buscar_indicadores_gerais(consolidacoes)
    )

    assert consumo == pytest.approx(4.0)   # média de 2, 6 e 4
    assert criticas == 3
    assert atencoes == 5
    assert normais == 22
    assert online == 27
    assert offline == 3


def test_consumo_por_setor_do_maior_para_o_menor(consolidacoes):
    setores = banco.buscar_consumo_por_setor(consolidacoes)

    assert setores[0][0] == "Fiscal"
    assert setores[0][1] == pytest.approx(6.0)

    # Diretoria aparece em dois dias: média de 2 e 4
    assert setores[1][0] == "Diretoria"
    assert setores[1][1] == pytest.approx(3.0)


def test_top_impressoras_respeita_o_limite(consolidacoes):
    assert len(banco.buscar_top_impressoras(consolidacoes, limite=2)) == 2

    topo = banco.buscar_top_impressoras(consolidacoes)

    assert topo[0][0] == "Fiscal"


def test_evolucao_traz_um_ponto_por_dia(consolidacoes):
    evolucao = banco.buscar_evolucao_consumo(consolidacoes)

    assert [linha[0] for linha in evolucao] == ["2026-10-01", "2026-10-02"]

    # dia 01: média de 2 e 6
    assert evolucao[0][1] == pytest.approx(4.0)
    assert evolucao[1][1] == pytest.approx(4.0)


def test_consultas_em_banco_vazio_nao_quebram(conexao):
    assert banco.buscar_ultimas_medicoes(conexao) == []
    assert banco.buscar_dias_historico(conexao) == []
    assert banco.buscar_consolidacoes(conexao) == []
    assert banco.buscar_consumo_por_setor(conexao) == []
    assert banco.buscar_data_ultima_medicao(conexao) is None
