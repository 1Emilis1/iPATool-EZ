import os

# identify the os
if os.name == 'nt':
    clear = 'cls'
    python_exec = 'python'
    operatingsystem = 'Windows'
else:
    clear = 'clear'
    python_exec = 'python3'
    operatingsystem = 'Linux/Mac'


import argparse
import json
import subprocess

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download a selected version for an app.")
    parser.add_argument("--appid", required=True, help="App ID")
    parser.add_argument("--country", required=True, help="Country code")
    parser.add_argument("--email", required=True, help="Apple ID email")
    parser.add_argument("--password", required=True, help="Apple ID password (2FA if needed)")
    args = parser.parse_args()

    appid = args.appid
    country = args.country
    email = args.email
    password = args.password

    apphistory_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../saved/apphistory', f'{appid}.json'))
    if not os.path.exists(apphistory_path):
        print(f"App history file not found: {apphistory_path}")
        exit(1)
    with open(apphistory_path, 'r', encoding='utf-8') as f:
        version_ids = json.load(f)
    if not isinstance(version_ids, list):
        print("App history JSON is not a list of version IDs.")
        exit(1)

    # List versions from latest to oldest
    print("The versions are listed from latest to oldest.")
    for idx, verid in enumerate(version_ids):
        print(f"{idx+1}: {verid}")

    # Prompt user to select a version
    try:
        selection = int(input("\nEnter the number of the version to download: "))
        if not (1 <= selection <= len(version_ids)):
            raise ValueError
    except ValueError:
        print("Invalid selection.")
        exit(1)

    selected_verid = version_ids[selection-1]

    ipatool_main = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ipatool-main/main.py'))
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../saved', str(appid)))
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nDownloading version {selected_verid} for app {appid}...")
    cmd = [
        python_exec, ipatool_main,
        'download', '-i', str(appid), '-c', str(country),
        '-e', str(email), '-p', str(password),
        '--appVerId', str(selected_verid),
        '-o', output_dir
    ]
    print("Running command:", ' '.join(map(str, cmd)))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Failed to download version {selected_verid} for app {appid}.")
    else:
        print(f"Downloaded version {selected_verid} for app {appid}.")
