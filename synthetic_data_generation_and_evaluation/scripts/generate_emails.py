import os
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

load_dotenv()
client = OpenAI(
            base_url=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )

def generate_batch(category, batch_size, start_id, max_tokens):
    prompt = f"""Generate {batch_size} {category} email examples in JSONL format. Each line should be a valid JSON object with exactly these keys: "id", "sender", "subject", "content".
- "id": an integer starting from {start_id} and incrementing by 1 for each email
- "sender": a realistic email address (e.g., name@domain.com)
- "subject": a brief subject line
- "content": the email body text, make it {category} in length
Make sure you are covering a variety of topics such as work, personal, promotional, and informational emails. It should be diverse in tone and style.
Output only the JSONL lines, no extra text, no markdown, no explanations."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        emails = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                try:
                    email = json.loads(line)
                    emails.append(email)
                except json.JSONDecodeError:
                    continue  # skip invalid lines
        return emails
    except Exception as e:
        print(f"Error generating batch: {e}")
        return []

def generate_category_emails(category, total_emails, start_id, max_tokens, filename):
    batch_size = 10
    num_batches = total_emails // batch_size
    all_emails = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for i in range(num_batches):
            batch_start_id = start_id + i * batch_size
            futures.append(executor.submit(generate_batch, category, batch_size, batch_start_id, max_tokens))

        for future in as_completed(futures):
            all_emails.extend(future.result())

    all_emails.sort(key=lambda x: x['id'])

    with open(filename, 'w') as f:
        for email in all_emails:
            f.write(json.dumps(email) + '\n')

    print(f"Generated {len(all_emails)} {category} emails in {filename}")

if __name__ == "__main__":
    # Short emails: 100, ids 1-100
    generate_category_emails("short", 100, 1, 1000, "short_emails.jsonl")

    # Medium emails: 100, ids 101-200
    generate_category_emails("medium", 100, 101, 2000, "medium_emails.jsonl")

    # Long emails: 100, ids 201-300
    generate_category_emails("long", 100, 201, 4000, "long_emails.jsonl")