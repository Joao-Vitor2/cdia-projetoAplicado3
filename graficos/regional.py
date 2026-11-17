"""Comparações regionais: as 27 UFs e os municípios da UF, sempre contra a nota do usuário.

Só desenha: as médias vêm prontas de tabela.medias_por_uf / medias_por_municipio.
A UF e o município do usuário são destacados em verde, marcando onde o candidato está.
"""

import altair as alt
import polars as pl

import formatacao as fmt
from graficos.paleta import (
    COR_LOCALIZACAO,
    COR_REFERENCIA,
    COR_TEXTO,
    COR_USUARIO,
)

# altura de cada linha dos gráficos horizontais, em pixels
ALTURA_LINHA_UF = 24
ALTURA_LINHA_MUNICIPIO = 30


def _eixo_x(titulo: str) -> alt.Axis:
    return alt.Axis(labelColor=COR_TEXTO, titleColor=COR_TEXTO, titleFontSize=11, gridColor='#2a2f3a')


def _eixo_y(limite: int = 400) -> alt.Axis:
    return alt.Axis(
        labelColor=COR_TEXTO, labelFontSize=12, labelLimit=limite,
        ticks=False, domain=False, titleColor=COR_TEXTO, gridColor='#2a2f3a',
    )


def _cor_da_diferenca(diferenca: float, destaque: bool) -> str:
    """Verde para a UF/município do candidato; azul se ele tirou mais; vermelho se tirou menos."""
    if destaque:
        return COR_LOCALIZACAO
    return COR_REFERENCIA if diferenca > 0 else COR_USUARIO


def _barras_divergentes(
    dados: pl.DataFrame,
    titulo_eixo: str,
    tooltips: list[alt.Tooltip],
    altura_linha: int,
    limite_rotulo: int = 400,
) -> alt.LayerChart:
    """Barras horizontais em torno da nota do usuário (zero), com rótulo na cor da barra.

    Espera em `dados`: ROTULO, MEDIA, DIFERENCA, DIFERENCA_TEXTO, COR e DESTAQUE (bool).
    """
    # escala centrada em 0 (a nota do usuário), com folga para os rótulos
    diffs = dados['DIFERENCA'].to_list()
    max_abs = max((abs(diferenca) for diferenca in diffs), default=0) or 100.0
    limite = max(max_abs * 1.3, 15.0)
    escala = alt.Scale(domain=[-limite, limite], nice=False)
    ordem = list(dados.sort('MEDIA', descending=True)['ROTULO'])

    base = alt.Chart(dados).encode(
        y=alt.Y('ROTULO:N', title=None, sort=ordem, axis=_eixo_y(limite=limite_rotulo)),
        x=alt.X(
            'DIFERENCA:Q',
            title=titulo_eixo,
            scale=escala,
            axis=_eixo_x(titulo_eixo),
        ),
    )

    barras = base.mark_bar(size=15, cornerRadiusEnd=3).encode(
        color=alt.Color('COR:N', scale=None, legend=None),
        tooltip=tooltips,
    )

    # contorno claro marcando a UF/município do usuário (a cor sozinha não basta)
    destaque = (
        alt.Chart(dados.filter(pl.col('DESTAQUE')))
        .mark_bar(size=21, fill=None, stroke='#ffffff', strokeWidth=1.5)
        .encode(
            x=alt.X('DIFERENCA:Q', scale=escala),
            y=alt.Y('ROTULO:N', sort=ordem),
        )
    )

    # rótulo do valor no fim da barra, na mesma cor da barra (azul, vermelho ou verde)
    rotulos_positivos = (
        alt.Chart(dados.filter(pl.col('DIFERENCA') >= 0))
        .mark_text(align='left', dx=4, fontSize=10)
        .encode(
            x=alt.X('DIFERENCA:Q', scale=escala),
            y=alt.Y('ROTULO:N', sort=ordem),
            text='DIFERENCA_TEXTO:N',
            color=alt.Color('COR:N', scale=None, legend=None),
        )
    )
    rotulos_negativos = (
        alt.Chart(dados.filter(pl.col('DIFERENCA') < 0))
        .mark_text(align='right', dx=-4, fontSize=10)
        .encode(
            x=alt.X('DIFERENCA:Q', scale=escala),
            y=alt.Y('ROTULO:N', sort=ordem),
            text='DIFERENCA_TEXTO:N',
            color=alt.Color('COR:N', scale=None, legend=None),
        )
    )
    # linha central: a nota do usuário (zero da escala)
    referencia_zero = (
        alt.Chart(pl.DataFrame({'X': [0.0]}))
        .mark_rule(color=COR_TEXTO, strokeWidth=2, strokeDash=[4, 4])
        .encode(x=alt.X('X:Q', scale=escala))
    )

    return (
        alt.layer(barras, destaque, rotulos_positivos, rotulos_negativos, referencia_zero)
        .properties(height=dados.height * altura_linha + 40)
    )


def grafico_ufs(
    df_medias_uf: pl.DataFrame,
    area: str,
    uf_usuario: str,
    nota_usuario: float,
) -> alt.LayerChart:
    """Barras divergentes: compara a nota do usuário com a média de cada UF.

    - Azul (direita): a UF tem média menor que a nota do usuário (ele tirou mais)
    - Vermelho (esquerda): a UF tem média maior que a nota do usuário (ele tirou menos)
    - UF do usuário: verde + contorno branco, marcando onde o candidato está
    """
    df = (
        df_medias_uf
        .filter((pl.col('AREA') == area) & pl.col('MEDIA').is_not_null())
        .sort('MEDIA')
    )

    dados = pl.DataFrame([
        {
            'ROTULO': linha['NO_UF'],
            'NO_UF': linha['NO_UF'],
            'MEDIA': linha['MEDIA'],
            'DIFERENCA': round(nota_usuario - linha['MEDIA'], 1),
            'MEDIA_TEXTO': fmt.numero(linha['MEDIA']),
            'DIFERENCA_TEXTO': fmt.com_sinal(nota_usuario - linha['MEDIA']),
            'CANDIDATOS_TEXTO': fmt.inteiro(linha['CANDIDATOS']),
            'DESTAQUE': linha['NO_UF'] == uf_usuario,
            'COR': _cor_da_diferenca(
                nota_usuario - linha['MEDIA'], linha['NO_UF'] == uf_usuario,
            ),
        }
        for linha in df.iter_rows(named=True)
    ])

    return _barras_divergentes(
        dados,
        titulo_eixo='Diferença: sua nota − média da UF (pontos)',
        tooltips=[
            alt.Tooltip('NO_UF:N', title='UF'),
            alt.Tooltip('MEDIA_TEXTO:N', title='Média'),
            alt.Tooltip('DIFERENCA_TEXTO:N', title='Diferença: você − UF'),
            alt.Tooltip('CANDIDATOS_TEXTO:N', title='Candidatos'),
        ],
        altura_linha=ALTURA_LINHA_UF,
    )


def grafico_municipios(
    df_medias_municipio: pl.DataFrame,
    area: str,
    co_municipio: int,
    nota_usuario: float,
    top: int = 10,
) -> alt.LayerChart | None:
    """Mesmo formato das UFs: top 10 municípios da UF + o município do usuário.

    Só entram municípios com pelo menos 30 candidatos na área (mesmo corte do ranking).
    Devolve None quando nenhum município da UF atinge o mínimo.
    """
    df = df_medias_municipio.filter((pl.col('AREA') == area) & pl.col('ELEGIVEL') & pl.col('MEDIA').is_not_null())
    if df.is_empty():
        return None

    melhores = df.sort('MEDIA', descending=True).head(top)
    do_usuario = df.filter(pl.col('CO_MUNICIPIO_REF') == co_municipio)
    if do_usuario.height and do_usuario['CO_MUNICIPIO_REF'][0] not in melhores['CO_MUNICIPIO_REF'].to_list():
        melhores = pl.concat([melhores, do_usuario])

    dados = pl.DataFrame([
        {
            'ROTULO': linha['MUNICIPIO'],
            'MUNICIPIO': linha['MUNICIPIO'],
            'MEDIA': linha['MEDIA'],
            'DIFERENCA': round(nota_usuario - linha['MEDIA'], 1),
            'MEDIA_TEXTO': fmt.numero(linha['MEDIA']),
            'DIFERENCA_TEXTO': fmt.com_sinal(nota_usuario - linha['MEDIA']),
            'POSICAO_TEXTO': f'{fmt.ordinal(linha["RANK"])} de {fmt.inteiro(linha["TOTAL_ELEGIVEIS"])}',
            'CANDIDATOS_TEXTO': fmt.inteiro(linha['CANDIDATOS']),
            'DESTAQUE': linha['CO_MUNICIPIO_REF'] == co_municipio,
            'COR': _cor_da_diferenca(
                nota_usuario - linha['MEDIA'], linha['CO_MUNICIPIO_REF'] == co_municipio,
            ),
        }
        for linha in melhores.iter_rows(named=True)
    ])

    return _barras_divergentes(
        dados,
        titulo_eixo='Diferença: sua nota − média do município (pontos)',
        tooltips=[
            alt.Tooltip('MUNICIPIO:N', title='Município'),
            alt.Tooltip('MEDIA_TEXTO:N', title='Média'),
            alt.Tooltip('DIFERENCA_TEXTO:N', title='Diferença: você − município'),
            alt.Tooltip('POSICAO_TEXTO:N', title='Posição na UF'),
            alt.Tooltip('CANDIDATOS_TEXTO:N', title='Candidatos'),
        ],
        altura_linha=ALTURA_LINHA_MUNICIPIO,
        limite_rotulo=260,
    )
