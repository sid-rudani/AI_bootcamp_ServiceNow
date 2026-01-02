import requests
import csv
import io
import pandas as pd
from collections import defaultdict, deque

ollama_url = "http://127.0.0.1:11434/api/generate"
model = "llama3.2:latest"

prompt = """
Generate a dataset of employees in a company hierarchy with the following constraints:
- Exactly 4 levels of hierarchy
- Level 1: CEO (1 employee, no manager)
- Level 2: 3 employees, each reporting to CEO
- Level 3: 9 employees, each reporting to one of the level 2 employees (3 per manager)
- Level 4: 27 employees, each reporting to one of the level 3 employees (3 per manager)
- Total: 40 employees
- Each employee has exactly one manager, except CEO
- No cycles in the hierarchy
- Each manager has exactly 3 direct reports

Provide the data as a CSV with columns: employee_id, employee_name, manager_id, level
Use employee_id as unique integers starting from 1.
For CEO, manager_id should be empty or null.
Make up realistic employee names.
Also don't forget to assign levels correctly from 1 to 4.
Don't include any explanation, just provide the CSV data.
Don't write code and give me the python code to generate the data. Just give me the CSV data directly. Don't use python.
Don't include any extra text before or after the CSV data.
Generate the header row as well.
"""

response = requests.post(ollama_url, json={
    "model": model,
    "prompt": prompt,
    "max_tokens": 6000,
    "stream": False
})

if response.status_code != 200:
    print(f"Error: {response.status_code} - {response.text}")
    exit()

data = response.json()
ollama_output = data["response"].strip()

print("Ollama Output:")
print(response.json())
print(ollama_output)
print("\n" + "="*50 + "\n")

csv_start = ollama_output.find("employee_id")
if csv_start == -1:
    print("CSV header not found in response")
    exit()

csv_content = ollama_output[csv_start:]

df = pd.read_csv(io.StringIO(csv_content), on_bad_lines='skip')

df['manager_id'] = df['manager_id'].replace('', pd.NA).fillna(pd.NA)
df['level'] = pd.to_numeric(df['level'], errors='coerce')
print("Parsed DataFrame:")
print(df.head(10))
print(f"Total rows: {len(df)}")
print("\n" + "="*50 + "\n")
verification_results = []

# 1. Total employees
total_employees = len(df)
expected_total = 40
verification_results.append({
    "check": "Total employees",
    "expected": expected_total,
    "actual": total_employees,
    "pass": total_employees == expected_total
})

# 2. Levels count
level_counts = df['level'].value_counts().sort_index()
expected_levels = {1: 1, 2: 3, 3: 9, 4: 27}
actual_levels = {level: level_counts.get(level, 0) for level in range(1, 5)}
verification_results.append({
    "check": "Level counts",
    "expected": str(expected_levels),
    "actual": str(actual_levels),
    "pass": actual_levels == expected_levels
})

# 3. CEO has no manager
ceo = df[df['level'] == 1]
ceo_no_manager = ceo['manager_id'].isna().all()
verification_results.append({
    "check": "CEO has no manager",
    "expected": True,
    "actual": ceo_no_manager,
    "pass": ceo_no_manager
})

# 4. Each employee has exactly one manager (except CEO)
non_ceo = df[df['level'] != 1]
has_manager = non_ceo['manager_id'].notna().all()
unique_managers = non_ceo.groupby('employee_id')['manager_id'].nunique()
one_manager = (unique_managers == 1).all()
verification_results.append({
    "check": "Each non-CEO has exactly one manager",
    "expected": True,
    "actual": has_manager and one_manager,
    "pass": has_manager and one_manager
})

# 5. Each manager has exactly 3 reports
managers = df['manager_id'].dropna().unique()
manager_reports = defaultdict(int)
for _, row in df.iterrows():
    if pd.notna(row['manager_id']):
        manager_reports[row['manager_id']] += 1

three_reports = all(count == 3 for count in manager_reports.values())
verification_results.append({
    "check": "Each manager has exactly 3 reports",
    "expected": True,
    "actual": three_reports,
    "pass": three_reports
})

# 6. No cycles
# Build graph and check for cycles
graph = defaultdict(list)
for _, row in df.iterrows():
    if pd.notna(row['manager_id']):
        graph[row['manager_id']].append(row['employee_id'])

def has_cycle(node, visited, rec_stack):
    visited.add(node)
    rec_stack.add(node)
    for child in graph.get(node, []):
        if child not in visited:
            if has_cycle(child, visited, rec_stack):
                return True
        elif child in rec_stack:
            return True
    rec_stack.remove(node)
    return False

visited = set()
rec_stack = set()
cycle_found = False
for node in df['employee_id']:
    if node not in visited:
        if has_cycle(node, visited, rec_stack):
            cycle_found = True
            break

verification_results.append({
    "check": "No cycles in hierarchy",
    "expected": False,
    "actual": cycle_found,
    "pass": not cycle_found
})

# Save data to CSV
df.to_csv('employee_hierarchy.csv', index=False)

# Save verification results
with open('hierarchy_verification.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ["check", "expected", "actual", "pass"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(verification_results)

print("Verification Results:")
for result in verification_results:
    print(f"{result['check']}: {'PASS' if result['pass'] else 'FAIL'}")
    print(f"  Expected: {result['expected']}")
    print(f"  Actual: {result['actual']}")
    print()

overall_pass = all(r['pass'] for r in verification_results)
print(f"Overall: {'PASS' if overall_pass else 'FAIL'}")

print("\nData saved to employee_hierarchy.csv")
print("Verification saved to hierarchy_verification.csv")