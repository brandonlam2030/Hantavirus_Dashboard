import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sheets import count, countUnwell, coords, fieldAgentForm, hospitalForm, smForm
import numpy as np
import news, datetime, gspread
from data import load_cases, load_coordinates
import pydeck as pdk
import matplotlib as mpl
import matplotlib.colors as mcolors

cases = load_cases()
coordinates = load_coordinates()

tab1, tab2, tab3 = st.tabs(["Home", "Predictions", "Report-Case"])

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
    st.session_state.selectCountry = None


st.set_page_config(layout = "wide")

        
groupedCountries = cases.groupby(["country", "year"]).size().reset_index(name = "case_count")
groupedCountries = pd.merge(groupedCountries, coordinates[["population", "country"]], on = "country", how = "left")
groupedCountries = groupedCountries.dropna()
groupedCountries["case_count"] = np.log1p(groupedCountries["case_count"]/groupedCountries["population"]) * 100000

case_points = cases.groupby("country").size().reset_index(name = "case_count")
case_map = pd.merge(case_points, coordinates, on = "country", how = "left")
case_map = case_map.dropna(subset = ["lat", "lon"])

with tab1:
    st.title("Hantavirus Tracking and Prediction Dashboard")

    topAnalytics = st.columns(3)
    upperMiddleGraphs = st.columns([2,1])
    lowerMiddleGraphs = st.columns(2)
    
    with topAnalytics[0]:
        with st.container(border = True, key = "mybox_countCase", height = "stretch"):
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

    norm = mcolors.Normalize(vmin=0, vmax=coordinates["count"].max())
    cmap = mpl.colormaps["YlOrRd"]  

    coordinates["color"] = coordinates["count"].apply(
        lambda c: [int(x*255) for x in cmap(norm(c))[:3]] + [200]
    )


    with upperMiddleGraphs[0]:

        viewState = pdk.ViewState(
            latitude = 0,
            longitude = 0,
            zoom = 1,
            min_zoom = 1,
            pitch = 0,
            bearing = 0
        )

        layer = pdk.Layer(
            "ScatterplotLayer",
            data = coordinates,
            get_position = ["lon", "lat"],
            get_radius = "count",
            radius_scale = 200,
            get_radius_min_pixels = 4,
            pickable = True,
            get_fill_color= "color",
            auto_highlight = True
        )
        
        mapView = pdk.View(
            type="MapView", 
            controller=True,
            wrap_longitude=False,  
            repeat=False          
        )
        
        worldView = pdk.Deck(
            initial_view_state = viewState,
            layers = [layer],
            map_style = "light",
            views = [mapView],
            tooltip = {"text": "{country}\nNumber of Cases to Date: {count}\nPopulation Size: {population}\n"}
        )
        
        st.pydeck_chart(worldView)


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

with tab3:
    fieldAgentDF = pd.DataFrame(fieldAgentForm.get_all_values(), columns = ["patient_id", "year", "country", "syndrome", "age", "sex", "symptoms", "status"])
    hospitalReportDF = pd.DataFrame(hospitalForm.get_all_values(), columns = ["patient_id", "year", "country", "syndrome", "age", "sex", "symptoms", "status"])

    cases["symptoms"] = cases["symptoms"].fillna("").astype(str).str.split(",")
    uniqueSymptoms = cases["symptoms"].explode().dropna().str.strip().unique().tolist()


    def contactForm(id:str):
        contact = st.form(id, clear_on_submit = True)
        
        name = contact.text_input("Full name:")
        city = contact.text_input("Enter city:")
        state = contact.text_input("Enter state:")
        country =  contact.text_input("Enter country:")
        zipCode = contact.text_input("Enter zipCode:")
        email = contact.text_input("Email:")
        
        #need fixing on structure in future
        age, sex = contact.columns(2)
        with age:
            ageNum = contact.number_input("Age", min_value = 1)
        with sex:
            sexVal = contact.segmented_control("Sex", ["Male", "Female"])
        
        symptoms = contact.multiselect("Symptom(s) (Select all that apply)", uniqueSymptoms)
        status = contact.segmented_control("Status", ["Recovered", "Deceased", "Unwell"])

        submit = contact.form_submit_button("Submit")



        if submit:
            if any(len(str(value)) == 0 for value in [name, city, state, country, zipCode, email, ageNum, sexVal, symptoms]): st.warning("Please fill out all sections!!")
            else:
                currentSheet = None
                if id == "FA": currentSheet = fieldAgentDF["patient_id"]
                elif id == "HR": currentSheet = hospitalReportDF["patient_id"]

                if currentSheet.size == 0:
                    currentId = 0
                else:
                    currentId = int(currentSheet.iloc[-1])+1
                results = [currentId, datetime.datetime.now().year, country, "None", ageNum, sexVal, ", ".join(symptoms), status]
                
                
                if country not in coordinates["country"].values:
                    
                    st.warning("Please enter a valid country")

                else:
                    if id == "FA":
                        fieldAgentForm.append_row(results)
                    elif id == "HR":
                        hospitalForm.append_row(results)


                    st.success("Form submitted successfully!")


    def smReport(id:str):
        contact = st.form(id, clear_on_submit = True)

        name = contact.text_input("Name")
        city = contact.text_input("Enter city:")
        state = contact.text_input("Enter state:")
        country = contact.text_input("Enter country")
        platform = contact.selectbox("Platform", ["X", "Instagram", "Facebook", "Discord", "LinkedIn", "Youtube", "Tiktok", "Snapchat", "WhatsApp", "Reddit"])
        user = contact.text_input("Social Media Username")
        age = contact.number_input("Age", min_value = 1)
        sex = contact.segmented_control("Sex", ["Male", "Female"])
        symptoms = contact.multiselect("Symptom(s) (Select all that apply)", uniqueSymptoms)
        status = contact.segmented_control("Status", ["Recovered", "Deceased", "Unwell"])
        submit = contact.form_submit_button("Submit")

        if submit:
            if any(len(str(value)) == 0 for value in [name, city, state, country, platform, user, age, sex, symptoms]): st.warning("Please fill out all sections!!")
            else:
                results = [name,city,state,country,platform,user,age,sex,", ".join(symptoms),datetime.datetime.now().year, status]
                
                if country not in coordinates["country"].values:
                    
                    st.warning("Please enter a valid country")
                else:
                    smForm.append_row(results)

                    st.success("Form submitted successfully!")



    st.title("Report Cases of Hantavirus")

    fieldAgent = st.expander("Submit field agent data")
    hospitalReport = st.expander("Report Hospital Cases")
    socialMedia = st.expander("Social Media Report Form")

    with fieldAgent:
        contactForm("FA")

    with hospitalReport:
        contactForm("HR")

    with socialMedia:
        smReport("SM")