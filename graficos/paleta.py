"""Paleta única do app (tema escuro), segura para daltônicos.

Cada cor tem um significado fixo, igual nos cartões e nos gráficos:
- laranja: você, e tudo em que você está na frente
- azul: os outros candidatos, e onde eles estão na sua frente
- turquesa: o seu lugar (a sua UF e o seu município)

Azul × laranja é o par complementar que continua distinguível em protanopia,
deuteranopia e tritanopia; nenhuma informação depende de vermelho × verde.
"""

COR_USUARIO = '#ff8a3d'      # laranja: o candidato / a nota dele
COR_REFERENCIA = '#7c8cff'   # azul: médias, referências, os outros candidatos
COR_LOCALIZACAO = '#2dd4bf'  # turquesa: UF e município do candidato
COR_CONTEXTO = '#7d86a8'     # hastes, faixas, média
COR_MEDIANA = '#d4d8ee'      # mediana: claro e neutro, para não competir com o laranja
COR_TEXTO = '#e8eaf5'        # rótulos legíveis no fundo escuro
COR_GRADE = '#262c45'        # linhas de grade
COR_POSITIVO = COR_USUARIO   # você acima da média
COR_NEGATIVO = COR_REFERENCIA
