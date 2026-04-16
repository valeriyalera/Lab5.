import pandas as pd
import numpy as np
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import re

df = pd.read_csv('weather2026.csv')

df.columns = df.columns.str.strip()

df = df.dropna(subset=['період'])

def extract_precipitation(value):
    if pd.isna(value) or value == '-':
        return 0
    if isinstance(value, str):
        numbers = re.findall(r'\d+', value)
        if numbers:
            return float(numbers[0])
    return 0

df['опади_мм'] = df['опади'].apply(extract_precipitation)

df['денна температура'] = df['денна температура повітря'].str.replace('°C', '').astype(float)
df['нічна температура'] = df['нічна температура повітря'].str.replace('°C', '').astype(float)

df['сила вітру'] = df['сила вітру'].str.replace(' м/с', '').astype(float)

df['хмарність'] = df['хмарність'].str.replace('%', '').astype(float)

df['місяць'] = df['період'].astype(str)

bins = [-float('inf'), 35, 70, float('inf')]
labels = ['Сонячний', 'Мінлива хмарність', 'Хмарний']
df['категорія хмарності'] = pd.cut(df['хмарність'], bins=bins, labels=labels, right=False)

df['розмір_бульбашки'] = df['опади_мм'].replace(0, 1)

app = dash.Dash(__name__)

months = sorted(df['місяць'].unique())

app.layout = html.Div([
    html.H1("Лабораторна робота №5", style={'textAlign': 'center'}),
    html.H3("Виконавець: Потєхіна Валерія, група К-27", style={'textAlign': 'center'}),
    html.H4("Викладач: Скибицький М.", style={'textAlign': 'center'}),
    html.Hr(),
    
    html.Div([
        html.Label("Оберіть період (місяць):"),
        dcc.Dropdown(
            id='month-dropdown',
            options=[{'label': m, 'value': m} for m in months],
            value=months[0] if months else None,
            clearable=False
        ),
    ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),
    
    html.Div([
        html.Label("Оберіть тип графіку:"),
        dcc.Dropdown(
            id='graph-type',
            options=[
                {'label': 'а) Денна та нічна температура', 'value': 'temp'},
                {'label': 'б) Хмарність', 'value': 'cloud'},
                {'label': 'в) Сила вітру', 'value': 'wind'},
                {'label': 'г) Бульбашковий графік (температура vs опади)', 'value': 'bubble'}
            ],
            value='temp',
            clearable=False
        ),
    ], style={'width': '30%', 'display': 'inline-block'}),
    
    html.Br(), html.Br(),
    
    html.Div([
        html.Label("Оберіть тип аналітики:"),
        dcc.Dropdown(
            id='analytics-type',
            options=[
                {'label': 'а) Гістограма відхилення температури (нічна від денної)', 'value': 'hist'},
                {'label': 'б) Стовпчикова діаграма хмарності (з накопиченням)', 'value': 'stacked'},
                {'label': 'в) Діаграма "сонячного вибуху"', 'value': 'sunburst'},
                {'label': 'г) Кругова діаграма днів з опадами', 'value': 'pie'}
            ],
            value='hist',
            clearable=False
        ),
    ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),
    
    html.Hr(),
    
    dcc.Graph(id='main-graph'),
    dcc.Graph(id='analytics-graph')
])

@app.callback(
    Output('main-graph', 'figure'),
    [Input('month-dropdown', 'value'),
     Input('graph-type', 'value')]
)
def update_main_graph(selected_month, graph_type):
    filtered_df = df[df['місяць'] == selected_month].copy()
    filtered_df = filtered_df.sort_values('день')
    
    if graph_type == 'temp':
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=filtered_df['день'], y=filtered_df['денна температура'],
                                 mode='lines+markers', name='Денна температура', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=filtered_df['день'], y=filtered_df['нічна температура'],
                                 mode='lines+markers', name='Нічна температура', line=dict(color='blue')))
        fig.update_layout(title=f'Температура за {selected_month}',
                          xaxis_title='День місяця', yaxis_title='Температура (°C)',
                          legend_title='Тип температури')
    
    elif graph_type == 'cloud':
        fig = px.line(filtered_df, x='день', y='хмарність', markers=True,
                      title=f'Хмарність за {selected_month}',
                      labels={'день': 'День місяця', 'хмарність': 'Хмарність (%)'})
        fig.update_traces(line=dict(color='green'))
    
    elif graph_type == 'wind':
        fig = px.line(filtered_df, x='день', y='сила вітру', markers=True,
                      title=f'Сила вітру за {selected_month}',
                      labels={'день': 'День місяця', 'сила вітру': 'Сила вітру (м/с)'})
        fig.update_traces(line=dict(color='purple'))
    
    elif graph_type == 'bubble':
        fig = px.scatter(filtered_df, x='день', y='денна температура',
                         size='розмір_бульбашки', size_max=30,
                         color='денна температура',
                         title=f'Бульбашковий графік: Денна температура vs Опади за {selected_month}',
                         labels={'день': 'День місяця', 'денна температура': 'Денна температура (°C)',
                                 'розмір_бульбашки': 'Опади (мм)'})
    
    return fig

@app.callback(
    Output('analytics-graph', 'figure'),
    [Input('analytics-type', 'value')]
)
def update_analytics_graph(analytics_type):
    
    if analytics_type == 'hist':
        df['відхилення'] = df['нічна температура'] - df['денна температура']
        fig = px.histogram(df, x='відхилення', nbins=20,
                           title='Гістограма відхилення нічної температури від денної (весь період)',
                           labels={'відхилення': 'Відхилення (нічна - денна) (°C)'})
        fig.update_layout(xaxis_title='Відхилення (°C)', yaxis_title='Кількість днів')
    
    elif analytics_type == 'stacked':
        stacked_df = df.groupby(['місяць', 'категорія хмарності']).size().reset_index(name='кількість')
        fig = px.bar(stacked_df, x='місяць', y='кількість', color='категорія хмарності',
                     title='Кількість днів за категоріями хмарності по місяцях',
                     labels={'місяць': 'Місяць', 'кількість': 'Кількість днів', 
                             'категорія хмарності': 'Тип хмарності'},
                     barmode='stack')
    
    elif analytics_type == 'sunburst':
        sunburst_df = df.groupby(['місяць', 'категорія хмарності']).size().reset_index(name='кількість')
        fig = px.sunburst(sunburst_df, path=['місяць', 'категорія хмарності'], values='кількість',
                          title='Діаграма "сонячного вибуху": Розподіл хмарності по місяцях')

    elif analytics_type == 'pie':
  
        rainy_days = df[df['опади_мм'] > 0].groupby('місяць').size().reset_index(name='кількість')
        
        fig = px.pie(rainy_days, values='кількість', names='місяць',
                     title='Розподіл днів з опадами по місяцях (весь період)',
                     hole=0.3)

        fig.update_traces(textposition='inside', textinfo='percent', textfont_size=12)
        fig.update_layout(showlegend=True, legend_title_text='Місяць')
    
    return fig

if __name__ == '__main__':
    app.run(debug=True)