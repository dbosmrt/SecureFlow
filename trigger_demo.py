import httpx

API_URL = "http://127.0.0.1:8000"

def trigger_demo():
    print("Triggering SecureFlow AI Agents...")
    print("Sending mock GitLab Merge Request event to the Webhook endpoint...\n")

    payload = {
        "object_kind": "merge_request",
        "project": {
            "id": 12345,
            "name": "payment-service"
        },
        "object_attributes": {
            "id": 99,
            "iid": 42,
            "title": "Update dependencies and add new API key",
            "state": "opened",
            "source_branch": "feature/update-deps",
            "target_branch": "main"
        }
    }

    try:
        response = httpx.post(
            f"{API_URL}/webhook/gitlab",
            json=payload,
            headers={"X-Gitlab-Token": "mock-secret"}
        )
        if response.status_code == 200:
            print(" Webhook accepted successfully!")
            print(" The Orchestrator Agent is now running in the background.")
            print("  It is spinning up 4 parallel scanners to analyze the code.")
            print("\nGo to your React Dashboard at http://localhost:5173")
            print(" Wait about 30-40 seconds, and you will see the findings and HITL approval requests appear live!")
        else:
            print(f" Failed to trigger webhook: {response.status_code} - {response.text}")
    except Exception as e:
        print(f" Error connecting to API: {e}")
        print("Make sure your FastAPI server is running on port 8000.")

if __name__ == "__main__":
    trigger_demo()
