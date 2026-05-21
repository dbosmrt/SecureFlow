"""
Scenario 2: Hardcoded Secret
Creates an MR adding a hardcoded AWS key.
"""
from .gitlab_helper import create_mock_mr
import time

def run():
    print("Simulating Hardcoded Secret MR creation...")
    files = {
        "config.py": "AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'\nAWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'\n"
    }
    branch_name = f"demo-secrets-{int(time.time())}"
    create_mock_mr("Update AWS configuration", branch_name, files)

if __name__ == "__main__":
    run()
