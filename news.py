from newsapi import NewsApiClient
import streamlit as st

newsapi = NewsApiClient(api_key = st.secrets["NEWS_API"])
headlines = ""

def getNews():
    headlines = newsapi.get_everything(
        q = "hantavirus",
        sort_by = "relevancy"
    )
    if headlines["status"] == "ok":
        return [headlines["articles"][0:10], headlines["totalResults"]]
    
    return []

