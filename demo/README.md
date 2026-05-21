# SecureFlow Demo Scenarios

These scripts simulate real-world GitLab Merge Requests containing various security vulnerabilities to trigger the SecureFlow agent.

## Usage
Ensure you have `GITLAB_TOKEN` and `GITLAB_PROJECT_ID` set in your `.env` file or exported.

```bash
./trigger_scenario.sh scenario_1_vuln_dep
```

## Scenarios
1. `scenario_1_vuln_dep`: Tests OSV lookup by adding `requests==2.6.0`
2. `scenario_2_secret`: Tests regex scanning by adding a mock AWS Key
3. `scenario_3_phantom`: Tests PyPI checking by adding a non-existent package
4. `scenario_4_pipeline`: Tests CI log auditing by echoing an env var in `.gitlab-ci.yml`
5. `scenario_5_all`: Combines all 4 for a stress test
