import os, json, zipfile, textwrap

BASE = "research_datalake"
dirs = [
    "config/modules", "data/incoming", "data/raw", "data/staging", "data/curated",
    "data/archive", "data/metadata", "logs", "reports", "src", "tests"
]

files = {}

# ---------- CONFIG FILES ----------
files["config/settings.yaml"] = textwrap.dedent("""\
sftp:
  host: huron-v12-sftp.example.com
  user: huron_feed
  private_key: ~/.ssh/id_rsa
  remote_dir: /outgoing/bu/
  local_dir: ./data/incoming/

paths:
  raw: ./data/raw/
  staging: ./data/staging/
  curated: ./data/curated/
  archive: ./data/archive/
  manifest: ./data/metadata/manifest.json
  log_file: ./logs/etl.log

email:
  sender: noreply@bu.edu
  recipients: ["research-admin@bu.edu"]
  smtp_host: mailhub.bu.edu
  smtp_port: 25

alerts:
  slack_webhook: "https://hooks.slack.com/services/XXXXXX"

settings:
  retention_days: 90
  max_parallel_jobs: 4
  allowed_extensions: [".csv"]
""")

files["config/modules/irb.yaml"] = "expected_columns: ['protocol_id', 'study_title', 'pi_name', 'status', 'last_updated']\n"
files["config/modules/grants.yaml"] = "expected_columns: ['award_id', 'sponsor', 'pi_name', 'amount', 'status']\n"

# ---------- MOCK CSV DATA ----------
files["data/incoming/IRB_PROTOCOL_2025-10-30.csv"] = textwrap.dedent("""\
protocol_id,study_title,pi_name,status,last_updated
IRB001,Stem Cell Research,Dr. Jane Smith,Active,2025-10-29
IRB002,Behavioral Study,Dr. Alan Roe,Closed,2025-10-28
IRB003,COVID Vaccine Trial,Dr. Nina Tran,Active,2025-10-27
""")

files["data/incoming/GRANTS_2025-10-30.csv"] = textwrap.dedent("""\
award_id,sponsor,pi_name,amount,status
GRANT001,NIH,Dr. Jane Smith,500000,Active
GRANT002,NSF,Dr. Alan Roe,200000,Active
GRANT003,DARPA,Dr. Nina Tran,750000,Pending
""")

files["data/metadata/manifest.json"] = json.dumps([], indent=2)

# ---------- PYTHON FILES ----------
files["src/transform_clean.py"] = textwrap.dedent("""\
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
""")

files["src/validate_schema.py"] = textwrap.dedent("""\
import pandas as pd, yaml, logging

def validate_schema(file_path, module_cfg):
    df = pd.read_csv(file_path)
    expected = module_cfg['expected_columns']
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"{file_path} missing columns: {missing}")
    logging.info(f"{file_path} passed schema validation")
    return df
""")

files["src/load_curated.py"] = textwrap.dedent("""\
import shutil, os, logging

def promote_to_curated(staged_file, curated_dir):
    os.makedirs(curated_dir, exist_ok=True)
    dest = os.path.join(curated_dir, os.path.basename(staged_file))
    shutil.copy2(staged_file, dest)
    logging.info(f"Promoted {staged_file} to curated zone")
    return dest
""")

files["src/metadata_utils.py"] = textwrap.dedent("""\
import json, os, datetime, hashlib, logging

def file_hash(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        while chunk := f.read(8192): h.update(chunk)
    return h.hexdigest()

def update_manifest(file_path, manifest_path):
    entry = {
        'filename': os.path.basename(file_path),
        'hash': file_hash(file_path),
        'timestamp': datetime.datetime.now().isoformat()
    }
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    manifest = []
    if os.path.exists(manifest_path):
        manifest = json.load(open(manifest_path))
    manifest.append(entry)
    json.dump(manifest, open(manifest_path, 'w'), indent=2)
    logging.info(f"Manifest updated with {file_path}")
""")

files["src/data_quality.py"] = textwrap.dedent("""\
import pandas as pd, logging

def profile_data(file_path):
    df = pd.read_csv(file_path)
    nulls = int(df.isna().sum().sum())
    completeness = 100 - (nulls / (len(df) * len(df.columns))) * 100
    logging.info(f"{file_path}: {len(df)} rows, completeness {completeness:.2f}%")
    return completeness
""")

files["src/main.py"] = textwrap.dedent("""\
import yaml, glob, logging, os
from src.validate_schema import validate_schema
from src.transform_clean import clean_data
from src.load_curated import promote_to_curated
from src.metadata_utils import update_manifest
from src.data_quality import profile_data

def run_module(module, cfg):
    logging.info(f"Running module {module}")
    module_cfg = yaml.safe_load(open(f'config/modules/{module}.yaml'))
    for f in glob.glob('data/incoming/*.csv'):
        if module.upper() in os.path.basename(f).upper():
            df = validate_schema(f, module_cfg)
            staged = clean_data(f, cfg['paths']['staging'])
            curated = promote_to_curated(staged, cfg['paths']['curated'])
            profile_data(curated)
            update_manifest(curated, cfg['paths']['manifest'])

if __name__ == '__main__':
    logging.basicConfig(filename='./logs/etl.log', level=logging.INFO)
    cfg = yaml.safe_load(open('./config/settings.yaml'))
    for m in ['irb','grants']: run_module(m, cfg)
    print('ETL completed successfully.')
""")

files["manage.py"] = textwrap.dedent("""\
import click, yaml
from src.main import run_module

@click.group()
def cli(): pass

@cli.command()
@click.option('--module', default='irb')
def run(module):
    cfg = yaml.safe_load(open('./config/settings.yaml'))
    run_module(module, cfg)

if __name__ == '__main__':
    cli()
""")

files["requirements.txt"] = "pandas\nyaml\nclick\n"

# ---------- BUILD FUNCTION ----------
def make_project():
    for d in dirs:
        os.makedirs(os.path.join(BASE, d), exist_ok=True)
    for path, content in files.items():
        full_path = os.path.join(BASE, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f: f.write(content)
    with zipfile.ZipFile(f"{BASE}_prototype_v1.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, fs in os.walk(BASE):
            for name in fs:
                p = os.path.join(root, name)
                z.write(p, os.path.relpath(p, "."))
    print(f"✅ Project created and zipped: {BASE}_prototype_v1.zip")

if __name__ == "__main__":
    make_project()

