import streamlit as st
import pandas as pd
from Main import cases


targetData = cases.copy()


if "filters" not in st.session_state:
    st.session_state.filters = []

if "pageIdx" not in st.session_state:
    st.session_state.pageIdx = 0
    

if st.session_state.filters:
    targetData = targetData[targetData[st.session_state.filters[0][0]] == st.session_state.filters[0][1]]


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
            if st.form_submit_button("Filter", width = "stretch"):
                replacementKeys = {
                    "Patient ID": "patient_id",
                    "Geographic Setting": "geographic_setting",
                    "Case Status": "case_status"
                }
                
                selectFilter = replacementKeys.get(selectFilter,selectFilter.lower())
                st.session_state.filters.clear()
                st.session_state.pageIdx = 0

                if selectFilter:
                    st.session_state.filters.append([selectFilter, specific])
    

st.table(targetData[["patient_id", "year", "country", "syndrome", "age", "sex", "symptoms", "severity", "geographic_setting", "case_status"]].iloc[st.session_state.pageIdx:st.session_state.pageIdx+15])

