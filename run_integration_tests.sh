#!/bin/bash
# Run integration tests for Freeman Sentient Agent

# Activate virtual environment
source venv/bin/activate

# Run integration tests with verbose output
python -m pytest tests/test_integration.py -v

# Exit with test status
exit $?
