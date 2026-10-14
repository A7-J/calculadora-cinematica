import math

import pytest

from cinematica.calculador import CalculadorCinematica
from cinematica.erros import (
    DadosInconsistentesErro,
    DadosInsuficientesErro,
    ErroCinematica,
)
from cinematica.projetil import Projetil2D


def _proj(**campos):
    p = Projetil2D()
    for nome, (valor, unidade) in campos.items():
        p.definir(nome, valor, unidade)
    return p


def _lancamento_30():
    return _proj(v0=(20, "m/s"), theta=(30, "°"))


def test_herda_da_base_abstrata():
    assert isinstance(Projetil2D(), CalculadorCinematica)


def test_padroes_pre_preenchidos():
    assert Projetil2D().valores == {"g": 9.8, "x0": 0.0, "y0": 0.0}


def test_limpar_restaura_padroes():
    p = _proj(v0=(20, "m/s"), g=(10, "m/s²"))
    p.limpar()
    assert p.valores == {"g": 9.8, "x0": 0.0, "y0": 0.0}


def test_alcance_automatico_e_formatacao():
    r = _lancamento_30().calcular()
    assert r.variavel == "R"
    assert r.valor == pytest.approx(400 * math.sin(math.radians(60)) / 9.8)
    assert r.formatar().startswith("R = 35,348 m · R = v₀·cos θ · t_voo, com v₀ = 20,0 m/s, θ = 30,0 °")


def test_alcance_classico_45_graus():
    r = _proj(v0=(10, "m/s"), theta=(45, "°"), g=(10, "m/s²")).calcular("alcance")
    assert r.valor == pytest.approx(10.0)


def test_altura_maxima_tempo_de_subida_e_de_voo():
    p = _lancamento_30()
    assert p.calcular("hmax").valor == pytest.approx(100 / 19.6)
    assert p.calcular("ts").valor == pytest.approx(10 / 9.8)
    assert p.calcular("tv").valor == pytest.approx(20 / 9.8)


def test_componentes_dos_eixos():
    p = _lancamento_30()
    assert p.calcular("vx").valor == pytest.approx(20 * math.cos(math.radians(30)))
    assert p.calcular("voy").valor == pytest.approx(10.0)


def test_lancamento_horizontal_de_uma_altura():
    p = _proj(v0=(10, "m/s"), theta=(0, "°"), g=(10, "m/s²"), y0=(20, "m"))
    assert p.calcular("tv").valor == pytest.approx(2.0)
    assert p.calcular("alcance").valor == pytest.approx(20.0)


def test_lancamento_para_baixo_nao_sobe():
    p = _proj(v0=(10, "m/s"), theta=(-30, "°"), y0=(5, "m"))
    assert p.calcular("hmax").valor == pytest.approx(5.0)
    assert p.calcular("ts").valor == 0.0


def test_posicao_e_velocidade_no_instante_t():
    p = _proj(v0=(20, "m/s"), theta=(30, "°"), t=(1, "s"))
    assert p.calcular("x").valor == pytest.approx(20 * math.cos(math.radians(30)))
    assert p.calcular("y").valor == pytest.approx(10 - 4.9)
    assert p.calcular("vy").valor == pytest.approx(0.2)


def test_x_com_x0():
    p = _proj(x0=(5, "m"), y0=(20, "m"), v0=(10, "m/s"), theta=(0, "°"),
              g=(10, "m/s²"), t=(1, "s"))
    assert p.calcular("x").valor == pytest.approx(15.0)


def test_t_maior_que_o_tempo_de_voo():
    p = _proj(v0=(20, "m/s"), theta=(30, "°"), t=(3, "s"))
    with pytest.raises(DadosInconsistentesErro):
        p.calcular("y")
    assert p.calcular("alcance").valor > 0      # alcance não depende de t


def test_alvos_possiveis_sem_e_com_t():
    p = _lancamento_30()
    assert p.alvos_possiveis() == ["vx", "voy", "ts", "tv", "hmax", "alcance"]
    p.definir("t", 1, "s")
    assert p.alvos_possiveis() == ["x", "y", "vx", "voy", "vy", "ts", "tv", "hmax", "alcance"]


def test_calcular_todos_isola_erros():
    p = _proj(v0=(20, "m/s"), theta=(30, "°"), t=(3, "s"))
    tudo = p.calcular_todos()
    assert isinstance(tudo["alcance"].valor, float)
    assert isinstance(tudo["x"], ErroCinematica)
    assert isinstance(tudo["y"], ErroCinematica)


def test_insuficiente_sem_v0_e_theta():
    with pytest.raises(DadosInsuficientesErro) as exc:
        Projetil2D().calcular()
    assert exc.value.faltantes == ["v₀", "θ"]


def test_insuficiente_so_com_v0():
    with pytest.raises(DadosInsuficientesErro) as exc:
        _proj(v0=(10, "m/s")).calcular()
    assert exc.value.faltantes == ["θ"]


def test_calcular_todos_sem_dados():
    with pytest.raises(DadosInsuficientesErro):
        Projetil2D().calcular_todos()


@pytest.mark.parametrize("campos", [
    {"v0": (-1, "m/s"), "theta": (30, "°")},
    {"v0": (10, "m/s"), "theta": (100, "°")},
    {"v0": (10, "m/s"), "theta": (30, "°"), "g": (0, "m/s²")},
    {"v0": (10, "m/s"), "theta": (30, "°"), "y0": (-1, "m")},
])
def test_entradas_fisicamente_invalidas(campos):
    with pytest.raises(DadosInconsistentesErro):
        _proj(**campos).calcular()


def test_noventa_graus_e_aceito():
    r = _proj(v0=(10, "m/s"), theta=(90, "°")).calcular("hmax")
    assert r.valor == pytest.approx(100 / 19.6)
