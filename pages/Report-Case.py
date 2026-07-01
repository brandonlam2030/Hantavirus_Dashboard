import streamlit as st
import pandas as pd
from sheets import coords, fieldAgentForm, hospitalForm, smForm
from Main import cases, coordinates
import datetime, gspread
from data import load_cases, load_coordinates

cases = load_cases()
coordinates = load_coordinates()

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