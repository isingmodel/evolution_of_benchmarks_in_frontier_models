import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import os

# Set aesthetic style
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Verdana', 'Arial', 'DejaVu Sans']

def load_data():
    models_df = pd.read_csv('data/models.csv')
    taxonomy_df = pd.read_csv('data/benchmark_taxonomy.csv')
    return models_df, taxonomy_df

def process_benchmark_dates(models_df):
    # Find the first appearance date for each benchmark
    benchmark_first_seen = {}
    
    for _, row in models_df.iterrows():
        date = pd.to_datetime(row['release date'])
        benchmarks_str = str(row['benchmarks'])
        if pd.isna(benchmarks_str) or benchmarks_str.lower() == 'nan':
            continue
            
        b_list = [b.strip() for b in benchmarks_str.split(',')]
        for b in b_list:
            b_clean = b.strip().lower() # normalize for key
            if b_clean not in benchmark_first_seen:
                benchmark_first_seen[b_clean] = date
            else:
                if date < benchmark_first_seen[b_clean]:
                    benchmark_first_seen[b_clean] = date
                    
    return benchmark_first_seen

def generate_trend_graph():
    models_df, taxonomy_df = load_data()
    
    # Categories of interest
    category_cols = [
        'Knowledge', 'Thinking & Reasoning', 'Math', 'Coding', 'Agent', 
        'Multimodal', 'Long Context', 'Safety', 'Instruction'
    ]
    
    # 1. Build lookup from taxonomy
    # Key: Lowercase clean name
    taxonomy_lookup = {}
    for _, row in taxonomy_df.iterrows():
        name = str(row['Benchmark']).strip().lower()
        
        # Only use Main Category
        main_cat = str(row.get('Main Category', '')).strip()
        if main_cat and main_cat.lower() != 'nan':
            cats = [main_cat]
        else:
            cats = []
        
        taxonomy_lookup[name] = cats
        
        # Split alias if exists (e.g. "MMLU / MMLU-Pro")
        if '/' in name:
            parts = [p.strip() for p in name.split('/')]
            for p in parts:
                taxonomy_lookup[p] = cats

    # 2. Find first seen dates
    benchmark_dates = process_benchmark_dates(models_df)
    
    # 3. Create Timeline Events: (Date, Category)
    events = []
    
    for b_name, date in benchmark_dates.items():
        # Find category
        cats = []
        if b_name in taxonomy_lookup:
            cats = taxonomy_lookup[b_name]
        else:
            # Fuzzy match attempt
            found = False
            for k, v in taxonomy_lookup.items():
                if b_name == k or b_name in k or k in b_name:
                    cats = v
                    found = True
                    break
            if not found:
                # print(f"Unknown category for benchmark: {b_name}")
                continue
        
        for c in cats:
            events.append({'Date': date, 'Category': c})
            
    events_df = pd.DataFrame(events)
    if events_df.empty:
        print("No events found.")
        return
        
    events_df.sort_values('Date', inplace=True)
    
    # 4. Create Cumulative Data
    # Min date to Max date
    min_date = events_df['Date'].min()
    max_date = events_df['Date'].max()
    # Extend max date a bit for future view
    max_date = max(max_date, pd.to_datetime('today'))
    
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    
    # DataFrame to hold cumulative counts
    # Index: Date, Columns: Categories
    cum_counts = pd.DataFrame(0, index=date_range, columns=category_cols)
    
    # Iterate through days and cumulative sum?
    # Easier: group by date and count, then reindex and cumsum
    
    # Pivot events: Date, Category -> Count
    # We aggregate by Day first
    daily_counts = events_df.groupby(['Date', 'Category']).size().unstack(fill_value=0)
    
    # Reindex to full range
    daily_counts = daily_counts.reindex(date_range, fill_value=0)
    
    # Ensure all columns exist
    for c in category_cols:
        if c not in daily_counts.columns:
            daily_counts[c] = 0
            
    # Cumulative Sum
    cum_data = daily_counts.cumsum()
    
    # Normalize to Percentage
    # Divide each row by its sum to get proportion (0-1)
    row_sums = cum_data.sum(axis=1)
    # Avoid division by zero
    cum_data_percent = cum_data.div(row_sums, axis=0).fillna(0)
    
    # Plotting
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Colors
    colors = sns.color_palette("Set3", n_colors=len(category_cols))
    
    # Stackplot
    # x needs to be separate
    x = cum_data_percent.index
    y = [cum_data_percent[col] for col in category_cols]
    
    ax.stackplot(x, y, labels=category_cols, colors=colors, alpha=0.9)
    
    # Aesthetics
    ax.set_title("Relative Composition of Benchmark Landscape over Time", fontsize=20, weight='bold', pad=20)
    ax.set_ylabel("Percentage of Total Benchmarks", fontsize=14, labelpad=10)
    ax.set_xlabel("Time", fontsize=14, labelpad=10)
    
    # Format Y axis as percentage
    import matplotlib.ticker as mtick
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    
    # Legend
    # Inverse legend order to match stack order usually?
    # Stackplot draws first bottom, so legend should match
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc='upper left', fontsize=12, title="Category", bbox_to_anchor=(1.02, 1))
    
    # Grid
    ax.grid(True, which='major', axis='y', linestyle='--', alpha=0.5)
    ax.grid(False, axis='x') # clean look
    
    # X-Axis Date formatting
    locator = mdates.MonthLocator(interval=3)
    fmt = mdates.DateFormatter('%Y-%m')
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(fmt)
    plt.xticks(rotation=45)
    
    # Limits
    ax.set_xlim(min_date, max_date)
    ax.set_ylim(0, cum_data.iloc[-1].sum() * 1.1)
    
    plt.tight_layout()
    
    os.makedirs('assets', exist_ok=True)
    out_path = 'assets/benchmark_growth.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"Graph generated at {out_path}")

if __name__ == "__main__":
    generate_trend_graph()
