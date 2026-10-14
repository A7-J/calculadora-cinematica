# Calculadora de Cinemática 1D e 2D com Orientação a Objetos

Aplicação desktop que resolve problemas de **MRU**, **MRUV** e **lançamento
oblíquo (projétil 2D)**. Você preenche o que sabe, deixa vazio o que quer
descobrir, e o motor escolhe a equação certa, converte tudo para o SI e mostra
o resultado com a fórmula usada.

Autores: Arthur Pires · Disciplina: Física Geral e Experimental

## Funcionalidades

- Movimentos 1D (MRU, MRUV) e 2D (projétil) no mesmo fluxo.
- Conversão automática para o SI (m, km, cm, s, ms, min, h, m/s, km/h, m/s²,
  km/h², rad, °) antes de qualquer cálculo.
- Dedução automática da fórmula a partir dos campos preenchidos.
- Validação com mensagens claras (dados insuficientes, tempo negativo, divisão
  por zero, raiz de número negativo, unidade incompatível com o campo).

## Requisitos

- Python 3.10 ou superior
- tkinter (Ubuntu/Mint: `sudo apt install python3-tk`)

## Instalação e execução

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python main.py
```

## Testes

```bash
python -m pytest -v
```

Os testes da janela são ignorados automaticamente se não houver display.

## Estrutura

```text
cinematica/
  erros.py        hierarquia de exceções do domínio
  conversor.py    ConversorUnidades (interface) e ConversorSI
  calculador.py   CalculadorCinematica (abstrata), Campo, Equacao, Resultado
  mru.py          CalculadoraMRU
  mruv.py         CalculadoraMRUV
  projetil.py     Projetil2D
  controlador.py  camada entre a GUI e o motor (sem tkinter)
  gui.py          interface tkinter
docs/uml.md       diagramas UML (Mermaid)
gerar_uml.py      regenera docs/uml.md a partir das classes reais
main.py           ponto de entrada da GUI
tests/            testes por fase
```

## Arquitetura

- **Interface** `ConversorUnidades`: contrato `para_si`, `grandeza_de`, `unidades_de`.
- **Classe abstrata** `CalculadorCinematica`: guarda os valores já em SI, valida
  unidade e grandeza, e deduz a equação (Template Method).
- **Classes concretas**: `CalculadoraMRU`, `CalculadoraMRUV`, `Projetil2D`.
  Cada uma só declara seus `CAMPOS` e suas `EQUACOES`.
- **Controlador + GUI**: a janela só desenha; nunca conhece unidades nem fórmulas.

Diagramas completos em [docs/uml.md](docs/uml.md).

## Uso pela API

```python
from cinematica.mruv import CalculadoraMRUV

c = CalculadoraMRUV()
c.definir("v0", 36, "km/h")
c.definir("a", 2, "m/s²")
c.definir("t", 5, "s")
print(c.calcular().formatar())
# v = 20,0 m/s · v = v₀ + a·t, com v₀ = 10,0 m/s, a = 2,0 m/s², t = 5,0 s
```

## Decisões físicas e limitações

- Campo vazio = incógnita. Se mais de uma for calculável, vale a ordem de
  prioridade das equações; `calcular("x")` escolhe explicitamente.
- Torricelli (v² = v₀² + 2aΔx) tem duas raízes: assume-se que não há inversão de
  sentido (v segue o sinal de v₀, ou de a se v₀ = 0).
- `t` pela equação quadrática devolve a menor raiz não negativa; com a = 0 o
  motor recusa (use o MRU).
- Projétil: solo em y = 0, g padrão 9,8 m/s², ângulo entre −90° e 90°. Problemas
  inversos (achar v₀ ou θ a partir do alcance) não estão incluídos.
- Dados em excesso são ignorados: o motor não confere a consistência entre os
  campos que sobram.

## Regenerar o UML

```bash
python gerar_uml.py
```
