import os


# identify the os
if os.name == 'nt':
    clear = 'cls'
    python_exec = 'python'
    operatingsystem = 'Windows'
else:
    clear = 'clear'
    python_exec = 'python3'
    operatingsystem = 'Linux/Mac'

def unavailable_feature():
    print("This feature is not available yet.")
    print("iPA-Online is expected to be released in Beta 3.")
    input("Press Enter to continue...")