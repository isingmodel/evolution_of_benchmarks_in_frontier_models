import pandas as pd
import os

def generate_markdown():
    # Load data
    models_df = pd.read_csv('data/models.csv')
    taxonomy_df = pd.read_csv('data/benchmark_taxonomy.csv')
    
    # Sort models by date descending
    models_df['release date'] = pd.to_datetime(models_df['release date'])
    models_df = models_df.sort_values('release date', ascending=False)
    # Format date back to string
    models_df['release date'] = models_df['release date'].dt.strftime('%Y-%m-%d')
    
    # Create Markdown content
    md_content = """# Benchmark Evolution in Frontier Models

This repository tracks the benchmarks used by frontier AI models (OpenAI, Google, etc.) over time.

## Evolution Graph
![Benchmark Evolution](assets/benchmark_evolution.png)

## Benchmark Landscape Growth
The following graph shows the cumulative growth of unique benchmarks per topic over time.
![Benchmark Growth](assets/benchmark_growth.png)

## Models Data
The following table lists the models and their associated benchmarks.

"""
    # Convert models dataframe to markdown table
    md_content += models_df.to_markdown(index=False)
    
    md_content += "\n\n## Benchmark Taxonomy\nClassification of various benchmarks by category.\n\n"
    
    # Convert taxonomy dataframe to markdown table
    # Clean up NaN in taxonomy for better display
    taxonomy_df_clean = taxonomy_df.fillna('')
    md_content += taxonomy_df_clean.to_markdown(index=False)
    
    md_content += """

## Categorization Logic
To simplify visualizations, each benchmark is assigned a single **Main Category**. When a benchmark maps to multiple categories, the following priority logic is applied:
1. **Agent**: Tasks requiring environment interaction or multi-step tool use.
2. **Multimodal**: Tasks involving vision, audio, or video.
3. **Math/Coding**: Specialized technical skills.
4. **Long Context**: Retrieval/reasoning over long sequences.
5. **Safety/Instruction**: Alignment, safety, or formatting constraints.
6. **Thinking & Reasoning**: General high-level reasoning.
7. **Knowledge**: General factual Q&A.

## Auto-Update
To keep this repository up-to-date, run:
```bash
python scripts/generate_visuals.py
python scripts/generate_trend_graph.py
python scripts/update_readme.py
```"""
    
    with open('README.md', 'w') as f:
        f.write(md_content)
    
    print("README.md updated.")

if __name__ == "__main__":
    generate_markdown()
