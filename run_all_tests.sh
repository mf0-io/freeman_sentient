#!/bin/bash

# Activate virtual environment
source ./venv/bin/activate

# Run all tests with verbose output
python -m pytest tests/ -v

# Capture exit code
TEST_EXIT_CODE=$?

# Print summary
echo ""
echo "========================================"
echo "Test Execution Summary"
echo "========================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
else
    echo "❌ TESTS FAILED (Exit code: $TEST_EXIT_CODE)"
fi

exit $TEST_EXIT_CODE
