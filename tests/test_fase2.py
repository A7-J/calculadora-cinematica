import pytest

from cinematica.calculador import CalculadorCinematica, Campo, Resultado
from cinematica.erros import (
    CampoDesconhecidoErro,
    DadosInconsistentesErro,
    DadosInsuficientesErro,
    UnidadeIncompativelErro,
    UnidadeInvalidaErro,
)


class _Deslocamento(CalculadorCinematica):
    CAMPOS = {
        "v": Campo("velocidade", "v"),
        "t": Campo("tempo", "t"),
        "x": Campo("comprimento", "x"),
    }

    def _resolver(self) -> Resultado:
        self._exigir("v", "t")
        v, t = self.valores["v"], self.valores["t"]
        if t < 0:
            raise DadosInconsistentesErro("O tempo não pode ser negativo.")
        return Resultado("x", v * t, "m", "x = v·t", self._entradas("v", "t"))


def test_classe_base_e_abstrata():
    with pytest.raises(TypeError):
        CalculadorCinematica()


def test_definir_converte_para_si():
    c = _Deslocamento()
    c.definir("v", 36, "km/h")
    c.definir("t", 500, "ms")
    assert c.valores == {"v": 10.0, "t": 0.5}


def test_calcular_e_formatar():
    c = _Deslocamento()
    c.definir("v", 36, "km/h")
    c.definir("t", 5, "s")
    r = c.calcular()
    assert r.valor == 50.0
    assert r.formatar() == "x = 50,0 m · x = v·t, com v = 10,0 m/s, t = 5,0 s"


def test_dados_insuficientes_aponta_o_campo():
    c = _Deslocamento()
    c.definir("v", 10, "m/s")
    with pytest.raises(DadosInsuficientesErro) as exc:
        c.calcular()
    assert exc.value.faltantes == ["t"]


def test_nada_preenchido():
    with pytest.raises(DadosInsuficientesErro):
        _Deslocamento().calcular()


def test_unidade_incompativel_nao_altera_estado():
    c = _Deslocamento()
    with pytest.raises(UnidadeIncompativelErro):
        c.definir("t", 5, "m")
    assert c.valores == {}


def test_unidade_incompativel_e_uma_unidade_invalida():
    with pytest.raises(UnidadeInvalidaErro):
        _Deslocamento().definir("t", 5, "m")


def test_campo_desconhecido():
    with pytest.raises(CampoDesconhecidoErro):
        _Deslocamento().definir("z", 1, "m")


def test_tempo_negativo_e_inconsistente():
    c = _Deslocamento()
    c.definir("v", 10, "m/s")
    c.definir("t", -1, "s")
    with pytest.raises(DadosInconsistentesErro):
        c.calcular()


def test_limpar():
    c = _Deslocamento()
    c.definir("v", 10, "m/s")
    c.limpar("v")
    assert c.valores == {}
