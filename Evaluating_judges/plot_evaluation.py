import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
sns.set_style("whitegrid")

# Read the evaluation results
df = pd.read_csv('evaluation_results.csv')

# Calculate the length of revised content
df['revised_length'] = df['revised_content'].str.len()

# Ensure mean is numeric
df['mean'] = pd.to_numeric(df['mean'], errors='coerce')
df['variance'] = pd.to_numeric(df['variance'], errors='coerce')

# Create plots directory if not exists
os.makedirs('plots', exist_ok=True)

# 1. Box plot of mean scores by dataset and judge_model
plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x='dataset', y='mean', hue='judge_model')
plt.title('Mean Scores by Dataset and Judge Model')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('plots/scores_by_dataset_model.png')
plt.show()

# 2. Scatter plot of revised_length vs mean, colored by judge_model, separated by dataset
for dataset in df['dataset'].unique():
    dataset_df = df[df['dataset'] == dataset]
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=dataset_df, x='revised_length', y='mean', hue='judge_model', alpha=0.7)
    plt.title(f'Revised Content Length vs Mean Score - {dataset}')
    plt.xlabel('Revised Content Length')
    plt.ylabel('Mean Score')
    plt.tight_layout()
    plt.savefig(f'plots/length_vs_score_{dataset}.png')
    plt.show()

# 3. Histogram of variance by judge_model
plt.figure(figsize=(10, 6))
for model in df['judge_model'].unique():
    subset = df[df['judge_model'] == model]
    plt.hist(subset['variance'].dropna(), alpha=0.5, label=model, bins=20)
plt.title('Distribution of Variance by Judge Model')
plt.xlabel('Variance')
plt.ylabel('Frequency')
plt.legend()
plt.tight_layout()
plt.savefig('plots/variance_distribution.png')
plt.show()

# 4. Bar plot of average mean score per model per metric
avg_scores = df.groupby(['judge_model', 'metric'])['mean'].mean().reset_index()
plt.figure(figsize=(10, 6))
sns.barplot(data=avg_scores, x='metric', y='mean', hue='judge_model')
plt.title('Average Mean Score by Metric and Judge Model')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('plots/avg_scores_by_metric.png')
plt.show()

# 5. Count of emails with varying scores (variance > 0) by model
varying_counts = df.groupby('judge_model')['variance'].apply(lambda x: (x > 0).sum()).reset_index()
varying_counts.columns = ['judge_model', 'count_varying']
plt.figure(figsize=(8, 5))
sns.barplot(data=varying_counts, x='judge_model', y='count_varying')
plt.title('Count of Emails with Varying Scores (Variance > 0) by Judge Model')
plt.xlabel('Judge Model')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig('plots/varying_scores_count.png')
plt.show()

# 6. Box plot of mean scores by metric and judge_model
plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x='metric', y='mean', hue='judge_model')
plt.title('Mean Scores by Metric and Judge Model')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('plots/scores_by_metric_model.png')
plt.show()

print("Plots generated and saved in 'plots' directory.")