from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable

from .conversor import ConversorSI, ConversorUnidades
from .erros import (
    CampoDesconhecidoErro,
    DadosInconsistentesErro,
    DadosInsuficientesErro,
    UnidadeIncompativelErro,
)

# Unidade de cada grandeza no Sistema Internacional (para exibir o resultado).
UNIDADE_SI: dict[str, str] = {
    "comprimento": "m",
    "tempo": "s",
    "velocidade": "m/s",
    "aceleracao": "m/s²",
    "angulo": "rad",
}


def _fmt(valor: float) -> str:
    """20.0 -> '20,0'; 0.05 -> '0,05'; -0.0 -> '0,0' (vírgula decimal, slide 7)."""
    texto = f"{valor + 0.0:.6g}"      # '+ 0.0' converte -0.0 em 0.0
    if "." not in texto and "e" not in texto and "n" not in texto:
        texto += ".0"
    return texto.replace(".", ",")


@dataclass(frozen=True)
class Campo:
    """Variável do calculador: qual grandeza e como rotular (x₀, v₀...)."""
    grandeza: str
    rotulo: str


@dataclass(frozen=True)
class Equacao:
    """Uma forma isolada de uma lei: calcula `alvo` a partir de `requer`."""
    alvo: str
    requer: tuple[str, ...]
    formula: str
    calcular: Callable[[dict[str, float]], float]   # recebe valores em SI


@dataclass(frozen=True)
class Resultado:
    variavel: str                                  # rótulo, ex.: "v"
    valor: float                                   # sempre em SI
    unidade: str                                   # unidade SI, ex.: "m/s"
    formula: str                                   # ex.: "v = v₀ + a·t"
    entradas: tuple[tuple[str, float, str], ...]   # (rótulo, valor SI, unidade SI)

    def formatar(self) -> str:
        texto = f"{self.variavel} = {_fmt(self.valor)} {self.unidade} · {self.formula}"
        if self.entradas:
            partes = ", ".join(f"{r} = {_fmt(v)} {u}" for r, v, u in self.entradas)
            texto += f", com {partes}"
        return texto


class CalculadorCinematica(ConversorUnidades):
    """Classe abstrata (slide 4). Subclasses definem CAMPOS, EQUACOES e _resolver()."""

    CAMPOS: dict[str, Campo] = {}
    EQUACOES: tuple[Equacao, ...] = ()

    def __init__(self, conversor: ConversorUnidades | None = None):
        self._conversor = conversor or ConversorSI()
        self.valores: dict[str, float] = {}   # sempre em SI
        self._alvo: str | None = None         # só existe durante um calcular()

    # --- contrato ConversorUnidades: delegação ---------------------------
    def para_si(self, valor: float, unidade: str) -> float:
        return self._conversor.para_si(valor, unidade)

    def grandeza_de(self, unidade: str) -> str:
        return self._conversor.grandeza_de(unidade)

    def unidades_de(self, grandeza: str) -> list[str]:
        return self._conversor.unidades_de(grandeza)

    # --- entrada de dados ------------------------------------------------
    def _campo(self, nome: str) -> Campo:
        if nome not in self.CAMPOS:
            raise CampoDesconhecidoErro(
                f"Campo desconhecido: {nome!r}. Válidos: {', '.join(self.CAMPOS)}"
            )
        return self.CAMPOS[nome]

    def definir(self, nome: str, valor: float, unidade: str) -> None:
        campo = self._campo(nome)
        if self.grandeza_de(unidade) != campo.grandeza:
            raise UnidadeIncompativelErro(
                f"'{unidade}' não é unidade de {campo.grandeza} (campo {campo.rotulo})"
            )
        self.valores[nome] = self.para_si(valor, unidade)

    def limpar(self, nome: str | None = None) -> None:
        if nome is None:
            self.valores.clear()
        else:
            self.valores.pop(nome, None)

    # --- cálculo (Template Method) --------------------------------------
    def calcular(self, alvo: str | None = None) -> Resultado:
        """alvo=None: o motor escolhe. alvo='t': força o cálculo desse campo."""
        if not self.valores:
            raise DadosInsuficientesErro(c.rotulo for c in self.CAMPOS.values())
        self._alvo = alvo
        try:
            return self._resolver()
        finally:
            self._alvo = None

    @abstractmethod
    def _resolver(self) -> Resultado: ...

    # --- dedução da equação (reutilizada por MRU, MRUV...) ---------------
    def _candidatas(self, equacoes: tuple[Equacao, ...],
                    alvo: str | None = None) -> list[Equacao]:
        preenchidos = set(self.valores)
        return [
            e for e in equacoes
            if e.alvo not in preenchidos
            and (alvo is None or e.alvo == alvo)
            and preenchidos.issuperset(e.requer)
        ]

    def alvos_possiveis(self) -> list[str]:
        """Campos vazios que já podem ser calculados (na ordem de CAMPOS)."""
        possiveis = {e.alvo for e in self._candidatas(self.EQUACOES)}
        return [n for n in self.CAMPOS if n in possiveis]

    def _faltantes_proximos(self, equacoes: tuple[Equacao, ...],
                            alvos: list[str]) -> list[str]:
        """Rótulos que faltam para a(s) equação(ões) mais próxima(s) de fechar."""
        preenchidos = set(self.valores)
        faltas = [set(e.requer) - preenchidos for e in equacoes if e.alvo in alvos]
        if not faltas:
            return [self.CAMPOS[n].rotulo for n in alvos]
        menor = min(len(f) for f in faltas)
        uniao = set().union(*(f for f in faltas if len(f) == menor))
        return [self.CAMPOS[n].rotulo for n in self.CAMPOS if n in uniao]

    def _resolver_por_equacoes(self, equacoes: tuple[Equacao, ...] | None = None) -> Resultado:
        equacoes = self.EQUACOES if equacoes is None else equacoes
        self._validar_tempos()
        preenchidos = set(self.valores)
        vazios = [n for n in self.CAMPOS if n not in preenchidos]
        alvo = self._alvo

        if alvo is not None:
            rotulo = self._campo(alvo).rotulo
            if alvo in preenchidos:
                raise DadosInconsistentesErro(
                    f"O campo {rotulo} já está preenchido: esvazie-o para calculá-lo."
                )
        elif not vazios:
            raise DadosInconsistentesErro(
                "Todos os campos estão preenchidos: deixe vazio o que deseja calcular."
            )

        candidatas = self._candidatas(equacoes, alvo)
        if not candidatas:
            raise DadosInsuficientesErro(
                self._faltantes_proximos(equacoes, [alvo] if alvo else vazios)
            )

        eq = candidatas[0]          # política: primeira declarada
        campo = self.CAMPOS[eq.alvo]
        try:
            valor = eq.calcular(self.valores)
        except ZeroDivisionError:
            raise DadosInconsistentesErro(
                f"Divisão por zero ao calcular {campo.rotulo}: confira os valores."
            ) from None
        except ValueError:
            raise DadosInconsistentesErro(
                f"Não existe solução real para {campo.rotulo} com esses valores."
            ) from None

        if campo.grandeza == "tempo" and valor < 0:
            raise DadosInconsistentesErro(
                f"O tempo calculado é negativo ({_fmt(valor)} s): confira os valores."
            )
        return Resultado(
            campo.rotulo, valor, UNIDADE_SI[campo.grandeza],
            eq.formula, self._entradas(*eq.requer),
        )

    def _validar_tempos(self) -> None:
        for nome, valor in self.valores.items():
            campo = self.CAMPOS[nome]
            if campo.grandeza == "tempo" and valor < 0:
                raise DadosInconsistentesErro(
                    f"O tempo {campo.rotulo} não pode ser negativo."
                )

    # --- utilitários para as subclasses ---------------------------------
    def _exigir(self, *nomes: str) -> None:
        faltam = [self._campo(n).rotulo for n in nomes if n not in self.valores]
        if faltam:
            raise DadosInsuficientesErro(faltam)

    def _entradas(self, *nomes: str) -> tuple[tuple[str, float, str], ...]:
        return tuple(
            (self.CAMPOS[n].rotulo, self.valores[n], UNIDADE_SI[self.CAMPOS[n].grandeza])
            for n in nomes
        )