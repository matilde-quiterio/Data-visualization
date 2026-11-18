import streamlit as st
import pandas as pd
import plotly.express as px
################################################################################
#------------------------Configuração inicial da página do Streamlit------------
st.set_page_config(
    page_title="Dashboard de Saúde - OMS",
    layout="wide",
    page_icon="",
)

# Função para carregar os dados (com cache para otimizar a performance)
@st.cache_data
def carregar_dados():
    df = pd.read_csv("health_indicators.csv")
    df['country_name'] = df['country_name'].str.strip()
    df['income_level'] = df['income_level'].str.strip()
    return df

dados = carregar_dados()

                                # --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros Globais")

                                # --- Filtros ---
# Filtro de Intervalo de Anos (para as séries temporais)
anos_min, anos_max = int(dados['year'].min()), int(dados['year'].max())
intervalo_anos = st.sidebar.slider("Selecione o Intervalo de Anos:", anos_min, anos_max, (anos_min, anos_max)) 

# Filtro de País 
lista_paises = ["Todos"] + sorted(dados['country_name'].unique())
pais_escolhido = st.sidebar.selectbox("Selecione o País:", options=lista_paises)


# Filtro de Grupo de Rendimento
lista_rendimentos = ["Todos"] + sorted(dados['income_level'].dropna().unique())
rendimento_escolhido = st.sidebar.selectbox("Selecione o Grupo de Rendimento:", options=lista_rendimentos)




#######################################################################################
#----------------------------------------Conteúdo--------------------------------------


#Cabeçalho Principal do Dashboard
st.title("Análise de Indicadores de saúde")
st.markdown("---")
st.markdown("### Dinâmica da Esperança de Vida e Disparidades Socioeconómicas")



                                # --- Gráficp 1: Seleção de tipo de análise ---
st.markdown("###### Selecione o Tipo de Análise:")


# Criar um seletor de modo em linha
modo_analise = st.radio(
    "Modo de Visualização:",
    options=["Análise por País (Micro)", "Análise por Grupo de Rendimento (Macro)", "Análise por Género (Feminino e Masculino)"],
    horizontal=True,
    label_visibility="collapsed"
)


# Filtrar o dataframe global com base no intervalo de anos selecionado na sidebar
dados_filtrados = dados[(dados['year'] >= intervalo_anos[0]) & (dados['year'] <= intervalo_anos[1])]

# OPÇÃO 1: SE O UTILIZADOR ESCOLHER "ANÁLISE POR PAÍS"
# ---------------------------------------------------------------------

if modo_analise == "Análise por País (Micro)":
    st.subheader("Evolução Temporal Da Esperança Média de Vida (País vs Média Global)")

    # ADICIONADO: Aviso caso o utilizador não tenha selecionado um país específico na barra lateral
    if pais_escolhido == "Todos":
        st.warning("⚠️ **Aviso:** Por favor, selecione um país específico nos filtros da barra lateral para visualizar a análise detalhada por país.")
    
# Calcular a média global anual com base no filtro de anos
    media_global_anual = dados_filtrados.groupby('year')['life_expectancy'].mean().reset_index()
    media_global_anual['metrica'] = 'Média Global'
    media_global_anual.rename(columns={'life_expectancy': 'esperanca_vida'}, inplace=True)

    if pais_escolhido == "Todos":
        # Se "Todos" estiver selecionado, mostra apenas a média global
        df_comparacao = media_global_anual.copy()
        titulo_grafico = "Evolução Anual da Esperança de Vida: Média Global"
    else:
        # Se um país específico for selecionado, mostra o país + média global
        df_pais = dados_filtrados[dados_filtrados['country_name'] == pais_escolhido].sort_values('year').copy()
        df_pais_dados = df_pais[['year', 'life_expectancy']].copy()
        df_pais_dados['metrica'] = f'{pais_escolhido} (Média Populacional)'
        df_pais_dados.rename(columns={'life_expectancy': 'esperanca_vida'}, inplace=True)

        df_comparacao = pd.concat([
            df_pais_dados,
            media_global_anual[media_global_anual['year'].isin(df_pais['year'])][['year', 'metrica', 'esperanca_vida']]
        ])
        titulo_grafico = f'Evolução Anual da Esperança de Vida: {pais_escolhido} vs Média Global'

    # Construção do Gráfico 1
        fig1 = px.line(
            df_comparacao, x='year', y='esperanca_vida', color='metrica', markers=True,
            labels={'year': 'Ano', 'esperanca_vida': 'Esperança Média de Vida (Anos)', 'metrica': 'Série Analítica'},
            title=titulo_grafico
        )
        fig1.update_layout(
                xaxis=dict(tickmode='linear', tick0=2000, dtick=5, tickangle=0, showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
                plot_bgcolor='white',
                title_font=dict(size=16, family='Arial', color='#2c3e50'),
                hovermode='x unified',
                legend_title_text='Legenda',
                margin=dict(t=60, b=50, l=50, r=50)
            )

        # Dicionário de cores 
        cores_linhas_pais = {
            f'{pais_escolhido} (Média Populacional)': '#000000',  
            f'{pais_escolhido} (Feminino)': '#E87EA1',           
            f'{pais_escolhido} (Masculino)': '#85C1E9',          
            'Média Global': '#95a5a6'                            
        }

        fig1.update_traces(hovertemplate='<b>Ano:</b> %{x}<br><b>Esperança de Vida:</b> %{y:.2f} anos<extra></extra>')

        fig1.for_each_trace(lambda trace: trace.update(
            line=dict(
                width=3 if '(Média Populacional)' in trace.name or pais_escolhido == "Todos" else 2.5, 
                color=cores_linhas_pais.get(trace.name, '#2c3e50')
            ),
            marker=dict(size=6, color=cores_linhas_pais.get(trace.name, '#2c3e50'))
        ))



        st.plotly_chart(fig1, use_container_width=True)


# OPÇÃO 2: SE O UTILIZADOR ESCOLHER "ANÁLISE POR GRUPO DE RENDIMENTO (MACRO)"
# ---------------------------------------------------------------------

elif modo_analise == "Análise por Grupo de Rendimento (Macro)":
    st.subheader("Perspetiva Macroeconómica: O País no seu Contexto de Rendimento")
    
    # Aplicar filtro de rendimento da sidebar se não for "Todos"
    if rendimento_escolhido != "Todos":
        df_macro = dados_filtrados[dados_filtrados['income_level'] == rendimento_escolhido]
    else:
        df_macro = dados_filtrados

    ordem_rendimento = ['Low income', 'Lower middle income', 'Upper middle income', 'High income']
    evolucao_rendimento = df_macro.groupby(['year', 'income_level'])['life_expectancy'].mean().reset_index()


    fig2 = px.line(
        evolucao_rendimento, x='year', y='life_expectancy', color='income_level',
        category_orders={'income_level': ordem_rendimento}, markers=True,
        labels={'year': 'Ano', 'life_expectancy': 'Esperança Média de Vida (Anos)', 'income_level': 'Grupo de Rendimento'},
        title='Evolução da Esperança de Vida: Grupos de Rendimento vs País Selecionado'
    )

    # Se estiver um país selecionado na sidebar (diferente de "Todos") podemos cruzar essa informação

    if pais_escolhido != "Todos":
        #descobrir a que grupo pertence o país selecionado
        pais_info = dados_filtrados[dados_filtrados['country_name'] == pais_escolhido]
        if not pais_info.empty:
            grupo_do_pais = pais_info['income_level'].iloc[0]
            #criar a serie de dados específica para o país
            df_pais_macro = pais_info[['year', 'life_expectancy']].copy()
            df_pais_macro.rename(columns={'life_expectancy': 'esperanca_vida'}, inplace=True)


            st.info(f"**Contexto Económico:** O país selecionado (**{pais_escolhido}**) pertence ao grupo de rendimento **'{grupo_do_pais}'**.")


        # Adicionar a linha do país ao gráfico existente
        fig2.add_scatter(
            x=df_pais_macro['year'],
            y=df_pais_macro['esperanca_vida'],
            mode='lines+markers',
            name=f'{pais_escolhido} (País Selecionado)',
            line=dict(color='black', width=3, dash='dash') # Linha preta a tracejado para destacar
        )

    fig2.update_layout(
        xaxis=dict(tickmode='linear', tick0=2000, dtick=5, tickangle=0, showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        plot_bgcolor='white',
        title_font=dict(size=16, family='Arial', color='#2c3e50'),
        hovermode='x unified',
        legend_title_text='Legenda',
        margin=dict(t=60, b=50, l=50, r=50)
    )


    st.plotly_chart(fig2, use_container_width=True)



# OPÇÃO 3: SE O UTILIZADOR ESCOLHER "ANÁLISE POR GÉNERO (FEMININO E MASCULINO)"
# ---------------------------------------------------------------------

else:
    st.subheader("Análise Comparativa por Género (Feminino vs Masculino)")

    if pais_escolhido == "Todos":
        # Se estiver em "Todos", calcula a média global para feminino e masculino
        df_genero_global = dados_filtrados.groupby('year')[['life_expectancy_female', 'life_expectancy_male']].mean().reset_index()
        df_genero_melted = df_genero_global.melt(
            id_vars=['year'],
            value_vars=['life_expectancy_female', 'life_expectancy_male'],
            var_name='metrica', value_name='esperanca_vida'
        )
        df_genero_melted['metrica'] = df_genero_melted['metrica'].map({
            'life_expectancy_female': 'Média Global (Feminino)',
            'life_expectancy_male': 'Média Global (Masculino)'
        })
        titulo_genero = "Evolução Global da Esperança de Vida por Género"
    else:
        # Se tiver um país selecionado, mostra os dados desse país por género
        df_pais = dados_filtrados[dados_filtrados['country_name'] == pais_escolhido].sort_values('year').copy()
        df_genero_melted = df_pais.melt(
            id_vars=['year', 'country_name'],
            value_vars=['life_expectancy_female', 'life_expectancy_male'],
            var_name='metrica', value_name='esperanca_vida'
        )
        df_genero_melted['metrica'] = df_genero_melted['metrica'].map({
            'life_expectancy_female': f'{pais_escolhido} (Feminino)',
            'life_expectancy_male': f'{pais_escolhido} (Masculino)'
        })
        titulo_genero = f'Evolução por Género em {pais_escolhido}'

    fig3 = px.line(
        df_genero_melted, x='year', y='esperanca_vida', color='metrica', markers=True,
        labels={'year': 'Ano', 'esperanca_vida': 'Esperança Média de Vida (Anos)', 'metrica': 'Género'},
        title=titulo_genero
    )
    fig3.update_layout(
        xaxis=dict(tickmode='linear', tick0=2000, dtick=5, tickangle=0, showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        plot_bgcolor='white',
        title_font=dict(size=16, family='Arial', color='#2c3e50'),
        hovermode='x unified',
        legend_title_text='Legenda',
        margin=dict(t=60, b=50, l=50, r=50)
    )

    cores_linhas_genero = {
        f'{pais_escolhido} (Feminino)': '#E87EA1',          
        f'{pais_escolhido} (Masculino)': '#85C1E9',       
        'Média Global (Feminino)': '#E87EA1',              
        'Média Global (Masculino)': '#85C1E9'               
    }

    fig3.update_traces(hovertemplate='<b>Ano:</b> %{x}<br><b>Esperança de Vida:</b> %{y:.2f} anos<extra></extra>')

    fig3.for_each_trace(lambda trace: trace.update(
        line=dict(width=2.5, color=cores_linhas_genero.get(trace.name, '#2c3e50')),
        marker=dict(size=6, color=cores_linhas_genero.get(trace.name, '#2c3e50'))
    ))
    
    st.plotly_chart(fig3, use_container_width=True)


