
import os
import subprocess
import zipfile
import plistlib
import json
import shutil

# identify the os
if os.name == 'nt':
    clear = 'cls'
    python_exec = 'python'
    operatingsystem = 'Windows'
else:
    clear = 'clear'
    python_exec = 'python3'
    operatingsystem = 'Linux/Mac'

def run_ipatool(appid, country, apple_email, apple_pwd, temp_dir):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ipatool_main = os.path.abspath(os.path.join(script_dir, '../../ipatool-main/main.py'))
    cmd = [
        python_exec, ipatool_main,
        'lookup', '-i', appid, '-c', country,
        'download', '-e', apple_email, '-p', apple_pwd, '-o', temp_dir
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ipatool failed: {result.stderr}")
    return temp_dir

def ipa_to_zip(ipa_path, zip_path):
    shutil.copy(ipa_path, zip_path)

def extract_plist_from_zip(zip_path, extract_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            if file.endswith('iTunesMetadata.plist'):
                zip_ref.extract(file, extract_dir)
                return os.path.join(extract_dir, file)
    raise FileNotFoundError('iTunesMetadata.plist not found in zip')

def parse_plist(plist_path):
    with open(plist_path, 'rb') as f:
        plist = plistlib.load(f)
    latest = plist.get('softwareVersionExternalIdentifier')
    all_versions = plist.get('softwareVersionExternalIdentifiers', [])
    return latest, all_versions

def save_versions_json(latest, all_versions, output_path):
    data = [latest] + [v for v in all_versions if v != latest]
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def cleanup(paths):
    for path in paths:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.isfile(path):
            os.remove(path)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Download IPA, extract version info, and save to JSON.')
    parser.add_argument('--appid', required=True, help='App ID')
    parser.add_argument('--country', required=True, help='Country code')
    parser.add_argument('--email', required=True, help='Apple ID email')
    parser.add_argument('--password', required=True, help='Apple ID password')
    # Remove --output argument, output path will be determined by appid
    args = parser.parse_args()
    # i forgot how this works so this script will not be updated for a long time
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    zip_path = None
    try:
        run_ipatool(args.appid, args.country, args.email, args.password, temp_dir)
        ipa_files = [f for f in os.listdir(temp_dir) if f.endswith('.ipa')]
        if not ipa_files:
            raise FileNotFoundError('No .ipa file found in temp directory')
        ipa_path = os.path.join(temp_dir, ipa_files[0])
        zip_path = ipa_path.replace('.ipa', '.zip')
        ipa_to_zip(ipa_path, zip_path)
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        plist_path = extract_plist_from_zip(zip_path, extract_dir)
        latest, all_versions = parse_plist(plist_path)
        # Save to ../../saved/apphistory/<appid>.json
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../saved/apphistory'))
        os.makedirs(save_dir, exist_ok=True)
        output_path = os.path.join(save_dir, f'{args.appid}.json')
        save_versions_json(latest, all_versions, output_path)
    finally:
        cleanup([temp_dir] + ([zip_path] if zip_path and os.path.exists(zip_path) else []))

if __name__ == '__main__':
    main()
