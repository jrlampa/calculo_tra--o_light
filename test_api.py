import subprocess
import time
import requests
import os
import sys

def run_test():
    print("=== SMOKE TEST: API PROJETOS (v2) ===")
    
    app_log = "python/app.log"
    if os.path.exists(app_log):
        try:
            os.remove(app_log)
        except:
            print("Warning: Could not remove old app.log")
    
    print("Starting Uvicorn in background...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "python")
    env["GUEST_MODE"] = "true"
    env["AUTH_REQUIRE_JWT_FOR_MUTATIONS"] = "false"
    
    # Use direct uvicorn command for better reliability
    proc = subprocess.Popen(
        [os.path.abspath(".venv/Scripts/uvicorn.exe"), "api.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd="python",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    print("Waiting for Uvicorn to be ready...")
    ready = False
    start_time = time.time()
    while time.time() - start_time < 30:
        if os.path.exists(app_log):
            with open(app_log, "r") as f:
                content = f.read()
                if "application_started" in content or "Uvicorn running on" in content:
                    ready = True
                    break
        time.sleep(1)
    
    if not ready:
        print("!!! Uvicorn timed out or failed to start !!!")
        if os.path.exists(app_log):
            with open(app_log, "r") as f: print(f.read())
        proc.terminate()
        return

    print("✓ Uvicorn is READY.")
    
    print("Sending POST /api/projetos...")
    payload = {
        "nome": "Projeto Automation FINAL V2",
        "orgao": "IM3",
        "ns": "AUTO-V2",
        "endereco": "Python Script",
        "estudado_por": "Auto Tester",
        "matricula": "T2",
        "data_estudo": "23/03/2026"
    }
    
    try:
        r = requests.post(
            "http://127.0.0.1:8000/api/projetos",
            json=payload,
            headers={"X-Guest-Access": "true"},
            timeout=10
        )
        print(f"Status Code: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Request failed: {e}")
        
    time.sleep(2)
    
    if os.path.exists(app_log):
        print("\n=== BACKEND LOGS (app.log) ===")
        with open(app_log, "r") as f:
            print(f.read())

    print("Terminating Uvicorn...")
    proc.terminate()
    proc.wait()

if __name__ == "__main__":
    run_test()
