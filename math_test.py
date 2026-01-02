import numpy as np
import pandas as pd
import requests
import csv
import re

# Set seed for reproducibility
np.random.seed(42)

# Generate data
while True:
    A = np.random.normal(0.2, 0.1, 100)
    A = np.clip(A, 0, 1)
    B = np.random.normal(0.3, np.sqrt(0.05), 100)
    B = np.clip(B, 0, 1)
    C = 1 - A - B
    
    # Handle cases where C < 0
    mask = C < 0
    if mask.any():
        total_ab = A[mask] + B[mask]
        A[mask] = A[mask] / total_ab
        B[mask] = B[mask] / total_ab
        C[mask] = 0
    
    count = np.sum(C > 0.8)
    if count == 17:
        break

# Verify constraints
print(f"Mean(A): {np.mean(A):.3f} (target: 0.200)")
print(f"Variance(B): {np.var(B):.3f} (target: 0.050)")
print(f"Rows with C > 0.8: {np.sum(C > 0.8)} (target: 17)")
print(f"All A+B+C=1: {np.allclose(A + B + C, 1)}")

# Save data to CSV
df = pd.DataFrame({'A': A, 'B': B, 'C': C})
df.to_csv('math_test_data.csv', index=False)

# Ollama setup
ollama_url = "http://127.0.0.1:11434/api/generate"
model = "llama3.2:latest"

# Queries to test
queries = [
    "What is the mean of column A in this CSV data? Provide only the numerical answer.",
    "What is the variance of column B in this CSV data? Provide only the numerical answer.",
    "How many rows have C > 0.8 in this CSV data? Provide only the numerical answer.",
    "For each row, calculate A + B + C. What is the most common sum? Provide only the numerical answer.",
    "What is the minimum value in column C? Provide only the numerical answer.",
    "What is the maximum value in column A? Provide only the numerical answer."
]

# Actual answers
actual_answers = [
    f"{np.mean(A):.4f}",
    f"{np.var(B):.4f}",
    str(np.sum(C > 0.8)),
    "1.0000",  # since A+B+C=1
    f"{np.min(C):.4f}",
    f"{np.max(A):.4f}"
]

# Function to extract number from response
def extract_number(text):
    match = re.search(r'(\d+\.?\d*)', text)
    return match.group(1) if match else "N/A"

results = []

for i, (query, actual) in enumerate(zip(queries, actual_answers)):
    prompt = f"Here is CSV data:\n{df.to_csv(index=False)}\n\n{query}"
    
    response = requests.post(ollama_url, json={
        "model": model,
        "prompt": prompt,
        "max_tokens": 100,
        "stream": False
    })
    
    if response.status_code == 200:
        data = response.json()
        ollama_response = data["response"].strip()
        ollama_answer = extract_number(ollama_response)
    else:
        ollama_answer = f"Error: {response.status_code}"
    
    correct = "Yes" if ollama_answer == actual else "No"
    
    results.append({
        "query": query,
        "ollama_response": ollama_response,
        "ollama_answer": ollama_answer,
        "actual_answer": actual,
        "correct": correct
    })
    
    print(f"Query {i+1}: {correct}")

# Save results to CSV
with open('math_test_results.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ["query", "ollama_response", "ollama_answer", "actual_answer", "correct"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print("Test completed. Data saved to math_test_data.csv and results to math_test_results.csv")