"""
GitLab Helper for Demo Scenarios
================================
Provides a utility to create a branch, commit files, and create a Merge Request
using the GitLab REST API. This fulfills the requirement to execute against a live GitLab account.
"""
import os
import sys
import httpx

def create_mock_mr(title: str, branch_name: str, files_to_update: dict):
    """
    Creates a mock Merge Request on GitLab containing specific file changes.
    
    Args:
        title (str): The title of the Merge Request.
        branch_name (str): The name of the new branch to create.
        files_to_update (dict): A dictionary mapping file paths to their new string content.
    """
    token = os.environ.get("GITLAB_TOKEN")
    project_id = os.environ.get("GITLAB_PROJECT_ID")
    
    if not token or not project_id:
        print("Error: GITLAB_TOKEN and GITLAB_PROJECT_ID environment variables must be set.")
        sys.exit(1)
        
    base_url = f"https://gitlab.com/api/v4/projects/{project_id}"
    headers = {"PRIVATE-TOKEN": token}
    
    print(f"Creating branch '{branch_name}'...")
    # Attempt to create branch. Ignore 400 if it already exists.
    httpx.post(f"{base_url}/repository/branches", headers=headers, json={
        "branch": branch_name,
        "ref": "main"
    })
    
    print(f"Committing {len(files_to_update)} files...")
    final_actions = []
    for filepath, content in files_to_update.items():
        resp = httpx.get(f"{base_url}/repository/files/{filepath.replace('/', '%2F')}?ref=main", headers=headers)
        action = "update" if resp.status_code == 200 else "create"
        final_actions.append({
            "action": action,
            "file_path": filepath,
            "content": content
        })

    commit_payload = {
        "branch": branch_name,
        "commit_message": f"Demo: {title}",
        "actions": final_actions
    }
    
    commit_resp = httpx.post(f"{base_url}/repository/commits", headers=headers, json=commit_payload)
    if commit_resp.status_code not in [200, 201]:
        print(f"Failed to commit. The branch might already have these changes or an error occurred: {commit_resp.text}")
        
    print(f"Creating Merge Request '{title}'...")
    mr_payload = {
        "source_branch": branch_name,
        "target_branch": "main",
        "title": title,
        "description": "This is an automated demo MR simulating a security vulnerability for SecureFlow testing."
    }
    mr_resp = httpx.post(f"{base_url}/merge_requests", headers=headers, json=mr_payload)
    if mr_resp.status_code in [200, 201]:
        print(f"Success! MR created: {mr_resp.json().get('web_url')}")
    else:
        print(f"MR creation failed (perhaps it already exists?): {mr_resp.text}")
