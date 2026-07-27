import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sheets import count, countUnwell, coords, fieldAgentForm, hospitalForm, smForm
import numpy as np
import news, datetime
from data import load_cases, load_coordinates
import pydeck as pdk
import matplotlib as mpl
import matplotlib.colors as mcolors
from streamlit_float import *
from langchain_learn.first import getAgent, invokeWithRetry
import requests
from model.spillover import getRiskAvg, getFactors, getGraphData, getRiskDistributionChart
from model.rodentMomentum import getMomentumScore
from model.infectionRate import getInfectionScore, getTopFactorsChart

otherGeojson = requests.get(
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
).json()

usGeojson = {
    "type": "FeatureCollection",
    "features": [
        f for f in otherGeojson["features"]
        if f["properties"].get("ADMIN") == "United States of America"
    ]
}

otherGeojson = {
    "type": "FeatureCollection",
    "features": [
        f for f in otherGeojson["features"]
        if f["properties"].get("ADMIN") != "United States of America"
    ]
}

usStatesGeojson = requests.get(
    "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
).json()


float_init()
cases = load_cases()
coordinates = load_coordinates()
tab1, tab2, tab3, tab4 = st.tabs(["Home", "Predictions", "Report Human Cases", "Details"])
github = ""
agent = getAgent()

def render_gauge(label, sublabel, value_pct, color, width=315, height=460):
    circle_dim = min(width, height)      
    radius = circle_dim * 0.41
    center = circle_dim / 2
    stroke_width = circle_dim * 0.07
    circumference = 2 * 3.14159 * radius
    offset = circumference * (1 - value_pct / 100)
    font_size = circle_dim * 0.18

    html = f"""
    <div style="background:#2D5133; border-radius:12px; padding:16px; text-align:center; width:{width}px; height:{height}px; display:flex; flex-direction:column; justify-content:center; align-items:center;">
        <div style="color:#e5e5e5; font-weight:600; font-size:14px;">{label}</div>
        <div style="color:{color}; font-weight:700; font-size:15px; margin-bottom:8px;">{sublabel}</div>
        <svg width="{circle_dim}" height="{circle_dim}" viewBox="0 0 {circle_dim} {circle_dim}">
            <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="#2d3d33" stroke-width="{stroke_width}"/>
            <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="{color}" stroke-width="{stroke_width}"
                stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                stroke-linecap="round" transform="rotate(-90 {center} {center})"/>
            <text x="{center}" y="{center + font_size*0.3}" text-anchor="middle" fill="#e5e5e5" font-size="{font_size}" font-weight="700">
                {value_pct:.0f}%
            </text>
        </svg>
        <div style="color:#8a9a90; font-size:12px;">Accuracy</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

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

st.markdown("""
<style>
/* Text input */
div[data-baseweb="input"] > div {
    background-color: white !important;
}

/* Number input */
div[data-baseweb="input"] input {
    background-color: white !important;
}

/* Selectbox */
div[data-baseweb="select"] > div {
    background-color: white !important;
}

/* Text area */
textarea {
    background-color: white !important;
}
</style>
""", unsafe_allow_html=True)

st.html("""
<style>
/* This single rule applies to ANY container containing "mybox" in its key */
div[class*="st-key-mybox"] {
    background-color: #2D5133 !important;
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
    stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #c0d1c9 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown("""
    <style>
    div[class*="st-key-chat_bubble"] button {
        border-radius: 50%;
        width: 60px;
        height: 60px;
        font-size: 24px;
        background-color: #5C3D53 !important;
        color: #f3f4ef !important;
        border: none !important;
        box-shadow: 0 4px 8px rgba(31,43,36,0.25);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    div[class*="st-key-mapContainer"] {
        position: relative;
    }
    </style>
""", unsafe_allow_html=True)

if "clickedMap" not in st.session_state:
    st.session_state.clickedMap = False

if "selectCountry" not in st.session_state:
    st.session_state.selectCountry = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "showChat" not in st.session_state:
    st.session_state.showChat = False

if "intro" not in st.session_state:
    st.session_state.intro = True

st.set_page_config(layout = "wide")     
groupedCountries = cases.groupby(["country", "year"]).size().reset_index(name = "case_count")
groupedCountries = pd.merge(groupedCountries, coordinates[["population", "country"]], on = "country", how = "left")
groupedCountries = groupedCountries.dropna()
groupedCountries["case_count"] = np.log1p(groupedCountries["case_count"]/groupedCountries["population"]) * 100000

case_points = cases.groupby("country").size().reset_index(name = "case_count")
case_map = pd.merge(case_points, coordinates, on = "country", how = "left")
case_map = case_map.dropna(subset = ["lat", "lon"])

bubble = st.container()
with bubble:
    if st.button("💬", key = "chat_bubble"):
        st.session_state.showChat = not st.session_state.showChat
        st.session_state.intro = False

    bubble.float("position: fixed; bottom: 35px; left: 20px; z-index: 9999; height:40px")

    if st.session_state.intro:
        introduction = st.container(border = True)
        with introduction:
            st.write("Hi, I am a Hantavirus assistance agent. Feel free to click below, and ask any questions or inquiries about the Hantavirus.\n⬇️")

        introduction.float(
            "position: fixed; bottom: 85px; z-index: 9999; height:100px; left:20px; width: 400px; background: white; border: 1px solid black;"
        )
if st.session_state.showChat:

    chatMessages = st.container(border = True, key = "chatMessages")
    
    with chatMessages:
        if st.session_state.messages:
            for message in st.session_state.messages:
                st.chat_message(message["role"]).markdown(message["content"])

    chatMessages.float(
        "position: fixed; bottom: 145px; left: 20px; width: 500px; height: 310px; "
        "overflow-y: auto; z-index: 999; background-color: white; "
        "border-radius: 8px; padding: 8px; border: 1px solid #3d5c46;"
    )
        
    prompt = st.chat_input("Type Here", max_chars = 80)


    st.markdown("""
        <style>
        div[data-testid="stChatInput"] {
            position: fixed !important;
            bottom: 85px !important;
            left: 20px !important;
            width: 500px !important;
            z-index: 998 !important;
            border: 1px solid #3d5c46 !important;
            border-radius:8px !important;
            
        }
        </style>
    """, unsafe_allow_html = True)


    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

      
        inputPrompt = {"messages":[{"role":"user", "content":prompt}]}
        response = invokeWithRetry(agent, inputPrompt)

        st.chat_message("assistant").markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
    


with tab1:
    st.title("Hantavirus Tracking and Prediction Dashboard")

    topAnalytics = st.columns(3)
    upperMiddleGraphs = st.columns([2,1])
    lowerMiddleGraphs = st.columns(2)
    
    with topAnalytics[0]:
        with st.container(border = True, key = "mybox_countCase", height = "stretch"):
            st.write("###### Number of Exposure Cases")
            st.subheader(f"10000")
            st.write(f"##### :red[+ {str(count())} cases pending review]")
            # st.write("###### Number of Rodent Hantavirus Carriers")
            # st.header(f"{len(rodent.loc[(rodent["testPathogenName"] == 'Hantaan virus') & (rodent["testResult"] == 'Positive')])} rodents")
            # st.write(f"##### :red[+ {str(count())} cases pending review]")


    with topAnalytics[1]:
        with st.container(border = True, key = "mybox_activeCase", height = "stretch"):
            st.write("###### Current Active Cases")
            st.subheader(f"{str(count())} active cases")
            time = datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S')
            st.write(f"##### :red[Last updated on {time[0:10]} at {time[10:]}]")


    with topAnalytics[2]:
        with st.container(border = True, key = "mybox_newsCount", height = "stretch"):
            st.subheader("TOTAL NUMBER OF RECENT ARTICLES")
            st.subheader(numOfResponses)

    norm = mcolors.Normalize(vmin=0, vmax=coordinates["count"].max())
    cmap = mpl.colormaps["YlOrRd"]  

    coordinates["color"] = coordinates["count"].apply(
        lambda c: [int(x*255) for x in cmap(norm(c))[:3]] + [200]
    )

    cdcData = pd.read_csv("data/cdc.csv")
    normState = mcolors.Normalize(vmin = 0, vmax = cdcData["cumulativeCases"].max())
    cmapState = mpl.colormaps["YlOrRd"]

    cdcData["color"] = cdcData["cumulativeCases"].apply(
        lambda c: [int(x*255) for x in cmapState(normState(c))[:3]] + [120]
    )

    with upperMiddleGraphs[0]:
        viewState = None
        mapContainer = st.container(key = "mapContainer")
        with mapContainer:

            if not st.session_state.clickedMap:
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
                    auto_highlight = True,
                    selectable = True,
                )
                us_layer = pdk.Layer(
                    "GeoJsonLayer",
                    data=usGeojson,         
                    id="us-outline",
                    pickable=True,             
                    auto_highlight=True,   
                    highlight_color=[255, 255, 0, 120],  
                    get_fill_color=[30, 100, 200, 60],
                    get_line_color=[60, 60, 60, 50],
                    get_line_width=2000,
                    stroked=True,
                    filled=True,
                    line_width_min_pixels = 1
                )
                ocean_layer = pdk.Layer(
                    "PolygonLayer",
                    data=[{"polygon": [[-300, -90], [300, -90], [300, 90], [-300, 90]]}],
                    get_polygon="polygon",
                    get_fill_color=[192,223,243, 160], 
                    stroked=False,
                )
                

                rest_of_world_layer = pdk.Layer(
                    "GeoJsonLayer",
                    data=otherGeojson,
                    id="background",
                    pickable=False,       
                    auto_highlight=False,
                    get_fill_color= [180,255,180, 150],
                    stroked=True,
                    get_line_color=[60, 60, 60, 50],   
                    get_line_width=1,
                    line_width_min_pixels=1
                )
                deck = pdk.Deck(layers=[ocean_layer, rest_of_world_layer, us_layer,layer], initial_view_state=viewState,map_style = "light",tooltip = {"text": "{country}\nNumber of Cases to Date: {count}\nPopulation Size: {population}\n"})

                event = st.pydeck_chart(deck, on_select="rerun", selection_mode="single-object",key=f"pydeck_{st.session_state.clickedMap}",)

                if event.selection and event.selection.get("objects", {}).get("us-outline"):
                    st.session_state.clickedMap = True
                    st.rerun()
            else:
                color_lookup = dict(zip(cdcData["state"], cdcData["color"])) 

                
                for feature in usStatesGeojson["features"]:
                    stateId = feature["properties"]["name"]  
                    feature["properties"]["color"] = color_lookup.get(stateId, [200, 200, 200, 100])
                    stateCount = cdcData.loc[cdcData["state"] == stateId, "cumulativeCases"] 
                    feature["properties"]["count"] = int(stateCount.values[0]) if not stateCount.empty else 0

                innerViewState = pdk.ViewState(
                    latitude = 38,
                    longitude = -97,
                    zoom = 3,
                    min_zoom = 3,
                    max_zoom = 3,
                    pitch = 0,
                    bearing = 0
                )

                states_layer = pdk.Layer(
                    "GeoJsonLayer",
                    data=usStatesGeojson,   
                    id="us-states",
                    pickable=True,
                    auto_highlight=True,
                    highlight_color=[255, 255, 0, 80],
                    get_fill_color= "properties.color",
                    get_line_color=[255, 255, 255, 200],
                    get_line_width=1000,
                )
                
                deck = pdk.Deck(layers=[states_layer], initial_view_state=innerViewState,map_style = "light",tooltip = {"text": "{name}\nNumber of Cases from 1993 - 2023: {count}"})
                event = st.pydeck_chart(deck, on_select="rerun", selection_mode="single-object",key=f"pydeck_{st.session_state.clickedMap}",)

                backButtonContainer = st.container(key="back_button_container")
                with backButtonContainer:
                    if st.button("← Back", key="back_to_world"):
                        st.session_state.clickedMap = False
                        st.rerun()
                backButtonContainer.float(
                    "position: absolute; top: 12px; left: 12px; z-index: 999;"
                )

            
        

        
        
        

        graphs = st.columns(2)
        with graphs[0]:
            with st.container(border = True, key="mybox_line"):
                lineChart = px.line(groupedCountries, x = "year", y = "case_count", color = "country", title = "Normalized Tracking of Cases per Country", labels = {"year":"Year", "case_count": "Normalized Case Count"})
                lineChart.update_layout(
                    plot_bgcolor = "#2D5133",
                    paper_bgcolor = "#2D5133",
                    title_font_color = "#c0d1c9",
                    title_subtitle_font_color= "#c0d1c9",
                    legend_font_color = "#c0d1c9",
                    font_color = "#c0d1c9",
                    legend_title_font_color = "#c0d1c9"
                )

                lineChart.update_xaxes(
                    title_font_color="#c0d1c9",  
                    tickfont_color="#c0d1c9"     
                )

                lineChart.update_yaxes(
                    title_font_color="#c0d1c9",  
                    tickfont_color="#c0d1c9"     
                )
                st.plotly_chart(lineChart)

                
                with graphs[1]:
                    with st.container(border = True, key = "mybox_pi"):
                        severityCounts = cases.groupby("severity").size().reset_index(name = "count")

                        piChart = px.pie(severityCounts, color = "severity", values = "count", names = "severity", title = "Case Severity", color_discrete_map = {
                            "Mild": "lightcyan",
                            "Severe": "cyan",
                            "Moderate": "royalblue",
                            "Critical": "darkblue"
                        })
                        
                        piChart.update_traces(textfont_color="black")
                        
                        piChart.update_layout(
                            plot_bgcolor = "#2D5133",
                            paper_bgcolor = "#2D5133",
                            title_font_color = "#c0d1c9",
                            title_subtitle_font_color= "#c0d1c9",
                            legend_font_color = "#c0d1c9",
                            font_color = "#c0d1c9",
                            legend_title_font_color = "#c0d1c9"
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
                height = 500,
                width = 400,
                title_font_color = "#c0d1c9",
                title_subtitle_font_color= "#c0d1c9",
                legend_font_color = "#c0d1c9",
                font_color = "#c0d1c9",
                legend_title_font_color = "#c0d1c9"
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



    st.title("Report Human Cases of the Hantavirus")

    fieldAgent = st.expander("Submit field agent data")
    hospitalReport = st.expander("Report Hospital Cases")
    socialMedia = st.expander("Social Media Report Form")

    with fieldAgent:
        contactForm("FA")

    with hospitalReport:
        contactForm("HR")

    with socialMedia:
        smReport("SM")


with tab4:
    
    with st.container(key = "mybox_hantaIntro", border = True):
        columns = st.columns(2)
        with columns[0]:
            st.subheader("Hantavirus")
            st.subheader("Ecology, Transmission, and Risks")
            st.write(f"##### Hantaviruses are rodent-born viruses that can cause severe respiratory disease in humans. This page provides key details about the virus, its origin/transmission and human spillover risks predicted by a geospatial-temporal epidemiology model.")

        with columns[1]:
            imageSpace = st.columns(2)

            with imageSpace[0]:
                st.image("mouse.jpg", width = "stretch")
            with imageSpace[1]:
                st.image("hv.jpg", width = "stretch")

    
    columns = st.columns(4)

    with columns[0]:
        with st.container(key = "mybox_detail1", border = True, height = "stretch"):
            st.subheader("What is Hantavirus?")
            st.write(f"##### Hantavirus are a group of rodent born viruses. Human cases exhibit 2 common scenarios: Hantavirus Pulmonary Syndrome (HPS) and Hemorrhagic Fever with Renal Syndrome (HFRS)")

    with columns[1]:
        with st.container(key = "mybox_detail4", border = True, height = "stretch"):
            st.subheader("Transmission")
            st.write(f"##### Though human cases are rare, they are not impossible. The virus typically spreads to humans through contact with rodents like rats and mice, especially from exposure to their urine, droppings and saliva.")
            
    with columns[2]:
        with st.container(key = "mybox_detail2", border = True, height = "stretch"):
            st.subheader("Symptoms")
            st.write(f"##### Symptoms of the hantavirus vary according to syndrome, however common symptoms are fever, headaches, nausea, muscle aches, and abdominal problems.")

    with columns[3]:
        with st.container(key = "mybox_detail3", border = True, height = "stretch"):
            st.subheader("Treatment")
            st.write(f"##### Though there is not specific treatment for the virus, patients should receive supportive care that includes rest, hydration and surveilance. HPS patients may need breathing assitance, whereas HFRS patients may require, dialysis to remove harmful toxins in the kidneys.")

    with st.container(key = "mybox_modelDiagram"):
        st.subheader("Hantavirus Transmission Chain of Events")

                
        split = st.columns([1,10,1])
        with split[1]: 
            st.image("diagram.png", width = "stretch")

    # factors = st.columns(3)

    # with factors[0]:
    #     with st.container(key = "mybox_modelDiagram2", width = "content"):
    #         st.subheader("Model Architecture")
    #         st.image("modelDiagram.png", width = 400)


with tab2:
    st.title("Hantavirus Prediction Engine")
    st.write("Multi-layer ecological-epidemiological risk prediction model")
    
    topAnalytics = st.columns(3)
    
    with topAnalytics[0]:
        container = st.container(key = "mybox_sr", border = True, height = "stretch")
        
        with container:
            st.write("###### Spillover Risk Index (Global Avg)")
            st.subheader(f"{getRiskAvg().round(2)}")
            st.write(f"##### placeholder")

    with topAnalytics[1]:
        container = st.container(key = "mybox_rm", border = True, height = "stretch")
        
        with container:
            st.write("###### Predicted Avg Rodent Momentum")
            st.subheader(f"{getFactors()[0].round(2)}")
            st.write(f"##### placeholder")

    with topAnalytics[2]:
        container = st.container(key = "mybox_ip", border = True, height = "stretch")
        
        with container:
            st.write("###### Estimated Infection Prevalence Probability")
            st.subheader(f"{(getFactors()[1]*100).round(3)}")
            st.write(f"##### placeholder")   
    
    upperMiddleAnalytics = st.columns([4,2])

    with upperMiddleAnalytics[0]:
        container = st.container(key = "mybox_pipeline", border = True)

        with container:
            st.image("pipeline.png", width = "stretch")

    
    with upperMiddleAnalytics[1]:
        layerAcc = st.columns(2)

        with layerAcc[0]:
            render_gauge("Layer 1", "Population Momentum", (getMomentumScore()*100).round(2), "#4ade80")
        
        with layerAcc[1]:
            render_gauge("Layer 2", "Infection Prevalence", (getInfectionScore()*100).round(2), "#facc15")


    lower = st.columns(2)

    with lower[0]:
        container = st.container(key = "mybox_forecastGraph", border = True)
        data = getGraphData()

        with container:
            forecast = px.line(data, x = "collectDate", y = "avgRisk", title = "Average Risk Index per Day within the US", labels = {"collectDate":"Date", "avgRisk": "Average Risk Index"})
            forecast.update_layout(
                plot_bgcolor = "#2D5133",
                paper_bgcolor = "#2D5133",
                title_font_color = "#c0d1c9",
                title_subtitle_font_color= "#c0d1c9",
                legend_font_color = "#c0d1c9",
                font_color = "#c0d1c9",
                legend_title_font_color = "#c0d1c9"
            )

            lineChart.update_xaxes(
                title_font_color="#c0d1c9",  
                tickfont_color="#c0d1c9"     
            )

            lineChart.update_yaxes(
                title_font_color="#c0d1c9",  
                tickfont_color="#c0d1c9"     
            )
            st.plotly_chart(forecast)
            
    
    with lower[1]:
        insightSpace = st.columns(2)

        with insightSpace[0]:
            container = st.container(key = "mybox_insights0", border = True)

            with container:
                st.plotly_chart(getTopFactorsChart())

        with insightSpace[1]:
            container = st.container(key = "mybox_insights1")

            with container:
                st.plotly_chart(getRiskDistributionChart())