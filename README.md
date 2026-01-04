# AI Email Editing Tool

An interactive web application built with Streamlit that uses AI to refine and evaluate email content. The tool allows users to select emails, apply various editing actions (elaborate, shorten, adjust tone), and evaluate the results using multiple metrics.

## Features

- **Email Editing**: Use AI models to elaborate, shorten, or adjust the tone of emails
- **Model Selection**: Choose between different base LLM models (gpt-4.1, gpt-4o-mini) for generation
- **Evaluation System**: Comprehensive evaluation using multiple metrics:
  - Faithfulness: How well the revised email maintains the original intent
  - Completeness: How complete and comprehensive the revised email is
  - Robustness: How well the email handles potential issues or edge cases
- **Judge Models**: Multiple judge models for evaluation (gpt-4.1, gpt-4o-mini)
- **Dataset Support**: Pre-built datasets for different email types:
  - Short emails (lengthen.jsonl)
  - Long emails (shorten.jsonl)
  - Tone adjustment emails (tone.jsonl)
- **Visualization**: Generate plots to analyze evaluation results, including:
  - Score distributions by dataset and model
  - Length vs score correlations
  - Variance analysis
  - Model performance comparisons

## Installation

1. **Clone or download the repository**

2. **Set up a Python virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory with your OpenAI API credentials:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_API_BASE=https://api.openai.com/v1  # or your custom endpoint
   ```

## Usage

### Running the Web Application

Start the Streamlit application:
```bash
streamlit run app.py
```

This will launch the web interface where you can:
- Select email datasets
- Choose base LLM and judge models
- Edit emails using AI
- View evaluation results

### Generating Evaluation Plots

Run the plotting script to analyze evaluation results:
```bash
python plot_evaluation.py
```

This will generate various plots in the `plots/` directory, including:
- `scores_by_dataset_model.png`: Box plots of scores by dataset and model
- `length_vs_score.png`: Scatter plot of content length vs scores
- `variance_distribution.png`: Histograms of score variances
- `avg_scores_by_metric.png`: Average scores by metric and model
- `varying_scores_count.png`: Count of emails with varying judge scores
- `scores_by_metric_model.png`: Scores distribution by metric

## Project Structure

```
ai_bootcamp_starter/
├── app.py                    # Main Streamlit application
├── generate.py              # Email generation and evaluation logic
├── plot_evaluation.py       # Script for generating analysis plots
├── prompts.yaml             # AI prompts and evaluation criteria
├── requirements.txt         # Python dependencies
├── evaluation_results.csv   # Evaluation results data
├── summary_results.csv      # Summarized evaluation results
├── datasets/                # Original email datasets
│   ├── lengthen.jsonl
│   ├── shorten.jsonl
│   └── tone.jsonl
├── self_generated_datasets/ # AI-generated email datasets
│   ├── gpt-4.1/
│   └── gpt-4o-mini/
├── tests/                   # Test files and data
└── plots/                   # Generated plots (created by plot_evaluation.py)
```

## Configuration

### Prompts
The `prompts.yaml` file contains:
- Email editing prompts for different actions
- Evaluation criteria and rating levels for each metric
- Judge model instructions

### Models
- **Base Models**: Used for generating email revisions
  - gpt-4.1
  - gpt-4o-mini
- **Judge Models**: Used for evaluating revisions
  - gpt-4.1
  - gpt-4o-mini

## Evaluation Metrics

1. **Faithfulness**: Measures how well the revised email preserves the original message's intent and key information
2. **Completeness**: Assesses whether the revised email includes all necessary information and details
3. **Robustness**: Evaluates how well the email handles potential misunderstandings or edge cases

Each evaluation uses 3 ratings from the judge model, providing mean scores and variance analysis.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Requirements

- Python 3.8+
- OpenAI API access
- Internet connection for API calls

## Troubleshooting

- **Rate Limit Errors**: The application may hit OpenAI API rate limits. Consider upgrading your OpenAI plan or implementing retry logic.
- **Environment Variables**: Ensure your `.env` file is properly configured with valid API credentials.
- **Dependencies**: Make sure all packages from `requirements.txt` are installed in your virtual environment.