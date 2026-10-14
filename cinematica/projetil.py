from math import cos, degrees, pi, sin, sqrt

from .calculador import CalculadorCinematica, Campo, Equacao, Resultado, _fmt
from .erros import DadosInconsistentesErro, ErroCinematica


def _vx(d: dict[str, float]) -> float:
    """Eixo x: velocidade constante (MRU)."""
    return d["v0"] * cos(d["theta"])


def _voy(d: dict[str, float]) -> float:
    """Eixo y: componente vertical inicial (MRUV com a = −g)."""
    return d["v0"] * sin(d["theta"])


def _tempo_de_voo(d: dict[str, float]) -> float:
    """Tempo até y = 0: raiz positiva de y₀ + v₀y·t − g·t²/2 = 0."""
    voy = _voy(d)
    return (voy + sqrt(voy ** 2 + 2 * d["g"] * d["y0"])) / d["g"]


class Projetil2D(CalculadorCinematica):
    """Lançamento oblíquo: eixos x e y independentes (slide 4). Solo em y = 0."""

    # Valores pré-preenchidos (editáveis): g = 9,8 m/s², lançamento em (0, 0).
    PADROES = {"g": (9.8, "m/s²"), "x0": (0, "m"), "y0": (0, "m")}

    CAMPOS = {
        # entradas
        "x0":    Campo("comprimento", "x₀"),
        "y0":    Campo("comprimento", "y₀"),
        "v0":    Campo("velocidade", "v₀"),
        "theta": Campo("angulo", "θ"),
        "g":     Campo("aceleracao", "g"),
        "t":     Campo("tempo", "t"),
        # saídas
        "x":       Campo("comprimento", "x"),
        "y":       Campo("comprimento", "y"),
        "vx":      Campo("velocidade", "vₓ"),
        "voy":     Campo("velocidade", "v₀y"),
        "vy":      Campo("velocidade", "vy"),
        "ts":      Campo("tempo", "t_sub"),
        "tv":      Campo("tempo", "t_voo"),
        "hmax":    Campo("comprimento", "H"),
        "alcance": Campo("comprimento", "R"),
    }

    # A ORDEM É A PRIORIDADE no modo automático.
    EQUACOES = (
        Equacao("alcance", ("v0", "theta", "g", "y0"),
                "R = v₀·cos θ · t_voo",
                lambda d: _vx(d) * _tempo_de_voo(d)),
        Equacao("hmax", ("v0", "theta", "g", "y0"),
                "H = y₀ + (máx(v₀·sen θ, 0))²/(2g)",
                lambda d: d["y0"] + max(_voy(d), 0.0) ** 2 / (2 * d["g"])),
        Equacao("tv", ("v0", "theta", "g", "y0"),
                "t_voo = (v₀·sen θ + √((v₀·sen θ)² + 2g·y₀))/g",
                _tempo_de_voo),
        Equacao("ts", ("v0", "theta", "g"),
                "t_sub = máx(v₀·sen θ, 0)/g",
                lambda d: max(_voy(d), 0.0) / d["g"]),
        Equacao("vx", ("v0", "theta"), "vₓ = v₀·cos θ", _vx),
        Equacao("voy", ("v0", "theta"), "v₀y = v₀·sen θ", _voy),
        Equacao("x", ("x0", "v0", "theta", "t"),
                "x = x₀ + v₀·cos θ·t",
                lambda d: d["x0"] + _vx(d) * d["t"]),
        Equacao("y", ("y0", "v0", "theta", "g", "t"),
                "y = y₀ + v₀·sen θ·t − g·t²/2",
                lambda d: d["y0"] + _voy(d) * d["t"] - d["g"] * d["t"] ** 2 / 2),
        Equacao("vy", ("v0", "theta", "g", "t"),
                "vy = v₀·sen θ − g·t",
                lambda d: _voy(d) - d["g"] * d["t"]),
    )

    _DEPENDEM_DE_T = frozenset({"x", "y", "vy"})

    def __init__(self, conversor=None):
        super().__init__(conversor)
        self._aplicar_padroes()

    def _aplicar_padroes(self) -> None:
        for nome, (valor, unidade) in self.PADROES.items():
            if nome not in self.valores:
                self.definir(nome, valor, unidade)

    def limpar(self, nome: str | None = None) -> None:
        super().limpar(nome)
        self._aplicar_padroes()          # g, x₀ e y₀ voltam ao padrão

    def _entradas(self, *nomes: str):
        """Mostra o ângulo em graus (é só exibição; o cálculo segue em rad)."""
        return tuple(
            (r, degrees(v), "°") if u == "rad" else (r, v, u)
            for r, v, u in super()._entradas(*nomes)
        )

    # --- validações físicas ------------------------------------------------
    def _validar_entradas(self) -> None:
        v = self.valores
        if v.get("v0", 0.0) < 0:
            raise DadosInconsistentesErro("A velocidade inicial não pode ser negativa.")
        if abs(v.get("theta", 0.0)) > pi / 2 + 1e-12:
            raise DadosInconsistentesErro("O ângulo de lançamento deve estar entre −90° e 90°.")
        if v.get("g", 1.0) <= 0:
            raise DadosInconsistentesErro("A gravidade g deve ser positiva.")
        if v.get("y0", 0.0) < 0:
            raise DadosInconsistentesErro("A altura inicial y₀ não pode ser negativa (solo em y = 0).")

    def _resolver(self) -> Resultado:
        self._validar_entradas()
        resultado = self._resolver_por_equacoes(self.EQUACOES)
        if resultado.variavel in self._DEPENDEM_DE_T:
            tv = _tempo_de_voo(self.valores)
            t = self.valores["t"]
            if t > tv * (1 + 1e-9) + 1e-12:
                raise DadosInconsistentesErro(
                    f"t = {_fmt(t)} s é maior que o tempo de voo ({_fmt(tv)} s): "
                    "o projétil já tocou o solo."
                )
        return resultado

    # --- painel completo ---------------------------------------------------
    def calcular_todos(self) -> dict[str, Resultado | ErroCinematica]:
        """Calcula todas as saídas possíveis; um erro em uma não derruba as outras."""
        self._validar_entradas()
        alvos = self.alvos_possiveis()
        if not alvos:
            self.calcular()              # levanta DadosInsuficientesErro com o que falta
            return {}
        saida: dict[str, Resultado | ErroCinematica] = {}
        for nome in alvos:
            try:
                saida[nome] = self.calcular(nome)
            except ErroCinematica as erro:
                saida[nome] = erro
        return saida
