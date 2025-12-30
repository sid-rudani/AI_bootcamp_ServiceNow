import streamlit as st
import json
import requests
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE"),
)

def evalResponse(reference_email, result_email,motive, criteria, rating_levels):
    # Escape curly braces in email content to avoid format issues
    ref_content = reference_email['content'].replace('{', '{{').replace('}', '}}')
    res_content = result_email['content'].replace('{', '{{').replace('}', '}}')
    # using string formatting for the prompt
    prompt_template = """
    Evaluate the following email content based on the instruction provided.
    Evaluation criteria: {criteria}
    Original Email Content: {email_content}
    Intent behind the operation: {motive}
    After the operation: {result_email_content}
    Provide a rating on a scale of 1 to 5 based on the following levels: {rating_levels}.
    Format your response as a JSON object with the following structure:
    {{
        "Reason": <reason>,
        "Rating" : <rating>,
    }}
    """
    response = client.chat.completions.create(
        model=os.getenv("judgeLLM"),
        messages=[
            {"role": "user", "content": prompt_template.format(email_content=ref_content, result_email_content=res_content, criteria=criteria, motive=motive, rating_levels=rating_levels)}
        ],
        temperature=0.7,
        max_tokens=200
    )
    #using reg ex to extract the evaluation from the response
    extracted_text = response.choices[0].message.content
    # Parsing the response to get rating and reason
    try:
        evaluation = json.loads(extracted_text)
        rating = evaluation.get("Rating", "N/A")
        reason = evaluation.get("Reason", "N/A")
    except json.JSONDecodeError:
        reason = extracted_text.strip()
    return rating, reason



def getResponse(selected_email, prompt):
    newprompt = f"Email Content: {selected_email['content']}\n\nInstruction: {prompt}"
    response = client.chat.completions.create(
        model=os.getenv("baseLLM"),
        messages=[
            {
                "role": "system", "content": " You are an expert email editor. You help users improve their email content based on given instructions. Generate responses that are clear, concise, and contextually appropriate in the following format: 'Revised Email Content should be in JSON format: with subject, sender, and content fields. template: {\"subject\": \"\", \"sender\": \"\", \"content\": \"\"}'."},
            {"role": "user", "content": newprompt}
        ],
        temperature=0.7,
        max_tokens=200
    )
    #using reg ex to extract the revised email content from the response
    extracted_text = response.choices[0].message.content
    try:
        revised_email = json.loads(extracted_text)
        revised_content = revised_email["content"]
        print(revised_email)
    except json.JSONDecodeError:
        revised_content = extracted_text.strip()
    st.session_state[f"new_email_text_{selected_email['id']}"] = revised_content

st.set_page_config(page_title="AI Email Editor", page_icon="📧", layout="wide")

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
def addMetric(reference_email, result_email, metric_name, motive, criteria, rating_levels):
    rating, reason = evalResponse(reference_email, result_email, motive, criteria, rating_levels)
    st.session_state[f"rating_{metric_name}_{reference_email['id']}"] = rating
    st.session_state[f"reason_{metric_name}_{reference_email['id']}"] = reason

st.button("Evaluate Faithfulness", on_click=addMetric, args=(selected_email, {"id": selected_id, "content": new_email_text}, "faithfulness", "Ensure the revised email maintains the original intent and meaning of the email.", "faithfulness to the original email content", "1: Not faithful at all, 2: Slightly faithful, 3: Moderately faithful, 4: Very faithful, 5: Completely faithful"), key=f"evaluate_faithfulness_{selected_id}")

st.button("Evaluate Completeness", on_click=addMetric, args=(selected_email, {"id": selected_id, "content": new_email_text}, "completeness", "Ensure the revised email addresses all key points and information present in the original email.", "completeness of information compared to the original email", "1: Very incomplete, 2: Somewhat incomplete, 3: Moderately complete, 4: Mostly complete, 5: Fully complete"), key=f"evaluate_completeness_{selected_id}")
st.markdown("### 📊 Evaluation Results")
faithfulness_rating = st.session_state.get(f"rating_faithfulness_{selected_id}", "N/A")
faithfulness_reason = st.session_state.get(f"reason_faithfulness_{selected_id}", "N/A")
completeness_rating = st.session_state.get(f"rating_completeness_{selected_id}", "N/A")
completeness_reason = st.session_state.get(f"reason_completeness_{selected_id}", "N/A")
st.markdown(f"**Faithfulness Rating:** {faithfulness_rating}")
st.markdown(f"**Reason:** {faithfulness_reason}")
st.markdown(f"**Completeness Rating:** {completeness_rating}")
st.markdown(f"**Reason:** {completeness_reason}")