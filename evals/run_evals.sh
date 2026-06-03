#!/bin/bash
echo "Running ADK Evals for SecureFlow..."
adk eval run --scenario-dir evals/scenarios --agent secureflow.agents.orchestrator:orchestrator
echo "Evals completed."
