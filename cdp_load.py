import subprocess
import time
import requests
import json
import sys
from urllib.parse import urlparse


def start_chrome(target_website):
    chrome_path = r"C:\Users\Administrator\AppData\Local\ms-playwright\chromium-1161\chrome-win\chrome.exe"
    remote_debugging_port = 9222
    subprocess.Popen([chrome_path, f'--remote-debugging-port={remote_debugging_port}', target_website])


def get_debugger_url():
    url = "http://127.0.0.1:9222/json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


def find_websocket_debugger_url(debugger_info, target_domain):
    target_domain_no_port = target_domain.split(':')[0]  # Remove port if any
    for entry in debugger_info:
        parsed_url = urlparse(entry.get("url", ""))
        entry_domain_no_port = parsed_url.netloc.split(':')[0]  # Remove port if any
        if target_domain_no_port in entry_domain_no_port:
            return entry.get("webSocketDebuggerUrl")
    return None


def connect_debugger(websocket_debugger_url):
    url = "http://127.0.0.1:3000/connect"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "wsUrl": websocket_debugger_url
    }
    proxies = {
        "http": "http://127.0.0.1:8080",
        "https": "http://127.0.0.1:8080"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data), proxies=proxies)
    return response.json()


def evaluate_expression(expression):
    url = "http://127.0.0.1:3000/evaluate"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "expression": expression
    }
    proxies = {
        "http": "http://127.0.0.1:8080",
        "https": "http://127.0.0.1:8080"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data), proxies=proxies)
    return response.json()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python chrome_debugger.py <target_website>")
        sys.exit(1)

    target_website = sys.argv[1]
    target_domain = urlparse(target_website).netloc.split(':')[0]  # Remove port if any

    # Start Chrome with remote debugging
    start_chrome(target_website)

    # Wait a few seconds to ensure Chrome has started
    time.sleep(2)

    # Retrieve debugger information
    debugger_info = get_debugger_url()

    if debugger_info:
        # Find the WebSocket Debugger URL
        websocket_debugger_url = find_websocket_debugger_url(debugger_info, target_domain)
        if websocket_debugger_url:
            print(f"Found URL: {target_website}")
            print(f"WebSocket Debugger URL: {websocket_debugger_url}")

            # Connect to the WebSocket Debugger
            connect_response = connect_debugger(websocket_debugger_url)
            print(f"Connect response: {connect_response}")

            # Evaluate an expression
            expression = "console"
            evaluate_response = evaluate_expression(expression)
            print(f"Evaluation result: {evaluate_response}")
        else:
            print("Target URL not found.")
    else:
        print("Failed to retrieve debugger information.")