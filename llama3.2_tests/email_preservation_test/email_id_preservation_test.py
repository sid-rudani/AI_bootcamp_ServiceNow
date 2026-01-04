import os
import requests
import re
import csv
from dotenv import load_dotenv
load_dotenv()

ollama_url = "http://127.0.0.1:11434/api/generate"
model = "llama3.2:latest"

# Function to extract email addresses using regex
def extract_emails(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

# Sample email contents with email IDs
sample_emails = [
    "Hello team here are a few email ids that you have to reach out to: rahul.sharma92@gmail.com, priya.verma18@yahoo.com, ankit.mehta07@gmail.com, neha.kapoor21@outlook.com, rohit.patel1995@gmail.com, simran.kaur88@hotmail.com, arjun.nair23@gmail.com, pooja.malhotra14@yahoo.com, aman.singh09@gmail.com. Please make sure to contact them by end of this week.",
    "Dear colleagues, the following contacts need to be emailed: john.doe@example.com, jane.smith@company.org, bob.jones@university.edu, alice.brown@startup.io, charlie.wilson@techfirm.com. Reach out ASAP.",
    "Team, here are the email addresses for the project: mike.taylor@business.com, sarah.lee@consulting.net, david.kim@agency.co, emily.chen@design.studio, frank.garcia@marketing.pro. Contact them soon.",
    "Hello, please email these people: lisa.nguyen@health.org, tom.harris@finance.biz, nancy.white@education.edu, paul.martin@lawfirm.com, karen.lopez@realestate.net. Urgent.",
    "Greetings, the list of emails is: steve.johnson@engineering.com, rachel.adams@sales.org, kevin.baker@support.io, laura.carter@admin.co, brian.evans@hr.net. Follow up quickly.",
    "Hi all, contact these: olivia.fisher@research.edu, william.gonzalez@it.com, sophia.hernandez@creative.studio, jacob.king@operations.org, isabella.lopez@quality.net. By tomorrow.",
    "Team, emails to reach: mason.moore@strategy.com, ava.nelson@planning.io, ethan.parker@execution.co, harper.ramirez@analysis.net, benjamin.rivera@review.org. Important.",
    "Dear team, here are contacts: elijah.roberts@dev.com, abigail.sanchez@ux.studio, logan.torres@backend.org, emma.wright@frontend.net, james.young@fullstack.io. Contact now.",
    "Hello, the email list: madison.zhang@data.com, noah.anderson@ml.org, chloe.brown@ai.net, lucas.clark@cloud.co, mia.davis@security.io. Reach out.",
    "Colleagues, please email: jack.evans@mobile.com, sophia.flores@web.org, henry.garcia@app.net, amelia.hall@software.co, alexander.lee@platform.io. ASAP."
]

results = []

for i, original_content in enumerate(sample_emails):
    print(f"Processing email {i+1}/{len(sample_emails)}")
    
    # Shorten the email using Ollama
    response = requests.post(ollama_url, json={
        "model": model,
        "prompt": f"Shorten this email while keeping all email addresses intact: {original_content}",
        "max_tokens": 1000,
        "stream": False
    })
    
    if response.status_code == 200:
        data = response.json()
        shortened_content = data["response"].strip()
    else:
        shortened_content = f"Error: {response.status_code} - {response.text}"
    
    # Extract emails
    original_emails = extract_emails(original_content)
    shortened_emails = extract_emails(shortened_content)
    
    # Check if emails match
    match = set(original_emails) == set(shortened_emails)
    
    results.append({
        "original_content": original_content,
        "shortened_content": shortened_content,
        "original_emails": ", ".join(original_emails),
        "shortened_emails": ", ".join(shortened_emails),
        "emails_match": "Yes" if match else "No"
    })

# Write to CSV
with open("email_shortening_test.csv", "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["original_content", "shortened_content", "original_emails", "shortened_emails", "emails_match"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print("Test completed. Results saved to email_shortening_test.csv")
print(f"Total samples: {len(results)}")
matches = sum(1 for r in results if r["emails_match"] == "Yes")
print(f"Emails preserved in {matches}/{len(results)} cases")