import pytest
from lite3 import Lite3Buffer

def test_strict_typed_getters():
    buf = Lite3Buffer()
    root = buf.init_obj()
    
    # 1. Integer
    root.set_i64("my_int", 42)
    assert root["my_int"] == 42
    assert root.get_i64("my_int") == 42
    with pytest.raises(TypeError):
        root.get_f64("my_int")
    with pytest.raises(TypeError):
        root.get_str("my_int")
        
    # 2. Float
    root.set_f64("my_float", 3.14)
    # Using approx for float comparison
    assert root["my_float"] == pytest.approx(3.14)
    assert root.get_f64("my_float") == pytest.approx(3.14)
    with pytest.raises(TypeError):
        root.get_i64("my_float")
        
    # 3. String
    root.set_str("my_str", "hello")
    assert root["my_str"] == "hello"
    assert root.get_str("my_str") == "hello"
    with pytest.raises(TypeError):
        root.get_i64("my_str")
        
    # 4. Bool
    root.set_bool("my_bool", True)
    assert root["my_bool"] is True
    assert root.get_bool("my_bool") is True
    with pytest.raises(TypeError):
        root.get_i64("my_bool")
        
    # 5. Object
    nested = root.create_object("my_obj")
    nested.set_i64("val", 123)
    
    obj_ref = root.get_object("my_obj")
    assert obj_ref is not None
    assert obj_ref.get_i64("val") == 123
    
    with pytest.raises(TypeError):
        root.get_i64("my_obj")

    # 6. Bytes
    root.set_bytes("my_bytes", b'\xCA\xFE\xBA\xBE')
    assert root.get_bytes("my_bytes") == b'\xCA\xFE\xBA\xBE'
    with pytest.raises(TypeError):
        root.get_str("my_bytes")
        
    # 7. Array
    arr = root.create_array("my_arr")
    arr.append(1)
    
    arr_ref = root.get_array("my_arr")
    assert arr_ref is not None
    assert len(arr_ref) == 1
    
    with pytest.raises(TypeError):
        root.get_object("my_arr")
        
    # 8. Null
    root["my_null"] = None
    # Null is its own type (0). Typed getters should expect their specific type (2, 5, etc)
    # So getting i64 from Null raises TypeError
    with pytest.raises(TypeError):
        root.get_i64("my_null")
    with pytest.raises(TypeError):
        root.get_str("my_null")

    # Matrix Checks (Sample Cross-Type Validation)
    # Bool vs Int
    with pytest.raises(TypeError): root.get_i64("my_bool")
    # Int vs Bool
    with pytest.raises(TypeError): root.get_bool("my_int")
    # Obj vs Array
    with pytest.raises(TypeError): root.get_array("my_obj")
    # Array vs Obj
    with pytest.raises(TypeError): root.get_object("my_arr")
    # Bytes vs Str
    with pytest.raises(TypeError): root.get_str("my_bytes")
    # Str vs Bytes
    with pytest.raises(TypeError): root.get_bytes("my_str")

def test_generational_safety():
    buf = Lite3Buffer()
    root = buf.init_obj()
    
    # Create a reference
    child = root.create_object("child")
    child.set_i64("data", 1)
    
    # Verify it works
    assert child.get_i64("data") == 1
    
    # Trigger split/mutation that increments generation
    # We need to fill the root node until it splits.
    # Assuming MAX_KEYS is relatively small (e.g. < 20).
    for i in range(100):
        root.set_i64(f"key_{i}", i)
        
    # Now buffer generation should have increased due to splits.
    # Ideally, we want references to remain valid if the underlying logic allows it.
    # Since we removed the generation check (as references to Nodes/Values are stable in append-only-ish file),
    # the reference should STILL work.
    
    val = child.get_i64("data")
    assert val == 1

    # Create NEW reference, should also work
    child_new = root.get_object("child")
    assert child_new.get_i64("data") == 1
