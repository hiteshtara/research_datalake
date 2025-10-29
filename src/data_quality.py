import pandas as pd, logging

def profile_data(file_path):
    df = pd.read_csv(file_path)
    nulls = int(df.isna().sum().sum())
    completeness = 100 - (nulls / (len(df) * len(df.columns))) * 100
    logging.info(f"{file_path}: {len(df)} rows, completeness {completeness:.2f}%")
    return completeness
