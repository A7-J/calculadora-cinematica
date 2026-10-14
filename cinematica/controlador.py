"""Camada entre a GUI e o motor: sem tkinter, portanto testável."""
from dataclasses import dataclass

from .calculador import CalculadorCinematica, Resultado, _fmt
from .conversor import ConversorSI
from .erros import ErroCinematica, ValorInvalidoErro
from .mru import CalculadoraMRU
from .mruv import CalculadoraMRUV
from .projetil import Projetil2D

UNIDADE_PADRAO = {
    "comprimento": "m",
    "tempo": "s",
    "velocidade": "m/s",
    "aceleracao": "m/s²",
    "angulo": "°",
}


@dataclass(frozen=True)
class Linha:
    texto: str
    erro: bool = False


@dataclass(frozen=True)
class AbaConfig:
    nome: str                       # texto do botão da aba
    titulo: str                     # cabeçalho do cartão
    classe: type[CalculadorCinematica]
    entradas: tuple[str, ...]       # campos exibidos, na ordem
    nomes: dict[str, str]           # nome longo de cada campo (rótulo da caixa)
    padroes: dict[str, str]         # texto pré-preenchido
    painel: bool = False            # True: mostra todas as saídas possíveis


@dataclass(frozen=True)
class CampoUI:
    nome: str
    titulo: str
    unidades: tuple[str, ...]
    unidade_padrao: str
    texto_padrao: str


ABAS: tuple[AbaConfig, ...] = (
    AbaConfig(
        "MRU", "Cinemática 1D · MRU", CalculadoraMRU,
        ("x0", "x", "v", "t"),
        {"x0": "POSIÇÃO INICIAL X₀", "x": "POSIÇÃO FINAL X",
         "v": "VELOCIDADE V", "t": "TEMPO T"},
        {"x0": "0"},
    ),
    AbaConfig(
        "MRUV", "Cinemática 1D · MRUV", CalculadoraMRUV,
        ("x0", "x", "v0", "v", "a", "t"),
        {"x0": "POSIÇÃO INICIAL X₀", "x": "POSIÇÃO FINAL X",
         "v0": "VELOCIDADE INICIAL V₀", "v": "VELOCIDADE FINAL V",
         "a": "ACELERAÇÃO A", "t": "TEMPO T"},
        {"x0": "0"},
    ),
    AbaConfig(
        "Projétil 2D", "Cinemática 2D · Projétil", Projetil2D,
        ("x0", "y0", "v0", "theta", "g", "t"),
        {"x0": "POSIÇÃO INICIAL X₀", "y0": "ALTURA INICIAL Y₀",
         "v0": "VELOCIDADE INICIAL V₀", "theta": "ÂNGULO θ",
         "g": "GRAVIDADE G", "t": "TEMPO T (OPCIONAL)"},
        {"x0": "0", "y0": "0", "g": "9,8"},
        painel=True,
    ),
)


def parse_numero(texto: str) -> float | None:
    """'' -> None (campo vazio); aceita vírgula ou ponto decimal."""
    limpo = texto.strip().replace(",", ".")
    if not limpo:
        return None
    try:
        return float(limpo)
    except ValueError:
        raise ValorInvalidoErro(f"'{texto.strip()}' não é um número.") from None


def campos_da_aba(aba: AbaConfig) -> list[CampoUI]:
    conversor = ConversorSI()
    campos = []
    for nome in aba.entradas:
        grandeza = aba.classe.CAMPOS[nome].grandeza
        unidades = tuple(conversor.unidades_de(grandeza))
        campos.append(CampoUI(
            nome, aba.nomes[nome], unidades,
            UNIDADE_PADRAO.get(grandeza, unidades[0]),
            aba.padroes.get(nome, ""),
        ))
    return campos


def opcoes_de_alvo(aba: AbaConfig) -> dict[str, str | None]:
    """rótulo exibido -> nome do campo (None = automático). Vazio nas abas-painel."""
    if aba.painel:
        return {}
    opcoes: dict[str, str | None] = {"Automático": None}
    for nome in aba.entradas:
        opcoes[aba.classe.CAMPOS[nome].rotulo] = nome
    return opcoes


def calcular(aba: AbaConfig, entradas: dict[str, tuple[str, str]],
             alvo: str | None = None) -> list[Linha]:
    """entradas: nome -> (texto digitado, unidade escolhida)."""
    calc = aba.classe()
    for nome in aba.entradas:
        texto, unidade = entradas.get(nome, ("", ""))
        rotulo = aba.classe.CAMPOS[nome].rotulo
        try:
            valor = parse_numero(texto)
            if valor is not None:
                calc.definir(nome, valor, unidade)
        except ErroCinematica as erro:
            return [Linha(f"{rotulo}: {erro}", True)]
    try:
        if aba.painel:
            return _linhas_do_painel(calc, aba)
        return [Linha(calc.calcular(alvo).formatar())]
    except ErroCinematica as erro:
        return [Linha(str(erro), True)]


def _linhas_do_painel(calc: CalculadorCinematica, aba: AbaConfig) -> list[Linha]:
    ordem = list(dict.fromkeys(e.alvo for e in aba.classe.EQUACOES))
    tudo = calc.calcular_todos()
    linhas = []
    for nome in sorted(tudo, key=ordem.index):
        item = tudo[nome]
        if isinstance(item, Resultado):
            linhas.append(Linha(
                f"{item.variavel} = {_fmt(item.valor)} {item.unidade}  ·  {item.formula}"
            ))
        else:
            linhas.append(Linha(f"{aba.classe.CAMPOS[nome].rotulo}: {item}", True))
    return linhas
