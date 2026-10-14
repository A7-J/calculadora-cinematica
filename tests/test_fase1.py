import pytest
from cinematica.conversor import ConversorSI, ConversorUnidades
from cinematica.erros import UnidadeInvalidaErro, ValorInvalidoErro

c = ConversorSI()


def test_e_uma_interface():
    assert isinstance(c, ConversorUnidades)


def test_kmh_para_ms():
    assert c.para_si(36, "km/h") == 10.0


def test_ms_para_s():
    assert c.para_si(500, "ms") == 0.5


def test_min_cm_km():
    assert c.para_si(2, "min") == 120.0
    assert c.para_si(250, "cm") == 2.5
    assert c.para_si(1.5, "km") == 1500.0


def test_graus_para_rad():
    assert c.para_si(90, "°") == pytest.approx(1.5707963267948966)


def test_unidades_por_grandeza():
    assert c.unidades_de("tempo") == ["s", "ms", "min", "h"]
    assert c.grandeza_de("km/h") == "velocidade"


def test_erros():
    with pytest.raises(UnidadeInvalidaErro):
        c.para_si(1, "kg")
    with pytest.raises(ValorInvalidoErro):
        c.para_si(float("nan"), "m")
    with pytest.raises(ValorInvalidoErro):
        c.para_si("abc", "m")
