import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sheets import count, countUnwell
import numpy as np
import news
from data import load_cases, load_coordinates


cases = load_cases()
coordinates = load_coordinates()


title, button = st.columns([20,1])
github = ""


@st.cache_data(ttl = 900)
def get_cached_news():
    results = news.getNews()
    
    return results[0], results[1]

data, numOfResponses = get_cached_news()

def createArticleBox(inputNews):
       
    organizedTitle = inputNews["title"].split()
    shortenedTitle = ""

    if len(organizedTitle) < 6: 
        shortenedTitle = (" ".join(organizedTitle))
    else:
        shortenedTitle = (" ".join(organizedTitle[0:6]) + "...")
    
    st.link_button(label = f"{shortenedTitle}  -  {inputNews["source"]["name"]}", url = inputNews["url"], width = "stretch")


st.html("""
<style>
/* This single rule applies to ANY container containing "mybox" in its key */
div[class*="st-key-mybox"] {
    background-color: #accfff !important;
    color: white !important;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 15px;
}
</style>
""")

st.markdown(
    """
    <style>
    /* Force color on all levels of Streamlit headers */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #4e5b68 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


if "clickedPoints" not in st.session_state:
    st.session_state.clickedPoints = {}

if "selectCountry" not in st.session_state:
    st.session_state.selectedCountry = None

with title:
    st.title("Hantavirus Tracking and Prediction Dashboard")
with button: 
    st.button("PowerBI", type = "primary")    
st.set_page_config(layout = "wide")




topAnalytics = st.columns(3)
upperMiddleGraphs = st.columns([2,1])
lowerMiddleGraphs = st.columns(2)
        
groupedCountries = cases.groupby(["country", "year"]).size().reset_index(name = "case_count")
groupedCountries = pd.merge(groupedCountries, coordinates[["population", "country"]], on = "country", how = "left")
groupedCountries = groupedCountries.dropna()
groupedCountries["case_count"] = np.log1p(groupedCountries["case_count"]/groupedCountries["population"]) * 100000

case_points = cases.groupby("country").size().reset_index(name = "case_count")
case_map = pd.merge(case_points, coordinates, on = "country", how = "left")
case_map = case_map.dropna(subset = ["lat", "lon"])


with topAnalytics[0]:
    with st.container(border = True, key = "mybox_countCase"):
        st.write("###### Number of Confirmed")
        st.header(len(cases))
        st.write(f"##### :red[+ {str(count())} cases pending review]")


with topAnalytics[1]:
    with st.container(border = True, key = "mybox_activeCase", height = "stretch"):
        st.write("###### Current Active Cases")
        st.header(countUnwell())


with topAnalytics[2]:
    with st.container(border = True, key = "mybox_newsCount", height = "stretch"):
        st.subheader("TOTAL NUMBER OF RECENT ARTICLES")
        st.header(numOfResponses)


with upperMiddleGraphs[0]:
    print("hello")

        # if st.session_state.selectCountry:
        #     fig = go.Figure()

        #     fig.trace(go.Bar(x = groupedCountries["year"]))


with lowerMiddleGraphs[0]:

    with st.container(border = True, key="mybox_line"):
        lineChart = px.line(groupedCountries, x = "year", y = "case_count", color = "country", title = "Normalized Tracking of Cases per Country", labels = {"year":"Year", "case_count": "Normalized Case Count"})
        lineChart.update_layout(
            plot_bgcolor = "#b0d2ff",
            paper_bgcolor = "#b0d2ff",
            title_font_color = "#4e5b68",
            title_subtitle_font_color= "#4e5b68",
            legend_font_color = "#4e5b68",
            font_color = "#4e5b68",
            legend_title_font_color = "#4e5b68"
        )

        lineChart.update_xaxes(
            title_font_color="#4e5b68",  
            tickfont_color="#4e5b68"     
        )

        lineChart.update_yaxes(
            title_font_color="#4e5b68",  
            tickfont_color="#4e5b68"     
        )
        st.plotly_chart(lineChart)

        yearlyCounts = cases.groupby("year").size().reset_index(name = "count")


with lowerMiddleGraphs[1]:
    with st.container(border = True, key = "mybox_pi"):
        severityCounts = cases.groupby("severity").size().reset_index(name = "count")

        piChart = px.pie(severityCounts, color = "severity", values = "count", names = "severity", title = "Case Severity", color_discrete_map = {
            "Mild": "lightcyan",
            "Severe": "cyan",
            "Moderate": "royalblue",
            "Critical": "darkblue"
        })
        
        
        piChart.update_layout(
            plot_bgcolor = "#accfff",
            paper_bgcolor = "#b0d2ff"
        )

        st.plotly_chart(piChart)


with upperMiddleGraphs[1]:
    with st.container(border = True, key = "mybox_newsContainer"):
        st.subheader("RECENT HANTAVIRUS NEWS")

        for article in data[0:6]:
            createArticleBox(article)

    with st.container(border = True, key="mybox_globe"):

        globe = go.Figure(data = go.Scattergeo(
        lon = coordinates["lon"],
        lat = coordinates["lat"],
        text = coordinates["country"],
        customdata = coordinates["country"],
        mode = "markers",
        marker = dict(size = coordinates["count"].astype("float32"), sizemode = "area", sizeref = 2*max(coordinates["count"].astype(int))/ (30**2), sizemin = 1,color=coordinates["count"].astype(int), colorscale = "YlOrRd", showscale = True)))
        
        globe.update_geos(
            projection = dict(type = "orthographic"),
            showcoastlines = True, coastlinecolor = "rgba(0,0,0,0.5)",
            showland = True, landcolor = "#B4FFB4",
            showocean = True, oceancolor = "LightSkyBlue",
            showlakes = True, lakecolor = "LightSkyBlue",
            showcountries=True, countrycolor="#888888",  
        )

        globe.update_layout(
            title = "Global Case Counts at a Glance",
            geo = dict(bgcolor = "rgba(0,0,0,0)", domain=dict(x=[0, 1], y=[0, 1])),
            paper_bgcolor = "rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=30, b=0),
            height = 400,
            width = 400
        )


        st.plotly_chart(globe)
