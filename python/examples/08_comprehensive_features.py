from lite3_example_common import setup_path
setup_path()
from lite3 import Lite3Buffer
import sys
import os

def main():
    # Create buffer
    ctx = Lite3Buffer(initial_capacity=4096)

    # 1. Initialize Root Object (Character Profile)
    root = ctx.init_obj()

    # 2. Basic Data Types (using Pythonic __setitem__)
    root["name"] = "Sir Bytealot"
    root["level"] = 60         # inferred as i64
    root["hit_chance"] = 0.95  # inferred as f64
    root["is_pvp_enabled"] = True
    root["guild"] = None
    
    # Bytes type support
    root["portrait_raw"] = b'\xCA\xFE\xBA\xBE'

    # 3. Explicit Types (if needed)
    root.set_i64("explicit_id", 9999)

    # 4. Nested Structures
    root.create_array("active_buffs")
    root.create_object("pet_stats")

    # Large Object
    stats = root.create_object("stats")
    stats["str"] = 18
    stats["dex"] = 14
    stats["int"] = 10
    stats["vit"] = 16
    stats["wis"] = 12
    stats["cha"] = 8
    stats["agi"] = 13
    stats["luc"] = 9
    stats["end"] = 15
    stats["per"] = 11

    # 5. Arrays
    spell_book = root.create_array("spell_book")
    spell_book.append(101)
    spell_book.append(205)
    spell_book.append(303)

    # 6. Object Array (Inventory)
    inventory = root.create_array("inventory")
    
    # Item 1
    sword = inventory.append_object()
    sword["type"] = "weapon"
    sword["name"] = "Rusty Sword"
    sword["dmg"] = 5

    # Item 2
    potion = inventory.append_object()
    potion["type"] = "potion"
    potion["name"] = "Healing Potion"
    potion["heal"] = 50

    # 7. Mixed-Type Array
    save_point = root.create_array("save_point")
    save_point.append("Dark Forest")
    save_point.append(1734900000)
    
    coords = save_point.append_object()
    coords["x"] = 120
    coords["y"] = 55

    # Output
    print("--- Lite3 Comprehensive Binary Format Dump (Pythonic API) ---")
    buffer_view = ctx.memory
    print(f"Total Size: {len(buffer_view)} bytes")
    
    data = ctx.hex_dump()
    print("Buffer (hex):", end="")
    for i in range(0, len(data), 2):
        if (i // 2) % 4 == 0:
            print(" ", end="")
        print(data[i:i+2], end="")
    print()

if __name__ == "__main__":
    main()
