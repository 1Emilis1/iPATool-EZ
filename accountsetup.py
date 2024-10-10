import os
import json

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

def account_setup():
    # Prompt for Apple ID
    apple_id = input("Enter your Apple ID: ")
    
    # Prompt for Password
    password = input("Enter your Password: ")

    # Prompt for 2FA
    two_factor = input("Do you have Two-Factor Authentication enabled? (yes/no): ").strip().lower()

    # Validation for 2FA input
    if two_factor not in ['yes', 'no']:
        print("Invalid input. Please answer with 'yes' or 'no'.")
        return account_setup()

    # Prompt for App Store Country
    app_store_country = input("What is the App Store country (ex. US, UK): ").strip().upper()

    # Prepare account data
    account_data = {
        "Apple ID": apple_id,
        "Password": password,  # Password stored in plain text
        "2FA Enabled": two_factor.capitalize(),
        "App Store Country": app_store_country
    }

    # Check for an available filename
    filename = get_available_filename()

    if filename:
        save_account_to_file(account_data, filename)
    else:
        print("Account limit reached. You can only save up to 15 accounts.")

if __name__ == "__main__":
    account_setup()
