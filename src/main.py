import yaml, glob, logging, os
from src.validate_schema import validate_schema
from src.transform_clean import clean_data
from src.load_curated import promote_to_curated
from src.metadata_utils import update_manifest
from src.data_quality import profile_data
from src.notify_email import send_notification
from src.notify_slack import send_slack_alert
from src.retention_cleanup import purge_old_files, archive_curated_data

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
    try:
        for m in ['irb','grants']:
            run_module(m, cfg)
        # Archive + Retention Cleanup
        archive_curated_data(cfg['paths']['curated'], cfg['paths']['archive'])
        purge_old_files(cfg['paths']['raw'], cfg['settings']['retention_days'])
        # Notifications
        send_notification(cfg, "ETL Success", "IRB + Grants modules completed successfully.")
        send_slack_alert(cfg['alerts']['slack_webhook'], "BU ETL Pipeline", "SUCCESS", "All modules completed successfully.")
        print("✅ ETL pipeline completed successfully.")
    except Exception as e:
        msg = f"ETL Failed: {str(e)}"
        send_notification(cfg, "ETL Failure", msg)
        send_slack_alert(cfg['alerts']['slack_webhook'], "BU ETL Pipeline", "FAILURE", msg)
        raise
