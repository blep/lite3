import pytest
from lite3 import Lite3Buffer
from lite3.constants import Lite3Type # Ensure constants available if needed? No, usually hidden.

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
        
    # 7. Array Getters (on Object)
    arr = root.create_array("my_arr")
    arr.append(1)
    
    arr_ref = root.get_array("my_arr")
    assert arr_ref is not None
    assert len(arr_ref) == 1
    
    with pytest.raises(TypeError):
        root.get_object("my_arr")
        
    # 8. Null
    root["my_null"] = None
    with pytest.raises(TypeError):
        root.get_i64("my_null")
    with pytest.raises(TypeError):
        root.get_str("my_null")

def test_array_typed_accessors():
    """Test typed getters/setters on Lite3Array."""
    buf = Lite3Buffer()
    root = buf.init_obj()
    arr = root.create_array("items")
    
    # Append some typed items
    arr.append_i64(10)      # 0
    arr.append_f64(3.14)    # 1
    arr.append(3.14)        # 2
    arr.append_str("text")  # 3
    
    # Check Typed Getters (Index based)
    assert arr.get_i64(0) == 10
    
    # Float check
    # Index 1 is float
    assert arr.get_f64(1) == pytest.approx(3.14)
    assert arr.get_f64(2) == pytest.approx(3.14)
    
    # String check
    assert arr.get_str(3) == "text"
    
    # Check TypeErrors
    with pytest.raises(TypeError):
        arr.get_str(0) # It is int
        
    with pytest.raises(TypeError):
        arr.get_i64(3) # It is str
        
    # Setters (Index based)
    # Overwrite index 0 (Int) with Int
    arr.set_i64(0, 99)
    assert arr.get_i64(0) == 99
    
    # Overwrite index 0 (Int) with Str? 
    # Calling set_str(0, "new")
    arr.set_str(0, "new")
    assert arr.get_str(0) == "new"
    
    # Check typed get mismatch on new type
    with pytest.raises(TypeError):
        arr.get_i64(0)

def test_generational_safety():
    buf = Lite3Buffer()
    root = buf.init_obj()
    
    # Create a reference
    child = root.create_object("child")
    child.set_i64("data", 1)
    
    # Verify it works
    assert child.get_i64("data") == 1
    
    # Trigger split/mutation
    for i in range(100):
        root.set_i64(f"key_{i}", i)
        
    val = child.get_i64("data")
    assert val == 1
