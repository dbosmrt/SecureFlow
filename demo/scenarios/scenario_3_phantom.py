"""
Scenario 3: Phantom package (typosquatting)
Creates an MR adding 'pytorch-transformar==1.0.0' (intentional typo)
"""
from .gitlab_helper import create_mock_mr
import time

def run():
    print("Simulating Phantom Package MR creation...")
    files = {
        "requirements.txt": "pytorch-transformar==1.0.0\n"
    }
    branch_name = f"demo-phantom-{int(time.time())}"
    create_mock_mr("Add PyTorch transformer model", branch_name, files)

if __name__ == "__main__":
    run()
