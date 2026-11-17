"""Frases do dashboard em português claro.

Tudo que é texto explicativo fica aqui, separado do desenho dos gráficos: assim o app só
costura os blocos e as frases não se repetem nem divergem entre si.
"""

import polars as pl

import formatacao as fmt

# diferença (em pontos) que ainda conta como "na média"
TOLERANCIA_MEDIA = 15.0

# até onde a diferença é "um pouco"; acima disso é "bem"
DIFERENCA_PEQUENA = 45.0
DIFERENCA_GRANDE = 90.0


def qualificar_diferenca(diferenca: float) -> str:
    """Traduz a diferença em pontos para uma expressão gradual ('bem acima', 'um pouco abaixo'...)."""
    tamanho = abs(diferenca)
    if tamanho <= TOLERANCIA_MEDIA:
        return 'na média'
    if tamanho <= DIFERENCA_PEQUENA:
        grau = 'um pouco'
    elif tamanho <= DIFERENCA_GRANDE:
        grau = ''
    else:
        grau = 'bem'

    sentido = 'acima' if diferenca > 0 else 'abaixo'
    return f'{grau} {sentido} da média'.strip()


def frase_desempenho(area: str, posicao: dict, percentil_brasil: float | None) -> str:
    """Frase única que resume o resultado sem jargão."""
    diferenca = posicao['diferenca_absoluta']
    qualificacao = qualificar_diferenca(diferenca)
    media = fmt.numero(posicao['media_grupo'])

    if qualificacao == 'na média':
        inicio = f'Sua nota em {area} está na média dos candidatos com perfil socioeconômico parecido ({media} pontos)'
    else:
        inicio = (
            f'Sua nota em {area} ficou {qualificacao} dos candidatos '
            f'com perfil socioeconômico parecido ({media} pontos)'
        )

    if percentil_brasil is None:
        return f'{inicio}.'
    return f'{inicio}, e você está à frente de {fmt.percentual(percentil_brasil)} dos candidatos do Brasil.'


def legenda_inse(fonte_nivel: str) -> str:
    """Explica o que é o grupo INSE e de onde veio o nível estimado."""
    origem = 'pela sua escola' if fonte_nivel == 'escola' else 'pelo seu município'
    return (
        'Grupo INSE: candidatos de municípios com nível socioeconômico parecido, '
        f'medido pelo Inep. O seu nível foi estimado {origem}.'
    )


def frase_escopo(estatisticas: dict, nota: float, percentil: float, escopo: str, area: str) -> str:
    """Resumo em texto do histograma, no escopo escolhido (grupo, UF ou Brasil)."""
    onde = {
        'grupo': 'do seu grupo INSE',
        'uf': 'da sua UF',
        'brasil': 'do Brasil',
    }[escopo]

    return (
        f'Entre os {fmt.inteiro(estatisticas["candidatos"])} candidatos {onde} em {area}, '
        f'{fmt.percentual(percentil)} ficaram abaixo de {fmt.pontos(nota, 0)}. '
        f'A metade central está entre {fmt.numero(estatisticas["p25"], 0)} e '
        f'{fmt.numero(estatisticas["p75"], 0)} pontos; a média é '
        f'{fmt.numero(estatisticas["media"])}.'
    )


def frase_regional_uf(df_ufs: pl.DataFrame, uf: str, area: str, media_brasil: float | None) -> str:
    """Compara a UF do usuário com as demais e com a média nacional, com a posição no ranking."""
    linha = df_ufs.filter(pl.col('NO_UF') == uf)
    if linha.height == 0 or media_brasil is None:
        return f'Não há candidatos suficientes em {area} para comparar as UFs.'

    media = linha['MEDIA'][0]
    posicao = int((df_ufs['MEDIA'] > media).sum()) + 1
    total = df_ufs.height
    diferenca = media - media_brasil

    if posicao == 1:
        ranking = 'a maior média'
    elif posicao == total:
        ranking = 'a menor média'
    else:
        ranking = f'a {fmt.ordinal(posicao)} maior média'

    if abs(diferenca) < 0.05:
        comparacao = 'praticamente igual à média nacional'
    else:
        comparacao = f'{fmt.com_sinal(diferenca)} pontos em relação à média nacional'

    return (
        f'{uf} tem {ranking} em {area} entre as {total} UFs: '
        f'{fmt.pontos(media)}, {comparacao} ({fmt.numero(media_brasil)}).'
    )


def frase_municipio(linha: pl.DataFrame, uf: str, area: str, media_uf: float | None) -> str:
    """Texto do município do usuário: posição no ranking e distância para a média da UF."""
    if linha.height == 0:
        return f'Não há dados do seu município em {area}.'

    dados = linha.row(0, named=True)
    if not dados['ELEGIVEL']:
        return (
            f'Seu município tem apenas {fmt.inteiro(dados["CANDIDATOS"])} candidatos em {area} '
            f'(o mínimo para entrar no ranking é 30), por isso não aparece no gráfico.'
        )

    texto = (
        f'{dados["MUNICIPIO"]} ocupa o {fmt.ordinal(dados["RANK"])} lugar entre os '
        f'{fmt.inteiro(dados["TOTAL_ELEGIVEIS"])} municípios de {uf} com pelo menos 30 candidatos: '
        f'{fmt.pontos(dados["MEDIA"])}'
    )
    if media_uf is not None:
        texto += f', {fmt.com_sinal(dados["MEDIA"] - media_uf)} pontos em relação à média da UF ({fmt.numero(media_uf)})'
    return f'{texto}.'


def frase_perfil(perfil: dict, nota: float) -> str:
    """Resumo do perfil socioeconômico/demográfico informado no formulário."""
    if perfil.get('media') is None:
        return (
            f'Há apenas {fmt.inteiro(perfil.get("candidatos", 0))} candidatos com esse perfil, '
            'poucos para uma comparação confiável.'
        )

    return (
        f'{fmt.inteiro(perfil["candidatos"])} candidatos com perfil parecido '
        f'(idade, sexo, cor/raça, nacionalidade e conclusão do ensino médio): '
        f'média de {fmt.numero(perfil["media"])} pontos, '
        f'você {fmt.com_sinal(nota - perfil["media"])} em relação a eles.'
    )