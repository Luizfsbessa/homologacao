import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# Carregar os dados
file_path = "backtest.xlsx"
df = pd.read_excel(file_path)

df['Data da solução'] = pd.to_datetime(df['Data da solução'], errors='coerce')

def time_to_hours(time_str):
    try:
        h, m, s = map(int, time_str.split(':'))
        return h + m / 60 + s / 3600
    except ValueError:
        return 0

df['Horas Decimais'] = df['Tempo em atendimento'].apply(time_to_hours)

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard de Atendimento", style={'textAlign': 'center'}),
    html.Div([
        html.Label("Selecionar Técnico:"),
        dcc.Dropdown(
            id='tecnico-dropdown',
            options=[{'label': tecnico, 'value': tecnico} for tecnico in sorted(df['Atribuído - Técnico'].dropna().unique())],
            value=df['Atribuído - Técnico'].dropna().iloc[0]
        )
    ], style={'width': '30%', 'display': 'inline-block'}),
    html.Div([
        html.Label("Filtrar por Tipo:"),
        dcc.Dropdown(
            id='tipo-dropdown',
            options=[{'label': tipo, 'value': tipo} for tipo in df['Tipo'].dropna().unique()],
            value=None,
            multi=True
        )
    ], style={'width': '30%', 'display': 'inline-block', 'marginLeft': '20px'}),
    html.Div([
        html.Label("Selecionar Intervalo de Data:"),
        dcc.DatePickerRange(
            id='date-picker-range',
            start_date=df['Data da solução'].min().date(),
            end_date=df['Data da solução'].max().date(),
            display_format='DD/MM/YYYY',
            style={'marginTop': '20px'}
        )
    ], style={'width': '30%', 'display': 'inline-block', 'marginLeft': '20px'}),
    html.Div(id='total-time-display', style={'marginTop': '20px', 'fontSize': '20px'}),
    dcc.Graph(id='histogram-graph')
])

@app.callback(
    [Output('total-time-display', 'children'),
     Output('histogram-graph', 'figure')],
    [Input('tecnico-dropdown', 'value'),
     Input('tipo-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_dashboard(selected_tecnico, selected_tipo, start_date, end_date):
    filtered_df = df[df['Atribuído - Técnico'] == selected_tecnico]
    if selected_tipo:
        filtered_df = filtered_df[filtered_df['Tipo'].isin(selected_tipo)]
    filtered_df = filtered_df[
        (filtered_df['Data da solução'] >= start_date) & (filtered_df['Data da solução'] <= end_date)
    ]
    total_time = filtered_df['Horas Decimais'].sum()
    total_time_str = f"Total de Tempo em Atendimento: {total_time:.2f} horas"
    histogram_fig = px.histogram(
        filtered_df,
        x='Tipo',
        title="Distribuição de Atendimentos por Tipo",
        labels={'Tipo': 'Tipo de Atendimento'},
        text_auto=True
    )
    return total_time_str, histogram_fig

if __name__ == '__main__':
    app.run_server(debug=True)
