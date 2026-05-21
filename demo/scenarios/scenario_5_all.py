"""
Scenario 5: Combined Vulnerabilities
Creates an MR containing multiple vulnerabilities across dependencies, secrets, and pipelines.
"""
from .gitlab_helper import create_mock_mr
import time

def run():
    print("Simulating Combined Vulnerabilities MR creation...")
    files = {
        "requirements.txt": "requests==2.6.0\npytorch-transformar==1.0.0\n",
        "config.py": "AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'\n",
        ".gitlab-ci.yml": """
stages:
  - deploy
deploy-job:
  stage: deploy
  script:
    - echo $PROD_DATABASE_PASSWORD
"""
    }
    branch_name = f"demo-all-vulns-{int(time.time())}"
    create_mock_mr("Implement new feature and debugging tools", branch_name, files)

if __name__ == "__main__":
    run()
