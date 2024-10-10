import os
import json
import subprocess
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IPATOOL_PATH = os.path.join(SCRIPT_DIR, 'ipatool-main', 'main.py')

# Function to save account details to a JSON file
def save_account_to_file(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Account saved in {filename}.")

# Function to check if a filename exists, and create new numbered files if needed
def get_available_filename(base_name="account", max_accounts=15):
    for i in range(1, max_accounts + 1):
        filename = f"{base_name}{i}.json"
        if not os.path.exists(filename):
            return filename
    return None

# Account Setup Function
def account_setup():
    apple_id = input("Enter your Apple ID: ")
    password = input("Enter your Password: ")
    two_factor = input("Do you have Two-Factor Authentication enabled? (yes/no): ").strip().lower()
    if two_factor not in ['yes', 'no']:
        print("Invalid input. Please answer with 'yes' or 'no'.")
        return account_setup()

    app_store_country = input("What is the App Store country (ex. US, UK): ").strip().upper()

    account_data = {
        "Apple ID": apple_id,
        "Password": password,
        "2FA Enabled": two_factor.capitalize(),
        "App Store Country": app_store_country
    }

    filename = get_available_filename()

    if filename:
        save_account_to_file(account_data, filename)
    else:
        print("Account limit reached. You can only save up to 15 accounts.")

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
    app_store_country = selected_account["App Store Country"]
    two_factor_enabled = selected_account["2FA Enabled"]

    print(f"\nSelected Apple ID: {apple_id}")
    print(f"2FA Enabled: {two_factor_enabled}")

    app_bundle_id = input("Enter bundle id (or app id) of app: ").strip()

    # Determine if it's a bundle ID or app ID
    if app_bundle_id.isdigit():
        id_type = '-i'
    else:
        id_type = '-b'

    # First, get the 2FA code using lookup
    if two_factor_enabled.lower() == 'yes':
        print("\nFetching 2FA code... (ignore anything)")
        command = [
            'python', IPATOOL_PATH, 'lookup',
            '-b', 'com.alexfox.camx',  # i want to thank this dev for making a good app
            '-c', app_store_country,
            'download', '-e', apple_id, '-p', password
        ]
        subprocess.run(command)
        print("Please wait, getting 2FA code...")
        time.sleep(1)

        two_factor_code = input("Enter the 2FA code: ")
        temporary_password = f"{password}{two_factor_code}"
    else:
        temporary_password = password

    print(f"\nDownloading app with {id_type} {app_bundle_id}...")
    command = [
        'python', IPATOOL_PATH, 'lookup',
        id_type, app_bundle_id,
        '-c', app_store_country,
        'download', '-e', apple_id, '-p', temporary_password
    ]
    subprocess.run(command)

def list_accounts():
    account_files = [f for f in os.listdir(SCRIPT_DIR) if f.startswith('account') and f.endswith('.json')]
    account_files = sorted(account_files)
    accounts = []
    for i, file in enumerate(account_files, 1):
        with open(os.path.join(SCRIPT_DIR, file)) as f:
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
        account_setup()
