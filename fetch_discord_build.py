#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime
from pathlib import Path

API_URL = "https://discord.sale/api/builds?page=1&limit=1&sort_by=build_date&sort_direction=desc"
BUILD_FILE = Path(__file__).parent / "build.json"
TIMEOUT = 30
MAX_RETRIES = 3

def fetch_build_number(retries=MAX_RETRIES):
    """Fetch the latest Discord build number with retry logic"""
    for attempt in range(1, retries + 1):
        try:
            print(f"[Attempt {attempt}/{retries}] Fetching Discord build number from {API_URL}")
            response = requests.get(API_URL, timeout=TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list) and len(data) > 0:
                build_data = data[0]
            elif isinstance(data, dict):
                build_data = data
            else:
                raise ValueError(f"Unexpected response format: {type(data)}")
            
            build_number = build_data.get("build_number")
            
            if build_number is None:
                raise ValueError("No 'build_number' field in response")
            
            print(f"✓ Successfully fetched build number: {build_number}")
            return build_number
            
        except requests.Timeout:
            print(f"✗ Timeout on attempt {attempt}/{retries}")
            if attempt < retries:
                continue
            else:
                raise
        except requests.RequestException as e:
            print(f"✗ Request error on attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                continue
            else:
                raise
        except (json.JSONDecodeError, ValueError) as e:
            print(f"✗ Parse error on attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                continue
            else:
                raise
    
    return None

def update_build_file(build_number):
    """Update the build.json file with the new build number"""
    try:
        # Read existing data if file exists
        if BUILD_FILE.exists():
            with open(BUILD_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {"build_number": None, "history": []}
        
        # Get old build number for history
        old_build = data.get("build_number")
        
        # Update build number
        data["build_number"] = build_number
        
        # Add to history
        if "history" not in data:
            data["history"] = []
        
        history_entry = {
            "build_number": build_number,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "updated": True if old_build != build_number else False
        }
        
        data["history"].append(history_entry)
        
        # Keep only last 100 entries
        if len(data["history"]) > 100:
            data["history"] = data["history"][-100:]
        
        # Write to file
        with open(BUILD_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Updated build.json")
        if old_build != build_number:
            print(f"  Build changed: {old_build} → {build_number}")
        else:
            print(f"  No change: {build_number}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to update build.json: {e}")
        return False

def main():
    """Main execution"""
    print("=" * 60)
    print("Discord Build Number Fetcher")
    print("=" * 60)
    print(f"Time: {datetime.utcnow().isoformat()}Z")
    print()
    
    try:
        build_number = fetch_build_number()
        if build_number is None:
            print("✗ Failed to fetch build number after all retries")
            sys.exit(1)
        
        if update_build_file(build_number):
            print()
            print("✓ Success!")
            sys.exit(0)
        else:
            print()
            print("✗ Failed to update file")
            sys.exit(1)
            
    except Exception as e:
        print()
        print(f"✗ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
