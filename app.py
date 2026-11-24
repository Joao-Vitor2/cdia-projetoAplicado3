"""Página única: formulário do candidato no topo e dashboard logo abaixo.

Só a interface: o cálculo e a decodificação ficam no main.py, o tratamento no tabela.py,
o desenho dos gráficos em graficos/ e as frases em textos.py.
"""

import html
import math
import sys

import polars as pl
import streamlit as st

import formatacao as fmt
import main
import textos
from graficos import areas, distribuicao, regional
from graficos.paleta import COR_CONTEXTO, COR_LOCALIZACAO, COR_REFERENCIA, COR_USUARIO

# permite rodar com "python app.py" (ex.: botão Run do VSCode), relançando via "streamlit run"
if __name__ == '__main__' and not st.runtime.exists():
    from streamlit.web import cli as stcli
    sys.argv = ['streamlit', 'run', __file__, *sys.argv[1:]]
    sys.exit(stcli.main())

st.set_page_config(page_title='Enem 2023: Compare seu desempenho', page_icon=':material/school:', layout='wide')

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

# Cores com papel fixo (mesmas de graficos/paleta.py), na proporção 60-30-10:
# neutros escuros dominam, o azul estrutura e o laranja só aparece onde está "você".
_CSS_ESTILOS = """
<style>
:root {
    --laranja: #ff8a3d;  --laranja-fundo: #2a1a10;  --laranja-borda: #5a3418;
    --azul: #5b6cff;     --azul-claro: #8c99ff;     --azul-fundo: #151a3d;  --azul-borda: #2b3370;
    --turquesa: #2dd4bf; --turquesa-fundo: #0d2a2a; --turquesa-borda: #1b4b47;
    --tinta: #0b0e1a; --sup-1: #131728; --sup-2: #1b2036; --borda: #262c45;
    --texto: #eef0f8; --texto-2: #a3aac8; --texto-3: #6f7697;
    --display: 'Sora', 'Plus Jakarta Sans', sans-serif;
}
[data-testid="stMainBlockContainer"] { max-width: none; padding-left: 4vw !important; padding-right: 4vw !important; }

/* ── Cabeçalho ── */
.hero { padding: 4px 0 18px; }
.hero-selo {
    display: inline-flex; align-items: center; gap: 10px;
    font-size: .72rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
    color: var(--texto-2); background: var(--sup-1); border: 1px solid var(--borda);
    padding: 6px 14px; border-radius: 999px;
}
.hero-selo i {
    width: 8px; height: 8px; border-radius: 50%; background: var(--laranja);
    box-shadow: 0 0 0 4px rgba(255,138,61,.18);
}
.hero-titulo {
    font-family: var(--display); font-size: clamp(2rem, 4.4vw, 3.2rem); font-weight: 800;
    line-height: 1.08; letter-spacing: -.035em; color: var(--texto); margin: 18px 0 12px;
}
.hero-titulo .marca {
    background: linear-gradient(transparent 60%, rgba(255,138,61,.5) 60%, rgba(255,138,61,.5) 92%, transparent 92%);
    padding: 0 .08em;
}
.hero-sub { font-size: 1.05rem; line-height: 1.55; color: var(--texto-2); max-width: 660px; margin: 0; }

/* ── Expander do formulário ── */
[data-testid="stExpander"] details {
    border: 1px solid var(--borda) !important; border-radius: 20px !important; background: var(--sup-1);
}
[data-testid="stExpander"] summary { font-family: var(--display); font-weight: 700; font-size: 1.02rem; }

/* ── Cartões do formulário: cada um no tom do seu papel ── */
.st-key-card_local, .st-key-card_nota, .st-key-card_perfil, .st-key-card_simulador {
    border: 1px solid var(--borda); border-top: 3px solid var(--tom);
    border-radius: 20px; padding: 20px 22px 18px;
    background: linear-gradient(180deg, var(--fundo) 0%, var(--sup-1) 75%);
}
.st-key-card_local     { --tom: var(--turquesa); --fundo: var(--turquesa-fundo); }
.st-key-card_nota      { --tom: var(--laranja);  --fundo: var(--laranja-fundo); }
.st-key-card_perfil    { --tom: var(--azul);     --fundo: var(--azul-fundo); }
.st-key-card_simulador { --tom: var(--laranja);  --fundo: var(--laranja-fundo); }
.st-key-card_nota [data-testid="stNumberInput"] input {
    font-family: var(--display); font-size: 1.6rem; font-weight: 800; color: var(--laranja);
}

.passo { display: flex; align-items: center; gap: 12px; margin-bottom: 6px; }
.passo-num {
    flex: none; width: 34px; height: 34px; border-radius: 11px; display: grid; place-items: center;
    font-family: var(--display); font-weight: 800; color: var(--tinta); background: var(--tom);
}
.passo-tit { font-family: var(--display); font-weight: 700; font-size: 1.08rem; color: var(--texto); line-height: 1.2; }
.passo-dica { font-size: .84rem; color: var(--texto-2); }

/* ── Botão principal: o único laranja sólido da tela ── */
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #ffa04d 0%, #ff7a2f 100%) !important;
    border: none !important; border-radius: 14px !important; min-height: 56px;
    box-shadow: 0 10px 30px rgba(255,138,61,.28) !important; transition: transform .15s ease, box-shadow .15s ease !important;
}
[data-testid="stFormSubmitButton"] button { color: #1f1206 !important; }
[data-testid="stFormSubmitButton"] button p {
    color: #1f1206 !important; font-family: var(--display); font-size: 1.05rem !important; font-weight: 800 !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-2px); box-shadow: 0 14px 36px rgba(255,138,61,.4) !important;
}

/* ── Cabeçalho das seções do dashboard ── */
.secao { display: flex; align-items: flex-start; gap: 16px; margin: 48px 0 16px; }
.secao-num {
    flex: none; font-family: var(--display); font-weight: 800; font-size: .82rem; letter-spacing: .06em;
    color: var(--azul-claro); background: var(--azul-fundo); border: 1px solid var(--azul-borda);
    border-radius: 10px; padding: 6px 10px; margin-top: 4px;
}
.secao-tit { font-family: var(--display); font-weight: 800; font-size: 1.65rem; letter-spacing: -.02em; color: var(--texto); line-height: 1.2; }
.secao-sub { font-size: .95rem; line-height: 1.5; color: var(--texto-2); margin-top: 4px; max-width: 780px; }
.mini-tit {
    font-size: .74rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
    color: var(--texto-3); margin: 26px 0 10px;
}

/* ── Cartões do dashboard ── */
.grade { display: grid; gap: 14px; }
.grade-2 { grid-template-columns: 1fr 1.35fr; }
.grade-3 { grid-template-columns: repeat(3, 1fr); }
.grade-4 { grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 6px 0 14px; }
@media (max-width: 760px) { .grade-2, .grade-3 { grid-template-columns: 1fr; } .grade-4 { grid-template-columns: 1fr 1fr; } }

.stat { border-radius: 16px; padding: 14px 16px; background: var(--sup-1); border: 1px solid var(--borda); }
.stat .rot {
    display: flex; align-items: center; gap: 7px;
    font-size: .7rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--texto-2);
}
.stat .rot i { flex: none; width: 10px; height: 10px; border-radius: 3px; }
.stat .rot i.linha { width: 14px; height: 0; border-radius: 0; border-top: 2px dashed; }
.stat .val { font-family: var(--display); font-size: 1.55rem; font-weight: 800; letter-spacing: -.02em; color: var(--texto); margin: 6px 0 2px; }
.stat .det { font-size: .8rem; line-height: 1.35; color: var(--texto-3); }
.stat.voce { background: var(--laranja-fundo); border-color: var(--laranja-borda); }
.stat.voce .rot, .stat.voce .val { color: var(--laranja); }

.cartao {
    position: relative; overflow: hidden; border-radius: 20px; padding: 22px 24px;
    background: var(--sup-1); border: 1px solid var(--borda);
}
.cartao-rot { font-size: .72rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--texto-2); }
.cartao-num {
    font-family: var(--display); font-size: 2.5rem; font-weight: 800; letter-spacing: -.04em;
    line-height: 1.05; margin: 8px 0 6px; color: var(--texto);
}
.cartao-num small { font-size: .42em; font-weight: 700; letter-spacing: 0; opacity: .85; }
.cartao-det { font-size: .88rem; line-height: 1.45; color: var(--texto-2); }
.cartao-det b { color: var(--texto); }

.cartao.solido-laranja { background: linear-gradient(135deg, #ffa04d 0%, #ff7a2f 100%); border: none; }
.cartao.solido-laranja * { color: #1f1206; }
.cartao.solido-laranja .cartao-num { font-size: 3.4rem; }
.cartao.solido-laranja::after {
    content: ''; position: absolute; right: -50px; top: -50px; width: 180px; height: 180px;
    border-radius: 50%; background: rgba(255,255,255,.16);
}
.cartao.solido-azul { background: linear-gradient(135deg, #5b6cff 0%, #3f4ed6 100%); border: none; }
.cartao.solido-azul * { color: #fff; }
.cartao.solido-azul .cartao-rot, .cartao.solido-azul .cartao-det { color: rgba(255,255,255,.82); }

.cartao.t-azul     { background: var(--azul-fundo);     border-color: var(--azul-borda);     --tom: var(--azul-claro); }
.cartao.t-turquesa { background: var(--turquesa-fundo); border-color: var(--turquesa-borda); --tom: var(--turquesa); }
.cartao.t-laranja  { background: var(--laranja-fundo);  border-color: var(--laranja-borda);  --tom: var(--laranja); }
.cartao.t-neutro   { background: var(--sup-2);          border-color: var(--borda);          --tom: #d4d8ee; }
.cartao .cartao-rot.tom { color: var(--tom); }
.cartao.dica { border-top: 3px solid var(--tom); }
.cartao.dica .cartao-tit { font-family: var(--display); font-weight: 700; font-size: 1.1rem; color: var(--texto); margin: 6px 0 6px; }

.barra { height: 10px; border-radius: 99px; background: rgba(255,255,255,.08); overflow: hidden; margin: 14px 0 10px; }
.barra > span { display: block; height: 100%; border-radius: 99px; background: var(--tom); }

/* ── Escada de metas ── */
.escada { position: relative; height: 100px; margin: 6px 4px 18px; }
.escada-trilho, .escada-prog { position: absolute; top: 48px; height: 12px; border-radius: 99px; }
.escada-trilho { left: 0; right: 0; background: var(--sup-2); border: 1px solid var(--borda); }
.escada-prog { left: 0; background: linear-gradient(90deg, rgba(255,138,61,.15), var(--laranja)); }
.escada-meta { position: absolute; top: 0; transform: translateX(-50%); text-align: center; }
.escada-meta .rot { font-size: .7rem; font-weight: 700; color: var(--texto-2); white-space: nowrap; }
.escada-meta .val { font-family: var(--display); font-size: .92rem; font-weight: 800; color: var(--texto); }
.escada-meta .tick { width: 2px; height: 20px; margin: 2px auto 0; background: var(--azul-claro); border-radius: 2px; }
.escada-voce { position: absolute; top: 42px; transform: translateX(-50%); text-align: center; }
.escada-voce .ponto {
    width: 24px; height: 24px; margin: 0 auto; border-radius: 50%;
    background: var(--laranja); border: 4px solid var(--tinta); box-shadow: 0 0 0 2px var(--laranja);
}
.escada-voce .rot { font-size: .8rem; font-weight: 800; color: var(--laranja); margin-top: 4px; white-space: nowrap; }

.meta { border-radius: 16px; padding: 16px 18px; background: var(--sup-1); border: 1px solid var(--borda); }
.meta .rot { font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--texto-2); }
.meta .val { font-family: var(--display); font-size: 1.9rem; font-weight: 800; letter-spacing: -.03em; color: var(--texto); margin: 4px 0 8px; }
.meta .status {
    display: inline-block; font-size: .8rem; font-weight: 700; padding: 4px 11px; border-radius: 99px;
    background: var(--azul-fundo); color: var(--azul-claro); border: 1px solid var(--azul-borda);
}
.meta.ok { background: linear-gradient(180deg, var(--laranja-fundo), var(--sup-1)); border-color: var(--laranja-borda); }
.meta.ok .status { background: rgba(255,138,61,.14); color: var(--laranja); border-color: var(--laranja-borda); }

.simulacao { font-size: 1.02rem; line-height: 1.5; color: var(--texto-2); }
.simulacao b { font-family: var(--display); font-size: 1.35rem; font-weight: 800; color: var(--laranja); }

/* ── Legenda dos gráficos ── */
.legenda { display: flex; flex-wrap: wrap; gap: 8px 18px; margin: 4px 0 8px; }
.legenda span { display: inline-flex; align-items: center; gap: 8px; font-size: .84rem; color: var(--texto-2); }
.legenda i { display: inline-block; width: 12px; height: 12px; border-radius: 4px; }
.legenda i.linha { width: 18px; height: 3px; border-radius: 2px; }

/* ── Abas da comparação regional: a aba ativa tem a cor do painel e "encaixa" no gráfico ── */
.st-key-abas_regiao {
    background: var(--sup-1); border: 1px solid var(--borda); border-radius: 20px;
    overflow: hidden; gap: 0 !important;
}
.st-key-abas_regiao [role="tablist"] {
    display: flex !important; gap: 6px !important; margin: 0 !important; padding: 8px 8px 0 !important;
    background: var(--tinta) !important; border: none !important; box-shadow: none !important;
}
.st-key-abas_regiao [role="tablist"]::before, .st-key-abas_regiao [role="tablist"]::after,
.st-key-abas_regiao [role="tablist"] > :not([data-testid="stTab"]),
.st-key-abas_regiao [data-testid="stTab"] > :last-child:not(:first-child) { display: none !important; }
.st-key-abas_regiao [data-testid="stTab"] {
    flex: 1 1 0; justify-content: center; min-height: 54px; margin: 0 !important; padding: 0 20px !important;
    border: none !important; border-radius: 14px 14px 0 0 !important;
    background: transparent !important; color: var(--texto-2) !important;
    transition: background .15s ease, color .15s ease;
}
.st-key-abas_regiao [data-testid="stTab"] p {
    font-family: var(--display); font-size: 1rem !important; font-weight: 700 !important; color: inherit !important;
}
.st-key-abas_regiao [data-testid="stTab"]:hover { background: var(--sup-2) !important; color: var(--texto) !important; }
.st-key-abas_regiao [data-testid="stTab"][aria-selected="true"] {
    background: var(--sup-1) !important; color: var(--texto) !important;
    box-shadow: inset 0 3px 0 var(--azul) !important;
}
.st-key-abas_regiao [data-testid="stTab"][aria-selected="true"] [data-testid="stIconMaterial"] { color: var(--azul-claro) !important; }
.st-key-abas_regiao [data-testid="stTabPanel"] { padding: 18px 20px 14px !important; }
</style>
"""


def _html(conteudo: str):
    st.markdown(conteudo, unsafe_allow_html=True)


def _injetar_estilos():
    _html(_CSS_ESTILOS)


def titulo_passo(numero: int | str, titulo: str, dica: str):
    _html(
        f'<div class="passo"><span class="passo-num">{numero}</span>'
        f'<div><div class="passo-tit">{titulo}</div><div class="passo-dica">{dica}</div></div></div>'
    )


def cabecalho_secao(numero: str, titulo: str, subtitulo: str = ''):
    sub = f'<div class="secao-sub">{subtitulo}</div>' if subtitulo else ''
    _html(
        f'<div class="secao"><span class="secao-num">{numero}</span>'
        f'<div><div class="secao-tit">{titulo}</div>{sub}</div></div>'
    )


def legenda(itens: list[tuple[str, str, bool]]):
    """Itens (cor, texto, é_linha): a legenda fica acima do gráfico, onde o olho chega primeiro."""
    partes = ''.join(
        f'<span><i class="{"linha" if linha else ""}" style="background:{cor}"></i>{texto}</span>'
        for cor, texto, linha in itens
    )
    _html(f'<div class="legenda">{partes}</div>')


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
    with st.container(key='card_local'):
        titulo_passo(1, 'Onde você está', 'Seu estado e sua cidade — é com eles que vamos te comparar.')
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
    with st.container(key='card_nota'):
        titulo_passo(2, 'Sua nota', 'Escolha a área e digite a nota que você tirou.')
        area = st.selectbox('Área de conhecimento', opcoes['areas'])
        nota = st.number_input(
            'Sua nota', min_value=0.0, max_value=1000.0, value=None, step=0.1, placeholder='Ex.: 650,5',
        )
    return area, nota


def cartao_perfil(opcoes: dict) -> tuple[dict, float | None, bool]:
    """Os campos do perfil ficam em duas colunas; o checkbox ocupa a largura do cartão."""
    with st.container(key='card_perfil'):
        titulo_passo(3, 'Sobre você', 'Só a idade é obrigatória; o resto deixa a comparação mais precisa.')
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
    tem_resultado = st.session_state.resultado is not None
    with st.expander(
        'Editar seus dados' if tem_resultado else 'Seus dados',
        expanded=not tem_resultado, icon=':material/edit_note:',
    ):
        uf, municipio, co_escola = barra_localizacao(opcoes)

        with st.form('form_candidato', border=False):
            coluna_nota, coluna_perfil = st.columns([2, 3])
            with coluna_nota:
                area, nota = cartao_nota(opcoes)
            with coluna_perfil:
                perfil, idade, treineiro = cartao_perfil(opcoes)

            enviar = st.form_submit_button(
                'Comparar minha nota', type='primary', width='stretch',
                icon=':material/arrow_forward:', icon_position='right',
            )

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


def estado_vazio():
    """Antes da primeira consulta: o que a pessoa vai descobrir, no tom de cada seção."""
    itens = (
        ('t-laranja', 'Sua posição', 'Veja à frente de quantos candidatos parecidos com você a sua nota te coloca.'),
        ('t-azul', 'Suas metas', 'Saiba quantos pontos faltam para a metade, o top 25% e o top 10% do seu grupo.'),
        ('t-turquesa', 'Sua região', 'Compare a sua nota com a média de cada estado e das cidades do seu estado.'),
    )
    _html('<div class="mini-tit">O que você vai descobrir</div>')
    _html(
        '<div class="grade grade-3">'
        + ''.join(
            f'<div class="cartao dica {tom}"><div class="cartao-rot tom">{numero:02d}</div>'
            f'<div class="cartao-tit">{titulo}</div><div class="cartao-det">{texto}</div></div>'
            for numero, (tom, titulo, texto) in enumerate(itens, start=1)
        )
        + '</div>'
    )


# ---------------------------------------------------------------- dashboard

def _cartao_escala(rotulo: str, percentil: float, total: int, tom: str) -> str:
    abaixo = round(percentil / 100 * total)
    largura = max(0.0, min(100.0, percentil))
    return (
        f'<div class="cartao {tom}">'
        f'<div class="cartao-rot tom">{rotulo}</div>'
        f'<div class="cartao-num">{fmt.percentual(percentil)}</div>'
        f'<div class="barra"><span style="width:{largura:.1f}%"></span></div>'
        f'<div class="cartao-det">à frente de <b>{fmt.inteiro(abaixo)}</b> de {fmt.inteiro(total)} candidatos</div>'
        '</div>'
    )


def bloco_resumo(resultado: dict):
    """1. Como o candidato se saiu: nota, distância para a média do grupo e percentil nas 3 escalas."""
    posicao = resultado['posicao']
    percentis = resultado['percentis']
    escopos = resultado['distribuicao_escopos']
    area = html.escape(resultado['area'])
    percentil_brasil = percentis.filter(pl.col('ESCALA') == 'Brasil')['PERCENTIL'].drop_nulls()
    percentil_brasil = percentil_brasil[0] if percentil_brasil.len() else None

    cabecalho_secao('01', 'Como você se saiu')

    diferenca = posicao['diferenca_absoluta']
    lado = 'acima' if diferenca >= 0 else 'abaixo'
    _html(
        '<div class="grade grade-2">'
        '<div class="cartao solido-laranja">'
        '<div class="cartao-rot">Sua nota</div>'
        f'<div class="cartao-num">{fmt.numero(posicao["nota_usuario"])}</div>'
        f'<div class="cartao-det">{area} · ENEM {resultado["ano"]}</div>'
        '</div>'
        '<div class="cartao solido-azul">'
        '<div class="cartao-rot">Comparado à média do seu grupo INSE</div>'
        f'<div class="cartao-num">{fmt.com_sinal(diferenca)} <small>pontos</small></div>'
        f'<div class="cartao-det">{lado} da média do grupo, que é <b>{fmt.numero(posicao["media_grupo"])}</b>. '
        f'Seu grupo tem {fmt.inteiro(posicao["tamanho_grupo"])} candidatos com nível socioeconômico parecido com o seu.</div>'
        '</div>'
        '</div>'
    )

    st.markdown(textos.frase_desempenho(resultado['area'], posicao, percentil_brasil))

    escalas = (
        ('grupo', 'Seu grupo INSE', 'Seu grupo INSE', 't-azul'),
        ('uf', 'Sua UF', f'Sua UF · {html.escape(resultado["uf"])}', 't-turquesa'),
        ('brasil', 'Brasil', 'Todo o Brasil', 't-neutro'),
    )
    cartoes = []
    for escopo, escala, rotulo, tom in escalas:
        percentil = percentis.filter(pl.col('ESCALA') == escala)['PERCENTIL'].item()
        total = escopos[escopo]['estatisticas']['candidatos']
        cartoes.append(_cartao_escala(rotulo, percentil, total, tom))

    _html('<div class="mini-tit">Você está à frente de…</div>')
    _html('<div class="grade grade-3">' + ''.join(cartoes) + '</div>')
    st.caption(textos.legenda_inse(resultado['fonte_nivel']))


def _cartoes_escopo(estatisticas: dict, nota: float, percentil: float, escopo: str, area: str) -> str:
    """Resumo do histograma em 4 números; a amostra de cor de cada um repete a do gráfico."""
    onde = {'grupo': 'do seu grupo INSE', 'uf': 'da sua UF', 'brasil': 'do Brasil'}[escopo]
    cartoes = (
        ('', '', 'Candidatos', fmt.inteiro(estatisticas['candidatos']), f'{onde} em {html.escape(area)}'),
        ('voce', f'<i style="background:{COR_USUARIO}"></i>', 'Abaixo de você',
         fmt.percentual(percentil), f'tiraram menos de {fmt.pontos(nota, 0)}'),
        ('', f'<i style="background:{COR_CONTEXTO};opacity:.6"></i>', 'Metade central',
         f'{fmt.numero(estatisticas["p25"], 0)}–{fmt.numero(estatisticas["p75"], 0)}', 'do P25 ao P75, em pontos'),
        ('', f'<i class="linha" style="border-color:{COR_CONTEXTO}"></i>', 'Média',
         fmt.numero(estatisticas['media']), f'mediana: {fmt.numero(estatisticas["mediana"])}'),
    )
    return '<div class="grade grade-4">' + ''.join(
        f'<div class="stat {classe}"><div class="rot">{amostra}{rotulo}</div>'
        f'<div class="val">{valor}</div><div class="det">{detalhe}</div></div>'
        for classe, amostra, rotulo, valor, detalhe in cartoes
    ) + '</div>'


def bloco_distribuicao(resultado: dict):
    """2. Onde a nota cai na distribuição, no escopo escolhido + bloco opcional por área."""
    cabecalho_secao(
        '02', 'Onde você está na distribuição',
        'Cada barra é a fatia de candidatos com notas naquela faixa. '
        'A faixa sombreada é a metade central dos candidatos (P25 a P75).',
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
    _html(_cartoes_escopo(dados['estatisticas'], nota, percentil, escopo, resultado['area']))
    legenda([
        (COR_USUARIO, 'Tiraram menos que você', False),
        (COR_REFERENCIA, 'Tiraram mais que você', False),
        (COR_USUARIO, 'Sua nota (ou a simulada)', True),
    ])
    st.altair_chart(
        distribuicao.grafico_histograma(dados, nota, resultado['area']),
        width='stretch',
    )

    bloco_areas_opcionais(resultado)


def bloco_areas_opcionais(resultado: dict):
    """Bloco opcional: notas das outras áreas para ver o ponto forte e o ponto a melhorar."""
    outras = [area for area in main.AREAS_NOTA if area != resultado['area']]

    with st.expander('Informar as demais áreas (opcional)', icon=':material/add_chart:'):
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
    _html('<div class="mini-tit">Seu desempenho por área</div>')
    legenda([
        (COR_USUARIO, 'Acima da média do seu grupo', False),
        (COR_REFERENCIA, 'Abaixo da média do seu grupo', False),
    ])
    st.altair_chart(areas.grafico_areas(dados), width='stretch')

    mais_forte = dados.sort('DIFERENCA', descending=True).row(0, named=True)
    mais_fraca = dados.sort('DIFERENCA').row(0, named=True)
    st.caption(
        f'Ponto mais forte: {mais_forte["AREA"]} ({mais_forte["DIFERENCA_TEXTO"]} pontos). '
        f'Ponto a melhorar: {mais_fraca["AREA"]} ({mais_fraca["DIFERENCA_TEXTO"]} pontos).'
    )


def _escada_metas(nota: float, alvos: list[tuple[str, float]]) -> str:
    """Trilho horizontal com as metas acima e você abaixo, preenchido até a sua nota."""
    valores = [nota, *(alvo for _, alvo in alvos)]
    menor, maior = min(valores), max(valores)
    folga = max((maior - menor) * 0.12, 10.0)
    inicio, fim = menor - folga, maior + folga

    def posicao(valor: float) -> float:
        return (valor - inicio) / (fim - inicio) * 100

    metas = ''.join(
        f'<div class="escada-meta" style="left:{posicao(alvo):.1f}%">'
        f'<div class="rot">{rotulo}</div><div class="val">{fmt.numero(alvo, 0)}</div><div class="tick"></div></div>'
        for rotulo, alvo in alvos
    )
    return (
        '<div class="escada">'
        '<div class="escada-trilho"></div>'
        f'<div class="escada-prog" style="width:{posicao(nota):.1f}%"></div>'
        f'{metas}'
        f'<div class="escada-voce" style="left:{posicao(nota):.1f}%">'
        f'<div class="ponto"></div><div class="rot">Você · {fmt.numero(nota, 0)}</div></div>'
        '</div>'
    )


def bloco_metas(resultado: dict):
    """3. Quanto falta para P50/P75/P90 e o simulador de nota (só consulta a CDF já calculada)."""
    cabecalho_secao(
        '03', 'Quanto falta para chegar lá',
        'Metas dentro do seu grupo INSE: o P50 deixa metade do grupo atrás de você; '
        'o P75 e o P90 são as notas do top 25% e do top 10%.',
    )

    dados = resultado['distribuicao_escopos'].get('grupo')
    if dados is None:
        st.info('Não há candidatos suficientes no seu grupo para calcular metas.')
        return

    nota = resultado['posicao']['nota_usuario']
    metas = (
        ('Metade do grupo', 'P50', 'p50'),
        ('Top 25%', 'P75', 'p75'),
        ('Top 10%', 'P90', 'p90'),
    )
    _html(_escada_metas(nota, [(sigla, dados['quantis'][chave]) for _, sigla, chave in metas]))

    cartoes = []
    for rotulo, sigla, chave in metas:
        alvo = dados['quantis'][chave]
        diferenca = nota - alvo
        if diferenca >= 0:
            classe, status = 'meta ok', f'✓ Você já passou · +{fmt.numero(diferenca, 0)} pts'
        else:
            classe, status = 'meta', f'Faltam {fmt.numero(-diferenca, 0)} pontos'
        cartoes.append(
            f'<div class="{classe}" title="Nota de corte do {sigla} entre os candidatos do seu grupo INSE.">'
            f'<div class="rot">{rotulo} · {sigla}</div>'
            f'<div class="val">{fmt.numero(alvo, 0)}</div>'
            f'<span class="status">{status}</span></div>'
        )
    _html('<div class="grade grade-3">' + ''.join(cartoes) + '</div>')

    est = dados['estatisticas']
    minimo = int(min(math.floor(est['minimo']), math.floor(nota)))
    maximo = int(max(math.ceil(est['maximo']), math.ceil(nota)))

    st.space('medium')
    with st.container(key='card_simulador'):
        titulo_passo('?', 'E se eu tirasse…?', 'Arraste para simular outra nota. O gráfico da seção 02 acompanha.')
        nota_simulada = st.slider(
            'Nota simulada', min_value=minimo, max_value=maximo, step=1,
            key='nota_simulada', label_visibility='collapsed',
        )
        percentil = main.percentil_estimado(resultado['distribuicao_escopos'], 'grupo', nota_simulada)
        _html(
            f'<div class="simulacao">Com <b>{fmt.inteiro(nota_simulada)}</b> pontos, você ficaria à frente de '
            f'<b>{fmt.percentual(percentil)}</b> do seu grupo INSE '
            f'({fmt.inteiro(est["candidatos"])} candidatos).</div>'
        )


def bloco_regional(resultado: dict):
    """4. Comparação regional: UFs contra o Brasil e municípios da UF do usuário."""
    cabecalho_secao(
        '04', 'Como a sua região se compara',
        'Cada barra é a diferença entre a sua nota e a média do lugar; a linha tracejada é a sua nota. '
        'Nos municípios, só entram os que têm pelo menos 30 candidatos na área.',
    )

    # o seletor nasce na área usada no formulário, mas só redesenha o bloco ao mudar
    if st.session_state.get('area_regional') not in main.AREAS_NOTA:
        st.session_state.area_regional = resultado['area']
    coluna_area, _ = st.columns([1, 2])
    area = coluna_area.selectbox('Área', list(main.AREAS_NOTA), key='area_regional')

    media_brasil = resultado['medias_brasil'].get(area)
    df_ufs = resultado['medias_uf'].filter(
        (pl.col('AREA') == area) & pl.col('MEDIA').is_not_null() & (pl.col('CANDIDATOS') >= 30),
    )
    st.markdown(textos.frase_regional_uf(df_ufs, resultado['uf'], area, media_brasil))

    linha_uf = df_ufs.filter(pl.col('NO_UF') == resultado['uf'])
    media_uf = linha_uf['MEDIA'][0] if linha_uf.height else None

    legenda([
        (COR_USUARIO, 'Você tirou mais que a média', False),
        (COR_REFERENCIA, 'Você tirou menos que a média', False),
        (COR_LOCALIZACAO, 'Seu estado / seu município', False),
    ])
    aba_estados, aba_municipios = st.tabs(
        [':material/map: Estados', f':material/location_city: Municípios de {resultado["uf"]}'],
        key='abas_regiao',
    )
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
    st.space('large')
    with st.expander('Detalhes e como ler os números', icon=':material/menu_book:'):
        st.markdown('**Média, mediana e percentis por área (Brasil)**')
        tabela = _tabela_estatisticas(resultado['estatisticas_areas'])
        st.dataframe(tabela, hide_index=True, width='stretch')
        st.download_button(
            'Baixar tabela em CSV',
            data=tabela.write_csv(separator=';').encode('utf-8-sig'),
            file_name=f'enem_{resultado["ano"]}_estatisticas_por_area.csv',
            mime='text/csv', icon=':material/download:',
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

    st.space('small')
    if st.button('Fazer nova consulta', width='stretch', icon=':material/restart_alt:'):
        st.session_state.resultado = None
        st.session_state.entrada = None
        st.rerun()


def dashboard(resultado: dict):
    bloco_resumo(resultado)
    bloco_distribuicao(resultado)
    bloco_metas(resultado)
    bloco_regional(resultado)
    bloco_detalhes(resultado)


# ---------------------------------------------------------------- página

def cabecalho(ano: int):
    coluna_texto, coluna_sair = st.columns([6, 1])
    with coluna_texto:
        _html(
            '<div class="hero">'
            f'<span class="hero-selo"><i></i>ENEM {ano} · Dados oficiais do INEP</span>'
            '<div class="hero-titulo">Sua nota do ENEM, <span class="marca">em perspectiva</span>.</div>'
            '<p class="hero-sub">Descubra como você se saiu em comparação com quem tem um perfil parecido '
            'com o seu: mesma realidade socioeconômica, mesmo estado, mesma cidade.</p>'
            '</div>'
        )
    with coluna_sair:
        # botão de sair: limpa o estado da sessão
        if st.button('Sair', type='tertiary', icon=':material/logout:', width='stretch'):
            for chave in list(st.session_state.keys()):
                del st.session_state[chave]
            st.rerun()


def pagina():
    _injetar_estilos()

    try:
        opcoes = opcoes_formulario()
    except main.DadosIndisponiveis as erro:
        st.error(str(erro))
        st.stop()

    cabecalho(opcoes['ano'])
    formulario(opcoes)

    if st.session_state.resultado is None:
        estado_vazio()
        return

    dashboard(st.session_state.resultado)


st.session_state.setdefault('resultado', None)
st.session_state.setdefault('entrada', None)

pagina()
