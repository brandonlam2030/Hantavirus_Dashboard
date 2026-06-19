import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import webbrowser

title, button = st.columns([20,1])
powerBI = ""


with title:
    st.title("Hantavirus Tracking and Prediction Dashboard")
with button: 
    st.button("PowerBI", type = "primary")    
st.set_page_config(layout = "wide")


tab1, tab2, tab3, tab4 = st.tabs(["Main", "Analysis", "Predictions", "Contact"])

cases = pd.read_csv("hantavirus.csv")
with tab1:
    
    yearlyCounts = cases.groupby("year").size().reset_index(name = "count")

    barChart, lineChart  = st.columns(2)
    with barChart:
        st.bar_chart(yearlyCounts, x = "year", y = "count",  x_label = "Year", y_label = "Number of Cases")
    with lineChart:
        st.line_chart(yearlyCounts, x = "year", y = "count", x_label = "Year", y_label = "Number of Cases")



with tab4:
    contact = st.form("Report a case", clear_on_submit = True)

    cases["symptoms"] = cases["symptoms"].str.split(",")
    uniqueSymptoms = cases["symptoms"].explode().str.strip().unique()
    

    userInfo = {
        "name": contact.text_input("Full name:"),
        "city":contact.text_input("Enter city:"),
        "state": contact.text_input("Enter state:"),
        "country": contact.text_input("Enter country:"),
        "zipCode": contact.text_input("Enter zipCode:"),
        "age": contact.number_input("Enter age:", min_value = 1, max_value = 116, step = 1),
        "email": contact.text_input("Email:"),
        "symptoms": contact.multiselect("Symptom(s) (Select all that apply)", uniqueSymptoms)
        }

    submit = contact.form_submit_button("Submit")

    if submit:
        if any(len(str(value)) == 0 for value in userInfo.values()): st.warning("Please fill out all sections!!")
        elif userInfo["age"] < 0: st.warning("Please enter a valid age")
        else: 
            print("stored")
            # need to implement persistent storage for reports on sickness



with tab2:
    regionCounts = cases.groupby("country").size().reset_index(name = "count")
    details, piChart  = st.columns(2)
    
    with piChart:
        fig, ax = plt.subplots()
        ax.pie(regionCounts["count"], labels = regionCounts["country"])
        st.pyplot(fig)




    