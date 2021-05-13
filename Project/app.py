import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas
import plotly.express as px
import sqlalchemy
from dash.dependencies import Input, Output, State, ALL
import plotly.graph_objs as go

import database

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options


# Generates the tables
def generate_table(dataframe, id, darkmode, max_rows=10):
    if darkmode:
        return dash_table.DataTable(id=id,
                                    columns=[{"name": i, "id": i} for i in dataframe.columns],
                                    data=dataframe.to_dict('records'),
                                    style_cell={'textAlign': 'left', 'backgroundColor': 'rgb(50, 50, 50)',
                                                'color': 'white'},
                                    style_as_list_view=True,
                                    style_header={
                                        'backgroundColor': 'rgb(30, 30, 30)',
                                        'fontWeight': 'bold'
                                    })
    else:
        return dash_table.DataTable(id=id,
                                    columns=[{"name": i, "id": i} for i in dataframe.columns],
                                    data=dataframe.to_dict('records'),
                                    style_cell={'textAlign': 'left'},
                                    style_as_list_view=True,
                                    style_data_conditional=[
                                        {
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': 'rgb(248, 248, 248)'
                                        }
                                    ],
                                    style_header={
                                        'backgroundColor': 'rgb(230, 230, 230)',
                                        'fontWeight': 'bold'
                                    })


# Generates the bubble graph as soon as the app is loaded up.
def generate_bubble_graph():
    results = database.pull_bubble_graph_data()
    fig = px.scatter(results, x='lbl', y='count', size="count",
                     hover_name="name", color='unit_name',
                     title='Nutrient Amount in All Foods')
    fig.update_layout(xaxis=dict(title='Nutrient Initial',
                                 tickfont=dict(color='crimson', size=14), showline=True, linecolor='green'),
                      yaxis=dict(title='Total Nutrient Count', tickfont=dict(color='blue', size=14),
                                 showline=False, linecolor='green')
                      )
    return fig


# Generates the pie chart based on which food you clicked on in the Foods table.
@app.callback(Output('pie-chart', 'figure'),
              Input('food-table', 'active_cell'),
              State("food-table", "derived_viewport_data"))
def generate_pie_chart(cell, data):
    pie_chart_title = ''
    if cell and data:
        food_fdc_id = data[cell["row"]]["fdc_id"]
        pie_chart_title = data[cell["row"]]["description"]
        results = database.pull_pie_chart_data(food_fdc_id)
    else:
        results = pandas.DataFrame(columns=['amount', 'name'])
    fig = px.pie(results, values='amount', names='name', title='Nutrients in Food {}'.format(pie_chart_title))
    return fig


# This is activated when the user clicks on a cell in the data table and adds the nutrients
# to the excludes list and saves that to the user.
@app.callback(Output('exclude-list', 'children'),
              [Input('nutrient-table', 'active_cell'), Input(component_id='user-name', component_property='value'), Input({'exclude-button': ALL}, 'value')],
              State("nutrient-table", "derived_viewport_data"),
              State('exclude-list', 'children'))
def nutrient_cell_clicked(cell, user_name, exclude_value, data, old_list):
    ctx = dash.callback_context
    if not ctx.triggered:
        return
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # If the user types into the nutrients table and clicks on a row to be added
    if triggered_id == 'nutrient-table' and cell and data:
        if not old_list:
            old_list = []
        for divs in old_list:
            if divs['props']['children'][0]['props'].get('id', '-1') == str(data[cell['row']]['nutrient_nbr']):
                return old_list
        div = html.Div([html.Div('Exclude: {name}'.format(name=data[cell['row']]['name']),
                                 id=str(data[cell['row']]['nutrient_nbr'])),
                        html.Button(id={'exclude-button': data[cell['row']]['nutrient_nbr']},
                                    n_clicks=0, children='Remove')])
        if user_name:
            database.save_user_nutrient(user_name, data[cell['row']]['nutrient_nbr'])
        old_list.append(div)
        return old_list
    # If the user types in their name then it pulls the nutrients saved under that user and displays them.
    elif triggered_id == 'user-name' and user_name:
        return pull_saved_nutrients(user_name)


# When user enters food to search and clicks the submit button, it will display
# foods that don't have the nutrients in the excluded list.
@app.callback(Output('food_output', 'children'),
              Input('submit-button-state', 'n_clicks'),
              State('food_search', 'value'),
              State("exclude-list", 'children'))
def pull_food_by_name(n_clicks, food_name, exclude_items):
    exclude_ids = []
    if exclude_items:
        exclude_ids = [float(div['props']['children'][0]['props']['id']) for div in exclude_items]
    results = database.pull_food_by_description(food_name, exclude_ids)
    if exclude_ids:
        exclude_df = results[results['nutrient_id'].isin(exclude_ids)]
        results = results[~results['fdc_id'].isin(exclude_df['fdc_id'].unique())]
    results = results.drop_duplicates(subset=['fdc_id', 'data_type', 'description'])
    results = results[['fdc_id', 'data_type', 'description', 'publication_date']]
    return generate_table(results.head(20), 'food-table', False)


# This generates the nutrients table depending on what the user is selecting
@app.callback(Output(component_id='nutrient_output', component_property='children'),
              Input(component_id='nutrient_search', component_property='value')
              )
def pull_nutrients_by_name(nutrient_term):
    results = database.pull_nutrients_by_name(nutrient_term)
    return generate_table(results, 'nutrient-table', True)


# This pulls the nutrients data from the user in the database and adds to the excludes list
def pull_saved_nutrients(user_name):
    nutrient_ids = database.get_user_nutrients(user_name)
    nutrient_map = database.get_nutrient_names(nutrient_ids)
    nutrient_divs = []
    for nutrient_id in nutrient_ids:
        div = html.Div([html.Div('Exclude: {name}'.format(name=nutrient_map[nutrient_id]),
                                 id=str(nutrient_id)),
                        html.Button(id={'exclude-button': nutrient_id},
                                    n_clicks=0, children='Remove')])
        nutrient_divs.append(div)
    return nutrient_divs


# App layout
app.layout = html.Div(style={'backgroundColor': 'rgb(0, 255, 130)'}, children=[
    html.H1("Food Nutrients Look Up", style={
        'text-align': 'center',
        'font_family': 'cursive',
        'font_size': '26px',
    }),
    html.H6("Search for food"),
    html.Div(["User: ", dcc.Input(id='user-name', value='', type='text')]),
    html.Div(["Food Search: ", dcc.Input(id='food_search', value='', type='text')]),
    html.Button(id="submit-button-state", n_clicks=0, children='Submit'),
    html.Div(id='exclude-list'),
    html.Div(dash_table.DataTable(id='food-table'), id='food_output', ),
    html.Br(),
    html.Div(["Search Nutrients (click on row to add to exclude list): ",
              dcc.Input(id='nutrient_search', value='', type='text')]),
    html.Br(),
    html.Div(dash_table.DataTable(id='nutrient-table'), id='nutrient_output'),
    html.Br(),
    html.Div(dcc.Graph(id='scatter-graph', figure=generate_bubble_graph())),
    html.Div(dcc.Graph(id='pie-chart', figure={'layout': {'title': 'Nutrients in Food'}})),
    html.Div(id='food-table-clicked'),
    html.Div(id='delete-exclude-button')
])

if __name__ == '__main__':
    app.run_server(debug=True)
