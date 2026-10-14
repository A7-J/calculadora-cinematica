from math import copysign, sqrt

from .calculador import CalculadorCinematica, Campo, Equacao, Resultado


def _dx(d: dict[str, float]) -> float:
    return d["x"] - d["x0"]


def _sentido(*valores: float) -> float:
    """+1 ou −1 conforme o primeiro valor não nulo (padrão: +1)."""
    for v in valores:
        if v != 0:
            return 1.0 if v > 0 else -1.0
    return 1.0


def _raiz(radicando: float, escala: float) -> float:
    """√ com tolerância a ruído de ponto flutuante; ValueError se for negativo."""
    if radicando < -1e-9 * max(1.0, escala):
        raise ValueError("radicando negativo")
    return sqrt(max(radicando, 0.0))


def _v_por_torricelli(d: dict[str, float]) -> float:
    rad = d["v0"] ** 2 + 2 * d["a"] * _dx(d)
    raiz = _raiz(rad, d["v0"] ** 2 + abs(2 * d["a"] * _dx(d)))
    return copysign(raiz, _sentido(d["v0"], d["a"]))


def _v0_por_torricelli(d: dict[str, float]) -> float:
    rad = d["v"] ** 2 - 2 * d["a"] * _dx(d)
    raiz = _raiz(rad, d["v"] ** 2 + abs(2 * d["a"] * _dx(d)))
    return copysign(raiz, _sentido(d["v"], -d["a"]))


def _t_por_posicao(d: dict[str, float]) -> float:
    """Resolve a·t²/2 + v₀·t − Δx = 0 e devolve a menor raiz ≥ 0."""
    v0, a, dx = d["v0"], d["a"], _dx(d)
    raiz = _raiz(v0 ** 2 + 2 * a * dx, v0 ** 2 + abs(2 * a * dx))
    raizes = ((-v0 - raiz) / a, (-v0 + raiz) / a)     # a = 0 -> ZeroDivisionError
    nao_negativas = [max(r, 0.0) for r in raizes if r >= -1e-12]
    if not nao_negativas:
        raise ValueError("sem raiz de tempo não negativa")
    return min(nao_negativas)


class CalculadoraMRUV(CalculadorCinematica):
    """MRUV: aceleração constante (slide 4)."""

    CAMPOS = {
        "x0": Campo("comprimento", "x₀"),
        "x":  Campo("comprimento", "x"),
        "v0": Campo("velocidade", "v₀"),
        "v":  Campo("velocidade", "v"),
        "a":  Campo("aceleracao", "a"),
        "t":  Campo("tempo", "t"),
    }

    # A ORDEM É A PRIORIDADE quando há mais de uma incógnita calculável.
    EQUACOES = (
        # 1) v = v₀ + a·t
        Equacao("v",  ("v0", "a", "t"), "v = v₀ + a·t",
                lambda d: d["v0"] + d["a"] * d["t"]),
        Equacao("v0", ("v", "a", "t"),  "v₀ = v − a·t",
                lambda d: d["v"] - d["a"] * d["t"]),
        Equacao("a",  ("v", "v0", "t"), "a = (v − v₀)/t",
                lambda d: (d["v"] - d["v0"]) / d["t"]),
        Equacao("t",  ("v", "v0", "a"), "t = (v − v₀)/a",
                lambda d: (d["v"] - d["v0"]) / d["a"]),
        # 2) x = x₀ + v₀·t + a·t²/2
        Equacao("x",  ("x0", "v0", "a", "t"), "x = x₀ + v₀·t + a·t²/2",
                lambda d: d["x0"] + d["v0"] * d["t"] + d["a"] * d["t"] ** 2 / 2),
        Equacao("x0", ("x", "v0", "a", "t"),  "x₀ = x − v₀·t − a·t²/2",
                lambda d: d["x"] - d["v0"] * d["t"] - d["a"] * d["t"] ** 2 / 2),
        Equacao("v0", ("x", "x0", "a", "t"),  "v₀ = (x − x₀ − a·t²/2)/t",
                lambda d: (_dx(d) - d["a"] * d["t"] ** 2 / 2) / d["t"]),
        Equacao("a",  ("x", "x0", "v0", "t"), "a = 2·(x − x₀ − v₀·t)/t²",
                lambda d: 2 * (_dx(d) - d["v0"] * d["t"]) / d["t"] ** 2),
        Equacao("t",  ("x", "x0", "v0", "a"), "t = (−v₀ ± √(v₀² + 2a·(x − x₀)))/a, menor raiz ≥ 0",
                _t_por_posicao),
        # 3) x = x₀ + (v₀ + v)·t/2   (não usa a)
        Equacao("x",  ("x0", "v0", "v", "t"), "x = x₀ + (v₀ + v)·t/2",
                lambda d: d["x0"] + (d["v0"] + d["v"]) * d["t"] / 2),
        Equacao("x0", ("x", "v0", "v", "t"),  "x₀ = x − (v₀ + v)·t/2",
                lambda d: d["x"] - (d["v0"] + d["v"]) * d["t"] / 2),
        Equacao("v0", ("x", "x0", "v", "t"),  "v₀ = 2·(x − x₀)/t − v",
                lambda d: 2 * _dx(d) / d["t"] - d["v"]),
        Equacao("v",  ("x", "x0", "v0", "t"), "v = 2·(x − x₀)/t − v₀",
                lambda d: 2 * _dx(d) / d["t"] - d["v0"]),
        Equacao("t",  ("x", "x0", "v0", "v"), "t = 2·(x − x₀)/(v₀ + v)",
                lambda d: 2 * _dx(d) / (d["v0"] + d["v"])),
        # 4) v² = v₀² + 2a·(x − x₀)   (Torricelli, não usa t)
        Equacao("a",  ("v", "v0", "x", "x0"), "a = (v² − v₀²)/(2·(x − x₀))",
                lambda d: (d["v"] ** 2 - d["v0"] ** 2) / (2 * _dx(d))),
        Equacao("x",  ("v", "v0", "a", "x0"), "x = x₀ + (v² − v₀²)/(2a)",
                lambda d: d["x0"] + (d["v"] ** 2 - d["v0"] ** 2) / (2 * d["a"])),
        Equacao("x0", ("v", "v0", "a", "x"),  "x₀ = x − (v² − v₀²)/(2a)",
                lambda d: d["x"] - (d["v"] ** 2 - d["v0"] ** 2) / (2 * d["a"])),
        Equacao("v",  ("v0", "a", "x", "x0"), "v² = v₀² + 2a·(x − x₀), com v no sentido de v₀",
                _v_por_torricelli),
        Equacao("v0", ("v", "a", "x", "x0"),  "v₀² = v² − 2a·(x − x₀), com v₀ no sentido de v",
                _v0_por_torricelli),
    )

    def _resolver(self) -> Resultado:
        return self._resolver_por_equacoes(self.EQUACOES)
