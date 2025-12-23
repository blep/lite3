
import struct
import json
import base64
import sys
import re

# Fixed constants for this specific build
NODE_SIZE = 96

# Load data from file to ensure accuracy
try:
    with open("d:/prg/prj/lite3/examples/buffer_api/08-comprehensive-features-output.txt", "r", encoding="utf-16") as f:
        content = f.read()
except UnicodeError:
    with open("d:/prg/prj/lite3/examples/buffer_api/08-comprehensive-features-output.txt", "r", encoding="utf-8") as f:
        content = f.read()

# Extract hex string
match = re.search(r"Buffer \(hex\):\s*([0-9a-fA-F \n]+)", content)
if match:
    hex_data = match.group(1)
    DATA = bytes.fromhex(hex_data.replace('\n', '').replace(' ', ''))
else:
    print("Error: Could not find Buffer (hex) in file")
    sys.exit(1)


def read_u32(offset):
    return struct.unpack("<I", DATA[offset:offset+4])[0]

def parse_key(offset):
    # Key Tag
    b = DATA[offset]
    # TagSize is (b & 3) + 1
    tag_size = (b & 0x03) + 1
    # Full tag value
    tag_val = int.from_bytes(DATA[offset:offset+tag_size], 'little')
    # Key Length is tag_val >> 2
    key_len = tag_val >> 2
    
    start_key = offset + tag_size
    # Key bytes include null terminator
    key_bytes = DATA[start_key:start_key+key_len-1] 
    # print(f"DEBUG: parse_key({offset}) tag={b:02x} len={key_len} bytes={key_bytes.hex()}")
    return key_bytes.decode('utf-8', errors='replace'), start_key + key_len

def parse_val(offset):
    if offset >= len(DATA):
        raise ValueError(f"Offset {offset} out of bounds {len(DATA)}")
        
    type_tag = DATA[offset]
    
    # Inline Nodes (Object/Array) start exactly at the type_tag position
    if type_tag == 6: # OBJECT
        val = parse_container(offset, is_array=False)
        return val, offset + NODE_SIZE
    elif type_tag == 7: # ARRAY
        val = parse_container(offset, is_array=True)
        return val, offset + NODE_SIZE

    offset += 1
    
    if type_tag == 0: # NULL
        return None, offset
    elif type_tag == 1: # BOOL
        val = (DATA[offset] != 0)
        return val, offset + 1
    elif type_tag == 2: # I64
        val = struct.unpack("<q", DATA[offset:offset+8])[0]
        return val, offset + 8
    elif type_tag == 3: # F64
        val = struct.unpack("<d", DATA[offset:offset+8])[0]
        return val, offset + 8
    elif type_tag == 4: # BYTES
        length = struct.unpack("<I", DATA[offset:offset+4])[0]
        offset += 4
        val = DATA[offset:offset+length]
        val_str = base64.b64encode(val).decode('ascii')
        return val_str, offset + length
    elif type_tag == 5: # STRING
        length = struct.unpack("<I", DATA[offset:offset+4])[0]
        offset += 4
        val = DATA[offset:offset+length-1].decode('utf-8', errors='replace')
        return val, offset + length
    else:
        # Invalid type
        return f"<Invalid Type {type_tag}>", offset

def parse_container(node_offset, is_array):
    entries = [] 
    
    def traverse(offset):
        if offset >= len(DATA): return
        
        hashes_start = offset + 4
        size_kc = read_u32(offset + 32)
        kv_ofs_start = offset + 36
        child_ofs_start = offset + 64
        
        key_count = size_kc & 0x07
        
        child_ofs = []
        for i in range(8):
            child_ofs.append(read_u32(child_ofs_start + i*4))
            
        kv_ofs = []
        for i in range(7):
            kv_ofs.append(read_u32(kv_ofs_start + i*4))
            
        node_hashes = []
        for i in range(7):
            node_hashes.append(read_u32(hashes_start + i*4))
            
        for i in range(key_count + 1):
             if child_ofs[i] != 0:
                 traverse(child_ofs[i])
                 
             if i < key_count:
                 entry_ptr = kv_ofs[i]
                 if entry_ptr != 0:
                     if is_array:
                         index = node_hashes[i]
                         val, _ = parse_val(entry_ptr)
                         entries.append((index, val))
                     else:
                         key, after_key = parse_key(entry_ptr)
                         val, _ = parse_val(after_key)
                         entries.append((key, val))

    traverse(node_offset)
    
    if is_array:
        entries.sort(key=lambda x: x[0])
        return [v for k, v in entries]
    else:
        return {k: v for k, v in entries}

def main():
    try:
        root_node = parse_container(0, is_array=False)
        print(json.dumps(root_node, indent=4, sort_keys=True))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
