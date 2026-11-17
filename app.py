"""Página única: formulário do candidato no topo e dashboard logo abaixo.

Só a interface: o cálculo e a decodificação ficam no main.py, o tratamento no tabela.py,
o desenho dos gráficos em graficos/ e as frases em textos.py.
"""

import math
import sys

import polars as pl
import streamlit as st

import formatacao as fmt
import main
import textos
from graficos import areas, distribuicao, regional

# permite rodar com "python app.py" (ex.: botão Run do VSCode), relançando via "streamlit run"
if __name__ == '__main__' and not st.runtime.exists():
    from streamlit.web import cli as stcli
    sys.argv = ['streamlit', 'run', __file__, *sys.argv[1:]]
    sys.exit(stcli.main())

st.set_page_config(page_title='Enem 2023: Compare seu desempenho', layout='wide')

# rótulo de cada escala de comparação do histograma
ROTULOS_ESCOPO = {
    'grupo': 'Meu grupo INSE',
    'uf': 'Minha UF',
    'brasil': 'Brasil',
}

# rótulo no formulário -> variável do dicionário (as opções vêm do main.opcoes_formulario)
CAMPOS_PERFIL = {
    'sexo': ('Sexo (opcional)', 'TP_SEXO'),
    'cor_raca': ('Cor/raça (opcional)', 'TP_COR_RACA'),
    'nacionalidade': ('Nacionalidade (opcional)', 'TP_NACIONALIDADE'),
    'st_conclusao': ('Situação do Ensino Médio (opcional)', 'TP_ST_CONCLUSAO'),
    'ano_concluiu': ('Ano de conclusão do Ensino Médio (opcional)', 'TP_ANO_CONCLUIU'),
}


# ---------------------------------------------------------------- carregamento (cache do Streamlit)

@st.cache_data(show_spinner=False)
def opcoes_formulario() -> dict:
    return main.opcoes_formulario()


@st.cache_data(show_spinner=False)
def opcoes_municipios(uf: str | None) -> list[str]:
    return main.opcoes_municipios(uf)


@st.cache_data(show_spinner=False)
def comparar(entrada: tuple) -> dict:
    """A entrada chega como tupla de pares (hashable) e vira dict para o main.analisar."""
    return main.analisar(dict(entrada))


# ---------------------------------------------------------------- formulário

def barra_localizacao(opcoes: dict) -> tuple[str | None, str | None, str]:
    """UF, município e escola ficam fora do st.form: a lista de municípios depende da UF."""
    with st.container(border=True):
        st.subheader('Localização')
        coluna_uf, coluna_municipio, coluna_escola = st.columns(3)

        with coluna_uf:
            uf = st.selectbox(
                'Unidade da Federação', opcoes['ufs'], index=None,
                placeholder='Selecione a sua UF',
            )
        with coluna_municipio:
            municipio = st.selectbox(
                'Município', opcoes_municipios(uf), index=None, key='municipio',
                placeholder='Selecione o seu município',
                help='Abra a lista e digite para filtrar pelo nome ou pelo código IBGE. '
                     'Com uma UF escolhida, só aparecem os municípios dela.',
            )
        with coluna_escola:
            co_escola = st.text_input(
                'Código da escola (opcional)', placeholder='Ex.: 35000000',
            )

    return uf, municipio, co_escola


def cartao_nota(opcoes: dict) -> tuple[str, float | None]:
    with st.container(border=True):
        st.subheader('Nota')
        area = st.selectbox('Área de conhecimento', opcoes['areas'])
        nota = st.number_input('Sua nota', min_value=0.0, max_value=1000.0, value=None, step=0.1)
    return area, nota


def cartao_perfil(opcoes: dict) -> tuple[dict, float | None, bool]:
    """Os campos do perfil ficam em duas colunas; o checkbox ocupa a largura do cartão."""
    with st.container(border=True):
        st.subheader('Perfil')
        coluna_esquerda, coluna_direita = st.columns(2)

        with coluna_esquerda:
            idade = st.number_input('Idade', min_value=10, max_value=100, value=None, step=1)

        perfil = {}
        for indice, (campo, (rotulo, variavel)) in enumerate(CAMPOS_PERFIL.items()):
            # a idade já ocupa a primeira linha da coluna da esquerda
            with coluna_direita if indice % 2 == 0 else coluna_esquerda:
                perfil[campo] = st.selectbox(
                    rotulo, opcoes[variavel], index=None, placeholder='Selecione',
                )

        treineiro = st.checkbox('Fiz a prova apenas para treinar (treineiro)')

    return perfil, idade, treineiro


def erros_do_formulario(uf, municipio, nota, co_escola, idade) -> list[str]:
    erros = []
    if uf is None:
        erros.append('Selecione a sua UF.')
    if municipio is None:
        erros.append('Selecione o seu município.')
    if nota is None:
        erros.append('Informe a sua nota.')
    if idade is None:
        erros.append('Informe a sua idade.')
    if co_escola.strip() and not co_escola.strip().isdigit():
        erros.append('O código da escola deve conter apenas números.')
    return erros


def calcular(entrada: dict):
    """Chama o main.analisar e guarda o resultado na sessão; erros de valor viram st.error."""
    try:
        resultado = comparar(tuple(sorted(entrada.items())))
    except ValueError as erro:
        st.error(str(erro))
        return False

    st.session_state.resultado = resultado
    st.session_state.entrada = entrada

    # o dashboard nasce apontando para a área escolhida e sem simulação/notas extras antigas
    st.session_state.area_regional = entrada['area']
    st.session_state.escopo_distribuicao = 'grupo'
    st.session_state.nota_simulada = int(round(entrada['nota']))
    for chave in [chave for chave in st.session_state if chave.startswith('nota_extra_')]:
        del st.session_state[chave]
    return True


def formulario(opcoes: dict):
    with st.expander('Dados do candidato', expanded=st.session_state.resultado is None):
        uf, municipio, co_escola = barra_localizacao(opcoes)

        with st.form('form_candidato'):
            coluna_nota, coluna_perfil = st.columns(2)
            with coluna_nota:
                area, nota = cartao_nota(opcoes)
            with coluna_perfil:
                perfil, idade, treineiro = cartao_perfil(opcoes)

            enviar = st.form_submit_button('Comparar', type='primary', use_container_width=True)

        if not enviar:
            return

        erros = erros_do_formulario(uf, municipio, nota, co_escola, idade)
        for erro in erros:
            st.error(erro)
        if erros:
            return

        entrada = {
            'area': area,
            'nota': nota,
            'uf': uf,
            'municipio': municipio,
            'co_escola': int(co_escola) if co_escola.strip() else None,
            'idade': idade,
            **perfil,
            'treineiro': treineiro,
        }

        with st.spinner('Comparando com os microdados do Enem...'):
            if not calcular(entrada):
                return
        # refaz a página já com o resultado: o expander recolhe e o dashboard sobe
        st.rerun()


# ---------------------------------------------------------------- dashboard

def bloco_resumo(resultado: dict):
    """1. Como o candidato se saiu: quatro números-chave, uma frase e o percentil nas 3 escalas."""
    posicao = resultado['posicao']
    percentis = resultado['percentis']
    percentil_brasil = percentis.filter(pl.col('ESCALA') == 'Brasil')['PERCENTIL'].drop_nulls()
    percentil_brasil = percentil_brasil[0] if percentil_brasil.len() else None

    st.subheader('Como você se saiu')
    coluna_nota, coluna_percentil, coluna_diferenca, coluna_posicao = st.columns(4)
    coluna_nota.metric(
        'Sua nota', fmt.numero(posicao['nota_usuario']),
        help=f'{resultado["area"]} · Enem {resultado["ano"]}',
    )
    coluna_percentil.metric(
        'Percentil no seu grupo', fmt.ordinal(posicao['percentil_usuario']),
        help=f'Entre os {fmt.inteiro(posicao["tamanho_grupo"])} candidatos do seu grupo INSE.',
    )
    coluna_diferenca.metric(
        'Diferença para a média do grupo',
        f'{fmt.com_sinal(posicao["diferenca_absoluta"])} pontos',
        delta=f'média do grupo: {fmt.numero(posicao["media_grupo"])}', delta_color='off',
        help='Sinal positivo: você tirou mais que a média do grupo. Sinal negativo: tirou menos.',
    )
    coluna_posicao.metric(
        'Posição estimada', f'à frente de {fmt.percentual(posicao["percentil_usuario"])}',
        help='Percentual de candidatos do seu grupo com nota menor que a sua.',
    )

    st.markdown(textos.frase_desempenho(resultado['area'], posicao, percentil_brasil))
    st.caption(textos.legenda_inse(resultado['fonte_nivel']))

    st.caption('Percentil: 0 = pior nota, 100 = melhor')

    # Helper function para cards laterais
    def render_card(label, abaixo, total, percentil):
        abaixo_f = fmt.inteiro(abaixo)
        total_f = fmt.inteiro(total)
        html = '<div style="flex: 1; background: #1a2027; border: 1px solid #30363d; border-radius: 8px; padding: 16px; color: #e6e6e6; min-height: 80px; display: flex; flex-direction: column; justify-content: space-between;">'
        html += '<div style="font-size: 0.8em; color: #7b8794; margin-bottom: 8px;">' + label + '</div>'
        html += '<div style="font-size: 1.8em; font-weight: bold; color: #e6e6e6; margin-bottom: 4px;">' + abaixo_f + '</div>'
        html += '<div style="font-size: 0.9em; color: #7b8794;">de ' + total_f + ' candidatos</div>'
        html += '<div style="background: #4c78a8; color: white; font-size: 0.9em; font-weight: bold; padding: 2px 8px; border-radius: 4px; margin-top: 4px;">' + str(int(percentil)) + 'º percentil</div>'
        html += '</div>'
        return html

    col1, col2, col3 = st.columns(3)

    # Card 1: Seu grupo INSE
    total_grupo = resultado['distribuicao_escopos']['grupo']['estatisticas']['candidatos']
    p_grupo = percentis.filter(pl.col('ESCALA') == 'Seu grupo INSE')['PERCENTIL'].item()
    ab_grupo = round(p_grupo / 100 * total_grupo)
    with col1:
        st.markdown(render_card('Seu grupo INSE', ab_grupo, total_grupo, p_grupo), unsafe_allow_html=True)

    # Card 2: Sua UF
    total_uf = resultado['distribuicao_escopos']['uf']['estatisticas']['candidatos']
    p_uf = percentis.filter(pl.col('ESCALA') == 'Sua UF')['PERCENTIL'].item()
    ab_uf = round(p_uf / 100 * total_uf)
    with col2:
        st.markdown(render_card('Sua UF', ab_uf, total_uf, p_uf), unsafe_allow_html=True)

    # Card 3: Brasil
    total_brasil = resultado['distribuicao_escopos']['brasil']['estatisticas']['candidatos']
    p_brasil = percentis.filter(pl.col('ESCALA') == 'Brasil')['PERCENTIL'].item()
    ab_brasil = round(p_brasil / 100 * total_brasil)
    with col3:
        st.markdown(render_card('Brasil', ab_brasil, total_brasil, p_brasil), unsafe_allow_html=True)


def bloco_distribuicao(resultado: dict):
    """2. Onde a nota cai na distribuição, no escopo escolhido + bloco opcional por área."""
    st.divider()
    st.subheader('Onde você está na distribuição')
    st.caption(
        'Cada barra é a fatia de candidatos com notas naquela faixa. A linha vermelha é a nota '
        'simulada: as barras vermelhas são quem tirou menos que você e as azuis, quem tirou mais. '
        'A faixa sombreada é a metade central dos candidatos (P25 a P75).'
    )

    escopos = resultado['distribuicao_escopos']
    opcoes = [chave for chave in ('grupo', 'uf', 'brasil') if chave in escopos]
    escopo = st.segmented_control(
        'Comparar com', options=opcoes, format_func=lambda chave: ROTULOS_ESCOPO[chave],
        key='escopo_distribuicao', label_visibility='collapsed',
    )
    escopo = escopo if escopo in escopos else opcoes[0]

    dados = escopos[escopo]
    nota = st.session_state.get('nota_simulada', int(round(resultado['posicao']['nota_usuario'])))
    percentil = main.percentil_estimado(escopos, escopo, nota)
    st.markdown(textos.frase_escopo(dados['estatisticas'], nota, percentil, escopo, resultado['area']))
    st.altair_chart(
        distribuicao.grafico_histograma(dados, nota, resultado['area']),
        width='stretch',
    )

    bloco_areas_opcionais(resultado)


def bloco_areas_opcionais(resultado: dict):
    """Bloco opcional: notas das outras áreas para ver o ponto forte e o ponto a melhorar."""
    outras = [area for area in main.AREAS_NOTA if area != resultado['area']]

    with st.expander('Informar as demais áreas (opcional)'):
        st.caption(
            'Preencha as notas que você teve nas outras áreas para comparar seu desempenho '
            'com a média do seu grupo INSE em cada uma.'
        )
        colunas = st.columns(2)
        notas = {}
        for indice, area in enumerate(outras):
            with colunas[indice % 2]:
                valor = st.number_input(
                    area, min_value=0.0, max_value=1000.0, value=None, step=0.1,
                    key=f'nota_extra_{indice}',
                )
            if valor is not None:
                notas[area] = valor

    if not notas:
        return

    medias = resultado['media_por_area']
    linhas = []
    for area, nota in notas.items():
        media = medias.get(area)
        if media is None:
            continue
        linhas.append({
            'AREA': area,
            'DIFERENCA': round(nota - media, 1),
            'DIFERENCA_TEXTO': fmt.com_sinal(nota - media),
            'MEDIA_TEXTO': fmt.numero(media),
        })
    if not linhas:
        st.info('Não há média do seu grupo para as áreas informadas.')
        return

    dados = pl.DataFrame(linhas)
    st.markdown('**Seu desempenho por área**')
    st.caption('Diferença em pontos para a média do seu grupo INSE. Barras para a direita: você foi melhor.')
    st.altair_chart(areas.grafico_areas(dados), width='stretch')

    mais_forte = dados.sort('DIFERENCA', descending=True).row(0, named=True)
    mais_fraca = dados.sort('DIFERENCA').row(0, named=True)
    st.caption(
        f'Ponto mais forte: {mais_forte["AREA"]} ({mais_forte["DIFERENCA_TEXTO"]} pontos). '
        f'Ponto a melhorar: {mais_fraca["AREA"]} ({mais_fraca["DIFERENCA_TEXTO"]} pontos).'
    )


def bloco_metas(resultado: dict):
    """3. Quanto falta para P50/P75/P90 e o simulador de nota (só consulta a CDF já calculada)."""
    st.divider()
    st.subheader('Quanto falta para chegar lá')
    st.caption(
        'Metas dentro do seu grupo INSE: o P50 é a nota que deixa metade do grupo atrás; '
        'o P75 e o P90 são metas mais altas.'
    )

    dados = resultado['distribuicao_escopos'].get('grupo')
    if dados is None:
        st.info('Não há candidatos suficientes no seu grupo para calcular metas.')
        return

    nota = resultado['posicao']['nota_usuario']
    metas = (
        ('Metade do grupo (P50)', 'p50'),
        ('Top 25% (P75)', 'p75'),
        ('Top 10% (P90)', 'p90'),
    )
    colunas = st.columns(3)
    for coluna, (rotulo, chave) in zip(colunas, metas):
        alvo = dados['quantis'][chave]
        diferenca = nota - alvo
        if diferenca >= 0:
            delta = f'você já superou em {fmt.pontos(diferenca, 0)}'
        else:
            delta = f'faltam {fmt.pontos(-diferenca, 0)}'
        coluna.metric(
            rotulo, fmt.numero(alvo, 0), delta=delta, delta_color='off',
            help=f'Nota de corte do {chave.upper()} entre os candidatos do seu grupo INSE.',
        )

    est = dados['estatisticas']
    minimo = int(min(math.floor(est['minimo']), math.floor(nota)))
    maximo = int(max(math.ceil(est['maximo']), math.ceil(nota)))

    st.markdown('**E se eu tirasse...?**')
    nota_simulada = st.slider(
        'Nota simulada', min_value=minimo, max_value=maximo, step=1,
        key='nota_simulada', label_visibility='collapsed',
    )
    percentil = main.percentil_estimado(resultado['distribuicao_escopos'], 'grupo', nota_simulada)
    st.caption(
        f'Com {fmt.pontos(nota_simulada, 0)}, você ficaria à frente de '
        f'{fmt.percentual(percentil)} do seu grupo INSE '
        f'({fmt.inteiro(est["candidatos"])} candidatos). '
        'O gráfico da seção anterior acompanha a simulação.'
    )


def bloco_regional(resultado: dict):
    """4. Comparação regional: UFs contra o Brasil e municípios da UF do usuário."""
    st.divider()
    st.subheader('Como a sua região se compara')
    st.caption(
        'As barras comparam a sua nota com a média de cada estado (ou município): à direita, onde '
        'você tirou mais; à esquerda, onde tirou menos. Sua UF e seu município aparecem em verde. '
        'Nos municípios, só entram os que têm pelo menos 30 candidatos na área.'
    )

    # o seletor nasce na área usada no formulário, mas só redesenha o bloco ao mudar
    if st.session_state.get('area_regional') not in main.AREAS_NOTA:
        st.session_state.area_regional = resultado['area']
    area = st.selectbox('Área', list(main.AREAS_NOTA), key='area_regional')

    media_brasil = resultado['medias_brasil'].get(area)
    df_ufs = resultado['medias_uf'].filter(
        (pl.col('AREA') == area) & pl.col('MEDIA').is_not_null() & (pl.col('CANDIDATOS') >= 30),
    )
    st.markdown(textos.frase_regional_uf(df_ufs, resultado['uf'], area, media_brasil))

    linha_uf = df_ufs.filter(pl.col('NO_UF') == resultado['uf'])
    media_uf = linha_uf['MEDIA'][0] if linha_uf.height else None

    aba_estados, aba_municipios = st.tabs(['Estados', f'Municípios de {resultado["uf"]}'])
    with aba_estados:
        st.altair_chart(
            regional.grafico_ufs(df_ufs, area, resultado['uf'], resultado['posicao']['nota_usuario']),
            width='stretch',
        )
    with aba_municipios:
        grafico = regional.grafico_municipios(
            resultado['medias_municipio'], area, resultado['co_municipio'],
            resultado['posicao']['nota_usuario'],
        )
        if grafico is None:
            st.info('Nenhum município da sua UF tem candidatos suficientes nessa área.')
        else:
            st.altair_chart(grafico, width='stretch')

        linha_usuario = resultado['medias_municipio'].filter(
            (pl.col('AREA') == area) & (pl.col('CO_MUNICIPIO_REF') == resultado['co_municipio']),
        )
        st.caption(textos.frase_municipio(linha_usuario, resultado['uf'], area, media_uf))


def _tabela_estatisticas(estatisticas_areas: pl.DataFrame) -> pl.DataFrame:
    """Tabela de detalhes com cabeçalhos legíveis e números no formato brasileiro."""
    return pl.DataFrame([
        {
            'Área': linha['AREA'],
            'Candidatos': fmt.inteiro(linha['CANDIDATOS']),
            'Média': fmt.numero(linha['MEDIA']),
            'Mediana': fmt.numero(linha['MEDIANA']),
            'P10': fmt.numero(linha['P10']),
            'P25': fmt.numero(linha['P25']),
            'P75': fmt.numero(linha['P75']),
            'P90': fmt.numero(linha['P90']),
        }
        for linha in estatisticas_areas.iter_rows(named=True)
    ])


def bloco_detalhes(resultado: dict):
    """5. Detalhes, download e explicações — escondidos para não competir com o essencial."""
    with st.expander('Detalhes e como ler os números'):
        st.markdown('**Média, mediana e percentis por área (Brasil)**')
        tabela = _tabela_estatisticas(resultado['estatisticas_areas'])
        st.dataframe(tabela, hide_index=True, width='stretch')
        st.download_button(
            'Baixar tabela em CSV',
            data=tabela.write_csv(separator=';').encode('utf-8-sig'),
            file_name=f'enem_{resultado["ano"]}_estatisticas_por_area.csv',
            mime='text/csv',
        )

        st.markdown('**Como ler**')
        st.markdown(
            '- O Enem usa TRI: as notas de áreas diferentes não são comparáveis como "% de acertos". '
            'O percentil é a melhor forma de comparar seu desempenho entre áreas.\n'
            '- O percentil mostra o percentual de candidatos com nota menor que a sua naquela escala.\n'
            '- As metas P50, P75 e P90 são as notas que deixam, respectivamente, metade, um quarto '
            'e um décimo do grupo atrás.'
        )

        st.markdown('**Seu perfil**')
        st.caption(textos.frase_perfil(resultado['perfil'], resultado['posicao']['nota_usuario']))

    st.divider()
    if st.button('Nova consulta', width='stretch'):
        st.session_state.resultado = None
        st.session_state.entrada = None
        st.rerun()


def dashboard(resultado: dict):
    st.divider()
    bloco_resumo(resultado)
    bloco_distribuicao(resultado)
    bloco_metas(resultado)
    bloco_regional(resultado)
    bloco_detalhes(resultado)


# ---------------------------------------------------------------- página

def pagina():
    try:
        opcoes = opcoes_formulario()
    except main.DadosIndisponiveis as erro:
        st.error(str(erro))
        st.stop()

    st.title(f'Enem {opcoes["ano"]}: Compare seu desempenho')
    st.caption(
        f'Comparação com os microdados do Enem {opcoes["ano"]}, usando o INSE '
        f'para comparar você com candidatos de perfil socioeconômico parecido.'
    )
    
    # Botão de sair - limpa o estado da sessão
    if st.button('Sair', width='stretch'):
        for chave in list(st.session_state.keys()):
            del st.session_state[chave]
        st.rerun()

    formulario(opcoes)

    if st.session_state.resultado is None:
        st.info('Preencha os dados do candidato e clique em **Comparar**.')
        return

    dashboard(st.session_state.resultado)


st.session_state.setdefault('resultado', None)
st.session_state.setdefault('entrada', None)

pagina()