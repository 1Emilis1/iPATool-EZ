import os
import json
import subprocess
import time
from datetime import datetime, timedelta
import requests
import zipfile
import shutil
import sys
import argparse
import io

# info
version = "1.2.0beta2"
rolling = 1          # 1 = Official (Rolling enabled), 0 = Fork (Disabled)
rollingversion = 0   # 1 = Recently updated/zip, 0 = Source code
BASE_URL = "https://1emilis1.github.io/ipa/ipaonline"

# arguments
parser = argparse.ArgumentParser(description="iPATool-EZ")
parser.add_argument('--force-update', action='store_true', help="Use the legacy GitHub updating system")
parser.add_argument('-debug', action='store_true', help="Show ALL console output")
args = parser.parse_args()

# fix for debug
debug = "true" if args.debug else "false"

# Logger class for debug mode
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("debug.log", "a", encoding="utf-8")
        self.log.write(f"\n--- SESSION START: {datetime.now()} ---\n")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

if args.debug:
    sys.stdout = Logger()
    sys.stderr = sys.stdout

def get_display_version(v_str):
    """Formats x.x.x.x: only displays x.x.x if y = 0 in x.x.x.y"""
    try:
        if "beta" in v_str:
            return v_str
        parts = v_str.split('.')
        if len(parts) == 4 and parts[3] == '0':
            return ".".join(parts[:3])
        return v_str
    except:
        return v_str

# Identify the OS
if os.name == 'nt':
    clear = 'cls'
    python = 'python'
    operatingsystem = 'Windows'
else:
    clear = 'clear'
    python = 'python3'
    operatingsystem = 'Linux/Mac'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IPATOOL_PATH = os.path.join(SCRIPT_DIR, 'ipatool-main', 'main.py')
SAVED_DIR = os.path.join(SCRIPT_DIR, "accounts")
GITHUB_API_URL = "https://api.github.com/repos/1Emilis1/iPATool-EZ/releases"
NEW_PAGE_URL = "https://site.com/"

os.makedirs(SAVED_DIR, exist_ok=True)

# --- New Notification & Update Logic ---
def startup_checks():
    try:
        # 1. Message.json
        m_res = requests.get(f"{BASE_URL}/message.json", timeout=3)
        if m_res.status_code == 200:
            print(f"iPATool-EZ ---------------\n{m_res.text}\n")

        # 2. Critical.json
        c_res = requests.get(f"{BASE_URL}/critical.json", timeout=3)
        if c_res.status_code == 200:
            crit_data = c_res.json()
            if version in crit_data and crit_data[version] == "required":
                print(f"!!! CRITICAL UPDATE REQUIRED FOR VERSION {get_display_version(version)} !!!")
                check_for_rolling_updates(auto_trigger=True)

    except Exception as e:
        if rolling == 0:
            if debug == "true": print(f"[DEBUG] Update server unreachable. rolling=0, skipping.")
        else:
            # fix updates
            print(f"Note: Could not check for updates (Update server unreachable).")

def check_for_rolling_updates(auto_trigger=False):
    """Fetches update.json and changelogs.json before offering a download."""
    try:
        if not auto_trigger: print("Checking for updates...")
        u_res = requests.get(f"{BASE_URL}/update.json", timeout=5)
        ch_res = requests.get(f"{BASE_URL}/changelogs.json", timeout=5)
        
        if u_res.status_code == 200:
            upd = u_res.json()
            latest_overall = upd.get("latest", "0.0.0.0")
            
            # old version logic
            branch_prefix = ".".join(version.split('.')[:2]) + ".*"
            archive_data = upd.get(branch_prefix)

            if latest_overall > version or auto_trigger:
                print(f"\nNew version available: {get_display_version(latest_overall)}")
                if ch_res.status_code == 200:
                    changelogs = ch_res.json()
                    print(f"Changelog: {changelogs.get(latest_overall, 'No notes provided.')}")
                
                print(f"\nUpdate options:")
                print(f"1. Update to Latest: {get_display_version(latest_overall)}")
                if archive_data and archive_data.get("version") > version:
                    print(f"2. Update to Latest {branch_prefix[:-2]} Stable: {get_display_version(archive_data['version'])}")
                print("3. Cancel")
                
                choice = input("Choice: ")
                if choice == "1":
                    download_update_zip(upd.get("link"))
                elif choice == "2" and archive_data:
                    download_update_zip(archive_data.get("link"))
            else:
                if not auto_trigger: print("You are on the latest version.")
                
    except Exception as e:
        print(f"Update check failed: {e}")

def download_update_zip(url=None):
    if not url: url = f"{BASE_URL}/update.zip"
    print(f"Downloading update from {url}...")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            z.extractall(SCRIPT_DIR)
        print("Update applied. Please restart.")
        sys.exit()
    except Exception as e:
        print(f"Download failed: {e}")

# legacy logic

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
    try:
        response = requests.get(GITHUB_API_URL, timeout=5)
        if response.status_code != 200:
            print("Error fetching release information from GitHub.")
            return None
        
        releases = response.json()
        latest_release = None
        latest_beta = None

        for release in releases:
            release_name = normalize_version(release['name'])

            if not release['prerelease'] and 'b' not in release_name:
                if latest_release is None or release_name > latest_release['name'].lower().replace(' ', ''):
                    latest_release = release

            elif 'b' in release_name: 
                if latest_beta is None or release_name > latest_beta['name'].lower().replace(' ', ''):
                    latest_beta = release

        return latest_release, latest_beta
    except:
        return None

def handle_update_legacy():
    latest_release, latest_beta = check_for_updates()

    if latest_release is None and latest_beta is None:
        print("Could not fetch latest releases.")
        return

    current_version = normalize_version(version)
    print(f"Current version: {version}")

    if "b" in current_version:
        if latest_beta and normalize_version(latest_beta['name']) > current_version:
            print(f"New beta version available: {latest_beta['name']}")
        else:
            print("You are already on the latest beta version.")

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

    else:
        if latest_release and normalize_version(latest_release['name']) > current_version:
            print(f"New main version available: {latest_release['name']}")
            choice = input("Do you want to update to the latest main release? (y/n): ")
            if choice.lower() == "y":
                update_script(latest_release)
            else:
                print("No update performed.")

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
                if debug == "true":
                    print(f"[DEBUG] Overwriting: {target_path}")
                os.remove(target_path)

            shutil.copyfile(source_file, target_path)

    shutil.rmtree(temp_extract_dir)
    os.remove(zip_path)
    print("Update complete. Restart the script to apply changes.")
          
def run_command(command, force_show=False):
    if debug == "true" or force_show:
        if debug == "true":
            print(f"[DEBUG] Running command: {' '.join(command)}")
        subprocess.run(command)
    else:
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def account_utility():
    os.system(clear)
    print(f"iPATool-EZ v{get_display_version(version)} by 1Emilis (based on iPATool-PY)")
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
        print(f"iPATool-EZ v{get_display_version(version)} by 1Emilis (based on iPATool-PY)")
        print("\nAccount Utility for:", apple_id)
        print("1. Change Password")
        print("2. Change Country")
        print("3. Remove Account")
        print("4. Exit")

        utility_choice = input("Choose an option (1/2/3/4): ")

        if utility_choice == "1":
            new_password = input("Enter your new password: ")
            selected_account["Password"] = new_password
            save_account_to_file(selected_account, account_file)
            print("Password updated.")
            return

        elif utility_choice == "2":
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
    print(f"iPATool-EZ v{get_display_version(version)} by 1Emilis (based on iPATool-PY)")
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
    print(f"iPATool-EZ v{get_display_version(version)} by 1Emilis (based on iPATool-PY)")
    print(f"\nSelected Apple ID: {apple_id}")
    print(f"2FA Enabled: {two_factor_enabled}")

    app_id = input("\nEnter app id: ").strip()

    if two_factor_enabled.lower() == 'yes':
        subprocess.run([python, 'ipatool-main/2fa.py', '-a', str(account_number)])
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
    print(f"iPATool-EZ v{get_display_version(version)} by 1Emilis (based on iPATool-PY)")
    print("\n# Select account:")
    accounts = list_accounts()
    if not accounts:
        print("No accounts available.")
        return
    try:
        account_number = int(input("\nEnter account number: "))
    except (ValueError, IndexError):
        print("Invalid account number.")
        return

    app_id = input("\nEnter app id: ").strip()

    downgrade_plugin_dir = os.path.join('ipatool-plugins', 'root7.1emilis.downgrade')
    main_py = os.path.join(downgrade_plugin_dir, 'main.py')
    if not (os.path.isdir(downgrade_plugin_dir) and os.path.isfile(main_py)):
        print("The downgrade plugin (root7.1emilis.downgrade) is not installed.")
        return
    
    # ADDED: pass -debug flag if active
    cmd = [python, main_py, "-action", "downgrade", "-id", app_id, "-account", str(account_number)]
    if args.debug:
        cmd.append("-debug")
    
    run_command(cmd, force_show=True)
    
def expert_utility():
    os.system(clear)
    print(f"iPATool-EZ v{version} by 1Emilis (based on iPATool-PY)")
    print("\nExpert Utility")
    print("1. Expert Download")
    print("2. Download all app versions")
    print("3. Get app history")
    print("4. Return to main menu.")
    choice = input("Choose an option (1/2/3/4): ")

    downgrade_plugin_dir = os.path.join('ipatool-plugins', 'root7.1emilis.downgrade')
    plugin_main_py = os.path.join(downgrade_plugin_dir, 'main.py')

    if not (os.path.isdir(downgrade_plugin_dir) and os.path.isfile(plugin_main_py)):
        print("The downgrade plugin (root7.1emilis.downgrade) is not installed.")
        return

    if choice in ['1', '2', '3']:
        print("\n# Select account:")
        accounts = list_accounts()
        if not accounts: return
        try:
            acc_num = int(input("\nEnter account number: "))
        except ValueError:
            print("Invalid input.")
            return
        
        app_id = input("Enter app id: ").strip()

        # Determine which action string to send to the plugin dispatcher
        action_map = {'1': 'downgrade', '2': 'downgradeall', '3': 'apphistory'}
        selected_action = action_map[choice]

        # CALLING THE PLUGIN DISPATCHER (ipatool-plugins/root7.1emilis.downgrade/main.py)
        # These flags must match the argparse in the plugin's main.py
        cmd = [
            python, plugin_main_py,
            "-id", str(app_id),
            "-account", str(acc_num),
            "-action", selected_action
        ]

        # Pass debug if it's active in the main script
        if debug == "true":
            cmd.append("-debug")
            print(f"[DEBUG] Dispatching to plugin: {' '.join(cmd)}")
            subprocess.run(cmd)
        else:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elif choice == '4':
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        print("Invalid option.")

if __name__ == "__main__":
    os.system(clear)

    if rolling == 1 and rollingversion == 0:
        print(f"iPATool-EZ v{get_display_version(version)} by 1Emilis")
        print("\n[!] NOTICE: This version was downloaded from source code.")
        print("\nIf you are a developer and you are developing a fork, please set rolling to 0 in the script.")
        repair = input("Would you like to fix this by reinstalling? (y/n): ").lower()
        if repair == 'y':
            # This uses your existing rolling download system to overwrite files
            download_update_zip()

    startup_checks()
    
    if rolling == 1 and rollingversion == 0:
        print("Note: This version was downloaded from source code.")

    print(f"iPATool-EZ v{get_display_version(version)} by 1Emilis (based on iPATool-PY)")
    print("Warning: Passwords are stored in plain text. Keep this script and the JSON files in a secure location.")
    print("\n1. Download an app")
    print("2. Expert Utility")
    print("3. Create a new account")
    print("4. Account Utility")
    print("5. Check for Updates")
    choice = input("Choose an option (1/2/3/4/5): ")

    if choice == '1':
        download_app()
    elif choice == '2':
        expert_utility()
    elif choice == '3':
        subprocess.run([python, 'accountsetup.py'])
    elif choice == '4':
        account_utility()
    elif choice == '5':
        if args.force_update:
            handle_update_legacy()
        else:
            check_for_rolling_updates()