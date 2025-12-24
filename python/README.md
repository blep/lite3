# Lite3 Python Package

This directory contains the Python implementation of the Lite3 binary data format.

## Structure

*   `lite3/`: The source code for the `lite3` python package.
*   `examples/`: Python ports of the C examples found in `../examples/buffer_api/`.
*   `tests/`: Pytest suite for validating the implementation.

## Setup

Before running tests or examples, you must set the `PYTHONPATH` so that the `lite3` package is visible.

**Windows:**
Run the provided batch script:
```cmd
set_python_path.bat
```

**Linux/Mac:**
```bash
export PYTHONPATH=$(pwd)
```

## Running Tests

We use `pytest` for testing.

1.  Set up the path (see above).
2.  Run pytest:
    ```cmd
    python -m pytest
    ```

To run a specific test file:
```cmd
python -m pytest tests/test_binary_data_build.py
```

## Running Examples

1.  Set up the path (see above).
2.  Run an example script:
    ```cmd
    python examples/01_building_messages.py
    ```
