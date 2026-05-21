#!/bin/bash
if [ -z "$1" ]; then
    echo "Usage: ./trigger_scenario.sh <scenario_name>"
    exit 1
fi
echo "Triggering $1..."
python "demo/scenarios/$1.py"
