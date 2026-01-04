import json
import csv
import os
from collections import defaultdict

def load_jsonl(file_path):
    emails = []
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    email = json.loads(line)
                    emails.append((line_num, email))
                except json.JSONDecodeError as e:
                    emails.append((line_num, None))
    return emails

def validate_email(email):
    if not isinstance(email, dict):
        return False, "Not a dict"
    required_keys = {"id", "sender", "subject", "content"}
    if not required_keys.issubset(email.keys()):
        return False, f"Missing keys: {required_keys - set(email.keys())}"
    if not isinstance(email["id"], int):
        return False, "id not int"
    for key in ["sender", "subject", "content"]:
        if not isinstance(email[key], str):
            return False, f"{key} not str"
    if "@" not in email["sender"]:
        return False, "sender invalid email format"
    return True, None

def compute_metrics(emails):
    valid_emails = [email for _, email in emails if email is not None]
    valid_validated = []
    errors = []
    for line_num, email in emails:
        if email is None:
            errors.append(f"Line {line_num}: Invalid JSON")
        else:
            is_valid, error = validate_email(email)
            if is_valid:
                valid_validated.append(email)
            else:
                errors.append(f"Line {line_num}: {error}")

    if not valid_validated:
        return {
            "total_lines": len(emails),
            "valid_json": len(valid_emails),
            "valid_emails": 0,
            "errors": errors,
            "avg_content_len": 0,
            "avg_subject_len": 0,
            "unique_senders": 0,
            "content_word_counts": [],
            "model_holes": ["No valid emails"]
        }
    content_lengths = [len(email["content"]) for email in valid_validated]
    subject_lengths = [len(email["subject"]) for email in valid_validated]
    senders = set(email["sender"] for email in valid_validated)
    content_word_counts = [len(email["content"].split()) for email in valid_validated]
    # Model holes: check for diversity
    holes = []
    if len(senders) < 10:
        holes.append("Low sender diversity")
    avg_content_len = sum(content_lengths) / len(content_lengths)
    if avg_content_len < 50:
        holes.append("Very short content")
    elif avg_content_len > 1000:
        holes.append("Very long content")
    # Check for duplicates
    ids = [email["id"] for email in valid_validated]
    if len(ids) != len(set(ids)):
        holes.append("Duplicate IDs")
    # Check content diversity
    unique_words = set()
    for email in valid_validated:
        unique_words.update(email["content"].lower().split())
    if len(unique_words) < 100:
        holes.append("Low content vocabulary")

    return {
        "total_lines": len(emails),
        "valid_json": len(valid_emails),
        "valid_emails": len(valid_validated),
        "errors": errors,
        "avg_content_len": avg_content_len,
        "avg_subject_len": sum(subject_lengths) / len(subject_lengths),
        "unique_senders": len(senders),
        "content_word_counts": content_word_counts,
        "model_holes": holes if holes else ["None detected"]
    }

def main():
    # Assume datasets are in parent directory
    base_dir = os.path.dirname(os.path.dirname(__file__))
    files = ["short_emails.jsonl", "medium_emails.jsonl", "long_emails.jsonl"]
    results = []

    for file in files:
        file_path = os.path.join(base_dir, file)
        if not os.path.exists(file_path):
            results.append({
                "file": file,
                "metric": "file_exists",
                "value": "False"
            })
            continue
        emails = load_jsonl(file_path)
        metrics = compute_metrics(emails)
        results.append({"file": file, "metric": "total_lines", "value": metrics["total_lines"]})
        results.append({"file": file, "metric": "valid_json", "value": metrics["valid_json"]})
        results.append({"file": file, "metric": "valid_emails", "value": metrics["valid_emails"]})
        results.append({"file": file, "metric": "avg_content_len", "value": round(metrics["avg_content_len"], 2)})
        results.append({"file": file, "metric": "avg_subject_len", "value": round(metrics["avg_subject_len"], 2)})
        results.append({"file": file, "metric": "unique_senders", "value": metrics["unique_senders"]})
        results.append({"file": file, "metric": "model_holes", "value": "; ".join(metrics["model_holes"])})
        # For errors, perhaps write separately or summarize
        if metrics["errors"]:
            results.append({"file": file, "metric": "num_errors", "value": len(metrics["errors"])})
            # Optionally, write errors to a separate file
            error_file = os.path.join(base_dir, f"errors_{file}.txt")
            with open(error_file, 'w') as ef:
                for error in metrics["errors"]:
                    ef.write(error + '\n')

    # Write to CSV
    csv_path = os.path.join(base_dir, "dataset_metrics.csv")
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ["file", "metric", "value"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"Metrics written to {csv_path}")

if __name__ == "__main__":
    main()
