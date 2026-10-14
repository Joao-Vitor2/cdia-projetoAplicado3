# Pipeline do projeto

Visão geral do fluxo, do download dos dados brutos do INEP até o dashboard no app.
Os diagramas são em [Mermaid](https://mermaid.js.org/) e renderizam direto no GitHub.

## Visão geral (as três etapas)

```mermaid
flowchart LR
    subgraph EXTRACAO["extrator_microdados.py"]
        direction TB
        A["Baixa microdados do ENEM .zip"] --> B["Descompacta com 7z"]
        B --> C["Converte CSVs 1,7 GB para .parquet"]
        D["Baixa planilhas INSE .xlsx"] --> E["Converte INSE para .parquet"]
        B --> F["Gera DICIONARIO_ano.json"]
    end

    subgraph TRATAMENTO["tabela.py + main.py"]
        direction TB
        G["Cruza microdados com INSE<br/>por escola/município"] --> H["Estima nível INSE<br/>de cada candidato"]
        H --> I["Filtra pelo perfil do usuário<br/>e calcula percentis/médias"]
    end

    subgraph APP["app.py"]
        direction TB
        J[Login] --> K["Formulário:<br/>nota, UF, perfil"] --> L["Dashboard:<br/>gráficos e tabelas"]
    end

    EXTRACAO -->|"parquet + json<br/>em dados/dados_ano/"| TRATAMENTO
    TRATAMENTO -->|"dicionários prontos<br/>para desenhar"| APP

    style EXTRACAO fill:#e3f2fd,stroke:#1976d2
    style TRATAMENTO fill:#e8f5e9,stroke:#388e3c
    style APP fill:#ffebee,stroke:#d32f2f
```

## Detalhe por camada

### 1. Extração (`extrator_microdados.py`)

Transforma os dados brutos do INEP em arquivos prontos para o app. Roda uma vez por ano.

```mermaid
flowchart TB
    inep[(Site do INEP)]

    inep -->|microdados_enem_ano.zip| z["Download com retry + resume"]
    z --> dump["Descompacta com 7z → dump/"]
    dump --> dic["DICIONÁRIO .xlsx → DICIONARIO_ano.json"]
    dump --> csv["CSVs em latin1"]
    csv -->|"conversão em streaming<br/>latin1 → UTF-8"| pq["MICRODADOS_ENEM_ano.parquet"]

    inep -->|"INSE_ano_escolas.xlsx<br/>INSE_ano_municipios.xlsx"| ix["Download planilhas INSE"]
    ix --> ip["INSE_ESCOLAS_ano.parquet<br/>INSE_MUNICIPIOS_ano.parquet"]

    pq --> out["dados/dados_ano/"]
    ip --> out
    dic --> out

    style inep fill:#fff3e0,stroke:#f57c00
    style out fill:#e3f2fd,stroke:#1976d2
```

> ⚠️ Só **2019, 2021 e 2023** têm INSE publicado, então só esses anos podem ser cruzados.

### 2. Tratamento (`tabela.py`) + orquestração (`main.py`)

`main.py` carrega os dados uma vez, decodifica o que vem do formulário (texto → código do INEP)
e chama o `tabela.py`, que só faz cálculo (sem Streamlit).

```mermaid
flowchart TB
    md[MICRODADOS .parquet] --> join
    esc[INSE escolas] --> join
    mun[INSE municípios] --> join

    join["resultados_nivel:<br/>cruza por escola, senão por município"] --> nivel["Cada candidato ganha NIVEL_ESTIMADO"]

    form["Formulário do usuário (texto)"] -->|"main.decodificar"| cod["Perfil em códigos<br/>+ nota, UF, município"]

    nivel --> calc
    cod --> calc

    calc{"Análises em tabela.py"}
    calc --> p1["estimar_posicao_candidato"]
    calc --> p2["calcular_percentis<br/>grupo INSE / UF / Brasil"]
    calc --> p3["calcular_media_por_nivel"]
    calc --> p4["resumir_perfil"]

    style calc fill:#e8f5e9,stroke:#388e3c
    style form fill:#ffebee,stroke:#d32f2f
```

> Grupos com menos de `MIN_CANDIDATOS` (30) não são calculados, para o resultado não ficar instável.

### 3. App (`app.py` + `graficos/`)

Três páginas em Streamlit. O app não lê dados nem conhece códigos do INEP — só desenha o que o `main.py` devolve.

```mermaid
flowchart LR
    login[Login] --> formulario["Formulário<br/>nota · UF · perfil"]
    formulario -->|"main.analisar(entrada)"| dash

    subgraph dash["Dashboard"]
        direction TB
        msg["Mensagem: acima / dentro / abaixo da média"]
        g1["Gráfico 1 · percentil<br/>graficos/percentil.py"]
        g2["Gráfico 2 · média por nível INSE<br/>na área escolhida"]
        t1["Tabela 1 · médias"]
        r1["Resumo"]
    end

    style login fill:#ffebee,stroke:#d32f2f
    style formulario fill:#ffebee,stroke:#d32f2f
    style dash fill:#ffebee,stroke:#d32f2f
```

## Arquivos gerados por ano

Em `dados/dados_{ano}/`:

| Arquivo | Conteúdo |
|---|---|
| `MICRODADOS_ENEM_{ano}.parquet` | Microdados do ENEM (notas + perfil) |
| `INSE_ESCOLAS_{ano}.parquet` | Nível socioeconômico por escola |
| `INSE_MUNICIPIOS_{ano}.parquet` | Nível socioeconômico por município |
| `DICIONARIO_{ano}.json` | `{variável: {código: descrição}}` do questionário |
