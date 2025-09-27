
import argparse
import json
import os
import subprocess

# identify the os
if os.name == 'nt':
    # windows
    clear = 'cls'
    python_exec = 'python'
    operatingsystem = 'Windows'
else:
    # linux/mac
    clear = 'clear'
    python_exec = 'python3'
    operatingsystem = 'Linux/Mac'

# ignore
parser = argparse.ArgumentParser(description="its ipatool-ez downgrade stuff")


# arguments, dont ignore if you want to add smth
parser.add_argument("-id", type=int, required=True, help="app ID")
parser.add_argument("-account", type=int, required=True, help="account number")
parser.add_argument("-action", choices=["apphistory", "downgrade", "downgradeall"], required=True, help="Action to perform")

# dont touch
args = parser.parse_args()


appid = args.id
account = args.account
action = args.action



script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.abspath(os.path.join(script_dir, '../../accounts', f'account{account}.json'))
twofa_path = os.path.abspath(os.path.join(script_dir, '../../ipatool-main/2fa.py'))
ipatoolmain_path = os.path.join("..", "..", "ipatool-main", "main.py")
apphistory_path = os.path.join(os.path.dirname(__file__), "apphistory.py")
downgradeall_path = os.path.join(os.path.dirname(__file__), "downgradeall.py")
downgrade_path = os.path.join(os.path.dirname(__file__), "downgrade.py")

# Load JSON
with open(json_path, "r", encoding="utf-8") as f:
    account_data = json.load(f)

apple_id = account_data.get("Apple ID")
password = account_data.get("Password")
two_fa = account_data.get("2FA Enabled")
country = account_data.get("App Store Country")


# Use python_exec for all subprocess calls - this is important for linux and mac users
# ALWAYS and i mean ALWAYS run 2fa.py first to ensure 2fa_password is set
subprocess.run([python_exec, twofa_path, "-a", str(account)])

# im deleting this if this breaks something cuz idk what this does, i forgor
with open(json_path, "r", encoding="utf-8") as f:
    account_data = json.load(f)

apple_id = account_data.get("Apple ID")
password = account_data.get("Password")
two_fa = account_data.get("2FA Enabled")
country = account_data.get("App Store Country")
twofa_password = account_data.get("2fa_password", password)

# Debug output control
debug = os.environ.get("IPATOOL_DEBUG", "false").lower() == "true"

if action == "apphistory":
    cmd = [
        python_exec, apphistory_path,
        "--appid", str(appid),
        "--country", str(country),
        "--email", str(apple_id),
        "--password", str(twofa_password)
    ]
    if debug:
        result = subprocess.run(cmd)
    else:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        print("apphistory.py failed.")
        exit(result.returncode)
    exit(0)
elif action == "downgradeall":
    cmd = [
        python_exec, downgradeall_path,
        "--appid", str(appid),
        "--country", str(country),
        "--email", str(apple_id),
        "--password", str(twofa_password)
    ]
    if debug:
        result = subprocess.run(cmd)
    else:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        print("downgradeall.py failed.")
        exit(result.returncode)
    exit(0)
elif action == "downgrade":
    cmd = [
        python_exec, downgrade_path,
        "--appid", str(appid),
        "--country", str(country),
        "--email", str(apple_id),
        "--password", str(twofa_password)
    ]
    # Always run downgrade.py interactively so user can select version
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("downgrade.py failed.")
        exit(result.returncode)
    exit(0)
# the error model from gmod
