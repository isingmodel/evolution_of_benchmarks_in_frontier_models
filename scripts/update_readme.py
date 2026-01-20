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
    # Read base markdown
    with open('data/base_readme.md', 'r') as f:
        md_content = f.read()
    
    # Generate tables
    models_table = models_df.to_markdown(index=False)
    
    taxonomy_df_clean = taxonomy_df.fillna('')
    taxonomy_table = taxonomy_df_clean.to_markdown(index=False)
    
    # Replace placeholders
    md_content = md_content.replace('{{MODELS_TABLE}}', models_table)
    md_content = md_content.replace('{{TAXONOMY_TABLE}}', taxonomy_table)
    
    with open('README.md', 'w') as f:
        f.write(md_content)
    
    print("README.md updated.")

if __name__ == "__main__":
    generate_markdown()
