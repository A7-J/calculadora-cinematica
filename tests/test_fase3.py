import pytest

from cinematica.calculador import CalculadorCinematica
from cinematica.conversor import ConversorUnidades
from cinematica.erros import DadosInconsistentesErro, DadosInsuficientesErro
from cinematica.mru import CalculadoraMRU


def _mru(**campos):
    """_mru(x0=(10, 'm'), v=(36, 'km/h')) -> calculadora já preenchida."""
    c = CalculadoraMRU()
    for nome, (valor, unidade) in campos.items():
        c.definir(nome, valor, unidade)
    return c


def test_herda_da_base_abstrata():
    c = CalculadoraMRU()
    assert isinstance(c, CalculadorCinematica)
    assert isinstance(c, ConversorUnidades)


def test_calcula_posicao_final():
    r = _mru(x0=(10, "m"), v=(36, "km/h"), t=(5, "s")).calcular()
    assert r.variavel == "x"
    assert r.valor == 60.0


def test_formatacao_posicao():
    r = _mru(x0=(10, "m"), v=(36, "km/h"), t=(5, "s")).calcular()
    assert r.formatar() == (
        "x = 60,0 m · x = x₀ + v·t, com x₀ = 10,0 m, v = 10,0 m/s, t = 5,0 s"
    )


def test_calcula_velocidade_com_conversao():
    r = _mru(x=(1, "km"), x0=(0, "m"), t=(1, "min")).calcular()
    assert r.variavel == "v"
    assert r.valor == pytest.approx(1000 / 60)


def test_calcula_tempo():
    r = _mru(x=(100, "m"), x0=(0, "m"), v=(36, "km/h")).calcular()
    assert r.variavel == "t"
    assert r.valor == pytest.approx(10.0)


def test_calcula_posicao_inicial():
    r = _mru(x=(100, "m"), v=(10, "m/s"), t=(5, "s")).calcular()
    assert r.variavel == "x₀"
    assert r.valor == pytest.approx(50.0)


def test_dois_campos_sao_insuficientes():
    with pytest.raises(DadosInsuficientesErro) as exc:
        _mru(v=(10, "m/s"), t=(5, "s")).calcular()
    assert exc.value.faltantes == ["x₀", "x"]


def test_todos_preenchidos_e_inconsistente():
    with pytest.raises(DadosInconsistentesErro):
        _mru(x0=(0, "m"), x=(50, "m"), v=(10, "m/s"), t=(5, "s")).calcular()


def test_velocidade_com_tempo_zero():
    with pytest.raises(DadosInconsistentesErro):
        _mru(x=(100, "m"), x0=(0, "m"), t=(0, "s")).calcular()


def test_tempo_com_velocidade_zero():
    with pytest.raises(DadosInconsistentesErro):
        _mru(x=(10, "m"), x0=(0, "m"), v=(0, "m/s")).calcular()


def test_tempo_calculado_negativo():
    with pytest.raises(DadosInconsistentesErro):
        _mru(x=(-10, "m"), x0=(0, "m"), v=(5, "m/s")).calcular()


def test_tempo_informado_negativo():
    with pytest.raises(DadosInconsistentesErro):
        _mru(x0=(0, "m"), v=(5, "m/s"), t=(-1, "s")).calcular()
