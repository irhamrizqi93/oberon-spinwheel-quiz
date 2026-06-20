#!/usr/bin/env python3
"""Tunnel watchdog: auto-restart SSH tunnel, update backend URL config."""
import subprocess, json, time, re, sys, os
from pathlib import Path

REPO = Path("/home/iruhamu/quiz-oberon")
CONFIG_FILE = REPO / "backend.json"
LOCAL_PORT = 8765

def start_tunnel():
    """Start serveo tunnel, return public URL or None."""
    proc = subprocess.Popen(
        ["ssh", "-o", "StrictHostKeyChecking=no",
         "-o", "ServerAliveInterval=30",
         "-o", "ServerAliveCountMax=3",
         "-o", "ExitOnForwardFailure=yes",
         "-R", f"80:localhost:{LOCAL_PORT}", "serveo.net"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    
    url = None
    start = time.time()
    # Baca output sampai dapat URL atau timeout 15 detik
    while time.time() - start < 15:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        # Cari URL serveo: https://xxxx.serveo.net atau serveousercontent.com
        m = re.search(r'(https://[a-zA-Z0-9.-]+\.(?:serveo\.net|serveousercontent\.com))', line)
        if m:
            url = m.group(1)
            break
    
    if not url:
        proc.kill()
        return None, None
    
    return proc, url

def update_config(url):
    """Update backend.json and push to GitHub."""
    config = {"backend_url": url, "updated": time.strftime("%Y-%m-%d %H:%M:%S WIB")}
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False))
    
    # Push to GitHub
    subprocess.run(["git", "-C", str(REPO), "add", "backend.json"], 
                   capture_output=True)
    subprocess.run(["git", "-C", str(REPO), "commit", "-m", 
                    f"auto: update tunnel URL → {url}"], 
                   capture_output=True)
    subprocess.run(["git", "-C", str(REPO), "push"], 
                   capture_output=True)
    print(f"[watchdog] Updated config: {url}")

def main():
    print("[watchdog] Starting tunnel watchdog...")
    
    while True:
        proc, url = start_tunnel()
        if not proc:
            print("[watchdog] Failed to start tunnel, retry in 10s...")
            time.sleep(10)
            continue
        
        print(f"[watchdog] Tunnel active: {url}")
        update_config(url)
        
        # Monitor tunnel
        while True:
            ret = proc.poll()
            if ret is not None:
                print(f"[watchdog] Tunnel died (exit={ret}), restarting in 5s...")
                break
            time.sleep(5)
        
        time.sleep(5)

if __name__ == "__main__":
    # Pastikan repo clean dulu
    subprocess.run(["git", "-C", str(REPO), "pull"], capture_output=True)
    main()
