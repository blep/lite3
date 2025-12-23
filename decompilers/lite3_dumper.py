
import struct
import sys
import json

def dump_node(data, node_offset, f_out, indent_level=0):
    if indent_level > 50:
        f_out.write(f"{'  ' * indent_level}Error: Max recursion depth exceeded at offset {node_offset}\n")
        return
    indent = "  " * indent_level
    NODE_SIZE = 96
    
    if node_offset + NODE_SIZE > len(data):
        f_out.write(f"{indent}Error: Offset {node_offset} out of bounds (Data Len: {len(data)})\n")
        return

    try:
        node_bytes = data[node_offset:node_offset+NODE_SIZE]
        ints = struct.unpack(f"<{24}I", node_bytes)
        
        gen_type = ints[0]
        hashes = ints[1:8]
        size_kc = ints[8]
        kv_ofs = ints[9:16]
        child_ofs = ints[16:24]
        
        gen = gen_type >> 8
        type_tag = gen_type & 0xFF
        
        # size_kc: upper 26 bits size, lower 6 bits (technically 3 used) key_count
        size_val = size_kc >> 6
        key_count = size_kc & 0x07
        
        node_type_str = 'Object' if type_tag==6 else 'Array' if type_tag==7 else f'Unknown({type_tag})'
        
        f_out.write(f"{indent}## Node at Offset {node_offset} (0x{node_offset:x})\n")
        f_out.write(f"{indent}- **GenType**: 0x{gen_type:08x} (Gen: {gen}, Type: {node_type_str})\n")
        f_out.write(f"{indent}- **KeyCount**: {key_count}\n")
        f_out.write(f"{indent}- **Total Size**: {size_val}\n")
        f_out.write(f"{indent}- **Hashes**: {[hex(h) for h in hashes]}\n")
        f_out.write(f"{indent}- **KvOfs**: {list(kv_ofs)}\n")
        f_out.write(f"{indent}- **ChildOfs**: {list(child_ofs)}\n")
        f_out.write("\n")

        # Parse Entries (Local to this node)
        sorted_kv_ofs = sorted([(ofs, i) for i, ofs in enumerate(kv_ofs) if ofs != 0])
        
        for ofs, idx in sorted_kv_ofs:
            f_out.write(f"{indent}### Entry {idx} (idx in node) at offset {ofs} (0x{ofs:x})\n")
            
            # Parse Key
            b0 = data[ofs]
            tag_len = (b0 & 0x03) + 1
            key_tag_val = int.from_bytes(data[ofs:ofs+tag_len], 'little')
            key_len = key_tag_val >> 2
            
            key_start = ofs + tag_len
            key_bytes = data[key_start:key_start+key_len]
            key_str = key_bytes[:-1].decode('utf-8', errors='replace') # remove null
            
            f_out.write(f"{indent}- **Key**: \"{key_str}\" (Offset: {ofs})\n")
            
            # Parse Value
            val_start = key_start + key_len
            val_type = data[val_start]
            val_start_payload = val_start + 1
            
            f_out.write(f"{indent}- **Value Type**: 0x{val_type:02x} (Offset: {val_start})\n")
            
            if val_type == 0x01: # BOOL
                val = data[val_start_payload]
                f_out.write(f"{indent}  - Value: {'true' if val else 'false'}\n")
            elif val_type == 0x02: # I64
                val = struct.unpack("<q", data[val_start_payload:val_start_payload+8])[0]
                f_out.write(f"{indent}  - Value: {val}\n")
            elif val_type == 0x03: # F64
                val = struct.unpack("<d", data[val_start_payload:val_start_payload+8])[0]
                f_out.write(f"{indent}  - Value: {val}\n")
            elif val_type == 0x04: # BYTES
                length = struct.unpack("<I", data[val_start_payload:val_start_payload+4])[0]
                p_start = val_start_payload + 4
                f_out.write(f"{indent}  - Length: {length}\n")
                f_out.write(f"{indent}  - Content: {data[p_start:p_start+length].hex()}\n")
            elif val_type == 0x05: # STRING
                length = struct.unpack("<I", data[val_start_payload:val_start_payload+4])[0]
                p_start = val_start_payload + 4
                s_bytes = data[p_start:p_start+length]
                s_val = s_bytes[:-1].decode('utf-8', errors='replace') if len(s_bytes)>0 else ""
                f_out.write(f"{indent}  - Length: {length}\n")
                f_out.write(f"{indent}  - String: \"{s_val}\"\n")
            elif val_type == 0x06 or val_type == 0x07: # NESTED OBJECT/ARRAY
                 nested_ofs = struct.unpack("<I", data[val_start_payload:val_start_payload+4])[0]
                 f_out.write(f"{indent}  - Nested Structure Offset: {nested_ofs}\n")
                 if nested_ofs == 0:
                     f_out.write(f"{indent}  -> Points to Root Node (Cycle/Empty Optimization?)\n")
                 else:
                     f_out.write(f"{indent}  -> Recursing into nested structure:\n")
                     dump_node(data, nested_ofs, f_out, indent_level + 2)
            elif val_type == 0x00:
                f_out.write(f"{indent}  - Value: null\n")
            else:
                 f_out.write(f"{indent}  - Unknown Value Type\n")
            
            f_out.write("\n")

        # Recurse into B-Tree Children
        for i, child_offset in enumerate(child_ofs):
            if child_offset != 0:
                f_out.write(f"{indent}-> Child Node {i} at Offset {child_offset}:\n")
                dump_node(data, child_offset, f_out, indent_level + 1)
    except Exception as e:
        f_out.write(f"{indent}Error parsing node at {node_offset}: {e}\n")

def parse_lite3(data_hex, output_filename):
    # Remove spaces and newlines
    data_hex = "".join(data_hex.split())
    data = bytes.fromhex(data_hex)
    
    with open(output_filename, 'w', encoding='utf-8') as f_out:
        f_out.write(f"Total Data Length: {len(data)}\n\n")
        dump_node(data, 0, f_out, 0)


if __name__ == "__main__":
    import os
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        hex_str = ""
        
        if os.path.isfile(arg):
            content = ""
            try:
                with open(arg, 'r', encoding='utf-16') as f:
                    content = f.read()
            except UnicodeError:
                with open(arg, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            import re
            match = re.search(r"Buffer \(hex\):\s*([0-9a-fA-F ]+)", content)
            if match:
                hex_str = match.group(1)
            else:
                hex_str = content
        else:
            hex_str = arg
            
        parse_lite3(hex_str, "d:\\prg\\prj\\lite3\\examples\\buffer_api\\08-analysis.md")
        print("Done.")
    else:
        print("Usage: python lite3_dumper.py <hex_string_or_filename>")
