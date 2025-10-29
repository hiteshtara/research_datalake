import shutil, os, logging

def promote_to_curated(staged_file, curated_dir):
    os.makedirs(curated_dir, exist_ok=True)
    dest = os.path.join(curated_dir, os.path.basename(staged_file))
    shutil.copy2(staged_file, dest)
    logging.info(f"Promoted {staged_file} to curated zone")
    return dest
