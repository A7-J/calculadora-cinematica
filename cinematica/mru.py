from .calculador import CalculadorCinematica, Campo, Equacao, Resultado


class CalculadoraMRU(CalculadorCinematica):
    """Movimento retilíneo uniforme: x = x₀ + v·t, com a = 0 (slide 4)."""

    CAMPOS = {
        "x0": Campo("comprimento", "x₀"),
        "x":  Campo("comprimento", "x"),
        "v":  Campo("velocidade", "v"),
        "t":  Campo("tempo", "t"),
    }

    EQUACOES = (
        Equacao("x",  ("x0", "v", "t"), "x = x₀ + v·t",
                lambda d: d["x0"] + d["v"] * d["t"]),
        Equacao("x0", ("x", "v", "t"),  "x₀ = x − v·t",
                lambda d: d["x"] - d["v"] * d["t"]),
        Equacao("v",  ("x", "x0", "t"), "v = (x − x₀)/t",
                lambda d: (d["x"] - d["x0"]) / d["t"]),
        Equacao("t",  ("x", "x0", "v"), "t = (x − x₀)/v",
                lambda d: (d["x"] - d["x0"]) / d["v"]),
    )

    def _resolver(self) -> Resultado:
        return self._resolver_por_equacoes(self.EQUACOES)
