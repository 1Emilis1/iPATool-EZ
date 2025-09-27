import os
import json
import subprocess
import time
from datetime import datetime, timedelta
import requests
import zipfile
import shutil
import sys

version = "1.2.0beta1"
debug = "false"

#beta

# identify the os
if os.name == 'nt':
    # windows
    clear = 'cls'
    python = 'python'
    operatingsystem = 'Windows'
else:
    # linux/mac
    clear = 'clear'
    python = 'python3'
    operatingsystem = 'Linux/Mac'



SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IPATOOL_PATH = os.path.join(SCRIPT_DIR, 'ipatool-main', 'main.py')
SAVED_DIR = os.path.join(SCRIPT_DIR, "accounts")
GITHUB_API_URL = "https://api.github.com/repos/1Emilis1/iPATool-EZ/releases"
NEW_PAGE_URL = "https://site.com/"

os.makedirs(SAVED_DIR, exist_ok=True)

def save_account_to_file(data, filename):
    # Always save to accounts folder
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
# i forgor how this works

def handle_update_legacy():
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

#dont touch, but i will fix this once last beta is released
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
# when did i change account utility, i guess it was for the "enhanced 2fa+"
def account_utility():
    os.system(clear)
    print(f"iPATool-EZ v{version} by 1Emilis (based on iPATool-PY)")
    print("# Select account:")
    accounts = list_accounts()
    if not accounts:
        print("No accounts available.")
        return

    try:
        account_number = int(input("\nEnter account number: "))
        selected_account = accounts[account_number - 1][2]
        account_file = accounts[account_number - 1][1]
    except (ValueError, IndexError):
        print("Invalid account number.")
        return

    apple_id = selected_account["Apple ID"]
    password = selected_account["Password"]

    while True:
        os.system(clear)
        print(f"iPATool-EZ v{version} by 1Emilis (based on iPATool-PY)")
        print("\nAccount Utility for:", apple_id)
        print("1. Change Password")
        print("2. Change Country")
        print("3. Remove Account")
        print("4. Exit")

        utility_choice = input("Choose an option (1/2/3/4/5): ")

        if utility_choice == "1":
            new_password = input("Enter your new password: ")
            selected_account["Password"] = new_password
            save_account_to_file(selected_account, account_file)
            print("Password updated.")
            return  # just boom

        elif utility_choice == "2":
            # why was this so hard??
            new_country = input("Enter new country code (2 letters, e.g., US, UK): ").strip().upper()
            if len(new_country) == 2 and new_country.isalpha():
                selected_account["Country"] = new_country
                save_account_to_file(selected_account, account_file)
                print(f"Country updated to {new_country}.")
            else:
                print("Invalid country code. Please enter exactly 2 letters.")
            input("Press Enter to continue...")
            return

        elif utility_choice == "3":
            confirm = input("Are you sure you want to remove this account? (y/n): ").lower()
            if confirm == "y":
                os.remove(os.path.join(SAVED_DIR, account_file))
                print("Account removed.")
                os.execv(sys.executable, [sys.executable] + sys.argv)

        elif utility_choice == "4":
            os.execv(sys.executable, [sys.executable] + sys.argv)

        else:
            print("Invalid option. Please try again.")

def download_app():
    os.system(clear)
    print(f"iPATool-EZ v{version} by 1Emilis (based on iPATool-PY)")
    print("\n# Select account:")
    accounts = list_accounts()
    if not accounts:
        print("No accounts available.")
        return

    try:
        account_number = int(input("\nEnter account number: "))
        selected_account = accounts[account_number - 1][2]
        account_file = accounts[account_number - 1][1]
    except (ValueError, IndexError):
        print("Invalid account number.")
        return

    apple_id = selected_account["Apple ID"]
    password = selected_account["Password"]
    two_factor_enabled = selected_account["2FA Enabled"]
    os.system(clear)
    print(f"iPATool-EZ v{version} by 1Emilis (based on iPATool-PY)")
    print(f"\nSelected Apple ID: {apple_id}")
    print(f"2FA Enabled: {two_factor_enabled}")

    app_id = input("\nEnter app id: ").strip()

    # important for 2fa, yes
    if two_factor_enabled.lower() == 'yes':
        subprocess.run([python, 'ipatool-main/2fa.py', '-a', str(account_number)])
        # get updated password (2fa password)
        with open(os.path.join(SAVED_DIR, account_file)) as f:
            updated_account = json.load(f)
        password = updated_account.get("2fa_password", password)

    print(f"\nDownloading app with app id {app_id}...")
    output_dir = os.path.join(SCRIPT_DIR, 'saved', str(app_id))
    os.makedirs(output_dir, exist_ok=True)
    command = [
        python, IPATOOL_PATH, 'download',
        '-i', app_id,
        '-e', apple_id,
        '-p', password,
        '-o', output_dir
    ]
    run_command(command)

def list_accounts():
    # Always list from accounts folder
    account_files = [f for f in os.listdir(SAVED_DIR) if f.startswith('account') and f.endswith('.json')]
    account_files = sorted(account_files)
    accounts = []
    for i, file in enumerate(account_files, 1):
        with open(os.path.join(SAVED_DIR, file)) as f:
            data = json.load(f)
        print(f"{i}: {data['Apple ID']}")
        accounts.append((i, file, data))
    return accounts

def expert_download():
    os.system(clear)
    print(f"iPATool-EZ v{version} by 1Emilis (based on iPATool-PY)")
    print("\n# Select account:")
    accounts = list_accounts()
    if not accounts:
        print("No accounts available.")
        return
    try:
        account_number = int(input("\nEnter account number: "))
        selected_account = accounts[account_number - 1][2]
        account_file = accounts[account_number - 1][1]
    except (ValueError, IndexError):
        print("Invalid account number.")
        return

    apple_id = selected_account["Apple ID"]
    password = selected_account["Password"]
    two_factor_enabled = selected_account["2FA Enabled"]
    os.system(clear)
    print(f"iPATool-EZ v{version} by 1Emilis (based on iPATool-PY)")
    print(f"\nSelected Apple ID: {apple_id}")
    print(f"2FA Enabled: {two_factor_enabled}")

    app_id = input("\nEnter app id: ").strip()

    # Call downgrade plugin with -action downgrade
    downgrade_plugin_dir = os.path.join('ipatool-plugins', 'root7.1emilis.downgrade')
    main_py = os.path.join(downgrade_plugin_dir, 'main.py')
    if not (os.path.isdir(downgrade_plugin_dir) and os.path.isfile(main_py)):
        print("The downgrade plugin (root7.1emilis.downgrade) is not installed.")
        return
    if debug == "true":
        subprocess.run([python, main_py, "-action", "downgrade", "-id", app_id, "-account", str(account_number)], check=False)
    else:
        subprocess.run([python, main_py, "-action", "downgrade", "-id", app_id, "-account", str(account_number)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    
def expert_utility():
    os.system(clear)
    print(f"iPATool-EZ v{version} by 1Emilis (based on iPATool-PY)")
    print("\nExpert Utility")
    print("1. Expert Download")
    print("2. Download all app versions (requires lots of storage)")
    print("3. Get app history")
    print("4. Return to main menu.")
    choice = input("Choose an option (1/2/3/4): ")

    # check for downgrade plugin, will be replaced in beta2 
    downgrade_plugin_dir = os.path.join('ipatool-plugins', 'root7.1emilis.downgrade')
    main_py = os.path.join(downgrade_plugin_dir, 'main.py')
    downgradeall_py = os.path.join(downgrade_plugin_dir, 'downgradeall.py')
    apphistory_py = os.path.join(downgrade_plugin_dir, 'apphistory.py')
    if not (os.path.isdir(downgrade_plugin_dir) and os.path.isfile(main_py) and os.path.isfile(downgradeall_py) and os.path.isfile(apphistory_py)):
        print("The downgrade plugin (root7.1emilis.downgrade) is not installed.")
        return

    if choice == '1':
        expert_download()
    elif choice == '2':
        # Download all app versions (downgradeall)
        print("\n# Select account:")
        accounts = list_accounts()
        if not accounts:
            print("No accounts available.")
            return
        try:
            account_number = int(input("\nEnter account number: "))
            selected_account = accounts[account_number - 1][2]
            account_file = accounts[account_number - 1][1]
        except (ValueError, IndexError):
            print("Invalid account number.")
            return
        app_id = input("Enter app id: ").strip()
        if debug == "true":
            subprocess.run([python, main_py, "-action", "downgradeall", "-id", app_id, "-account", str(account_number)], check=False)
        else:
            subprocess.run([python, main_py, "-action", "downgradeall", "-id", app_id, "-account", str(account_number)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    elif choice == '3':
        # Get app history (apphistory)
        print("\n# Select account:")
        accounts = list_accounts()
        if not accounts:
            print("No accounts available.")
            return
        try:
            account_number = int(input("\nEnter account number: "))
            selected_account = accounts[account_number - 1][2]
            account_file = accounts[account_number - 1][1]
        except (ValueError, IndexError):
            print("Invalid account number.")
            return
        app_id = input("Enter app id: ").strip()
        if debug == "true":
            subprocess.run([python, main_py, "-action", "apphistory", "-account", str(account_number), "-id", app_id], check=False)
        else:
            subprocess.run([python, main_py, "-action", "apphistory", "-account", str(account_number), "-id", app_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    elif choice == '4':
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        print("Invalid option. Please try again.")
    

if __name__ == "__main__":
    os.system(clear)
    print(f"iPATool-EZ v{version} by 1Emilis (based on iPATool-PY)")
    print("Warning: Passwords are stored in plain text. Keep this script and the JSON files in a secure location.")
    print("\n1. Download an app")
    print("2. Expert Utility")
    print("3. iPA-Online")
    print("4. Create a new account")
    print("5. Account Utility")
    print("6. Check for Updates")
    choice = input("Choose an option (1/2/3/4/5/6): ")

    if choice == '1':
        download_app()
    elif choice == '2':
        expert_utility()
    elif choice == '3':
        # iPA-Online plugin, not done lil bro
        ipaonline_plugin_dir = os.path.join('ipatool-plugins', 'root7.1emilis.ipaonline')
        ipaonline_main = os.path.join(ipaonline_plugin_dir, 'main.py')
        if not (os.path.isdir(ipaonline_plugin_dir) and os.path.isfile(ipaonline_main)):
            print("The iPA-Online plugin (root7.1emilis.ipaonline) is not installed.")
        else:
            subprocess.run([python, ipaonline_main])
    elif choice == '4':
        subprocess.run([python, 'accountsetup.py'])
    elif choice == '5':
        account_utility()
    elif choice == '6':
        handle_update_legacy()

