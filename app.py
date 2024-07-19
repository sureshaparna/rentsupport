#Importing Libraries
from dash import Dash, dcc, html, Input, Output
from plotly.express import data
import pandas as pd
import dash_bootstrap_components as dbc

#Reading Data File
data = pd.read_csv(r"data_charity.csv")
data["inside_vic"] = data["State"].apply(lambda x: "Only Victorian support organisations" if x in ['Victoria', 'VIC','Vic', 'victoria', 'St Helena Victoria', 'VICTORIA', 'Benalla Victoria', 'vic' 'Victoria,', 'VIC ', 'Victora'] else "Support organisations that operate across Australia including Victoria")

#Webpage HTML
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server
app.layout = html.Div(children=[
    html.Br(),
    html.H3('Select your location preference for the Support organisation', style = {'textAlign':'center'}),
    html.P('''Please note that all the organisations given below operate in Victoria. 
           There are some support service organisations that are based on the other states of Australia, 
           but all of them operate in Victoria remotely. All the organisation details that you see, operate in 
           Victoria, Australia.''', style = {'margin-left': '10%', 'width': '80%', 'textAlign':'center'}),
    
    html.Br(),
    html.H4('Please enter your preferred support organisation:', style = {'textAlign':'center'}),
    
    dcc.RadioItems(
        id='radio-filter',
        options=[{'label': i, 'value': i} for i in data['inside_vic'].unique()],
        value = data['inside_vic'].unique()[0],
        labelStyle={'display': 'inline-block', 'margin-right': '20px'},
        inputStyle={'margin-right': '10px'},
        style = {'textAlign':'center'}
    ),
    
    html.Br(),
    html.H4('Select from the given Suburbs:', style = {'textAlign':'center'}),
    dcc.Dropdown(
        id='dropdown-filtered',
        options=[],
        value=None,
        multi = True,
        style={'margin-left': '15%', 'width': '70%'}
    ),
    
    html.Br(),
    html.Div(id='output', style={'width': '90%', 'border': 'solid', 'border-width': '2px', 'border-collapse': 'separate', 'margin-left':'5%'}),
    html.Br(),
    html.Br()
], style={'backgroundColor': '#EAE8DC', 'minHeight': '100vh', 'height': '100%'})

@app.callback(
    Output('dropdown-filtered', 'options'),
    Input('radio-filter', 'value')
)

def update_dropdown(value):
    if(value == "Only Victorian organisations"):
        filtered_data = data[data['inside_vic'] == value]
    else:
        filtered_data = data
    list_of_suburbs = sorted([str(suburb) for suburb in filtered_data["Town_City"].unique()])
    options = [{'label': str(suburb), 'value': str(suburb)} for suburb in list_of_suburbs]
    return options

@app.callback(
    Output('output', 'children'),
    Input('dropdown-filtered', 'value')
)

def update_table(value):
    final_df = pd.DataFrame(columns=["Name", "Website", "Type", "E-mail", "Phone number"])

    if((value is not None) and (len(value) != 0)):
        filtered_df = data[data["Town_City"].isin(value)]
        filtered_df = filtered_df[['Charity_Legal_Name', 'Charity_Website', 'Advancing_Education', 'Promoting_or_protecting_human_rights', 'Advancing_social_or_public_welfare', 'Children', 'Families', 'Females', 'Financially_Disadvantaged', 'Males', 'People_at_risk_of_homelessness', 'email', 'contact']]

        for index, row in filtered_df.iterrows():
            charity_type = [col for col, value in row.items() if str(value).strip() == "Y"]
            final_df = final_df._append({"Name": row['Charity_Legal_Name'], "Website": row['Charity_Website'], "Type": str(charity_type).replace("[", "").replace("]", ""), "E-mail": row['email'],"Phone number": row['contact']}, ignore_index=True)

    table_data = [html.Tr([html.Th(col, style={'width':'27%', 'padding': '10px', 'border-bottom': '2px solid black'}) for col in final_df.columns])] + \
                 [html.Tr([html.Td(final_df.iloc[i][col], style={'padding': '10px'})  if col != "Website" else html.Td(html.A(final_df.iloc[i][col], href = final_df.iloc[i][col])) for col in final_df.columns])
                  for i in range(len(final_df))]
    return table_data


if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0", port=8002)
