import os
import json
import subprocess
import time
from datetime import datetime, timedelta
import requests
import zipfile
import shutil

version = "1.1.0"
debug = "false"

#verify

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

def normalize_version(version):
    """ Normalize the version string for comparison. """
    return version.lower().replace('releasecandidate', 'rc').replace(' ', '').replace('beta', 'b')

def check_for_updates():
    response = requests.get(GITHUB_API_URL)
    if response.status_code != 200:
        print("Error fetching release information from GitHub.")
        return None
    
    releases = response.json()
    latest_release = None
    latest_beta = None

    current_version = normalize_version(version)

    for release in releases:
        release_name = normalize_version(release['name'])

        # Compare main release versions
        if not release['prerelease'] and 'b' not in release_name:
            if latest_release is None or release_name > latest_release['name'].lower().replace(' ', ''):
                latest_release = release

        # Compare beta versions
        elif 'b' in release_name:  # use 'b' instead of 'beta' after normalization
            if latest_beta is None or release_name > latest_beta['name'].lower().replace(' ', ''):
                latest_beta = release

    return latest_release, latest_beta

def handle_update():
    latest_release, latest_beta = check_for_updates()

    if latest_release is None and latest_beta is None:
        print("Could not fetch latest releases.")
        return

    # Normalize the current version for comparison
    current_version = normalize_version(version)
    print(f"Current version: {version}")

    # If on a beta version
    if "b" in current_version:
        # Check if a newer beta version is available
        if latest_beta and normalize_version(latest_beta['name']) > current_version:
            print(f"New beta version available: {latest_beta['name']}")
        else:
            print("You are already on the latest beta version.")

        # Check if the main release is newer than the current beta version
        if latest_release and normalize_version(latest_release['name']) > current_version:
            print(f"New main version available: {latest_release['name']}")

        print("\nUpdate options:")
        print("1. Update to the latest beta version")
        print("2. Switch to the latest main release")
        print("3. Cancel update")

        choice = input("Choose an option (1/2/3): ")
        if choice == "1" and latest_beta:
            update_script(latest_beta)
        elif choice == "2" and latest_release:
            update_script(latest_release)
        else:
            print("No update performed.")

    # If on a main release
    else:
        if latest_release and normalize_version(latest_release['name']) > current_version:
            print(f"New main version available: {latest_release['name']}")
            choice = input("Do you want to update to the latest main release? (y/n): ")
            if choice.lower() == "y":
                update_script(latest_release)
            else:
                print("No update performed.")

        # Check if a newer beta version is available
        if latest_beta and normalize_version(latest_beta['name']) > current_version:
            print(f"New beta version available: {latest_beta['name']}")
            choice = input("Do you want to switch to the latest beta version? (y/n): ")
            if choice.lower() == "y":
                update_script(latest_beta)
        else:
            print("You are already on the latest version.")

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
          
def run_command(command):
    if debug == "true":
        print(f"[DEBUG] Running command: {' '.join(command)}")
    subprocess.run(command)

def account_utility():
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

    while True:
        print("\nAccount Utility for:", apple_id)
        print("1. Change Password")
        print("2. Enter 2FA Code")
        print("3. Revoke Auto 2FA Password (Not Recommended)")
        print("4. Remove Account")
        print("5. Exit")

        utility_choice = input("Choose an option (1/2/3/4/5): ")

        if utility_choice == "1":
            new_password = input("Enter your new password: ")
            selected_account["Password"] = new_password
            save_account_to_file(selected_account, f"account{account_number}.json")
            print("Password updated.")

        elif utility_choice == "2":
            print("Get 2FA Code from going onto an Apple device. Go to settings > Apple Account > Sign-In & Security > Two-Factor Authentication > Get Verification Code.")
            two_factor_code = input("Enter the 2FA code: ")
            temporary_password = f"{password}{two_factor_code}"
            selected_account['Temporary'] = {
                'Temporary Password': temporary_password,
                'Expires At': (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            }
            save_account_to_file(selected_account, f"account{account_number}.json")
            print("2FA code entered and temporary password updated.")

        elif utility_choice == "3":
            print("Revoking Auto 2FA Password...")
            if "Temporary" in selected_account:
                del selected_account["Temporary"]
                save_account_to_file(selected_account, f"account{account_number}.json")
                print("Auto 2FA password revoked.")

        elif utility_choice == "4":
            confirm = input("Are you sure you want to remove this account? (y/n): ").lower()
            if confirm == "y":
                os.remove(os.path.join(SAVED_DIR, f"account{account_number}.json"))
                print("Account removed.")
                return  # Exit to darkness

        elif utility_choice == "5":
            return  # Exit the utility into darkness, spooky

        else:
            print("Invalid option. Please try again.")

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
        expiration_time = datetime.strptime(expiration_time_str, "%Y-%m-%d %H:%M:%S")
        if datetime.now() < expiration_time:
            print("Using temporary password for download.")
        else:
            print("Temporary password has expired.")
            temporary_password = None

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
        print("2FA code entered. Temporary password is valid for 24 hours.")

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
    print("Warning: Passwords are stored in plain text. Keep this script and the JSON files in a secure location.")
    print("\n1. Download an app")
    print("2. Create a new account")
    print("3. Account Utility")
    print("4. Check for Updates")
    choice = input("Choose an option (1/2/3/4): ")

    if choice == '1':
        download_app()
    elif choice == '2':
        subprocess.run(['python', 'accountsetup.py'])
    elif choice == '3':
        account_utility()
    elif choice == '4':
        handle_update()
