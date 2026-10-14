from abc import ABC, abstractmethod
from fractions import Fraction
from math import isfinite, pi

from .erros import UnidadeInvalidaErro, ValorInvalidoErro


class ConversorUnidades(ABC):
    """Contrato de conversão (slide 4). Em Python: para_si == paraSI."""

    @abstractmethod
    def para_si(self, valor: float, unidade: str) -> float: ...

    @abstractmethod
    def grandeza_de(self, unidade: str) -> str: ...

    @abstractmethod
    def unidades_de(self, grandeza: str) -> list[str]: ...


# unidade -> (grandeza, fator para o SI). Fraction evita erros de ponto
# flutuante: 36 km/h vira exatamente 10 m/s, e 500 ms vira exatamente 0,5 s.
_TABELA: dict[str, tuple[str, Fraction]] = {
    "m":     ("comprimento", Fraction(1)),
    "km":    ("comprimento", Fraction(1000)),
    "cm":    ("comprimento", Fraction(1, 100)),
    "s":     ("tempo", Fraction(1)),
    "ms":    ("tempo", Fraction(1, 1000)),
    "min":   ("tempo", Fraction(60)),
    "h":     ("tempo", Fraction(3600)),
    "m/s":   ("velocidade", Fraction(1)),
    "km/h":  ("velocidade", Fraction(1000, 3600)),
    "m/s²":  ("aceleracao", Fraction(1)),
    "km/h²": ("aceleracao", Fraction(1000, 3600 ** 2)),
    "rad":   ("angulo", Fraction(1)),
    "°":     ("angulo", Fraction(pi) / 180),
}

# Índice invertido, construído uma única vez ao importar o módulo.
_POR_GRANDEZA: dict[str, list[str]] = {}
for _unid, (_gran, _) in _TABELA.items():
    _POR_GRANDEZA.setdefault(_gran, []).append(_unid)


class ConversorSI(ConversorUnidades):
    def _buscar(self, unidade: str) -> tuple[str, Fraction]:
        chave = unidade.strip() if isinstance(unidade, str) else unidade
        if chave not in _TABELA:
            raise UnidadeInvalidaErro(f"Unidade desconhecida: {unidade!r}")
        return _TABELA[chave]

    def para_si(self, valor: float, unidade: str) -> float:
        if (isinstance(valor, bool)
                or not isinstance(valor, (int, float))
                or not isfinite(valor)):
            raise ValorInvalidoErro(f"Valor inválido: {valor!r}")
        _, fator = self._buscar(unidade)
        return float(Fraction(valor) * fator)

    def grandeza_de(self, unidade: str) -> str:
        return self._buscar(unidade)[0]

    def unidades_de(self, grandeza: str) -> list[str]:
        if grandeza not in _POR_GRANDEZA:
            raise UnidadeInvalidaErro(f"Grandeza desconhecida: {grandeza!r}")
        return list(_POR_GRANDEZA[grandeza])
