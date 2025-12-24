import pytest
import subprocess
import os
import sys
import re

# Paths
EXAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples'))
BUFFER_API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'buffer_api'))

def run_example(script_name):
    """Runs a python example script and returns stdout."""
    script_path = os.path.join(EXAMPLES_DIR, script_name)
    # Ensure current python env is used
    result = subprocess.run(
        [sys.executable, script_path], 
        capture_output=True, 
        text=True
    )
    if result.returncode != 0:
        pytest.fail(f"Script {script_name} failed:\n{result.stderr}")
    return result.stdout

def get_buffer_hex_dumps(output_text):
    """Extracts all 'Buffer (hex): ...' lines from output."""
    return re.findall(r"Buffer \(hex\):\s*([0-9a-fA-F ]+)", output_text)

def read_reference_output(filename):
    """Reads reference output, handling potential encodings."""
    path = os.path.join(BUFFER_API_DIR, filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(path, 'r', encoding='utf-16') as f:
                return f.read()
        except Exception as e:
            pytest.fail(f"Could not read reference file {filename}: {e}")

@pytest.mark.skip(reason="Lite3Buffer not fully implemented yet")
def test_01_building_messages_match():
    # 1. Run Python example
    py_output = run_example("01_building_messages.py")
    py_hexes = get_buffer_hex_dumps(py_output)
    
    # 2. Read Reference
    ref_output = read_reference_output("01-building-messages-output.txt")
    ref_hexes = get_buffer_hex_dumps(ref_output)
    
    # 3. Compare
    assert len(py_hexes) == len(ref_hexes), "Mismatch in number of buffer dumps"
    
    for i, (py_hex, ref_hex) in enumerate(zip(py_hexes, ref_hexes)):
        # Normalize (remove spaces)
        py_clean = py_hex.replace(" ", "").lower()
        ref_clean = ref_hex.replace(" ", "").lower()
        assert py_clean == ref_clean, f"Buffer mismatch at dump #{i+1}"

@pytest.mark.skip(reason="Lite3Buffer not fully implemented yet")
def test_08_comprehensive_match():
    # 1. Run Python example
    py_output = run_example("08_comprehensive_features.py")
    py_hexes = get_buffer_hex_dumps(py_output)
    
    # 2. Read Reference
    ref_output = read_reference_output("08-comprehensive-features-output.txt")
    ref_hexes = get_buffer_hex_dumps(ref_output)
    
    # 3. Compare
    assert len(py_hexes) == len(ref_hexes), "Mismatch in number of buffer dumps"
    
    for i, (py_hex, ref_hex) in enumerate(zip(py_hexes, ref_hexes)):
        py_clean = py_hex.replace(" ", "").lower()
        ref_clean = ref_hex.replace(" ", "").lower()
        assert py_clean == ref_clean, f"Buffer mismatch at dump #{i+1}"

def test_examples_run_smoke():
    """Ensure all examples run without crashing (even if output is wrong/stubbed)."""
    scripts = [
        "01_building_messages.py",
        "02_reading_messages.py",
        "03_strings.py",
        "04_nesting.py",
        "05_arrays.py", 
        "06_iterators.py",
        "07_json_conversion.py",
        "08_comprehensive_features.py"
    ]
    for script in scripts:
        print(f"Running {script}...")
        run_example(script)
