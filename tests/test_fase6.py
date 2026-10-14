import pytest

from cinematica.controlador import (
    ABAS,
    calcular,
    campos_da_aba,
    opcoes_de_alvo,
    parse_numero,
)
from cinematica.erros import ValorInvalidoErro

MRU, MRUV, PROJETIL = ABAS


def _entradas(aba, **preenchidos):
    """Monta o dicionário da GUI: padrões da aba + o que foi digitado."""
    base = {c.nome: (c.texto_padrao, c.unidade_padrao) for c in campos_da_aba(aba)}
    for nome, valor in preenchidos.items():
        texto, unidade = valor if isinstance(valor, tuple) else (valor, base[nome][1])
        base[nome] = (texto, unidade)
    return base


# --- parse_numero ---------------------------------------------------------
@pytest.mark.parametrize("texto, esperado", [
    ("5", 5.0), ("1,5", 1.5), (" 2.25 ", 2.25), ("1e3", 1000.0), ("-3", -3.0),
    ("", None), ("   ", None),
])
def test_parse_numero(texto, esperado):
    assert parse_numero(texto) == esperado


def test_parse_numero_invalido():
    with pytest.raises(ValorInvalidoErro):
        parse_numero("abc")


# --- configuração das abas ------------------------------------------------
def test_tres_abas_na_ordem_do_slide():
    assert [a.nome for a in ABAS] == ["MRU", "MRUV", "Projétil 2D"]


def test_campos_trazem_unidades_e_padroes():
    campos = {c.nome: c for c in campos_da_aba(MRUV)}
    assert campos["v0"].unidades == ("m/s", "km/h")
    assert campos["v0"].unidade_padrao == "m/s"
    assert campos["x0"].texto_padrao == "0"
    angulo = {c.nome: c for c in campos_da_aba(PROJETIL)}["theta"]
    assert angulo.unidade_padrao == "°" and "rad" in angulo.unidades


def test_opcoes_de_alvo():
    assert list(opcoes_de_alvo(MRU)) == ["Automático", "x₀", "x", "v", "t"]
    assert opcoes_de_alvo(MRU)["x"] == "x"
    assert opcoes_de_alvo(PROJETIL) == {}


# --- cálculo via controlador ------------------------------------------------
def test_exemplo_do_slide_7_pela_gui():
    e = _entradas(MRUV, v0=("36", "km/h"), a=("2", "m/s²"), t=("5", "s"))
    (linha,) = calcular(MRUV, e)
    assert not linha.erro
    assert linha.texto == (
        "v = 20,0 m/s · v = v₀ + a·t, com v₀ = 10,0 m/s, a = 2,0 m/s², t = 5,0 s"
    )


def test_alvo_escolhido_na_gui():
    e = _entradas(MRUV, v0=("36", "km/h"), a=("2", "m/s²"), t=("5", "s"))
    (linha,) = calcular(MRUV, e, alvo="x")
    assert linha.texto.startswith("x = 75,0 m")


def test_mru_com_virgula_decimal():
    e = _entradas(MRU, v=("2,5", "m/s"), t=("10", "s"))
    (linha,) = calcular(MRU, e)
    assert linha.texto.startswith("x = 25,0 m")


def test_numero_invalido_aponta_o_campo():
    e = _entradas(MRU, v=("abc", "m/s"), t=("10", "s"))
    (linha,) = calcular(MRU, e)
    assert linha.erro and linha.texto.startswith("v: ")


def test_dados_insuficientes_viram_linha_de_erro():
    e = _entradas(MRUV, a=("2", "m/s²"))
    (linha,) = calcular(MRUV, e)
    assert linha.erro and "Faltam" in linha.texto


def test_tempo_negativo_vira_linha_de_erro():
    e = _entradas(MRU, v=("5", "m/s"), t=("-1", "s"))
    (linha,) = calcular(MRU, e)
    assert linha.erro


def test_painel_do_projetil_ordem_e_conteudo():
    e = _entradas(PROJETIL, v0=("20", "m/s"), theta=("30", "°"))
    linhas = calcular(PROJETIL, e)
    assert len(linhas) == 6 and not any(l.erro for l in linhas)
    assert linhas[0].texto.startswith("R = 35,348 m")
    assert linhas[1].texto.startswith("H = 5,10204 m")


def test_painel_do_projetil_isola_erros_de_t():
    e = _entradas(PROJETIL, v0=("20", "m/s"), theta=("30", "°"), t=("3", "s"))
    linhas = calcular(PROJETIL, e)
    assert sum(l.erro for l in linhas) == 3        # x, y e vy
    assert linhas[0].texto.startswith("R = ") and not linhas[0].erro


def test_painel_sem_dados():
    (linha,) = calcular(PROJETIL, _entradas(PROJETIL))
    assert linha.erro and "v₀" in linha.texto
