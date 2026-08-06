import os
import sys
import time
import requests
import asyncio
from mnemosyne.api.main import app
import uvicorn
import multiprocessing

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

def run_demo():
    print("Starting MNEMOSYNE Demo...")
    # Start server in background
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    
    try:
        # Wait for server to boot
        time.sleep(3)
        print("Uploading sample Enron email...")
        
        sample_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "samples", "enron_sample_1.txt")
        if not os.path.exists(sample_file):
            print(f"Sample file not found at {sample_file}")
            sys.exit(1)
            
        with open(sample_file, "rb") as f:
            files = {"file": (os.path.basename(sample_file), f, "text/plain")}
            response = requests.post("http://127.0.0.1:8000/api/v1/upload", files=files)
            
        print(f"Upload Response: {response.status_code} - {response.json()}")
        print("Demo complete. You can now connect the React frontend to see the graph and agent monitor.")
        print("Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nExiting demo.")
    finally:
        server_process.terminate()
        server_process.join()

if __name__ == "__main__":
    run_demo()
