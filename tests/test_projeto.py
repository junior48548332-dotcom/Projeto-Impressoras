"""
Testes de estrutura do projeto.

Conferem se os módulos carregam e se as configurações básicas
estão no lugar. Os testes das regras do sistema ficam nos
outros arquivos desta pasta.
"""

from pathlib import Path

import config


# ================================================================
# MÓDULOS DO PROJETO
# ================================================================

def test_modulos_do_projeto_carregam():
    """Todos os módulos devem ser importáveis sem erro."""

    import app
    import banco
    import planilha
    import monitor
    import consolidador
    import importar_planilha

    from coleta import simulador

    assert callable(simulador.coletar)
    assert callable(banco.conectar)
    assert callable(planilha.ler_planilha)
    assert callable(app.carregar_impressoras)
    assert callable(monitor.classificar_nivel)
    assert callable(consolidador.consolidar_dia)
    assert callable(importar_planilha.importar)


# ================================================================
# CONFIGURAÇÃO
# ================================================================

def test_caminhos_apontam_para_a_pasta_do_projeto():
    """Os caminhos do config não podem depender de onde o programa é executado."""

    assert config.PASTA_PROJETO.is_dir()

    for caminho in (
        config.ARQUIVO_EXCEL,
        config.BANCO_DADOS,
        config.ARQUIVO_ESTADO_SIMULACAO,
    ):
        assert isinstance(caminho, Path)
        assert caminho.is_absolute()
        assert caminho.parent == config.PASTA_PROJETO


def test_planilha_de_cadastro_existe():
    assert config.ARQUIVO_EXCEL.exists()


def test_intervalos_sao_positivos():
    assert config.INTERVALO_COLETA > 0
    assert config.INTERVALO_ATUALIZACAO_DASHBOARD > 0
