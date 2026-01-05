import streamlit as st
import json
import requests
import pandas as pd
from openai import OpenAI
import os
from generate import GenerateEmail

st.set_page_config(page_title="AI Email Editor", page_icon="📧", layout="wide")

def process_email(selected_email, content, action, **kwargs):
    response = generator.generate(action, content, **kwargs)
    try:
        revised_email = json.loads(response)
        revised_content = revised_email["content"]
    except json.JSONDecodeError:
        revised_content = response.strip()
    st.session_state[f"new_email_text_{selected_email['id']}"] = revised_content

def updatedEmailList(filename):
    emails_internal = []
    filepath = os.path.join("datasets", filename)
    try:
        with open(filepath, 'r') as file:
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
datasetNames = {
    "Short Mails": "lengthen.jsonl", 
    "Long Mails": "shorten.jsonl", 
    "Tone Mails" : "tone.jsonl"
    }
judgeLLM = st.sidebar.selectbox("Select judge model", options=["gpt-4.1", "gpt-4o-mini", "gpt-5.1"], key="judge_model")
baseLLM = st.sidebar.selectbox("Select base LLM model", options=["gpt-4.1", "gpt-4o-mini"], key="baseLLM")

# Create instance of GenerateEmail with selected baseLLM
generator = GenerateEmail(baseLLM)

st.title("📧 AI Email Editing Tool")
st.write("Select an email record by ID and use AI to refine it.")
datasetNames = {
    "Short Mails": "lengthen.jsonl", 
    "Long Mails": "shorten.jsonl", 
    "Tone Mails" : "tone.jsonl"
    }
st.sidebar.title("Dataset Selection")
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

# Excerpt selection
with st.expander("Use custom Excerpt for Editing"):
    excerpt = st.text_area(
        "Selected Excerpt (copy-paste the part you want to edit, or leave blank to edit the entire email)",
        value="",
        height=100,
        key=f"excerpt_{selected_id}",
    )

optionList = ["Original", "Friendly", "Sympathetic", "Professional"]
col1, col2, col3 = st.columns(3)

content_to_process = excerpt.strip() if excerpt.strip() else selected_email.get("content", "")

with col1:
    st.button("Elaborate", on_click=process_email, args=(selected_email, content_to_process, "elaborate"))
with col2:
    st.button("Shorten", on_click=process_email, args=(selected_email, content_to_process, "shorten"))
with col3:
    st.selectbox("Change Tone", options=optionList, on_change=lambda: process_email(selected_email, content_to_process, "tone", tone=st.session_state.selected_tone.lower()), key="selected_tone")

if f"new_email_text_{selected_id}" not in st.session_state:
    st.session_state[f"new_email_text_{selected_id}"] = ""

new_email_text = st.text_area(
    "New Email Content",
    height=250,
    key=f"new_email_text_{selected_id}",
)
def addMetric(reference_email, result_email, metric_name, judge_model):
    rating, reason = generator.evalResponse(reference_email, result_email, metric_name, judge_model)
    st.session_state[f"rating_{metric_name}_{reference_email['id']}"] = rating
    st.session_state[f"reason_{metric_name}_{reference_email['id']}"] = reason

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.button("Evaluate Faithfulness", on_click=addMetric, args=(selected_email, {"id": selected_id, "content": new_email_text}, "faithfulness", judgeLLM), key=f"evaluate_faithfulness_{selected_id}")
with col2:
    st.button("Evaluate Completeness", on_click=addMetric, args=(selected_email, {"id": selected_id, "content": new_email_text}, "completeness", judgeLLM), key=f"evaluate_completeness_{selected_id}")
with col3:
    st.button("Evaluate Robustness", on_click=addMetric, args=(selected_email, {"id": selected_id, "content": new_email_text}, "robustness", judgeLLM), key=f"evaluate_robustness_{selected_id}")
with col4:
    st.button("Evaluate All Metrics", on_click=lambda: [addMetric(selected_email, {"id": selected_id, "content": new_email_text}, metric, judgeLLM) for metric in ["faithfulness", "completeness", "robustness"]], key=f"evaluate_all_{selected_id}")
st.markdown("### 📊 Evaluation Results")
faithfulness_rating = st.session_state.get(f"rating_faithfulness_{selected_id}", "N/A")
faithfulness_reason = st.session_state.get(f"reason_faithfulness_{selected_id}", "N/A")
completeness_rating = st.session_state.get(f"rating_completeness_{selected_id}", "N/A")
completeness_reason = st.session_state.get(f"reason_completeness_{selected_id}", "N/A")
robustness_rating = st.session_state.get(f"rating_robustness_{selected_id}", "N/A")
robustness_reason = st.session_state.get(f"reason_robustness_{selected_id}", "N/A")

col1, col2, col3, col4 = st.columns(4)

with col1:
    with st.expander(f"Faithfulness Rating: {faithfulness_rating}"):
        st.write(f"**Reason:** {faithfulness_reason}")

with col2:
    with st.expander(f"Completeness Rating: {completeness_rating}"):
        st.write(f"**Reason:** {completeness_reason}")

with col3:
    with st.expander(f"Robustness Rating: {robustness_rating}"):
        st.write(f"**Reason:** {robustness_reason}")

with col4:
    try:
        ratings = [str(faithfulness_rating).strip(), str(completeness_rating).strip(), str(robustness_rating).strip()]
        if all(r.isdigit() for r in ratings):
            total = sum(int(r) for r in ratings)
            summary_text = f"Overall Summary: {total}/15"
        else:
            summary_text = f"Overall Summary: N/A (incomplete evaluations) - Ratings: {ratings}"
    except (ValueError, AttributeError):
        summary_text = f"Overall Summary: N/A - Error with ratings: {ratings}"
    with st.expander(summary_text):
        st.write("**Summary:** Average of all ratings obtained above.")