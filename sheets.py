import gspread
import streamlit as st
import pandas as pd

gc = gspread.service_account_from_dict(st.secrets["AUTH"])
sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1OMYd89ViYPjpKFo28gV1dnuWBuQMuIgG5HCTZpReO7U/edit?gid=0#gid=0")
worksheet = sheet.sheet1
coords = sheet.worksheet("coords")
fieldAgentForm = sheet.worksheet("FA")
hospitalForm = sheet.worksheet("HR")
smForm = sheet.worksheet("SM")

def count():
    sheets = [fieldAgentForm,hospitalForm,smForm]
    count = 0

    for sheet in sheets:
        count+=len(sheet.get_all_values())

    return count-5


def countUnwell():
    sheets = [fieldAgentForm,hospitalForm,smForm]
    count = 0

    for sheet in sheets:
        raw = sheet.get_all_values()
        df = pd.DataFrame(raw[1:], columns = raw[0])
        df = df.groupby("status").size().reset_index(name = "count")
        
        count += df[df["status"] == "Unwell"]["count"]

    return count