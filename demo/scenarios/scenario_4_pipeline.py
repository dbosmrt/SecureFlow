"""
Scenario 4: Pipeline Secret Leak
Creates an MR modifying .gitlab-ci.yml to echo an environment variable.
"""
from .gitlab_helper import create_mock_mr
import time

def run():
    print("Simulating Pipeline Secret Leak MR creation...")
    files = {
        ".gitlab-ci.yml": """
stages:
  - build

build-job:
  stage: build
  script:
    - echo "Building..."
    - echo $PROD_DATABASE_PASSWORD
    - echo "Done."
"""
    }
    branch_name = f"demo-pipeline-leak-{int(time.time())}"
    create_mock_mr("Debug database connection in CI", branch_name, files)

if __name__ == "__main__":
    run()
