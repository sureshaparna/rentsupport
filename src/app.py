#Importing Libraries
import os, io, re
import boto3
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from flask_caching import Cache
from dotenv import load_dotenv

# Credentials
load_dotenv()
aws_region = "ap-south-1"
aws_access_key_id = os.environ.get("aws_access_key_id")
aws_secret_access_key = os.environ.get("aws_secret_access_key")

# Image Source
image_source_location = "https://github-projects-resume.s3.ap-south-1.amazonaws.com/Rent_Support/resources/"

# Defining App
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Rent Support"
server = app.server
cache = Cache(server, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})

# Reading Data File
@cache.memoize(timeout=86400)
def read_s3():
    s3_data_path = "s3://github-projects-resume/Rent_Support/data/charity_data.csv"
    s3_client = boto3.client("s3", region_name=aws_region, aws_access_key_id=os.environ.get("aws_access_key_id"),
                                    aws_secret_access_key=os.environ.get("aws_secret_access_key"))

    bucket_name = s3_data_path.split("/")[2]
    file_key = "/".join(s3_data_path.split("/")[3:])
    obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    data = obj['Body'].read().decode('utf-8')

    df = pd.read_csv(io.StringIO(data), header=0)
    df["inside_vic"] = df["State"].apply(
        lambda x: "Victoria-based support organisations" if x in ['Victoria', 'VIC', 'Vic', 'victoria', 'St Helena Victoria', 'VICTORIA', 'Benalla Victoria',
                              'vic' 'Victoria,', 'VIC ', 'Victora'] else "Include national organisations that also operate in Victoria")
    return df


# Webpage HTML Layout
app.layout = html.Div(className="main_page", id="main_page", children=[
    dcc.Location(id='hidden_trigger_url', refresh=False),

    html.Div(className="header", id="header", children=[
        html.Img(className="header_logo", src=image_source_location+"header_support.png"),
        html.P(className="header_title", children="Melbourne Rent Support Finder")
    ]),

    html.Div(className="information_div", id="information_div", children=[
        html.Img(className="information_logo", src=image_source_location+"information_logo.png"),
        html.Div(className="main_information_div", children=[
            html.P(className="information_title", children="Select Your Location Preference for the Support Organisation"),
            html.P(className="information", children="Please note that all organisations listed below operate within Victoria, Australia. Some support service organisations are based in other states, but they deliver services remotely across Victoria. All organisation details provided here apply to services available in Victoria.")
        ])
    ]),

    html.Div(className="radio_button_div", children=[
        html.P(children="Please select your preferred support organisation type:"),
        dcc.RadioItems(className="radio-filter", id='radio-filter',
            labelStyle={'display': 'inline-block', 'margin-right': '20px'},
            inputStyle={'margin-right': '10px'}
        )
    ]),
    
    html.Div(className="dropdown_div", children=[
        html.P("Select your Suburb:"),
        dcc.Dropdown(className="dropdown-filter", id='dropdown-filter',
            options=[], value=None, multi = True
        )
    ]),

    dmc.MantineProvider(html.Div(className= "table_view", id='table_view'))
])


@app.callback(
    [Output("radio-filter", "options"), Output("radio-filter", "value")],
    Input("hidden_trigger_url", "pathname")
)
def update_radio(_):
    data = read_s3()
    values = data['inside_vic'].unique()
    options = [{'label': i, 'value': i} for i in values]
    return options, values[0]


@app.callback(
    Output('dropdown-filter', 'options'),
    Input('radio-filter', 'value')
)
def update_dropdown(value):
    data = read_s3()
    if(value == "Victoria-based support organisations"):
        filtered_data = data[data['inside_vic'] == value]
    else:
        filtered_data = data

    list_of_suburbs = sorted([str(suburb) for suburb in filtered_data["Town_City"].unique()])
    options = [{'label': str(suburb), 'value': str(suburb)} for suburb in list_of_suburbs]
    return options


@app.callback(
    Output('table_view', 'children'),
    Input('dropdown-filter', 'value')
)
def update_table(value):
    data = read_s3()
    final_df = pd.DataFrame(columns=["Name", "Website", "Type", "E-mail", "Phone number"])

    if((value is not None) and (len(value) != 0)):
        filtered_df = data[data["Town_City"].isin(value)]
        filtered_df = filtered_df[['Charity_Legal_Name', 'Charity_Website', 'Advancing_Education', 'Promoting_or_protecting_human_rights', 'Advancing_social_or_public_welfare', 'Children', 'Families', 'Females', 'Financially_Disadvantaged', 'Males', 'People_at_risk_of_homelessness', 'email', 'contact']]

        for index, row in filtered_df.iterrows():
            charity_type = ", ".join([col.replace("_", " ") for col, value in row.items() if str(value).strip() == "Y"])
            final_df = final_df._append({"Name": row['Charity_Legal_Name'].replace("_", " "), "Website": row['Charity_Website'], "Type": charity_type, "E-mail": row['email'],"Phone number": re.sub(r'\D', '', str(row['contact'])) }, ignore_index=True)

    columns = [html.Thead( html.Tr([html.Th(className="table_column_name", children=col) for col in final_df.columns]) )]
    rows = [html.Tr([html.Td(className="table_row", children=final_df.iloc[i][col])  if col != "Website" else html.Td(className="table_row", children=html.A(final_df.iloc[i][col], href = final_df.iloc[i][col], target="_blank")) for col in final_df.columns]) for i in range(len(final_df))]
    body = [html.Tbody(rows)]

    return dmc.Table(children = columns + body, withColumnBorders=True)


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=8002)