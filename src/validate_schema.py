import pandas as pd, yaml, logging

def validate_schema(file_path, module_cfg):
    df = pd.read_csv(file_path)
    expected = module_cfg['expected_columns']
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"{file_path} missing columns: {missing}")
    logging.info(f"{file_path} passed schema validation")
    return df
