import subprocess
import sys
from keep_alive import keep_alive

if __name__ == "__main__":
    print("Starting Keep-Alive server...")
    keep_alive()
    
    print("Launching Bot 1 and Bot 2...")
    p1 = subprocess.Popen([sys.executable, "bot1.py"])
    p2 = subprocess.Popen([sys.executable, "bot2.py"])
    
    p1.wait()
    p2.wait()