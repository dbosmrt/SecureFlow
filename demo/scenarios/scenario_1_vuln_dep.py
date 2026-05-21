"""
Scenario 1: Vulnerable dependency
Creates an MR adding requests==2.6.0 (CVE-2018-18074) and Pillow==8.1.0 (CVE-2021-25287)
"""
from .gitlab_helper import create_mock_mr
import time

def run():
    print("Simulating GitLab API calls to create branch and MR with vulnerable dependencies...")
    files = {
        "requirements.txt": "requests==2.6.0\nPillow==8.1.0\n"
    }
    branch_name = f"demo-vuln-deps-{int(time.time())}"
    create_mock_mr("Add dependencies", branch_name, files)

if __name__ == "__main__":
    run()
