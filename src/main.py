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
