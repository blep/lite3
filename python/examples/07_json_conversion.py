from lite3_example_common import setup_path
setup_path()
from lite3 import Lite3Buffer
import sys
import json

def main():
    ctx = Lite3Buffer()
    
    # 1. Decode JSON (Simulated)
    # Theoretically: Lite3Buffer.from_json_file("...")
    # Manual build for now to match structure
    root = ctx.init_obj()
    data = root.create_array("data")
    
    el1 = data.append_object()
    el1["name"] = "Hydrogen"
    el1["density_kg_per_m3"] = 0.08988
    
    el2 = data.append_object()
    el2["name"] = "Osmium"
    el2["density_kg_per_m3"] = 22590.0
    
    el3 = data.append_object()
    el3["name"] = "Lead"
    el3["density_kg_per_m3"] = 11342.0
    
    # 2. Find densest element logic
    densest_el = None
    max_density = -1.0
    
    # The C example uses lite3_iter_next to loop over "data"
    for el in data:
        # Check density field exists/is not null
        density = el.get("density_kg_per_m3")
        if density is not None:
             # Logic match: if (kg_per_m3 > el_densest_kg_per_m3)
             if density > max_density:
                 max_density = density
                 densest_el = el

    if densest_el:
        name = densest_el["name"]
        print(f"densest element: {name}\n")
        
        # In C: lite3_json_enc_pretty of just that element
        # Logic: Convert that specific object to JSON
        # Our API ctx.to_json_string() dumps the whole buffer (root).
        # We might want densest_el.to_json_string() ideally.
        # For now, let's just print the whole buffer as the C example printed a specific subtree.
        # If we want to support subtree printing, we need to add method to Lite3Ref.
        pass

    # 3. Print
    print("Convert Lite3 to JSON (prettified):")
    print(ctx.to_json_string(indent=4))
    
    print("Convert Lite3 to JSON (compact):")
    print(ctx.to_json_string(indent=0))

if __name__ == "__main__":
    main()
