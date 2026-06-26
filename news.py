from newsapi import NewsApiClient
import streamlit as st

newsapi = NewsApiClient(api_key = st.secrets["NEWS_API"])

def getNews():
    headlines = newsapi.get_everything(
        q = "hantavirus",
        language = "en",
        sort_by = "relevancy"
    )
    
    if headlines["status"] == "ok":
        return headlines["articles"][0:10]
    
    return []