import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread, datetime

gc = gspread.service_account_from_dict(st.secrets["AUTH"])
sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1OMYd89ViYPjpKFo28gV1dnuWBuQMuIgG5HCTZpReO7U/edit?gid=0#gid=0")
worksheet = sheet.sheet1

title, button = st.columns([20,1])
powerBI = ""

if "pageIdx" not in st.session_state:
    st.session_state.pageIdx = 0


if "filters" not in st.session_state:
    st.session_state.filters = []

with title:
    st.title("Hantavirus Tracking and Prediction Dashboard")
with button: 
    st.button("PowerBI", type = "primary")    
st.set_page_config(layout = "wide")


tab1, tab2, tab3, tab4 = st.tabs(["Main", "Data", "Predictions", "Contact"])

cases = pd.DataFrame(worksheet.get_all_values(), columns = ["patient_id", "year", "country", "syndrome", "age", "sex", "symptoms", "incubation_days", "severity", "hospitalized", "icu_admission", "mechanical_ventilation", "ecmo_used", "dialysis", "comorbidity", "exposure_type", "outcome", "length_of_stay_days", "blood_type", "viral_load_category", "days_to_diagnosis", "treatment_protocol", "geographic_setting", "nationality", "case_status", "sequence_id"])
cases = cases.fillna("None")
cases.columns = cases.iloc[0]
cases = cases[1:].reset_index(drop = True)


image = st.components.v1

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
    st.line_chart(yearlyCounts, x = "year", y = "count", x_label = "Year", y_label = "Number of Cases")
    image.iframe("https://app.powerbi.com/groups/me/reports/b9da4980-5c10-4295-8a3d-0d8118c8f8e2/ab6528c30b6aeaaaaa5c?experience=power-bi")



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
            
            worksheet.append_row(results)
            st.success("Form submitted successfully!")


firstLoad = True

with tab2:
    dataTable = st.empty()
    dataTable.empty()



    dataTable.table(cases[["patient_id", "year", "country", "syndrome", "age", "sex", "symptoms", "severity", "geographic_setting", "case_status"]].iloc[st.session_state.pageIdx:st.session_state.pageIdx+15])
    

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
                selectFilter = st.multiselect("", ["Patient ID", "Year", "Country", "Syndrome", "Age", "Sex", "Symptoms", "Severity", "Geographic Setting", "Case Status"], label_visibility = "collapsed")

            with formattedCol[2]:
                st.write("#### WHERE")

            with formattedCol[3]:
                specific = st.text_input("SPECIFICS", label_visibility = "collapsed")
            
            with formattedCol[4]:
                filterSubmit = st.form_submit_button("Filter", use_container_width = True)

                if filterSubmit:
                    st.session_state.filters.append([selectFilter, specific])

        

    


    