"""Percentil do candidato em três escalas (grupo INSE, UF e Brasil) — versão compacta.

Só desenha; os percentis vêm prontos de tabela.calcular_percentis (via main.analisar).
"""

import altair as alt
import polars as pl

import formatacao as fmt
from graficos.paleta import COR_REFERENCIA, COR_TEXTO


def grafico_percentis(df_percentis: pl.DataFrame) -> alt.LayerChart:
    dados = pl.DataFrame([
        {
            'ESCALA': linha['ESCALA'],
            'PERCENTIL': linha['PERCENTIL'],
            'ROTULO': f'{fmt.ordinal(linha["PERCENTIL"])} · {fmt.inteiro(linha["CANDIDATOS"])} candidatos',
        }
        for linha in df_percentis.filter(pl.col('PERCENTIL').is_not_null()).iter_rows(named=True)
    ])
    ordem = list(dados['ESCALA'])

    base = alt.Chart(dados).encode(
        y=alt.Y(
            'ESCALA:N', title=None, sort=ordem,
            axis=alt.Axis(labelColor=COR_TEXTO, labelFontSize=11, ticks=False, domain=False,
                          titleColor=COR_TEXTO, gridColor='#2a2f3a'),
        ),
        x=alt.X(
            'PERCENTIL:Q', title=None,
            scale=alt.Scale(domain=[0, 100], nice=False),
            axis=alt.Axis(values=[0, 25, 50, 75, 100], labelColor=COR_TEXTO, gridColor='#2a2f3a'),
        ),
    )

    barras = base.mark_bar(size=16, cornerRadiusEnd=3).encode(
        color=alt.value(COR_REFERENCIA),
        tooltip=[
            alt.Tooltip('ESCALA:N', title='Escala'),
            alt.Tooltip('ROTULO:N', title='Posição'),
        ],
    )
    # rótulo fora da barra quando há espaço; dentro dela quando o percentil passa de 70
    fora = (
        alt.Chart(dados.filter(pl.col('PERCENTIL') < 70))
        .mark_text(align='left', dx=6, fontSize=10, color=COR_TEXTO)
        .encode(x=alt.X('PERCENTIL:Q'), y=alt.Y('ESCALA:N', sort=ordem), text='ROTULO:N')
    )
    dentro = (
        alt.Chart(dados.filter(pl.col('PERCENTIL') >= 70))
        .mark_text(align='right', dx=-6, fontSize=10, color='#ffffff')
        .encode(x=alt.X('PERCENTIL:Q'), y=alt.Y('ESCALA:N', sort=ordem), text='ROTULO:N')
    )

    return alt.layer(barras, fora, dentro).properties(height=110)