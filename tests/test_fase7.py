"""Fase 7: diagramas em sincronia com o código e aceitação dos slides."""
import gerar_uml
from cinematica.calculador import CalculadorCinematica
from cinematica.conversor import ConversorSI
from cinematica.erros import DadosInsuficientesErro
from cinematica.mruv import CalculadoraMRUV
from cinematica.projetil import Projetil2D


# --- UML ------------------------------------------------------------------
def test_uml_nucleo_tem_as_relacoes_do_slide_4():
    d = gerar_uml.diagrama_nucleo()
    assert "<<interface>>" in d and "<<abstract>>" in d
    assert "ConversorUnidades <|.. CalculadorCinematica" in d
    for sub in ("CalculadoraMRU", "CalculadoraMRUV", "Projetil2D"):
        assert f"CalculadorCinematica <|-- {sub}" in d


def test_uml_de_erros_cobre_a_hierarquia():
    d = gerar_uml.diagrama_erros()
    for nome in ("ErroCinematica", "DadosInsuficientesErro", "UnidadeIncompativelErro"):
        assert f"class {nome}" in d
    assert "UnidadeInvalidaErro <|-- UnidadeIncompativelErro" in d


def test_uml_e_deterministico_e_tem_tres_diagramas():
    texto = gerar_uml.gerar()
    assert texto == gerar_uml.gerar()
    assert texto.count("```mermaid") == 3


# --- aceitação: cada afirmação dos slides vira um teste -------------------------
def test_slide_5_500_ms_viram_0_5_s():
    assert ConversorSI().para_si(500, "ms") == 0.5


def test_slide_7_exemplo_da_maquete():
    c = CalculadoraMRUV()
    c.definir("v0", 36, "km/h")
    c.definir("a", 2, "m/s²")
    c.definir("t", 5, "s")
    assert c.calcular().valor == 20.0


def test_slide_6_aponta_o_campo_faltante_em_vez_de_um_numero():
    p = Projetil2D()
    p.definir("v0", 10, "m/s")
    try:
        p.calcular()
    except DadosInsuficientesErro as erro:
        assert erro.faltantes == ["θ"]
    else:
        raise AssertionError("deveria ter recusado o cálculo")


def test_slide_4_projetil_e_calculadores_sao_especializacoes():
    for classe in (CalculadoraMRUV, Projetil2D):
        assert issubclass(classe, CalculadorCinematica)
