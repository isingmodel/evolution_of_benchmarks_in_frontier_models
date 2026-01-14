import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import seaborn as sns
import os

# Set aesthetic style
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Verdana', 'Arial', 'DejaVu Sans']

def load_data():
    models_df = pd.read_csv('data/models.csv')
    taxonomy_df = pd.read_csv('data/benchmark_taxonomy.csv')
    return models_df, taxonomy_df

def process_data(models_df, taxonomy_df):
    # Categories of interest (used for graph structure)
    category_cols = [
        'Knowledge', 'Thinking & Reasoning', 'Math', 'Coding', 'Agent', 
        'Multimodal', 'Long Context', 'Safety', 'Instruction'
    ]
    
    # 1. Map benchmarks to categories
    benchmark_cats = {}
    for _, row in taxonomy_df.iterrows():
        name = str(row['Benchmark']).strip()
        
        # Only use Main Category column
        main_cat = str(row.get('Main Category', '')).strip()
        if main_cat and main_cat.lower() != 'nan':
            cats = [main_cat]
        else:
            cats = []
        
        benchmark_cats[name.lower()] = cats

    # 2. Process each model
    models_data = []
    
    for _, row in models_df.iterrows():
        model_name = row['Model name']
        # Handle duplicate indices or NaN
        if pd.isna(model_name): continue
        
        provider = row['Provider']
        date_str = row['release date']
        benchmarks_str = str(row['benchmarks'])
        
        bench_list = []
        if not (pd.isna(benchmarks_str) or benchmarks_str.lower() == 'nan'):
            bench_list = [b.strip() for b in benchmarks_str.split(',')]
            
        # Count categories
        cat_counts = {c: 0 for c in category_cols}
        total_hits = 0
        
        for b in bench_list:
            b_clean = b.strip().lower()
            
            # Find matching categories
            found = False
            # Direct match
            if b_clean in benchmark_cats:
                for c in benchmark_cats[b_clean]:
                    cat_counts[c] += 1
                    total_hits += 1
                found = True
            else:
                # Substring/Fuzzy match
                for k, v in benchmark_cats.items():
                    # k is taxonomy name, b_clean is model's bench name
                    # e.g. "MMLU / MMLU-Pro" vs "MMLU"
                    if b_clean == k or b_clean in k.split('/') or k in b_clean:
                         for c in v:
                            cat_counts[c] += 1
                            total_hits += 1
                         found = True
                         break
            
            if not found:
                # print(f"Warning: Category not found for benchmark '{b}' in model '{model_name}'")
                pass

        # Normalize to ratios
        ratios = []
        if total_hits > 0:
            ratios = [cat_counts[c] / total_hits for c in category_cols]
        else:
            # If no info, maybe a gray placeholder? 
            # Or equal distribution? Let's do empty list to handle specially.
            ratios = [0] * len(category_cols)

        entry = {
            'Model': model_name,
            'Provider': provider,
            'Date': pd.to_datetime(date_str),
            'Ratios': ratios,
            'TotalHits': total_hits
        }
        models_data.append(entry)
        
    return pd.DataFrame(models_data), category_cols

def generate_graph():
    models_df_raw, taxonomy_df = load_data()
    df, cat_cols = process_data(models_df_raw, taxonomy_df)
    
    if df.empty:
        print("No data.")
        return

    df = df.sort_values('Date')
    
    # Setup Figure
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Provider Y-Axis Mapping
    providers = sorted(df['Provider'].unique())
    # You might want specific order (e.g. OpenAI top, Google bottom, or vice versa)
    # Let's keep alphabetical or just sorted
    y_map = {p: i for i, p in enumerate(providers)}
    
    # Color Palette
    # Using a distinct palette
    colors = sns.color_palette("Set3", n_colors=len(cat_cols))
    # Or "Paired" if not enough differentiation
    # colors = sns.color_palette("tab10", n_colors=len(cat_cols)) 
    
    # Title & Labels
    ax.set_title("Evolution of Frontier Model Benchmarks", fontsize=20, weight='bold', pad=20)
    ax.set_xlabel("Release Date", fontsize=14, labelpad=10)
    # ax.set_ylabel("Provider", fontsize=14)
    
    # Timeline Lines
    for p in providers:
        y = y_map[p]
        ax.axhline(y, color='gray', alpha=0.3, linestyle='-', linewidth=1.5, zorder=1)
        # Provider Label on Left
        # ax.text(df['Date'].min() - pd.Timedelta(days=30), y, p, 
        #         ha='right', va='center', fontsize=14, fontweight='bold', color='#333')

    # Configure Axes
    ax.set_yticks(range(len(providers)))
    ax.set_yticklabels(providers, fontsize=14, fontweight='bold')
    ax.tick_params(axis='y', length=0) # hide tick marks
    
    # X-Axis Date formatting
    locator = mdates.MonthLocator(interval=3)
    fmt = mdates.DateFormatter('%Y-%m')
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(fmt)
    plt.xticks(rotation=45, fontsize=10)
    
    # Margins
    min_date = df['Date'].min() - pd.Timedelta(days=60)
    max_date = df['Date'].max() + pd.Timedelta(days=60)
    ax.set_xlim(min_date, max_date)
    ax.set_ylim(-0.8, len(providers) - 0.2)
    
    # Draw Model Pies
    # Increase zorder to be on top
    
    # Track label positions to minimize overlap (simple alternation)
    last_x_per_y = {y: min_date for y in y_map.values()}
    
    for idx, row in df.iterrows():
        y_val = y_map[row['Provider']]
        date_val = row['Date']
        x_val = mdates.date2num(date_val)
        ratios = row['Ratios']
        
        # Pie Size
        # If no data (sum=0), show a gray dot
        if sum(ratios) == 0:
            ax.scatter(date_val, y_val, s=100, color='#cccccc', zorder=3)
        else:
            # Create Inset Axis for Pie
            # width/height in inches. 
            # 0.5 inches is a decent size for 16x9 figure
            pie_size = 0.55
            sub_ax = inset_axes(ax, width=pie_size, height=pie_size, 
                                loc='center', 
                                bbox_to_anchor=(x_val, y_val), 
                                bbox_transform=ax.transData,
                                borderpad=0)
            
            sub_ax.pie(ratios, colors=colors, startangle=90)
            sub_ax.set_aspect('equal') # Ensure circle
            sub_ax.axis('off') # Hide box
    
        # Label Annotation
        # Alternating top/bottom to reduce collision
        # Simple heuristic: alternating based on index? Or random?
        # Let's just alternate.
        offset_y = 25 if idx % 2 == 0 else -35
        
        ax.annotate(row['Model'], 
                    (date_val, y_val), 
                    xytext=(0, offset_y), 
                    textcoords='offset points', 
                    ha='center', va='center',
                    fontsize=9, 
                    fontweight='normal',
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7, ec="none"),
                    arrowprops=dict(arrowstyle="-", color='gray', alpha=0.5))

    # Legend
    legend_handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=12, label=cat) 
                      for cat, c in zip(cat_cols, colors)]
    
    # Place legend outside or neatly inside
    ax.legend(handles=legend_handles, title="Benchmark Category", 
              loc='upper center', bbox_to_anchor=(0.5, -0.15),
              ncol=5, frameon=False, fontsize=11, title_fontsize=12)
    
    plt.tight_layout()
    # Adjust layout to make room for legend at bottom
    plt.subplots_adjust(bottom=0.2)
    
    os.makedirs('assets', exist_ok=True)
    out_path = 'assets/benchmark_evolution.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"Graph generated at {out_path}")

if __name__ == "__main__":
    generate_graph()
