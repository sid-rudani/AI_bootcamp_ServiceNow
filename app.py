import streamlit as st
import json
import requests
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

def getResponse(selected_email, prompt):
    newprompt = f"Email Content: {selected_email['content']}\n\nInstruction: {prompt}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that elaborates emails to understand. The emails are the one that the user has received and elaborate without making the email lose it's essence"},
            {"role": "user", "content": newprompt}
        ],
        temperature=0.7,
        max_tokens=200
    )

    elaborated_text = response.choices[0].message.content
    st.session_state[f"new_email_text_{selected_email['id']}"] = elaborated_text

# --- CONFIG ---
st.set_page_config(page_title="AI Email Editor", page_icon="📧", layout="wide")

# Setting up the OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE"),
)

# Importing email datasets
def updatedEmailList(filename):
    emails_internal = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                emails_internal.append(json.loads(line))
    except Exception:
        emails_internal = [{
            "id": 1,
            "sender": "alice@example.com",
            "subject": "Meeting Follow-Up",
            "content": "Hi, just checking in on the meeting notes."
        }]
    return emails_internal
st.title("📧 AI Email Editing Tool")
st.write("Select an email record by ID and use AI to refine it.")
datasetNames = {
    "Short Mails": "lengthen.jsonl", 
    "Long Mails": "shorten.jsonl", 
    "Tone Mails" : "tone.jsonl"
    }
selected_dataset = st.sidebar.selectbox("Select any Dataset", options=datasetNames)
emails = updatedEmailList(datasetNames[selected_dataset])
email_ids = [email["id"] for email in emails]
selected_id = st.sidebar.selectbox("📂 Select Email ID", options=email_ids)
selected_email = next((email for email in emails if email["id"] == selected_id), None)

if not selected_email:
    st.error(f"No email found with ID {selected_id}.")
    st.stop()

# --- DISPLAY SELECTED EMAIL ---
st.markdown(f"### ✉️ Email ID: `{selected_id}`")
st.markdown(f"**From:** {selected_email.get('sender', '(unknown)')}")
st.markdown(f"**Subject:** {selected_email.get('subject', '(no subject)')}")

# Original Email Content (read-only)
st.text_area(
    "Original Email Content",
    value=selected_email.get("content", ""),
    height=150,
)

optionList = ["Original", "Friendly", "Sympathetic", "Professional"]
col1, col2, col3 = st.columns(3)

with col1:
    st.button("Elaborate", on_click=getResponse, args=(selected_email, "Elaborate the email content to make it more detailed and easier to understand. Do it in approximately 200 words without losing the original meaning."))
with col2:
    st.button("Shorten", on_click=getResponse, args=(selected_email, "Shorten the email content to make it more concise while retaining the original meaning. Do it in approximately 50 words."))
with col3:
    st.selectbox("Change Tone", options=optionList, on_change=getResponse, args=(selected_email, f"Change the tone of the email to be more {st.session_state.get('selected_tone', 'Original').lower()}."), key="selected_tone")

new_email_text = st.text_area(
    "New Email Content",
    value=st.session_state.get(f"new_email_text_{selected_id}", ""),
    height=250,
    key=f"new_email_text_{selected_id}",
)
