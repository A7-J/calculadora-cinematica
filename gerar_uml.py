"""Gera docs/uml.md (diagramas Mermaid) a partir das classes reais do projeto.

Uso:  python gerar_uml.py
"""
import dataclasses
import inspect
import types
from pathlib import Path

from cinematica import calculador, controlador, conversor, erros, mru, mruv, projetil

try:                                   # a GUI exige tkinter instalado
    from cinematica import gui
except ImportError:                    # pragma: no cover
    gui = None

INTERFACES = {conversor.ConversorUnidades}
ATRIBUTOS_DE_CLASSE = ("CAMPOS", "EQUACOES", "PADROES")
METODOS_PROTEGIDOS_EXIBIDOS = {"_resolver"}
EXTRAS = {calculador.CalculadorCinematica: ["+valores dict"]}


def _tipo(t) -> str:
    origem = getattr(t, "__origin__", None)
    if origem is not None:
        return getattr(origem, "__name__", "obj")
    if isinstance(t, types.UnionType):
        return " ou ".join(_tipo(a) for a in t.__args__)
    return getattr(t, "__name__", "obj")


def _estereotipo(cls) -> str | None:
    if cls in INTERFACES:
        return "interface"
    if inspect.isabstract(cls):
        return "abstract"
    if dataclasses.is_dataclass(cls):
        return "dataclass"
    return None


def _membros(cls) -> list[str]:
    linhas = []
    if dataclasses.is_dataclass(cls):
        linhas += [f"+{_tipo(f.type)} {f.name}" for f in dataclasses.fields(cls)]
    linhas += EXTRAS.get(cls, [])
    linhas += [f"+{n}" for n in ATRIBUTOS_DE_CLASSE if n in vars(cls)]
    for nome, obj in vars(cls).items():
        if not inspect.isfunction(obj) or nome == "__init__":
            continue
        if nome.startswith("_") and nome not in METODOS_PROTEGIDOS_EXIBIDOS:
            continue
        params = ", ".join(p for p in inspect.signature(obj).parameters if p != "self")
        marca = "*" if getattr(obj, "__isabstractmethod__", False) else ""
        prefixo = "#" if nome.startswith("_") else "+"
        linhas.append(f"{prefixo}{nome}({params}){marca}")
    return linhas


def _classe(cls, nome: str | None = None, estereotipo: str | None = None,
            membros: list[str] | None = None) -> list[str]:
    nome = nome or cls.__name__
    estereotipo = estereotipo or _estereotipo(cls)
    membros = _membros(cls) if membros is None else membros
    saida = [f"    class {nome} {{"]
    if estereotipo:
        saida.append(f"        <<{estereotipo}>>")
    saida += [f"        {m}" for m in membros]
    saida.append("    }")
    return saida


def _heranca(classes: list) -> list[str]:
    conjunto = set(classes)
    linhas = []
    for cls in classes:
        for base in cls.__bases__:
            if base in conjunto:
                seta = "<|.." if base in INTERFACES else "<|--"
                linhas.append(f"    {base.__name__} {seta} {cls.__name__}")
    return linhas


def diagrama_nucleo() -> str:
    cls = [conversor.ConversorUnidades, conversor.ConversorSI,
           calculador.CalculadorCinematica, mru.CalculadoraMRU,
           mruv.CalculadoraMRUV, projetil.Projetil2D,
           calculador.Campo, calculador.Equacao, calculador.Resultado]
    linhas = ["classDiagram", "    direction TB"]
    for c in cls:
        linhas += _classe(c)
    linhas += _heranca(cls)
    linhas += [
        "    CalculadorCinematica o-- Campo : CAMPOS",
        "    CalculadorCinematica o-- Equacao : EQUACOES",
        "    CalculadorCinematica ..> Resultado : devolve",
        '    note for CalculadorCinematica "Implementa ConversorUnidades delegando a um ConversorSI"',
    ]
    return "\n".join(linhas)


def diagrama_apresentacao() -> str:
    funcoes = [
        f"+{n}({', '.join(inspect.signature(f).parameters)})"
        for n, f in vars(controlador).items()
        if inspect.isfunction(f) and f.__module__ == controlador.__name__
        and not n.startswith("_")
    ]
    cls = [controlador.AbaConfig, controlador.CampoUI, controlador.Linha]
    linhas = ["classDiagram", "    direction LR"]
    if gui is not None:
        linhas += _classe(gui.App, membros=[f"+{n}()" for n in
                          ("selecionar_aba", "calcular", "limpar", "texto_resultado")])
    linhas += _classe(None, "Controlador", "module", funcoes)
    for c in cls:
        linhas += _classe(c)
    linhas += _classe(calculador.CalculadorCinematica, membros=["+calcular(alvo)"])
    if gui is not None:
        linhas += ["    App ..> Controlador : chama"]
    linhas += [
        "    Controlador ..> CalculadorCinematica : instancia e usa",
        "    Controlador --> AbaConfig : lê",
        "    Controlador ..> CampoUI : monta",
        "    Controlador ..> Linha : devolve",
        "    AbaConfig --> CalculadorCinematica : classe",
    ]
    return "\n".join(linhas)


def diagrama_erros() -> str:
    cls = [c for _, c in inspect.getmembers(erros, inspect.isclass)
           if c.__module__ == erros.__name__]
    linhas = ["classDiagram", "    direction TB"]
    for c in cls:
        linhas += _classe(c, estereotipo=None, membros=[])
    linhas += _heranca(cls)
    return "\n".join(linhas)


def gerar() -> str:
    partes = ["# Diagramas UML", "",
              "Gerado por `python gerar_uml.py` a partir das classes reais.", ""]
    for titulo, diagrama in (
        ("Núcleo (regras e modelos)", diagrama_nucleo()),
        ("Apresentação (GUI e controlador)", diagrama_apresentacao()),
        ("Erros", diagrama_erros()),
    ):
        partes += [f"## {titulo}", "", "```mermaid", diagrama, "```", ""]
    return "\n".join(partes)


def main() -> None:
    destino = Path(__file__).parent / "docs" / "uml.md"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(gerar(), encoding="utf-8")
    print(f"Diagramas gravados em {destino}")


if __name__ == "__main__":
    main()
