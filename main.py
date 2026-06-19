import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread, datetime

gc = gspread.service_account(filename = "data.json")
sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1OMYd89ViYPjpKFo28gV1dnuWBuQMuIgG5HCTZpReO7U/edit?gid=0#gid=0")
worksheet = sheet.sheet1

title, button = st.columns([20,1])
powerBI = ""


with title:
    st.title("Hantavirus Tracking and Prediction Dashboard")
with button: 
    st.button("PowerBI", type = "primary")    
st.set_page_config(layout = "wide")


tab1, tab2, tab3, tab4 = st.tabs(["Main", "Analysis", "Predictions", "Contact"])

cases = pd.DataFrame(worksheet.get_all_values(), columns = ["patient_id", "year", "country", "syndrome", "age", "sex", "symptoms", "incubation_days", "severity", "hospitalized", "icu_admission", "mechanical_ventilation", "ecmo_used", "dialysis", "comorbidity", "exposure_type", "outcome", "length_of_stay_days", "blood_type", "viral_load_category", "days_to_diagnosis", "treatment_protocol", "geographic_setting", "nationality", "case_status", "sequence_id"])
cases = cases.fillna("None")
cases.columns = cases.iloc[0]
cases = cases[1:].reset_index(drop = True)



with tab1:
    
    yearlyCounts = cases.groupby("year").size().reset_index(name = "count")

    # barChart, lineChart  = st.columns(2)
    # with barChart:
    #     st.bar_chart(yearlyCounts, x = "year", y = "count",  x_label = "Year", y_label = "Number of Cases")
    # with lineChart:
    st.write("Progression of Hantavirus Cases")
    st.line_chart(yearlyCounts, x = "year", y = "count", x_label = "Year", y_label = "Number of Cases")



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


with tab2:
    regionCounts = cases.groupby("country").size().reset_index(name = "count")
    details, piChart  = st.columns(2)
    
    with piChart:
        fig, ax = plt.subplots()
        ax.pie(regionCounts["count"], labels = regionCounts["country"])
        st.pyplot(fig)




    