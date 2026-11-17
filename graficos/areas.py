"""Desempenho do candidato por área: diferença em pontos para a média do grupo INSE.

Usado no bloco opcional "Informar as demais áreas": mostra de relance onde o candidato
é mais forte e onde precisa melhorar. Só desenha; as médias do grupo vêm de main.analisar.
"""

import altair as alt
import polars as pl

from graficos.paleta import COR_CONTEXTO, COR_NEGATIVO, COR_POSITIVO, COR_TEXTO


def grafico_areas(df_diferencas: pl.DataFrame) -> alt.LayerChart:
    """Barras horizontais centradas em zero, ordenadas da maior para a menor diferença."""
    dados = df_diferencas.sort('DIFERENCA', descending=True)
    ordem = list(dados['AREA'])
    limite = max(abs(dados['DIFERENCA'].min()), abs(dados['DIFERENCA'].max())) * 1.35
    limite = max(limite, 10.0)
    escala = alt.Scale(domain=[-limite, limite], nice=False)

    base = alt.Chart(dados).encode(
        y=alt.Y(
            'AREA:N', title=None, sort=ordem,
            axis=alt.Axis(labelColor=COR_TEXTO, labelFontSize=12, ticks=False, domain=False,
                          labelLimit=260, titleColor=COR_TEXTO),
        ),
        x=alt.X(
            'DIFERENCA:Q',
            title='Diferença para a média do seu grupo (pontos)',
            scale=escala,
            axis=alt.Axis(labelColor=COR_TEXTO, titleColor=COR_TEXTO, titleFontSize=11,
                          gridColor='#2a2f3a', format='.0f'),
        ),
    )

    barras = base.mark_bar(size=20, cornerRadiusEnd=3).encode(
        color=alt.condition(
            alt.datum.DIFERENCA >= 0,
            alt.value(COR_POSITIVO),
            alt.value(COR_NEGATIVO),
        ),
        tooltip=[
            alt.Tooltip('AREA:N', title='Área'),
            alt.Tooltip('DIFERENCA_TEXTO:N', title='Diferença'),
            alt.Tooltip('MEDIA_TEXTO:N', title='Média do grupo'),
        ],
    )
    rotulos_positivos = (
        alt.Chart(dados.filter(pl.col('DIFERENCA') >= 0))
        .mark_text(align='left', dx=5, fontSize=11, color=COR_TEXTO)
        .encode(x=alt.X('DIFERENCA:Q', scale=escala), y=alt.Y('AREA:N', sort=ordem), text='DIFERENCA_TEXTO:N')
    )
    rotulos_negativos = (
        alt.Chart(dados.filter(pl.col('DIFERENCA') < 0))
        .mark_text(align='right', dx=-5, fontSize=11, color=COR_TEXTO)
        .encode(x=alt.X('DIFERENCA:Q', scale=escala), y=alt.Y('AREA:N', sort=ordem), text='DIFERENCA_TEXTO:N')
    )
    referencia_zero = (
        alt.Chart(pl.DataFrame({'X': [0.0]}))
        .mark_rule(color=COR_CONTEXTO, strokeWidth=1)
        .encode(x=alt.X('X:Q', scale=escala))
    )

    return alt.layer(barras, rotulos_positivos, rotulos_negativos, referencia_zero).properties(
        height=dados.height * 42 + 30,
    )