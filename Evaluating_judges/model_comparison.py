import json
import pandas as pd
from generate import GenerateEmail
import os
from dotenv import load_dotenv
import concurrent.futures
import logging
import time

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

datasets = {
    "lengthen": {"file": "lengthen.jsonl", "action": "elaborate", "kwargs": {}},
    "shorten": {"file": "shorten.jsonl", "action": "shorten", "kwargs": {}},
    "tone": {"file": "tone.jsonl", "action": "tone", "kwargs": {"tone": "professional"}}
}

base_model = "gpt-4.1"
generator = GenerateEmail(base_model)
judge_models = ["gpt-4.1", "gpt-4o-mini"]
metrics = ["faithfulness", "completeness", "robustness"]
num_emails = 30

# Number of evaluations per metric per judge
num_runs = 3

def load_emails(filename, num=30):
    emails = []
    with open(filename, 'r') as f:
        for i, line in enumerate(f):
            if i >= num:
                break
            try:
                email = json.loads(line.strip())
                emails.append(email)
            except json.JSONDecodeError:
                continue
    return emails

# Function to generate revised email
def generate_revised(email, action, **kwargs):
    content = email["content"]
    response = generator.generate(action, content, **kwargs)
    try:
        revised = json.loads(response)
        return revised["content"]
    except json.JSONDecodeError:
        return response.strip()

# Function to evaluate single run
def evaluate_single(reference, result, metric, judge):
    rating, _ = generator.evalResponse(reference, result, metric, judge)
    try:
        return int(rating)
    except (ValueError, TypeError):
        return None

# Main processing
results = []
start_time = time.time()
logger.info("Starting model comparison process")

for dataset_name, config in datasets.items():
    dataset_start = time.time()
    logger.info(f"Processing dataset: {dataset_name}")
    emails = load_emails(config["file"], num_emails)
    logger.info(f"Loaded {len(emails)} emails for {dataset_name}")
    
    # Generate revised emails
    revised_emails = []
    for email in emails:
        revised_content = generate_revised(email, config["action"], **config["kwargs"])
        revised_emails.append({"id": email["id"], "content": revised_content, "original": email})
    logger.info(f"Generated revised emails for {dataset_name}, elapsed: {time.time() - dataset_start:.2f}s")
    
    # Prepare evaluation tasks
    tasks = []
    for rev_email in revised_emails:
        for metric in metrics:
            for judge in judge_models:
                for run in range(num_runs):
                    tasks.append((rev_email["original"], rev_email, metric, judge, run))
    logger.info(f"Prepared {len(tasks)} evaluation tasks for {dataset_name}")
    
    # Run evaluations in parallel
    eval_start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_task = {executor.submit(evaluate_single, ref, res, met, jud): (ref["id"], met, jud, run) for ref, res, met, jud, run in tasks}
        ratings_dict = {}  # key: (email_id, metric, judge) -> list of ratings
        completed = 0
        for future in concurrent.futures.as_completed(future_to_task):
            email_id, met, jud, run = future_to_task[future]
            rating = future.result()
            key = (email_id, met, jud)
            if key not in ratings_dict:
                ratings_dict[key] = []
            ratings_dict[key].append(rating)
            completed += 1
            if completed % 100 == 0:
                logger.info(f"Completed {completed}/{len(tasks)} evaluations for {dataset_name}")
    logger.info(f"Completed all evaluations for {dataset_name}, elapsed: {time.time() - eval_start:.2f}s, total dataset time: {time.time() - dataset_start:.2f}s")
    
    # Process ratings to compute mean and variance
    for rev_email in revised_emails:
        email_id = rev_email["id"]
        for metric in metrics:
            for judge in judge_models:
                key = (email_id, metric, judge)
                ratings = ratings_dict.get(key, [])
                valid_ratings = [r for r in ratings if r is not None]
                if valid_ratings:
                    mean = sum(valid_ratings) / len(valid_ratings)
                    variance = sum((r - mean)**2 for r in valid_ratings) / len(valid_ratings)
                else:
                    mean = None
                    variance = None
                results.append({
                    "dataset": dataset_name,
                    "email_id": email_id,
                    "action": config["action"],
                    "original_content": rev_email["original"]["content"],
                    "revised_content": rev_email["content"],
                    "metric": metric,
                    "judge_model": judge,
                    "rating1": ratings[0] if len(ratings) > 0 else None,
                    "rating2": ratings[1] if len(ratings) > 1 else None,
                    "rating3": ratings[2] if len(ratings) > 2 else None,
                    "mean": mean,
                    "variance": variance
                })

logger.info(f"All datasets processed, saving results. Total time: {time.time() - start_time:.2f}s")

# Save detailed results to CSV
df = pd.DataFrame(results)
df.to_csv("evaluation_results.csv", index=False)

# Compute summary statistics
summary = df.groupby(["dataset", "judge_model", "metric"]).agg(
    avg_mean=("mean", "mean"),
    avg_variance=("variance", "mean")
).reset_index()

summary.to_csv("summary_results.csv", index=False)

logger.info("Evaluation completed. Results saved to evaluation_results.csv and summary_results.csv")