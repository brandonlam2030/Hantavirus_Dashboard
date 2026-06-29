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
    return news.getNews()

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
    background-color: #2c3b50 !important;
    color: white !important;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 15px;
}
</style>
""")

if "clickedPoints" not in st.session_state:
    st.session_state.clickedPoints = {}


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


with topAnalytics[0]:
    with st.container(border = True, key = "mybox_countCase"):
        st.write("###### Number of Confirmed")
        st.header(len(cases))
        st.write("+" + str(count()) + " cases pending review")

with topAnalytics[1]:
    with st.container(border = True, key = "mybox_activeCase"):
        st.write("###### Current Active Cases")
        st.header(4)

with upperMiddleGraphs[0]:
    with st.container(border = True, key="mybox_globe"):

        globe = go.Figure(data = go.Scattergeo(
        lon = coordinates["lon"],
        lat = coordinates["lat"],
        text = coordinates["country"],
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
            title = "Mapping Cases Globally (2000-Present)",
            geo = dict(bgcolor = "rgba(0,0,0,0)"),
            paper_bgcolor = "rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height = 600,
            width = 600
        )


        globeClick = st.plotly_chart(globe, width = "stretch", on_select = "ignore")

       


with lowerMiddleGraphs[0]:

    with st.container(border = True, key="mybox_line"):
        lineChart = px.line(groupedCountries, x = "year", y = "case_count", color = "country", title = "Normalized Tracking of Cases per Country", labels = {"year":"Year", "case_count": "Normalized Case Count"})
        lineChart.update_layout(
            plot_bgcolor = "#2c3b50",
            paper_bgcolor = "#2c3b50",
            title_font_color = "white",
            title_subtitle_font_color= "white",
            legend_font_color = "white",
            font_color = "white",
            legend_title_font_color = "white"
        )

        lineChart.update_xaxes(
            title_font_color="white",  
            tickfont_color="white"     
        )

        lineChart.update_yaxes(
            title_font_color="white",  
            tickfont_color="white"     
        )
        st.plotly_chart(lineChart)

        yearlyCounts = cases.groupby("year").size().reset_index(name = "count")


with upperMiddleGraphs[1]:

    with st.container(border = True, key = "mybox_newsContainer"):
        st.subheader("RECENT HANTAVIRUS NEWS")

        data = get_cached_news()

        for article in data[0:5]:
            createArticleBox(article)

