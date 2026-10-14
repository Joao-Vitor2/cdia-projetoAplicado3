"""Gráficos do dashboard.

Cada módulo tem o desenho de um gráfico (Altair/Streamlit) e, quando faz sentido,
uma frase que explica o resultado. O cálculo mora em tabela.py; aqui só se desenha.
"""

from graficos import percentil

__all__ = ['percentil']
