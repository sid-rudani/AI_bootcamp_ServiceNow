import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

datasets = {"short": [], "medium": [], "long": []}
file_paths = ["short_emails.jsonl", "medium_emails.jsonl", "long_emails.jsonl"]

for file_path in file_paths:
    dataset_name = file_path.split('_')[0]
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    email = json.loads(line)
                    datasets[dataset_name].append(email)
                except json.JSONDecodeError:
                    pass

content_lengths = {name: [len(email["content"]) for email in emails] for name, emails in datasets.items()}
subject_lengths = {name: [len(email["subject"]) for email in emails] for name, emails in datasets.items()}

all_content_lengths = [len(email["content"]) for emails in datasets.values() for email in emails]
all_subject_lengths = [len(email["subject"]) for emails in datasets.values() for email in emails]

xmin_c, xmax_c = min(all_content_lengths), max(all_content_lengths)
xmin_s, xmax_s = min(all_subject_lengths), max(all_subject_lengths)

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
colors = {'short': 'blue', 'medium': 'green', 'long': 'red'}

# Content
ax = axes[0]
for name, lengths in content_lengths.items():
    ax.hist(lengths, bins=50, density=True, alpha=0.5, color=colors[name], label=name.capitalize())
    mu, std = norm.fit(lengths)
    x = np.linspace(xmin_c, xmax_c, 100)
    p = norm.pdf(x, mu, std)
    ax.plot(x, p, color=colors[name], linewidth=2, linestyle='--')
ax.set_xlim(xmin_c, xmax_c)
ax.set_title('Content Length Distribution')
ax.set_xlabel('Length of Content')
ax.set_ylabel('Density')
ax.legend()

# Subject
ax = axes[1]
for name, lengths in subject_lengths.items():
    ax.hist(lengths, bins=50, density=True, alpha=0.5, color=colors[name], label=name.capitalize())
    mu, std = norm.fit(lengths)
    x = np.linspace(xmin_s, xmax_s, 100)
    p = norm.pdf(x, mu, std)
    ax.plot(x, p, color=colors[name], linewidth=2, linestyle='--')
ax.set_xlim(xmin_s, xmax_s)
ax.set_title('Subject Length Distribution')
ax.set_xlabel('Length of Subject')
ax.set_ylabel('Density')
ax.legend()

plt.tight_layout()
plt.savefig('dataset_variance.png')
plt.show()