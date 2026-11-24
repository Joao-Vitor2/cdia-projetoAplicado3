"""Histograma da distribuição de notas, com a posição do candidato em destaque.

Só desenha: os bins, a CDF e as estatísticas vêm prontos de tabela.distribuicao_escopos
(via main.analisar). Um ponto por faixa de 10 pontos, então o gráfico nunca recebe
milhões de linhas.
"""

import altair as alt
import polars as pl

import formatacao as fmt
from graficos.paleta import COR_CONTEXTO, COR_GRADE, COR_MEDIANA, COR_REFERENCIA, COR_TEXTO, COR_USUARIO

ALTURA = 340


def _inicio_visivel(bins: pl.DataFrame, percentual_corte: float = 1.0) -> int:
    """Primeira faixa que deixa `percentual_corte`% dos candidatos para trás.

    As notas muito baixas (menos de 1% dos candidatos) ficam fora do eixo para o
    histograma não virar uma parede de barras vazias perto do zero.
    """
    acumulado = 0.0
    for inicio, percentual in bins.select('INICIO', 'PERCENTUAL').iter_rows():
        acumulado += percentual
        if acumulado >= percentual_corte:
            return int(inicio)
    return int(bins['INICIO'].min())


def _rotulo_faixa(inicio: int, fim: int) -> str:
    return f'{fmt.inteiro(inicio)} a {fmt.inteiro(fim)} pontos'


def grafico_histograma(dados: dict, nota: float, area: str) -> alt.LayerChart:
    """Barras em % de candidatos, faixa P25–P75, média/mediana e a linha da nota do usuário."""
    bins = dados['bins']
    estatisticas = dados['estatisticas']

    inicio = _inicio_visivel(bins)
    fim = int(bins['FIM'].max())
    altura_max = float(bins['PERCENTUAL'].max())
    escala_x = alt.Scale(domain=[inicio, fim], nice=False)

    visiveis = (
        bins
        .filter(pl.col('INICIO') >= inicio)
        .with_columns(
            pl.when(pl.col('INICIO') < nota).then(pl.lit('Abaixo de você')).otherwise(pl.lit('Acima de você')).alias('LADO'),
        )
    )
    visiveis = pl.DataFrame([
        {
            'INICIO': linha['INICIO'],
            'FIM': linha['FIM'],
            'PERCENTUAL': linha['PERCENTUAL'],
            'LADO': linha['LADO'],
            'FAIXA': _rotulo_faixa(linha['INICIO'], linha['FIM']),
            'PERCENTUAL_TEXTO': fmt.percentual(linha['PERCENTUAL'], 1),
            'CANDIDATOS_TEXTO': fmt.inteiro(linha['CANDIDATOS']),
        }
        for linha in visiveis.iter_rows(named=True)
    ])

    base = alt.Chart(visiveis).encode(
        x=alt.X(
            'INICIO:Q', title=f'Nota em {area}',
            scale=escala_x,
            axis=alt.Axis(labelColor=COR_TEXTO, titleColor=COR_TEXTO, gridColor=COR_GRADE),
        ),
        x2='FIM:Q',
        y=alt.Y(
            'PERCENTUAL:Q', title='% de candidatos',
            scale=alt.Scale(domain=[0, altura_max * 1.24], nice=False),
            axis=alt.Axis(labelColor=COR_TEXTO, titleColor=COR_TEXTO, gridColor=COR_GRADE),
        ),
    )

    barras = base.mark_bar().encode(
        color=alt.Color(
            'LADO:N',
            scale=alt.Scale(domain=['Abaixo de você', 'Acima de você'], range=[COR_USUARIO, COR_REFERENCIA]),
            legend=None,
        ),
        opacity=alt.value(0.6),
        tooltip=[
            alt.Tooltip('FAIXA:N', title='Notas'),
            alt.Tooltip('PERCENTUAL_TEXTO:N', title='Fatia dos candidatos'),
            alt.Tooltip('CANDIDATOS_TEXTO:N', title='Candidatos'),
        ],
    )

    # metade central dos candidatos (P25 a P75)
    faixa = (
        alt.Chart(pl.DataFrame({
            'INICIO': [estatisticas['p25']],
            'FIM': [estatisticas['p75']],
            'RÓTULO': ['Metade central (P25–P75)'],
        }))
        .mark_rect(opacity=0.16)
        .encode(
            x=alt.X('INICIO:Q', scale=escala_x),
            x2='FIM:Q',
            color=alt.Color(
                'RÓTULO:N',
                scale=alt.Scale(domain=['Metade central (P25–P75)'], range=[COR_CONTEXTO]),
                legend=alt.Legend(title=None, orient='top', labelColor=COR_TEXTO),
            ),
        )
    )

    # média e mediana: linhas pontilhadas, com legenda
    linhas_referencia = (
        alt.Chart(pl.DataFrame({
            'RÓTULO': ['Média', 'Mediana'],
            'VALOR': [estatisticas['media'], estatisticas['mediana']],
            'VALOR_TEXTO': [fmt.numero(estatisticas['media']), fmt.numero(estatisticas['mediana'])],
        }))
        .mark_rule(strokeDash=[5, 4], strokeWidth=1.5)
        .encode(
            x=alt.X('VALOR:Q', scale=escala_x),
            color=alt.Color(
                'RÓTULO:N',
                scale=alt.Scale(domain=['Média', 'Mediana'], range=[COR_CONTEXTO, COR_MEDIANA]),
                legend=alt.Legend(title=None, orient='top', labelColor=COR_TEXTO),
            ),
            tooltip=[
                alt.Tooltip('RÓTULO:N', title=''),
                alt.Tooltip('VALOR_TEXTO:N', title='Nota'),
            ],
        )
    )

    # a nota do usuário: linha cheia na cor de destaque
    linha_usuario = (
        alt.Chart(pl.DataFrame({'VALOR': [nota]}))
        .mark_rule(color=COR_USUARIO, strokeWidth=3)
        .encode(x=alt.X('VALOR:Q', scale=escala_x))
    )
    rotulo_usuario = (
        alt.Chart(pl.DataFrame({
            'X': [nota],
            'Y': [altura_max * 1.15],
            'TEXTO': [f'Você: {fmt.numero(nota, 0)}'],
        }))
        .mark_text(align='left', dx=6, color=COR_USUARIO, fontSize=12, fontWeight='bold')
        .encode(x=alt.X('X:Q', scale=escala_x), y=alt.Y('Y:Q'), text='TEXTO:N')
    )

    return (
        alt.layer(faixa, barras, linhas_referencia, linha_usuario, rotulo_usuario)
        .resolve_scale(color='independent')
        .properties(height=ALTURA)
    )