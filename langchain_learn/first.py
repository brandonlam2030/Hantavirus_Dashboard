from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
import time
import streamlit as st

load_dotenv()
def getRecentReports(city:str) -> str: 
    '''Get recent hantavirus news reports in a given city'''
    return f"news for {city}"



@st.cache_resource
def getAgent():
    geminiModel = ChatGoogleGenerativeAI(
        model = "gemini-3.1-flash-lite",
        timeout=30
    )
    
    agent = create_agent(
        model = geminiModel,
        tools = [getRecentReports],
        system_prompt = "You are a hantavirus disease assistance agent, answer prompts in 50 to 60 words.",
    )
    return agent

def invokeWithRetry(agent, inputs, max_retries=5):
    for attempt in range(max_retries):
        try:
            return agent.invoke(inputs)["messages"][-1].text
        except Exception as e:
            msg = str(e).lower()
            if any(kw in msg for kw in ["overloaded", "503", "unavailable", "timeout", "timed out", "resource_exhausted", "429", "quota"]):
                wait = 2 ** attempt
                print(f"Rate/quota limited, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")
