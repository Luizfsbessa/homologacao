import streamlit as st
import pandas as pd
import plotly.express as px

# Carregar dados
file_path = "backtest.xlsx"
df = pd.read_excel(file_path)

# Certificar-se de que a coluna 'Data de abertura' está no formato datetime
df['Data de Abertura'] = pd.to_datetime(df['Data da Solução'], errors='coerce')

# Adicionar a coluna 'Mês/Ano' apenas com mês e ano
df['Mês/Ano'] = df['Data de Abertura'].dt.to_period('M').astype(str)

# Determinar a data inicial padrão com base na base de dados
min_date = df['Data da Solução'].min()
if pd.notnull(min_date):
    default_start_date = min_date.replace(day=1)
else:
    default_start_date = None

max_date = df['Data da Solução'].max()

# Converter a coluna 'Tempo em atendimento' para horas decimais
def time_to_hours(time_str):
    try:
        h, m, s = map(int, time_str.split(':'))
        return h + m / 60 + s / 3600
    except ValueError:
        return 0

# Formatar horas decimais no formato 6680:02:58
def format_hours_to_hms(decimal_hours):
    h = int(decimal_hours)
    m = int((decimal_hours - h) * 60)
    s = int(((decimal_hours - h) * 60 - m) * 60)
    return f"{h:02}:{m:02}:{s:02}"

df['Horas Decimais'] = df['Tempo em atendimento'].apply(time_to_hours)

# Título do app
st.title("Dashboard de Atendimento")

# Estilizando o fundo e a cor do texto das caixas de seleção e data
custom_style = """
    <style>
        .stSelectbox, .stDateInput, .stMultiselect, .stCheckbox, .stTextInput, .stTextArea {
            background-color: white;
            color: black;
            padding: 15px;
            font-size: 16px;
            border-radius: 5px;
            margin-bottom: 10px;
            border: 1px solid #A1C6D8;
        }
        .stSelectbox select, .stDateInput input {
            background-color: white;
            color: black;
            border: 1px solid #A1C6D8;
        }
        .stSelectbox, .stDateInput {
            font-size: 16px;
        }
    </style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# Filtro de técnico
tecnico = st.selectbox(
    "Selecionar Técnico:",
    options=[""] + sorted(df['Atribuído - Técnico'].dropna().unique()),
    format_func=lambda x: "Selecione um técnico" if x == "" else x,
    key="tecnico_selectbox",  # Chave única
    help="Escolha o técnico para filtrar os dados",
)

# Filtro de intervalo de datas
start_date = st.date_input(
    "Data de Início", 
    value=default_start_date, 
    min_value=min_date, 
    max_value=max_date, 
    format="DD/MM/YYYY",
    key="star_date_input",  # Chave única
    help="Escolha a data inicial para o filtrar os dados",
)

end_date = st.date_input(
    "Data de Fim", 
    value=max_date, 
    min_value=min_date, 
    max_value=max_date, 
    format="DD/MM/YYYY",
    key="end_date_input",  # Chave única
    help="Escolha a data final para o filtrar os dados",
)

# Estilo para garantir que o texto fique visível no modo escuro
st.markdown("""
    <style>
    .streamlit-expanderHeader {
        color: white !important;
    }
    .stTextInput, .stDateInput, .stSelectbox, .stRadio {
        color: white !important;
        background-color: #333333 !important;  /* Fundo escuro */
        border: 1px solid #5e5e5e !important;  /* Cor de borda clara */
    }
    .stTextInput input, .stDateInput input, .stSelectbox select {
        color: white !important;
        background-color: #333333 !important;  /* Fundo escuro no campo */
    }
    .stTextInput input::placeholder {
        color: #aaaaaa !important;  /* Cor do texto do placeholder */
    }
    </style>
""", unsafe_allow_html=True)

# Estilo para garantir visibilidade no modo claro e escuro
st.markdown("""
    <style>
    /* Ajuste do texto e fundo dos componentes para modo claro e escuro */
    .stSelectbox, .stDateInput, .stTextInput {
        color: var(--secondary-text-color) !important;  /* Cor do texto ajustada automaticamente */
        background-color: var(--background-color) !important;  /* Fundo adaptável ao tema */
        border: 1px solid var(--border-color) !important;  /* Cor da borda ajustada */
    }
    .stSelectbox select, .stDateInput input, .stTextInput input {
        color: var(--text-color) !important;
        background-color: var(--background-color) !important;  /* Fundo adaptável */
    }

    /* Ajuste do placeholder */
    .stTextInput input::placeholder, .stDateInput input::placeholder {
        color: var(--secondary-text-color) !important;  /* Ajuste automático no placeholder */
    }

    /* Melhorando a visibilidade de seleções */
    .stSelectbox select:focus, .stDateInput input:focus {
        border-color: var(--primary-color) !important;  /* Cor da borda ao focar */
    }
    </style>
""", unsafe_allow_html=True)

# Validar se as datas foram preenchidas corretamente
if start_date and end_date and start_date > end_date:
    st.error("A data de início não pode ser maior que a data de fim.")
elif tecnico:  # Só filtrar se o técnico foi selecionado
    # Filtragem de dados
    filtered_df = df[df['Atribuído - Técnico'] == tecnico]
    if start_date:
        filtered_df = filtered_df[filtered_df['Data da Solução'] >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[filtered_df['Data da Solução'] <= pd.to_datetime(end_date)]

    # Calcular o total de horas por tipo
    incidentes_df = filtered_df[filtered_df['Tipo'] == 'Incidente']
    requisicoes_df = filtered_df[filtered_df['Tipo'] == 'Requisição']

    # Exibir os tempos em atendimento com informações detalhadas de prioridade
    if not incidentes_df.empty:
        # Cálculo de tempos médios por prioridade em Incidentes
        tempos_incidentes = incidentes_df.groupby('Prioridade')['Horas Decimais'].agg(['mean', 'max']).reset_index()
        tempos_incidentes['Média'] = tempos_incidentes['mean'].apply(format_hours_to_hms)
        tempos_incidentes['Máximo'] = tempos_incidentes['max'].apply(format_hours_to_hms)

        # Gerar o texto com os detalhes
        incidentes_detalhes = "".join([  
            f"<li><b>{row['Prioridade']}:</b> Média: {row['Média']} | Máximo: {row['Máximo']}</li>"
            for _, row in tempos_incidentes.iterrows()
        ])

        st.markdown(
            f"""
            <div style='background-color: #C1D8E3; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
                <b>Tempo total em Incidentes:</b> {format_hours_to_hms(incidentes_df['Horas Decimais'].sum())}
                <ul>
                    {incidentes_detalhes}
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    if not requisicoes_df.empty:
        # Cálculo de tempos médios por prioridade em Requisições
        tempos_requisicoes = requisicoes_df.groupby('Prioridade')['Horas Decimais'].agg(['mean', 'max']).reset_index()
        tempos_requisicoes['Média'] = tempos_requisicoes['mean'].apply(format_hours_to_hms)
        tempos_requisicoes['Máximo'] = tempos_requisicoes['max'].apply(format_hours_to_hms)

        # Gerar o texto com os detalhes
        requisicoes_detalhes = "".join([  
            f"<li><b>{row['Prioridade']}:</b> Média: {row['Média']} | Máximo: {row['Máximo']}</li>"
            for _, row in tempos_requisicoes.iterrows()
        ])

        st.markdown(
            f"""
            <div style='background-color: #C1D8E3; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
                <b>Tempo total em Requisições:</b> {format_hours_to_hms(requisicoes_df['Horas Decimais'].sum())}
                <ul>
                    {requisicoes_detalhes}
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

      # Gráficos de número de atendimentos por mês, separados por Tipo (Requisição e Incidente)
    incidentes_por_mes = incidentes_df.groupby('Mês/Ano').size().reset_index(name='Número de Atendimentos')
    requisicoes_por_mes = requisicoes_df.groupby('Mês/Ano').size().reset_index(name='Número de Atendimentos')

    # Verificar se os DataFrames não estão vazios e exibir os gráficos de barras
    if not incidentes_por_mes.empty:
        fig_incidentes = px.bar(
            incidentes_por_mes,
            x='Mês/Ano',
            y='Número de Atendimentos',
            text='Número de Atendimentos',
            title="Número de Atendimentos por Mês - Incidentes",
            color_discrete_sequence=['#1EA4B6']  # Cor para Incidentes
        )
        fig_incidentes.update_traces(texttemplate='<b>%{text}</b>', textposition='outside')
        fig_incidentes.update_layout(
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            font=dict(color="black"),  # Cor do texto do gráfico
        )
        fig_incidentes.update_xaxes(showgrid=False)
        fig_incidentes.update_yaxes(
            showgrid=False,      # Opcional: remove a grade do eixo Y
            zeroline=False,      # Opcional: remove a linha do eixo Y
            showline=False,      # Opcional: remove a linha do gráfico
            showticklabels=False  # Remove os valores do eixo Y
        )

        st.plotly_chart(fig_incidentes)

    if not requisicoes_por_mes.empty:
        fig_requisicoes = px.bar(
            requisicoes_por_mes,
            x='Mês/Ano',
            y='Número de Atendimentos',
            text='Número de Atendimentos',
            title="Número de Atendimentos por Mês - Requisições",
            color_discrete_sequence=['#00C6E0']  # Cor para Requisições
        )
        fig_requisicoes.update_traces(texttemplate='<b>%{text}</b>', textposition='outside')
        fig_requisicoes.update_layout(
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            font=dict(color="black"),  # Cor do texto do gráfico
        )
        fig_requisicoes.update_xaxes(showgrid=False)
        fig_requisicoes.update_yaxes(
            showgrid=False,      # Opcional: remove a grade do eixo Y
            zeroline=False,      # Opcional: remove a linha do eixo Y
            showline=False,      # Opcional: remove a linha do gráfico
            showticklabels=False  # Remove os valores do eixo Y
        )

        st.plotly_chart(fig_requisicoes)

    # Gráficos de Pizza - Distribuição de Incidentes e Requisições por Prioridade
    incidentes_por_prioridade = incidentes_df.groupby('Prioridade').size().reset_index(name='Número de Atendimentos')
    requisicoes_por_prioridade = requisicoes_df.groupby('Prioridade').size().reset_index(name='Número de Atendimentos')

    # Definir cores personalizadas para cada prioridade
    prioridade_cores = {
        'Baixa': '#90ACB8',
        'Média': '#587D8E',
        'Alta': '#C1D8E3',
        'Muito Alta': '#2D55263'
    }

    # Verificar se os DataFrames não estão vazios e exibir os gráficos de pizza
    if not incidentes_por_prioridade.empty:
        fig_incidentes_pizza = px.pie(
            incidentes_por_prioridade,
            names='Prioridade',
            values='Número de Atendimentos',
            title="Distribuição de Incidentes por Prioridade",
            color='Prioridade',
            color_discrete_map=prioridade_cores
        )
        st.plotly_chart(fig_incidentes_pizza)

    if not requisicoes_por_prioridade.empty:
        fig_requisicoes_pizza = px.pie(
            requisicoes_por_prioridade,
            names='Prioridade',
            values='Número de Atendimentos',
            title="Distribuição de Requisições por Prioridade",
            color='Prioridade',
            color_discrete_map=prioridade_cores
        )
        st.plotly_chart(fig_requisicoes_pizza)
