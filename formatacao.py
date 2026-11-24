"""Formatação de números em pt-BR: fonte única do que aparece na tela.

Nada de nome de variável ou ponto decimal do inglês chegando ao usuário: todo texto
numérico do dashboard passa por aqui.
"""

MENOS = '−'  # sinal tipográfico, alinhado com o resto dos textos


def numero(valor, casas: int = 1) -> str:
    """1234.5 -> '1.234,5'. None vira '—'."""
    if valor is None:
        return '—'
    texto = f'{valor:,.{casas}f}'
    return texto.replace(',', '\x00').replace('.', ',').replace('\x00', '.')


def inteiro(valor) -> str:
    return numero(valor, 0)


def pontos(valor, casas: int = 1) -> str:
    return f'{numero(valor, casas)} pontos'


def com_sinal(valor, casas: int = 1) -> str:
    """Diferença sempre com sinal explícito: '+19,4' ou '−19,4'."""
    sinal = '+' if valor >= 0 else MENOS
    return f'{sinal}{numero(abs(valor), casas)}'


def percentual(valor, casas: int = 0) -> str:
    return f'{numero(valor, casas)}%'


def ordinal(valor) -> str:
    return f'{inteiro(valor)}º'