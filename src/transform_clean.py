import pandas as pd, os, logging, datetime

def clean_data(input_file, output_dir):
    df = pd.read_csv(input_file)
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    df['load_date'] = datetime.date.today().isoformat()
    os.makedirs(output_dir, exist_ok=True)
    out = os.path.join(output_dir, os.path.basename(input_file))
    df.to_csv(out, index=False)
    logging.info(f"Cleaned {input_file} -> {out}")
    return out
