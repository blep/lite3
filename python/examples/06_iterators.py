from lite3_example_common import setup_path
setup_path()
from lite3 import Lite3Buffer
import sys

def main():
    ctx = Lite3Buffer()
    
    names = ["Boris", "John", "Olivia", "Tanya", "Paul", "Sarah"]
    
    # Build array
    root = ctx.init_arr()
    for i, name in enumerate(names):
        obj = root.append_object()
        obj["id"] = i
        obj["vip_member"] = False
        obj["benefits"] = None
        obj["name"] = name
        
    print(ctx.to_json_string())
    
    # Iterate over array objects
    # This matches the C logic: iterating processing elements
    print("\nIterating over array elements:")
    for obj in root:
        # Note: In C example, it reads props manually
        # id = lite3_get_i64(..., "id")
        user_id = obj.get("id")
        name = obj.get("name")
        vip = obj.get("vip_member")
        benefits = obj.get("benefits")
        
        has_benefits = benefits is not None
        
        print(f"id: {user_id}\tname: {name}\tvip_member: {'true' if vip else 'false'}\tbenefits: {'yes' if has_benefits else 'no'}")

    # Iterate over object key-value pairs
    # In C example, it takes the last object from the previous loop iteration (val_ofs)
    # We will grab the last object explicitly
    if len(root) > 0:
        last_obj = root[len(root) - 1]
        print("\nObject keys (last element):")
        for key, val in last_obj.items():
            # Mimic C switch-case printing
            val_str = "null"
            if val is None:
                val_str = "null" 
            elif isinstance(val, bool):
                val_str = "true" if val else "false"
            else:
                val_str = str(val)
                
            print(f"key: {key}\tvalue: {val_str}")

if __name__ == "__main__":
    main()
