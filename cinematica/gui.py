import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from .controlador import ABAS, calcular, campos_da_aba, opcoes_de_alvo

# Paleta do slide 7
BG = "#0a0e2e"
CARD = "#161a47"
ENTRY_BG = "#0a0e2e"
BORDA = "#2d3260"
TEXTO = "#e8e8ff"
SUAVE = "#9aa0c8"
ACENTO = "#4c1d95"
ERRO = "#7f1d1d"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora de Cinemática 1D e 2D")
        self.configure(bg=BG)
        self.resizable(False, False)

        familia = tkfont.nametofont("TkDefaultFont").actual("family")
        self.f_titulo = tkfont.Font(family=familia, size=13, weight="bold")
        self.f_rotulo = tkfont.Font(family=familia, size=8)
        self.f_campo = tkfont.Font(family=familia, size=12)
        self.f_aba = tkfont.Font(family=familia, size=10, weight="bold")
        self.f_result = tkfont.Font(family=familia, size=11, weight="bold")
        self._estilo()

        self.aba_idx = tk.IntVar(value=1)          # abre em MRUV, como no slide
        self.vars: dict[str, tuple[tk.StringVar, tk.StringVar]] = {}
        self.alvo_var = tk.StringVar(value="Automático")
        self.opcoes: dict[str, str | None] = {}

        self.cartao = tk.Frame(self, bg=CARD, padx=22, pady=18,
                               highlightthickness=1, highlightbackground=SUAVE)
        self.cartao.pack(padx=24, pady=24)

        self.lbl_titulo = tk.Label(self.cartao, bg=CARD, fg=TEXTO, font=self.f_titulo)
        self.lbl_titulo.pack(anchor="w")

        barra = tk.Frame(self.cartao, bg=CARD)
        barra.pack(anchor="w", pady=(6, 10))
        for i, aba in enumerate(ABAS):
            tk.Radiobutton(
                barra, text=aba.nome, value=i, variable=self.aba_idx, indicatoron=False,
                command=self._ao_trocar_aba, font=self.f_aba, bg=CARD, fg=SUAVE,
                selectcolor=BG, activebackground=BG, activeforeground=TEXTO,
                relief="flat", bd=0, padx=12, pady=4, highlightthickness=1,
                highlightbackground=CARD, takefocus=0,
            ).pack(side="left", padx=(0, 4))

        self.form = tk.Frame(self.cartao, bg=CARD)
        self.form.pack(anchor="w")
        self.quadro_alvo = tk.Frame(self.cartao, bg=CARD)

        self.botoes = tk.Frame(self.cartao, bg=CARD)
        self.botoes.pack(fill="x", pady=(14, 8))
        botoes = self.botoes
        tk.Button(botoes, text="Calcular", command=self.calcular, font=self.f_aba,
                  bg=ACENTO, fg="white", activebackground=ACENTO, activeforeground="white",
                  relief="flat", padx=18, pady=6, bd=0).pack(side="left")
        tk.Button(botoes, text="Limpar", command=self.limpar, font=self.f_aba,
                  bg=CARD, fg=SUAVE, activebackground=BG, activeforeground=TEXTO,
                  relief="flat", padx=14, pady=6, bd=0,
                  highlightthickness=1, highlightbackground=BORDA).pack(side="left", padx=8)

        self.resultado = tk.Label(self.cartao, text="", bg=CARD, fg="white",
                                  font=self.f_result, justify="left", anchor="w",
                                  wraplength=520, padx=12, pady=10)
        self.bind("<Return>", self.calcular)
        self.selecionar_aba(1)

    # --- estilo ---------------------------------------------------------
    def _estilo(self) -> None:
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("Escuro.TCombobox", fieldbackground=ENTRY_BG, background=CARD,
                         foreground=TEXTO, arrowcolor=TEXTO, bordercolor=BORDA,
                         lightcolor=BORDA, darkcolor=BORDA)
        estilo.map("Escuro.TCombobox",
                   fieldbackground=[("readonly", ENTRY_BG)],
                   foreground=[("readonly", TEXTO)],
                   selectbackground=[("readonly", ENTRY_BG)],
                   selectforeground=[("readonly", TEXTO)])
        self.option_add("*TCombobox*Listbox.background", ENTRY_BG)
        self.option_add("*TCombobox*Listbox.foreground", TEXTO)
        self.option_add("*TCombobox*Listbox.selectBackground", ACENTO)

    # --- abas e formulário ------------------------------------------------
    def selecionar_aba(self, indice: int) -> None:
        self.aba_idx.set(indice)
        self._ao_trocar_aba()

    def _ao_trocar_aba(self) -> None:
        aba = ABAS[self.aba_idx.get()]
        self.lbl_titulo.config(text=aba.titulo)
        for filho in self.form.winfo_children():
            filho.destroy()
        self.vars = {}
        campos = campos_da_aba(aba)
        colunas = 2 if len(campos) > 4 else 1
        for i, campo in enumerate(campos):
            celula = tk.Frame(self.form, bg=CARD)
            celula.grid(row=i // colunas, column=i % colunas, sticky="w",
                        padx=(0, 18 if colunas == 2 else 0), pady=(0, 8))
            tk.Label(celula, text=campo.titulo, bg=CARD, fg=SUAVE,
                     font=self.f_rotulo).pack(anchor="w")
            linha = tk.Frame(celula, bg=CARD)
            linha.pack(anchor="w")
            texto = tk.StringVar(value=campo.texto_padrao)
            unidade = tk.StringVar(value=campo.unidade_padrao)
            tk.Entry(linha, textvariable=texto, width=12, font=self.f_campo,
                     bg=ENTRY_BG, fg=TEXTO, insertbackground=TEXTO, relief="flat",
                     highlightthickness=1, highlightbackground=BORDA,
                     highlightcolor=SUAVE).pack(side="left", ipady=4)
            ttk.Combobox(linha, textvariable=unidade, values=campo.unidades, width=6,
                         state="readonly", style="Escuro.TCombobox",
                         font=self.f_campo).pack(side="left", padx=(6, 0))
            self.vars[campo.nome] = (texto, unidade)

        self.opcoes = opcoes_de_alvo(aba)
        for filho in self.quadro_alvo.winfo_children():
            filho.destroy()
        self.alvo_var.set("Automático")
        if self.opcoes:
            tk.Label(self.quadro_alvo, text="CALCULAR", bg=CARD, fg=SUAVE,
                     font=self.f_rotulo).pack(anchor="w")
            ttk.Combobox(self.quadro_alvo, textvariable=self.alvo_var,
                         values=list(self.opcoes), width=14, state="readonly",
                         style="Escuro.TCombobox", font=self.f_campo).pack(anchor="w")
            self.quadro_alvo.pack(anchor="w", pady=(4, 0), before=self.botoes)
        else:
            self.quadro_alvo.pack_forget()
        self.resultado.pack_forget()

    # --- ações --------------------------------------------------------------
    def calcular(self, _evento=None) -> None:
        aba = ABAS[self.aba_idx.get()]
        entradas = {nome: (t.get(), u.get()) for nome, (t, u) in self.vars.items()}
        alvo = self.opcoes.get(self.alvo_var.get()) if self.opcoes else None
        self._mostrar(calcular(aba, entradas, alvo))

    def limpar(self) -> None:
        self._ao_trocar_aba()

    def _mostrar(self, linhas) -> None:
        tem_erro = any(l.erro for l in linhas)
        self.resultado.config(text="\n".join(l.texto for l in linhas),
                              bg=ERRO if tem_erro else ACENTO)
        self.resultado.pack(fill="x", pady=(6, 0))

    def texto_resultado(self) -> str:
        return self.resultado.cget("text")


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
