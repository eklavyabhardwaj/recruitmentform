import subprocess
import time
from datetime import datetime 

def run_script():
    command = ["python", "playwrighth.py"]

    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Subprocess Opportunity 2 : Started at {current_time}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            print("Script output:\n", stdout)
        else:
            print("Script failed with error:\n", stderr)
    except Exception as e:
        print(f"Subprocess encountered an error: {e}")

def main():
    while True:
        run_script()
        time.sleep(7200)  
        print("2hrs ended, Restarting the process.")

if __name__ == "__main__":
    main()
