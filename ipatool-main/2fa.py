import subprocess
import json
import os
import argparse
import time

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


IPATOOL_PATH = "main.py"

apple_id = None
password = None
tmp_password = None
code = 0

activated = 0

parser = argparse.ArgumentParser()

parser.add_argument('-a', type=int, help='Account')

argparse = parser.parse_args()

accountjson = None # do not remove


def find_account():
    global accountjson
    if argparse.a is not None:
        # i think if it runs from ipatool-main it will need to run up one folder
        candidate = f"accounts/account{argparse.a}.json"
        if os.path.exists(candidate):
            accountjson = candidate
        else:
            # idfk what im doing here, lets hope it just works
            candidate_parent = os.path.join("..", "accounts", f"account{argparse.a}.json")
            if os.path.exists(candidate_parent):
                accountjson = candidate_parent
            else:
                print(f"Account file not found: {candidate} or {candidate_parent}")
                accountjson = None
    account_info()

def account_info():
    global apple_id, password  # add global
    if accountjson is None:
        print("No account specified.")
        return
    try:
        with open(accountjson, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Account file not found: {accountjson}")
        return
    apple_id = data.get("Apple ID")
    password = data.get("Password")
    security_enabled = data.get("2FA Enabled")
    twofa_password = data.get("2fa_password")
    if security_enabled == "No":
        print("Account does not have 2FA enabled. Please do not run this script.")
    else:
        check_2fa(twofa_password)

def activate_2fa():
    global tmp_password
    time.sleep(3)
    os.system(clear)
    code = input("Enter the 2FA code that you received: ")
    tmp_password = password + code
    commandtmp = [
        python, IPATOOL_PATH, 'download',
        '-i', '0',
        '-e', apple_id,
        '-p', tmp_password
    ]
    result = subprocess.run(commandtmp, capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    if "license not found" in output.lower():
        print("2FA activation failed. Please try again.")
        activate_2fa()
    else:
        print("2FA activated successfully.")
        # Save the 2FA password to the account JSON
        if accountjson:
            try:
                with open(accountjson, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['2fa_password'] = tmp_password
                with open(accountjson, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Failed to save 2FA password: {e}")
        return

def check_2fa(twofa_password=None):
    os.system(clear)
    # Try 2fa_password if available, else use normal password
    tried_2fa = False
    if twofa_password:
        command = [
            python, IPATOOL_PATH, 'download',
            '-i', '0',
            '-e', apple_id,
            '-p', twofa_password
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        output = (result.stdout or "") + (result.stderr or "")
        if "license not found" not in output.lower():
            print("2FA is already active. 2FA code is not needed.")
            return
        else:
            tried_2fa = True
    # If no 2fa_password or it failed, try normal password and activate if needed
    command = [
        python, IPATOOL_PATH, 'download',
        '-i', '0',
        '-e', apple_id,
        '-p', password
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    if "license not found" in output.lower():
        print("2FA is already active. 2FA code is not needed.")
        return
    else:
        if tried_2fa:
            print("Saved 2FA password did not work. Please enter a new 2FA code.")
        activate_2fa()

# should work
find_account()

#final words, i think it actually works now
