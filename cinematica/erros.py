class ErroCinematica(Exception):
    """Base de todos os erros previstos do domínio."""


class UnidadeInvalidaErro(ErroCinematica):
    """Unidade ou grandeza inexistente na tabela de conversão."""


class UnidadeIncompativelErro(UnidadeInvalidaErro):
    """Unidade existe, mas não pertence à grandeza do campo (ex.: 'm' em tempo)."""


class ValorInvalidoErro(ErroCinematica):
    """Valor não numérico, NaN ou infinito."""


class CampoDesconhecidoErro(ErroCinematica):
    """Nome de variável que o calculador não possui."""


class DadosInconsistentesErro(ErroCinematica):
    """Valores que contradizem o modelo físico (ex.: tempo negativo)."""


class DadosInsuficientesErro(ErroCinematica):
    """Faltam variáveis para resolver o problema; lista quais."""

    def __init__(self, faltantes):
        self.faltantes = list(faltantes)
        super().__init__("Dados insuficientes. Faltam: " + ", ".join(self.faltantes))