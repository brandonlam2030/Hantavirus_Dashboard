import gspread
import streamlit as st

gc = gspread.service_account_from_dict(st.secrets["AUTH"])
sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1OMYd89ViYPjpKFo28gV1dnuWBuQMuIgG5HCTZpReO7U/edit?gid=0#gid=0")
worksheet = sheet.sheet1
coords = sheet.worksheet("coords")
fieldAgentForm = sheet.worksheet("FA")
hospitalForm = sheet.worksheet("HR")