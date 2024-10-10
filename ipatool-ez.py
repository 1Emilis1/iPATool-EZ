import os
import json
import subprocess
import time
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IPATOOL_PATH = os.path.join(SCRIPT_DIR, 'ipatool-main', 'main.py')
SAVED_DIR = SCRIPT_DIR  # Store accounts in the same folder as ipatool-ez.py

# Ensure the "saved" directory exists
os.makedirs(SAVED_DIR, exist_ok=True)

# Function to save account details to a JSON file
def save_account_to_file(data, filename):
    filepath = os.path.join(SAVED_DIR, filename)
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Account saved in {filepath}.")

# Function to check if a filename exists, and create new numbered files if needed
def get_available_filename(base_name="account", max_accounts=15):
    for i in range(1, max_accounts + 1):
        filename = f"{base_name}{i}.json"
        filepath = os.path.join(SAVED_DIR, filename)
        if not os.path.exists(filepath):
            return filename
    return None

# Function to handle downloading apps and 2FA code entry
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

    app_bundle_id = input("Enter bundle id (or app id) of app: ").strip()

    # Determine if it's a bundle ID or app ID
    id_type = '-i' if app_bundle_id.isdigit() else '-b'

    # Check for temporary password
    temporary_data = selected_account.get("Temporary", {})
    temporary_password = temporary_data.get("Temporary Password")
    expiration_time = temporary_data.get("Expires At")

    if temporary_password and expiration_time:
        if datetime.now() < datetime.strptime(expiration_time, "%Y-%m-%d %H:%M:%S"):
            print("Using temporary password for download.")
        else:
            print("Temporary password has expired.")
            temporary_password = None  # Reset temporary password if expired

    # If there's no valid temporary password, fetch 2FA code
    if two_factor_enabled.lower() == 'yes' and not temporary_password:
        print("\nFetching 2FA code...")
        command = [
            'python', IPATOOL_PATH, 'download',  # Use download instead of lookup
            '-b', 'com.alexfox.camx',  # Example lookup bundle
            '-e', apple_id,
            '-p', password
        ]
        subprocess.run(command)
        time.sleep(5)

        two_factor_code = input("Enter the 2FA code: ")
        temporary_password = f"{password}{two_factor_code}"

        # Store the temporary password and expiration time in the account data
        selected_account['Temporary'] = {
            'Temporary Password': temporary_password,
            'Expires At': (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")  # Set for 24 hours
        }
        save_account_to_file(selected_account, f"account{account_number}.json")

    # Use the original password for downloading if no temporary password is available
    if not temporary_password:
        temporary_password = password

    # Now, download the app using the temporary password
    print(f"\nDownloading app with {id_type} {app_bundle_id}...")
    command = [
        'python', IPATOOL_PATH, 'download',
        id_type, app_bundle_id,
        '-e', apple_id,
        '-p', temporary_password
    ]
    subprocess.run(command)

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
    print("iPATool-EZ v1.0.0 by 1Emilis (based on iPATool-PY)")
    print("Warning: Passwords are stored in plain text. Keep this script and the JSON files in a secure location.")
    print("\n1. Download an app")
    print("2. Create a new account")
    choice = input("Choose an option (1/2): ")

    if choice == '1':
        download_app()
    elif choice == '2':
        subprocess.run(['python', 'accountsetup.py'])  # Call accountsetup.py to create a new account
