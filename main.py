import subprocess
import sys
import time
from keep_alive import keep_alive

if __name__ == "__main__":
    print("Starting Keep-Alive server...")
    keep_alive()
    
    print("Launching Bot 1...")
    p1 = subprocess.Popen([sys.executable, "bot1.py"])
    
    # Wait 5 seconds so Discord doesn't hit you with a 429 rate limit
    print("Waiting 5 seconds before launching Bot 2...")
    time.sleep(5)
    
    print("Launching Bot 2...")
    p2 = subprocess.Popen([sys.executable, "bot2.py"])
    
    p1.wait()
    p2.wait()