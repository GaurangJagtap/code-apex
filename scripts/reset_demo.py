#!/usr/bin/env python3
"""
Reset script for the controlled sample e-commerce application.
Restores synthetic test data and clears all sessions, orders, and carts.
"""
import sys
import httpx

SAMPLE_APP_URL = "http://127.0.0.1:5001/api/reset"

def reset_demo():
    try:
        response = httpx.post(SAMPLE_APP_URL, timeout=5.0)
        if response.status_code == 200:
            print("Successfully reset sample app state:", response.json())
            return 0
        else:
            print(f"Failed to reset demo: HTTP {response.status_code} - {response.text}")
            return 1
    except Exception as e:
        print(f"Error connecting to sample app at {SAMPLE_APP_URL}: {e}")
        print("Ensure the sample app server is running on http://127.0.0.1:5001")
        return 1

if __name__ == "__main__":
    sys.exit(reset_demo())
