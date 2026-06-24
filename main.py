import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread, datetime, plotly
import plotly.graph_objects as go

gc = gspread.service_account_from_dict(st.secrets["AUTH"])
sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1OMYd89ViYPjpKFo28gV1dnuWBuQMuIgG5HCTZpReO7U/edit?gid=0#gid=0")
worksheet = sheet.sheet1
coords = sheet.worksheet("coords")

title, button = st.columns([20,1])
powerBI = ""

if "pageIdx" not in st.session_state:
    st.session_state.pageIdx = 0


if "filters" not in st.session_state:
    st.session_state.filters = []


if "clickedPoints" not in st.session_state:
    st.session_state.clickedPoints = {}


with title:
    st.title("Hantavirus Tracking and Prediction Dashboard")
with button: 
    st.button("PowerBI", type = "primary")    
st.set_page_config(layout = "wide")


tab1, tab2, tab3, tab4 = st.tabs(["Main", "Data", "Predictions", "Report A Case"])

cases = pd.DataFrame(worksheet.get_all_values(), columns = ["patient_id", "year", "country", "syndrome", "age", "sex", "symptoms", "incubation_days", "severity", "hospitalized", "icu_admission", "mechanical_ventilation", "ecmo_used", "dialysis", "comorbidity", "exposure_type", "outcome", "length_of_stay_days", "blood_type", "viral_load_category", "days_to_diagnosis", "treatment_protocol", "geographic_setting", "nationality", "case_status", "sequence_id"])
cases = cases.fillna("None")
cases.columns = cases.iloc[0]
cases = cases[1:].reset_index(drop = True)

coordinates = pd.DataFrame(coords.get_all_values(), columns = ["country", "lat", "lon", "count"])
coordinates = coordinates[1:].reset_index(drop = True)
coordinates = coordinates[coordinates["count"].astype("float32") > 0]



with tab1:
    box1, box2, box3 = st.columns(3)

    with box1:
        with st.container(width = 300, height = 200, border = True):
            st.subheader(str(len(cases)), text_alignment = "center")
            st.header("Cases Tracked", text_alignment = "center")
            

    with box2:
        with st.container(width = 300, height = 200, border = True):
            st.subheader(str(len(cases["country"])), text_alignment = "center")
            st.header("Involved Countries", text_alignment = "center")
            

    yearlyCounts = cases.groupby("year").size().reset_index(name = "count")



    st.header("Progression of Hantavirus Cases (2000 - Present)")
    fig1 = go.Figure(data = go.Scatter(x = yearlyCounts["year"], y = yearlyCounts["count"]))
    st.plotly_chart(fig1)
    
    globe = go.Figure(data = go.Scattergeo(
        lon = coordinates["lon"],
        lat = coordinates["lat"],
        text = coordinates["country"],
        mode = "markers",
        marker = dict(size = coordinates["count"].astype("float32"), sizemode = "area", sizeref = 2*max(coordinates["count"].astype(int))/ (30**2), sizemin = 1,color=coordinates["count"].astype(int), colorscale = "YlOrRd", showscale = True))
    )
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
        height = 800,
        width = 1000
    )

    
    globeClick = st.plotly_chart(globe, use_container_width = True, on_select = "rerun")

    if globeClick and globeClick.selection.points:
        st.session_state.clickedPoints = globeClick.selection.points[0]






with tab4:
    contact = st.form("Report a case", clear_on_submit = True)

    cases["symptoms"] = cases["symptoms"].str.split(",")
    uniqueSymptoms = cases["symptoms"].explode().str.strip().unique()
    
    name = contact.text_input("Full name:")
    city = contact.text_input("Enter city:")
    state = contact.text_input("Enter state:")
    country =  contact.text_input("Enter country:")
    zipCode = contact.text_input("Enter zipCode:")
    email = contact.text_input("Email:")
    
    #need fixing on structure in future
    age, sex = st.columns(2)
    with age:
        ageNum = contact.number_input("Age", min_value = 1)
    with sex:
        sexVal = contact.segmented_control("Sex", ["Male", "Female"])
    
    symptoms = contact.multiselect("Symptom(s) (Select all that apply)", uniqueSymptoms)
    

    submit = contact.form_submit_button("Submit")
    

    if submit:
        if any(len(str(value)) == 0 for value in [name, city, state, country, zipCode, email, ageNum, sexVal, symptoms]): st.warning("Please fill out all sections!!")
        elif ageNum < 0: st.warning("Please enter a valid age")
        else:
            currentId = int(cases["patient_id"].iloc[-1][cases["patient_id"].iloc[-1].find("-")+1:])+1
            results = [currentId, datetime.datetime.now().year, country, "None", ageNum, sexVal, ", ".join(symptoms)]
            
            
            if country in coordinates["country"]:
                worksheet.append_row(results)
                coordinates.iloc[coordinates["country"] == country, "count"] += 1
                st.success("Form submitted successfully!")
            else:
                st.warning("Please enter a valid country")


with tab2:
    dataTable = st.empty()
    dataTable.empty()
    
    targetData = cases.copy()
    for item in st.session_state.filters:
        targetData = targetData[targetData[item[0]] == item[1]]

    dataTable.table(targetData[["patient_id", "year", "country", "syndrome", "age", "sex", "symptoms", "severity", "geographic_setting", "case_status"]].iloc[st.session_state.pageIdx:st.session_state.pageIdx+15])
    

    left, r1, right = st.columns([1,25,1])

    
    with right:
        if st.button("→", type = "primary"):
            st.session_state.pageIdx += 15
    
    with left:
        if st.session_state.pageIdx > 0 and st.button("←", type = "primary"):
            st.session_state.pageIdx -= 15

    with r1:
        filterArea = st.form("Filter data", clear_on_submit = False)

        with filterArea:
            formattedCol = st.columns([1,4,1,4,2])

            with formattedCol[0]:
                st.write("#### SELECT")

            with formattedCol[1]:
                selectFilter = st.selectbox("", ["", "Patient ID", "Year", "Country", "Syndrome", "Age", "Sex", "Symptoms", "Severity", "Geographic Setting", "Case Status"], label_visibility = "collapsed")

            with formattedCol[2]:
                st.write("#### WHERE")

            with formattedCol[3]:
                specific = st.text_input("SPECIFICS", label_visibility = "collapsed")
            
            with formattedCol[4]:
                filterSubmit = st.form_submit_button("Filter", use_container_width = True)

                if filterSubmit:
                    st.session_state.filters.append([selectFilter, specific])

        

    


    