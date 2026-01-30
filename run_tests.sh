#!/bin/bash
# Run test suite for Sentient integration

# Activate virtual environment
source venv/bin/activate

# Run pytest with verbose output
python -m pytest tests/test_sentient_integration.py -v

# Exit with pytest's exit code
exit $?
