"""Teste de fumaça da janela. É ignorado se não houver tkinter ou display."""
import pytest

tk = pytest.importorskip("tkinter")


@pytest.fixture
def app():
    from cinematica.gui import App
    try:
        janela = App()
    except tk.TclError:
        pytest.skip("sem display disponível")
    janela.withdraw()
    yield janela
    janela.destroy()


def test_exemplo_do_slide_na_janela(app):
    app.selecionar_aba(1)
    app.vars["v0"][0].set("36")
    app.vars["v0"][1].set("km/h")
    app.vars["a"][0].set("2")
    app.vars["t"][0].set("5")
    app.calcular()
    assert app.texto_resultado().startswith("v = 20,0 m/s · v = v₀ + a·t")


def test_trocar_de_aba_recria_os_campos(app):
    app.selecionar_aba(0)
    assert list(app.vars) == ["x0", "x", "v", "t"]
    app.selecionar_aba(2)
    assert list(app.vars) == ["x0", "y0", "v0", "theta", "g", "t"]
    assert app.vars["g"][0].get() == "9,8"


def test_erro_aparece_no_resultado(app):
    app.selecionar_aba(0)
    app.vars["v"][0].set("abc")
    app.calcular()
    assert app.texto_resultado().startswith("v: ")


def test_limpar_restaura_padroes(app):
    app.selecionar_aba(1)
    app.vars["a"][0].set("7")
    app.limpar()
    assert app.vars["a"][0].get() == ""
    assert app.vars["x0"][0].get() == "0"
