from covid_india import states
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
import plotly_express as px

rcParams.update({'figure.autolayout': True})

SUBHEAD_TITLE = "COVID-19 Dashboard and Vulnerability Analysis"
SUBHEAD_CREDITS = "Made by Epochalypse Team for HackJaipur 2020"

def get_ui_for_data(data_input):
    column_properties = "margin:3%; float:right; width:15%; text-align: right"
    base_card_styling = "margin:1%; padding:1%; " \
                        "text-align:center;" \
                        "width:16%; " \
                        "box-shadow:0 4px 8px 0 rgba(0,0,0,0.2);"
    return f"<div class='row'>" \
           f"<h5 style='color:black; {column_properties}'>{data_input[0]}</h5>" \
           f"<h5 style='color:blue; {base_card_styling}'><h6>Total</h6>{data_input[1]}</h5> " \
           f"<h5 style='color:red; {base_card_styling}'><h6>Active</h6>{data_input[2]}</h5> " \
           f"<h5 style='color:green; {base_card_styling}'><h6>Saved</h6>{data_input[3]}</h5> " \
           f"<h5 style='color:orange; {base_card_styling}'><h6>Deaths</h6>{data_input[4]}</h5> " \
           f"</div>"

@st.cache
def load_global_death_data():
    # Pull data from Johns Hopkins source
   data = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv', error_bad_lines=False)
   # Drop columns province/state, geographic coordinates
   data.drop(['Province/State', 'Lat', 'Long'], axis=1, inplace=True)
   # Groupby country
   data = data.groupby(['Country/Region']).sum()
   return data

def date_convert(df):
    # transpose the frame
    df_tran = df.transpose().reset_index()
    # Next rename the column 
    df_tran.rename({'index': 'Date'}, axis=1, inplace=True)
    # Convert the date column to datetime
    df_tran['Date'] =  pd.to_datetime(df_tran['Date'])
    return df_tran

def tidy_death_data(df,group):
    df_tidy = pd.melt(df, id_vars=['Date'])
    df_tidy.drop(df_tidy[df_tidy['value'] < 10].index, inplace=True) # Drop all dates and countries with less than 10 recorded deaths
    df_tidy = df_tidy.assign(Days=df_tidy.groupby(group).Date.apply(lambda x: x - x.iloc[0]).dt.days) # Calculate # of days since 10th death by country
    # calculate daily change in deaths (raw)
    df_tidy['daily_change'] = df_tidy.sort_values([group,'Days']).groupby(group)['value'].diff()
    # calculate daily change in deaths (%)
    df_tidy['daily_pct_change'] = df_tidy.sort_values([group,'Days']).groupby(group)['value'].pct_change() * 100
    # calculate 7-day rolling average in deaths (raw)
    df_tidy['daily_roll_avg'] = df_tidy.groupby(group)['daily_change'].rolling(7).mean().round().reset_index(0,drop= True)
    # calculate 7-day rolling average in deaths (%)
    df_tidy['daily_pctchange_roll_avg'] = df_tidy.groupby(group)['daily_pct_change'].rolling(7).mean().round().reset_index(0,drop= True)

    # Replace the first day (NaN) as zero and missing rolling averages with the value that day
    df_tidy['daily_change'].fillna(0, inplace=True)
    df_tidy['daily_pct_change'].fillna(0, inplace=True)
    df_tidy['daily_roll_avg'].fillna(df_tidy['daily_change'], inplace=True)
    df_tidy['daily_pctchange_roll_avg'].fillna(df_tidy['daily_pct_change'], inplace=True)
    return df_tidy

def global_plot_create(data, x, y, title, xaxis, yaxis):
    fig = px.line(data, x=x, y=y, color='Country/Region', width=800, height=600)
    fig.update_layout(title=title, 
                      xaxis_title= xaxis, 
                      yaxis_title = yaxis,
                      legend_title_text='Countries',
                      yaxis_type="log", 
                      yaxis_tickformat = 'f',
                      xaxis_gridcolor = 'LightBlue',
                      yaxis_gridcolor = 'LightBlue',
                      paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)')
    return fig    

def load_data_and_return_dataframe():
    all_cases = states.getdata()
    data = []
    for state in all_cases:
        temp = []
        temp.append(state)
        for key in all_cases[state]:
            temp.append(all_cases[state][key])
        data.append(temp)
    return pd.DataFrame(data, columns=["State", "Total", "Active", "Cured", "Death"])

df = load_data_and_return_dataframe()
def main():
    page = st.sidebar.selectbox("Choose a feature", ['Homepage', 'Global' ,'INDIA', 'Another One'])

    if page == 'Homepage':
        st.title("COVID-19 Dashboard")
        st.header("Exploration of COVID-19 Deaths")
        st.subheader("Use the selection panel on the left.")
    elif page == 'Global':
        global_data = load_global_death_data()
        global_data = date_convert(global_data)
        global_deaths = tidy_death_data(global_data, group = 'Country/Region')

        st.title('Global COVID-19 Deaths')
        st.header('Daily COVID-19 deaths by country from Jan 22, 2020 - Present.')
        st.write("Raw Data:", global_data)

        # Create a list to pick the countries we want to look at
        # list uses the column names (the countries) of our original data
        cols = list(global_data[global_data.columns.difference(['Date'])])
        countries = st.multiselect('Select countries display', cols, ["US", "India", "China"])

        # Set index in order to use loc operation
        global_deaths.set_index('Country/Region', inplace=True)
        # Limit the data to the countries selected above. 
        data_plot = global_deaths.loc[countries] 
        data_plot.reset_index(inplace=True)

        # Select the variable to be plotted
        cols = ['Total Confirmed Deaths', 'Deaths per Day','Daily Percentage Change']
        variable = st.selectbox('Select variable to display', cols)

        if variable == 'Total Confirmed Deaths':
            fig=global_plot_create(data = data_plot, 
                        x = 'Days',
                        y = 'value',
                        title = 'Global COVID-19 Deaths - Total',
                        xaxis = 'Number of days since 10th death',
                        yaxis = 'Confirmed Deaths')
            st.plotly_chart(fig)

    elif page == 'INDIA':
        st.title("COVID19 India DashBoard")
        st.header("COVID19 Dashboard made using Python and Streamlit")
        st.subheader("Check any State Status")
        sel_state = st.multiselect(label="Select State", options=df["State"])
        if sel_state:
            states = []
            for c in sel_state:
                states.append(df[df["State"] == c].values)
            for arr in states:
                data = arr[0]
                st.markdown(get_ui_for_data(data), unsafe_allow_html=True)

        st.markdown("<h2>Top 10 States affected</h2>", unsafe_allow_html=True)
        top_10 = df.nlargest(10, ["Total"])
        fig = go.Figure(data = [
            go.Bar(name="Total", x=top_10["State"], y=top_10["Total"]),
            go.Bar(name="Active", x=top_10["State"], y=top_10["Active"]),
            go.Bar(name="Cured", x=top_10["State"], y=top_10["Cured"]),
            go.Bar(name="Deaths", x=top_10["State"], y=top_10["Death"])
        ])
        st.plotly_chart(fig, use_container_width=True)

        for data in df.nlargest(10, ["Total"]).values:
            st.markdown(get_ui_for_data(data), unsafe_allow_html=True)

        st.markdown("<h3> All States Data</h3>", unsafe_allow_html=True)
        st.write("Raw Data:", df)
        
st.sidebar.title(SUBHEAD_TITLE)
st.sidebar.subheader(SUBHEAD_CREDITS)
if __name__ == '__main__':
    main()
