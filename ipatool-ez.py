import os
import json
import subprocess
import time
from datetime import datetime, timedelta
import requests
import zipfile
import shutil

version = "1.1.0beta1"
debug = "false"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IPATOOL_PATH = os.path.join(SCRIPT_DIR, 'ipatool-main', 'main.py')
SAVED_DIR = SCRIPT_DIR
GITHUB_API_URL = "https://api.github.com/repos/1Emilis1/iPATool-EZ/releases"

os.makedirs(SAVED_DIR, exist_ok=True)

def save_account_to_file(data, filename):
    filepath = os.path.join(SAVED_DIR, filename)
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Account saved in {filepath}.")

def check_for_updates():
    response = requests.get(GITHUB_API_URL)
    if response.status_code != 200:
        print("Error fetching release information from GitHub.")
        return None
    
    releases = response.json()
    latest_release = None
    latest_beta = None

    for release in releases:
        release_name = release['name'].lower().replace(' ', '')
        if not release['prerelease']:
            if latest_release is None or release_name > latest_release['name'].lower():
                latest_release = release
        elif release['prerelease']:
            if latest_beta is None or release_name > latest_beta['name'].lower():
                latest_beta = release
    
    return latest_release, latest_beta

def update_script(release):
    zip_url = release['zipball_url']
    print(f"Downloading update from {zip_url}...")

    response = requests.get(zip_url)
    zip_path = os.path.join(SCRIPT_DIR, "update.zip")

    with open(zip_path, 'wb') as file:
        file.write(response.content)

    temp_extract_dir = os.path.join(SCRIPT_DIR, "temp_update")
    os.makedirs(temp_extract_dir, exist_ok=True)

    print("Extracting update...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_dir)

    extracted_folder_name = os.listdir(temp_extract_dir)[0]
    extracted_folder_path = os.path.join(temp_extract_dir, extracted_folder_name)

    for root, dirs, files in os.walk(extracted_folder_path):
        for file in files:
            source_file = os.path.join(root, file)
            target_path = os.path.join(SCRIPT_DIR, os.path.relpath(source_file, extracted_folder_path))

            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            if os.path.exists(target_path):
                print(f"Warning: {target_path} already exists. Removing it.")
                os.remove(target_path)

            shutil.copyfile(source_file, target_path)
            if debug == "true":
                print(f"[DEBUG] Copied and overwritten: {target_path}")

    shutil.rmtree(temp_extract_dir)
    os.remove(zip_path)
    print("Update complete. Restart the script to apply changes.")

def handle_update():
    latest_release, latest_beta = check_for_updates()

    if latest_release is None:
        print("Could not fetch latest releases.")
        return

    current_version = version.lower()

    print(f"Current version: {current_version}")
    
    if "beta" in current_version:
        if latest_beta and latest_beta['name'].lower().replace(' ', '') > current_version:
            print(f"New beta version available: {latest_beta['name']}")
        if latest_release and latest_release['name'].lower().replace(' ', '') > current_version:
            print(f"New main version available: {latest_release['name']}")
        
        print("\nUpdate options:")
        print("1. Update to the latest beta version")
        print("2. Switch to the latest main release")
        print("3. Cancel update")

        choice = input("Choose an option (1/2/3): ")
        if choice == "1" and latest_beta and latest_beta['name'].lower().replace(' ', '') > current_version:
            update_script(latest_beta)
        elif choice == "2" and latest_release and latest_release['name'].lower().replace(' ', '') > current_version:
            update_script(latest_release)
        else:
            print("No update performed.")
    
    else:
        if latest_release and latest_release['name'].lower().replace(' ', '') > current_version:
            print(f"New main version available: {latest_release['name']}")
            choice = input("Do you want to update to the latest main release? (y/n): ")
            if choice.lower() == "y":
                update_script(latest_release)
            else:
                print("No update performed.")
        else:
            print("You are already on the latest version.")

def run_command(command):
    if debug == "true":
        print(f"[DEBUG] Running command: {' '.join(command)}")
    subprocess.run(command)

def download_app():
    print("# Select account:")
    accounts = list_accounts()
    if not accounts:
        print("No accounts available.")
        return

    try:
        account_number = int(input("\nEnter account number: "))
        selected_account = accounts[account_number - 1][2]
    except (ValueError, IndexError):
        print("Invalid account number.")
        return

    apple_id = selected_account["Apple ID"]
    password = selected_account["Password"]
    two_factor_enabled = selected_account["2FA Enabled"]

    print(f"\nSelected Apple ID: {apple_id}")
    print(f"2FA Enabled: {two_factor_enabled}")

    app_id = input("Enter app id: ").strip()

    temporary_data = selected_account.get("Temporary", {})
    temporary_password = temporary_data.get("Temporary Password")
    expiration_time_str = temporary_data.get("Expires At")

    if temporary_password and expiration_time_str:
        expiration_time = datetime.strptime(expiration_time_str, "%Y-%m-%d %H:%M:%S")  # Convert string to datetime
        if datetime.now() < expiration_time:
            print("Using temporary password for download.")
        else:
            print("Temporary password has expired.")
            temporary_password = None  # Reset temporary password if expired

    if two_factor_enabled.lower() == 'yes' and not temporary_password:
        print("\nFetching 2FA code...")
        command = [
            'python', IPATOOL_PATH, 'download',
            '-i', '0',
            '-e', apple_id,
            '-p', password
        ]
        run_command(command)
        time.sleep(5)

        two_factor_code = input("Enter the 2FA code: ")
        temporary_password = f"{password}{two_factor_code}"

        selected_account['Temporary'] = {
            'Temporary Password': temporary_password,
            'Expires At': (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        }
        save_account_to_file(selected_account, f"account{account_number}.json")

    if not temporary_password:
        temporary_password = password

    print(f"\nDownloading app with app id {app_id}...")
    command = [
        'python', IPATOOL_PATH, 'download',
        '-i', app_id,
        '-e', apple_id,
        '-p', temporary_password
    ]
    run_command(command)

def list_accounts():
    account_files = [f for f in os.listdir(SAVED_DIR) if f.startswith('account') and f.endswith('.json')]
    account_files = sorted(account_files)
    accounts = []
    for i, file in enumerate(account_files, 1):
        with open(os.path.join(SAVED_DIR, file)) as f:
            data = json.load(f)
        print(f"{i}: {data['Apple ID']}")
        accounts.append((i, file, data))
    return accounts

if __name__ == "__main__":
    print(f"iPATool-EZ v{version} by 1Emilis (based on iPATool-PY)")
    print("\n1. Download an app")
    print("2. Create a new account")
    print("3. Check for Updates")
    choice = input("Choose an option (1/2/3): ")

    if choice == '1':
        download_app()
    elif choice == '2':
        subprocess.run(['python', 'accountsetup.py'])
    elif choice == '3':
        handle_update()
