import subprocess
import sys
import os

def install_requirements():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def start_server():
    os.system("uvicorn main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    print("Installing requirements...")
    install_requirements()
    print("Starting FastAPI server...")
    start_server()
