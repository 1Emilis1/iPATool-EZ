# iPATool-EZ

## Overview
iPATool-EZ is a user-friendly tool for downloading and managing iOS application packages (IPAs), It's designed to be an easier-to-use version of iPATool-PY, providing a great experience for downloading apps from the App Store, and also for downloading delisted apps (or by other terms shadowbanned apps)

This project heavily relies on a modified version of [iPATool-PY](https://github.com/NyaMisty/ipatool-py) created by NyaMisty, credits to her.

## Features

### Current Features
- Simpler user interface
- Good Account management (supports up to 20 Apple IDs)
- 2FA support

### Planned Features
- Version Downgrading
- Additional features (suggestions welcome)
- GUI (maybe coming in iPATool-EZ 2.0.0)

## Installation

### Windows
1. Ensure Python 3+ is installed on your system
2. Download the latest iPATool-EZ version from the [Releases](https://github.com/1Emilis1/iPATool-EZ/releases)
3. Unzip the package
4. Run `install.bat` and wait for the installation to complete
5. Run `ipatool-ez.bat` to set up your Apple ID account
6. Relaunch `ipatool-ez.bat` to start using iPATool-EZ

### macOS & Linux
1. Ensure Python 3+ is installed on your system
2. Download the latest iPATool-EZ version from the [Releases](https://github.com/1Emilis1/iPATool-EZ/releases)
3. Unzip the package
4. Run `install.sh` to install the required dependencies
5. Run `ipatool-ez.sh` and select "Create account" to set up your Apple ID
6. Relaunch `ipatool-ez.sh` to start downloading IPAs

## Usage
After setting up your account, you can use iPATool-EZ to:
- Download apps from the App Store or download delisted apps using your Apple ID
- Manage multiple Apple IDs

## Important Note
If you intend to share IPA files with other people, you need to decrypt the IPAs using a jailbroken iOS device (or a non-jailbroken one if you have trollstore), IPAs downloaded with this tool come encrypted.

## Where do I find App IDs?
- You can by going to [Sensor tower](https://app.sensortower.com/) (Search for the app you want and once you find it the ID should be in the URL) (You also need to own the app, check for it in purchase history on your device)

## Troubleshooting
- if you have issues with installing the python libraries, try to install them manually by saying `py -m pip install rich requests` on Windows, or by saying `pip3 install rich requests` on macOS & Linux
- If you encounter issues with logging in, make sure your Apple ID credentials are correct
- For 2FA issues, make sure you enter the verification code correctly when prompted, if the code doesn’t pop up you can get it manually through your iPhone/iPad's settings

## Contributions
Contributions to this project are welcome, Feel free to submit issues or pull requests if you have anything to say

## License
iPATool-EZ is licensed under **AGPL-3.0**, See [`LICENSE`](LICENSE) for more details

## Disclaimer
>[!WARNING]
> This tool is for personal use only, We do not take any responsibility for any actions or consequences that may arise from downloading, or using the extracted applications, This tool is not affiliated with, endorsed by, or sponsored by Apple Inc.

Happy extracting!
