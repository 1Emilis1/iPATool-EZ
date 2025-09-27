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

# ...rest of your script...
