import pytest

from cinematica.calculador import CalculadorCinematica, _fmt
from cinematica.erros import (
    CampoDesconhecidoErro,
    DadosInconsistentesErro,
    DadosInsuficientesErro,
)
from cinematica.mruv import CalculadoraMRUV


def _mruv(**campos):
    c = CalculadoraMRUV()
    for nome, (valor, unidade) in campos.items():
        c.definir(nome, valor, unidade)
    return c


def test_herda_da_base_abstrata():
    assert isinstance(CalculadoraMRUV(), CalculadorCinematica)


def test_exemplo_do_slide_7():
    r = _mruv(v0=(36, "km/h"), a=(2, "m/s²"), t=(5, "s")).calcular()
    assert r.variavel == "v"
    assert r.valor == 20.0
    assert r.formatar() == (
        "v = 20,0 m/s · v = v₀ + a·t, com v₀ = 10,0 m/s, a = 2,0 m/s², t = 5,0 s"
    )


def test_aceleracao_por_velocidades_e_tempo():
    r = _mruv(v0=(10, "m/s"), v=(20, "m/s"), t=(5, "s")).calcular()
    assert (r.variavel, r.valor) == ("a", 2.0)


def test_tempo_por_velocidades_e_aceleracao():
    r = _mruv(v0=(10, "m/s"), v=(20, "m/s"), a=(2, "m/s²")).calcular()
    assert (r.variavel, r.valor) == ("t", 5.0)


def test_velocidade_inicial_por_v_a_t():
    r = _mruv(v=(20, "m/s"), a=(2, "m/s²"), t=(5, "s")).calcular()
    assert (r.variavel, r.valor) == ("v₀", 10.0)


def test_posicao_final():
    r = _mruv(x0=(0, "m"), v0=(10, "m/s"), a=(2, "m/s²"), t=(5, "s")).calcular("x")
    assert r.valor == 75.0


def test_tempo_pela_equacao_quadratica():
    c = _mruv(x0=(0, "m"), x=(75, "m"), v0=(10, "m/s"), a=(2, "m/s²"))
    assert c.calcular("t").valor == pytest.approx(5.0)


def test_tempo_pelo_trapezio_sem_aceleracao():
    r = _mruv(x0=(0, "m"), x=(75, "m"), v0=(10, "m/s"), v=(20, "m/s")).calcular("t")
    assert r.valor == pytest.approx(5.0)


def test_torricelli_velocidade_final():
    r = _mruv(x0=(0, "m"), x=(50, "m"), v0=(10, "m/s"), a=(3, "m/s²")).calcular("v")
    assert r.valor == pytest.approx(20.0)


def test_torricelli_frenagem_ate_parar():
    r = _mruv(x0=(0, "m"), x=(50, "m"), v0=(20, "m/s"), a=(-4, "m/s²")).calcular("v")
    assert r.valor == pytest.approx(0.0)
    assert "-0,0" not in r.formatar()


def test_torricelli_velocidade_inicial_com_sentido():
    r = _mruv(x0=(0, "m"), x=(40, "m"), v=(0, "m/s"), a=(-5, "m/s²")).calcular("v0")
    assert r.valor == pytest.approx(20.0)


def test_torricelli_aceleracao():
    r = _mruv(x0=(0, "m"), x=(75, "m"), v0=(10, "m/s"), v=(20, "m/s")).calcular("a")
    assert r.valor == pytest.approx(2.0)


def test_alvos_possiveis_do_slide_7():
    assert _mruv(v0=(10, "m/s"), a=(2, "m/s²"), t=(5, "s")).alvos_possiveis() == ["v"]


def test_ambiguidade_resolve_pela_ordem_e_lista_alternativas():
    c = _mruv(x0=(0, "m"), v0=(10, "m/s"), a=(2, "m/s²"), t=(5, "s"))
    assert c.alvos_possiveis() == ["x", "v"]
    assert c.calcular().variavel == "v"
    assert c.calcular("x").variavel == "x"


def test_alvo_nao_persiste_entre_chamadas():
    c = _mruv(x0=(0, "m"), v0=(10, "m/s"), a=(2, "m/s²"), t=(5, "s"))
    c.calcular("x")
    assert c.calcular().variavel == "v"


def test_insuficiente_aponta_o_que_falta():
    with pytest.raises(DadosInsuficientesErro) as exc:
        _mruv(v0=(10, "m/s"), a=(2, "m/s²")).calcular()
    assert exc.value.faltantes == ["v", "t"]


def test_insuficiente_com_alvo_explicito():
    with pytest.raises(DadosInsuficientesErro) as exc:
        _mruv(v0=(10, "m/s"), a=(2, "m/s²")).calcular("x")
    assert "x₀" in exc.value.faltantes


def test_alvo_ja_preenchido():
    with pytest.raises(DadosInconsistentesErro):
        _mruv(v0=(10, "m/s"), a=(2, "m/s²"), t=(5, "s")).calcular("t")


def test_alvo_desconhecido():
    with pytest.raises(CampoDesconhecidoErro):
        _mruv(v0=(10, "m/s")).calcular("z")


def test_todos_preenchidos():
    with pytest.raises(DadosInconsistentesErro):
        _mruv(x0=(0, "m"), x=(1, "m"), v0=(1, "m/s"), v=(1, "m/s"),
              a=(1, "m/s²"), t=(1, "s")).calcular()


def test_raiz_de_numero_negativo():
    c = _mruv(x0=(0, "m"), x=(10, "m"), v0=(0, "m/s"), a=(-2, "m/s²"))
    with pytest.raises(DadosInconsistentesErro):
        c.calcular("v")


def test_quadratica_sem_tempo_nao_negativo():
    c = _mruv(x0=(0, "m"), x=(10, "m"), v0=(-5, "m/s"), a=(-1, "m/s²"))
    with pytest.raises(DadosInconsistentesErro):
        c.calcular("t")


def test_quadratica_com_aceleracao_zero():
    c = _mruv(x0=(0, "m"), x=(10, "m"), v0=(5, "m/s"), a=(0, "m/s²"))
    with pytest.raises(DadosInconsistentesErro):
        c.calcular("t")


def test_fmt_nao_mostra_zero_negativo():
    assert _fmt(-0.0) == "0,0"
