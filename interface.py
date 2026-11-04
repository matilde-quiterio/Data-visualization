import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração inicial da página do Streamlit
st.set_page_config(
    page_title="Dashboard de Saúde - OMS",
    layout="wide",
    page_icon="",
)

# 2. Função para carregar os dados (com cache para otimizar a performance)
@st.cache_data
def carregar_dados():
    df = pd.read_csv("health_indicators.csv")
    df['country_name'] = df['country_name'].str.strip()
    df['income_level'] = df['income_level'].str.strip()
    return df

dados = carregar_dados()

# 3. Cabeçalho Principal do Dashboard
st.title("Análise de Indicadores de saúde")
st.markdown("### Tema 1: Dinâmica da Esperança de Vida e Disparidades Socioeconómicas")
st.markdown("---")


st.markdown("###### Selecione o Tipo de Análise:")

# Criar um seletor de modo em linha
modo_analise = st.radio(
    "Modo de Visualização:",
    options=["Análise por País (Micro)", "Análise por Grupo de Rendimento (Macro)"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")


# OPÇÃO A: SE O UTILIZADOR ESCOLHER "ANÁLISE POR PAÍS"
# ---------------------------------------------------------------------

if modo_analise == "Análise por País (Micro)":
    st.subheader("Evolução Temporal Da Esperança Média de Vida")
    
    # Seletor do país
    lista_paises = sorted(dados['country_name'].unique())
    default_index = lista_paises.index("Portugal") if "Portugal" in lista_paises else 0

    pais_escolhido = st.selectbox(
        "Selecione o País para análise detalhada:",
        options=lista_paises,
        index=default_index,
        key="selectbox_pais_unico"
    )

    # Checkbox  para o utilizador decidir se quer ver a desagregação por género
    mostrar_genero = st.checkbox(
        "Mostrar desagregação por género (Feminino e Masculino)", 
        value=False, 
        key="check_desagregacao_genero"
    )

    # Filtrar dados para o país selecionado
    df_pais = dados[dados['country_name'] == pais_escolhido].sort_values('year').copy()

    # Lógica condicional: Se a checkbox estiver ativa, usa o melt (formato longo) para as 3 linhas; se não, usa apenas a média populacional
    if mostrar_genero:
        df_pais_melted = df_pais.melt(
            id_vars=['year', 'country_name'],
            value_vars=['life_expectancy', 'life_expectancy_female', 'life_expectancy_male'],
            var_name='metrica',
            value_name='esperanca_vida'
        )
        traducao_metricas = {
            'life_expectancy': f'{pais_escolhido} (Média Populacional)',
            'life_expectancy_female': f'{pais_escolhido} (Feminino)',
            'life_expectancy_male': f'{pais_escolhido} (Masculino)'
        }
        df_pais_melted['metrica'] = df_pais_melted['metrica'].map(traducao_metricas)
        df_pais_dados = df_pais_melted[['year', 'metrica', 'esperanca_vida']]
    else:
        df_pais_dados = df_pais[['year', 'life_expectancy']].copy()
        df_pais_dados['metrica'] = f'{pais_escolhido} (Média Populacional)'
        df_pais_dados.rename(columns={'life_expectancy': 'esperanca_vida'}, inplace=True)

    # Calcular a média global anual para referência
    media_global_anual = dados.groupby('year')['life_expectancy'].mean().reset_index()
    media_global_anual['metrica'] = 'Média Global'
    media_global_anual.rename(columns={'life_expectancy': 'esperanca_vida'}, inplace=True)

    # Unir os dados do país com a média global
    df_comparacao = pd.concat([
        df_pais_dados,
        media_global_anual[media_global_anual['year'].isin(df_pais['year'])][['year', 'metrica', 'esperanca_vida']]
    ])

    # Construção do Gráfico com Plotly
    fig1 = px.line(
        df_comparacao, 
        x='year', 
        y='esperanca_vida',
        color='metrica',
        markers=True,
        labels={
            'year': 'Ano',
            'esperanca_vida': 'Esperança Média de Vida (Anos)',
            'metrica': 'Série Analítica'
        },
        title=f'Evolução Anual da Esperança de Vida: {pais_escolhido} (2000–2024)'
    )

    fig1.update_layout(
        xaxis=dict(tickmode='linear', tick0=2000, dtick=1, tickangle=-45, showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        plot_bgcolor='white',
        title_font=dict(size=16, family='Arial', color='#2c3e50'),
        hovermode='x unified',
        legend_title_text='Legenda',
        margin=dict(t=60, b=50, l=50, r=50)
    )

    fig1.update_traces(hovertemplate='<b>Ano:</b> %{x}<br><b>Esperança de Vida:</b> %{y:.2f} anos<extra></extra>')

    # Dicionário de cores adaptado para as várias linhas possíveis
    cores_linhas = {
        f'{pais_escolhido} (Média Populacional)': '#000000',  # Preto / Linha principal
        f'{pais_escolhido} (Feminino)': '#E87EA1',           # Rosa suave
        f'{pais_escolhido} (Masculino)': '#85C1E9',          # Azul suave
        'Média Global': '#95a5a6'                            # Cinzento de referência
    }

    fig1.update_traces(hovertemplate='<b>Ano:</b> %{x}<br><b>Esperança de Vida:</b> %{y:.2f} anos<extra></extra>')

    fig1.for_each_trace(lambda trace: trace.update(
        line=dict(
            width=3 if '(Média Populacional)' in trace.name else 2.5, 
            color=cores_linhas.get(trace.name, '#2c3e50')
        ),
        marker=dict(size=6, color=cores_linhas.get(trace.name, '#2c3e50'))
    ))

    st.plotly_chart(fig1, use_container_width=True)

# OPÇÃO B: SE O UTILIZADOR ESCOLHER "ANÁLISE POR GRUPO DE RENDIMENTO"
# ---------------------------------------------------------------------
else:
    st.subheader("Perspetiva Macroeconómica: A Dinâmica do Fosso Económico")
    st.write("Análise da convergência ou divergência da esperança média de vida entre os diferentes patamares de rendimento global (2000–2024).")

    # Agrupar os dados por ano e por nível de rendimento
    ordem_rendimento = ['Low income', 'Lower middle income', 'Upper middle income', 'High income']
    evolucao_rendimento = dados.groupby(['year', 'income_level'])['life_expectancy'].mean().reset_index()

    # Construção do Gráfico Plotly
    fig2 = px.line(
        evolucao_rendimento, 
        x='year', 
        y='life_expectancy',
        color='income_level',
        category_orders={'income_level': ordem_rendimento},
        markers=True,
        labels={
            'year': 'Ano',
            'life_expectancy': 'Esperança Média de Vida (Anos)',
            'income_level': 'Grupo de Rendimento'
        },
        title='Evolução da Esperança Média de Vida por Patamar Socioeconómico (2000–2024)'
    )

    fig2.update_layout(
        xaxis=dict(tickmode='linear', tick0=2000, dtick=1, tickangle=-45, showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        plot_bgcolor='white',
        title_font=dict(size=14, family='Arial', color='#2c3e50'),
        hovermode='x unified',
        legend_title_text='Grupo de Rendimento',
        margin=dict(t=50, b=50, l=50, r=50)
    )

    fig2.update_traces(hovertemplate='<b>Ano:</b> %{x}<br><b>Esperança Média:</b> %{y:.2f} anos<extra></extra>')

    st.plotly_chart(fig2, use_container_width=True)
