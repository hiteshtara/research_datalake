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
