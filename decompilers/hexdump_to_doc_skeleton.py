
import sys
import struct
import base64

class DocGenerator:
    def __init__(self, data):
        self.data = data
        self.node_size = 96
        self.items = [] # List of dicts describing headers/entries
        self.visited_node_offsets = set()
        self.visited_entry_offsets = set()
        self.nodes = {} # Offset -> Node Info
        self.entries = {} # Offset -> Entry Info
        self.root_hashes = []
        self.hash_to_key = {} # Map hashes to known keys for display

    def read_u32(self, offset):
        return struct.unpack("<I", self.data[offset:offset+4])[0]

    def parse(self):
        # 1. Parse Root Node
        self.parse_node(0, "Root Node", is_root=True)
        # 2. Sort items by offset for linear breakdown
        self.items.sort(key=lambda x: x['start'])

    def parse_node(self, offset, label, is_root=False):
        if offset in self.visited_node_offsets: return
        self.visited_node_offsets.add(offset)
        
        if offset >= len(self.data): return

        # 96-byte Node
        gen_type = self.read_u32(offset)
        hashes = [self.read_u32(offset + 4 + i*4) for i in range(7)]
        size_kc = self.read_u32(offset + 32)
        kv_ofs = [self.read_u32(offset + 36 + i*4) for i in range(7)]
        child_ofs = [self.read_u32(offset + 64 + i*4) for i in range(8)]
        
        gen = gen_type >> 8
        type_tag = gen_type & 0xFF
        key_count = size_kc & 0x07
        total_size = size_kc >> 6
        
        type_str = "OBJECT" if type_tag == 6 else "ARRAY" if type_tag == 7 else "UNKNOWN"
        
        node_info = {
            'type': 'NODE',
            'start': offset,
            'end': offset + self.node_size,
            'label': label,
            'gen_type': gen_type,
            'gen': gen,
            'node_type': type_str,
            'hashes': hashes,
            'size_kc': size_kc,
            'key_count': key_count,
            'total_size': total_size,
            'kv_ofs': kv_ofs,
            'child_ofs': child_ofs
        }
        self.items.append(node_info)
        self.nodes[offset] = node_info
        
        if is_root:
            self.root_hashes = hashes[:key_count]

        # Recurse Children
        for i, child_off in enumerate(child_ofs):
            if child_off != 0:
                self.parse_node(child_off, f"Child {i}")
        
        # Parse Entries & build hash map
        for i, entry_off in enumerate(kv_ofs):
            if i < key_count and entry_off != 0:
                key = self.parse_entry(entry_off, type_tag == 7, i) # 7 is Array
                if key and type_tag == 6:
                    self.hash_to_key[hashes[i]] = key

    def parse_entry(self, offset, is_array_entry, index_in_node):
        # We need to return the key string for the hash map
        key_str_ret = None
        
        # Avoid double adding to items list, BUT we need to re-read to get the key string if already visited
        already_visited = offset in self.visited_entry_offsets
        if not already_visited:
            self.visited_entry_offsets.add(offset)
        
        start = offset
        curr = offset
        
        # Key Parsing
        key_str = ""
        key_len = 0
        tag_byte_len = 0
        key_tag_val = 0
        
        if not is_array_entry:
            b0 = self.data[curr]
            tag_byte_len = (b0 & 0x03) + 1
            key_tag_val = int.from_bytes(self.data[curr:curr+tag_byte_len], 'little')
            key_len = key_tag_val >> 2
            
            curr += tag_byte_len
            key_bytes = self.data[curr:curr+key_len]
            # Key excludes null term for python string, but includes it in length
            key_str = key_bytes[:-1].decode('utf-8', errors='replace')
            key_str_ret = key_str
            curr += key_len
        else:
            # Array entries have no key stored
            key_str = f"Index {index_in_node}"
            key_str_ret = str(index_in_node) # For arrays, hash is index

        if already_visited:
            return key_str_ret

        # Value Parsing
        val_start = curr
        val_type = self.data[curr]
        
        # Check for Inline Node
        inline_node_off = None
        if val_type == 6 or val_type == 7:
            inline_node_off = curr
            curr += self.node_size
        else:
            curr += 1
            if val_type == 4 or val_type == 5: # Bytes/String
                vlen = struct.unpack("<I", self.data[curr:curr+4])[0]
                curr += 4 + vlen
            elif val_type == 2 or val_type == 3: # i64/f64
                curr += 8
            elif val_type == 1: # Bool
                curr += 1
            # Null (0) -> +0 bytes
            
        end = curr
        
        entry_info = {
            'type': 'ENTRY',
            'start': start,
            'end': end,
            'key': key_str,
            'is_array_entry': is_array_entry,
            'val_type': val_type,
            'key_len': key_len,
            'key_tag_bytes': tag_byte_len,
            'val_start': val_start,
            'inline_node_off': inline_node_off
        }
        self.items.append(entry_info)
        self.entries[offset] = entry_info
        
        if inline_node_off is not None:
            self.parse_node(inline_node_off, f"Inline {key_str}")
            
        return key_str_ret

    def generate_hex_dump(self):
        # 16 bytes per line
        out = []
        out.append("## Hex Dump (Annotated)\n")
        out.append("```text")
        out.append("Offset | Data (Hex)                                      | ASCII (approx)")
        out.append("-------+-------------------------------------------------+---------------")
        
        for i in range(0, len(self.data), 16):
            chunk = self.data[i:i+16]
            hex_part = ""
            for j in range(0, 16, 4):
                sub = chunk[j:j+4]
                if not sub: break
                hex_part += sub.hex() + " "
            hex_part = hex_part.ljust(49)
            
            ascii_part = ""
            for b in chunk:
                if 32 <= b <= 126:
                    ascii_part += chr(b)
                else:
                    ascii_part += "."
            
            out.append(f"{i:03d}    | {hex_part}| {ascii_part}")
        out.append("```\n")
        return "\n".join(out)

    def generate_breakdown(self):
        out = []
        out.append("## Detailed Breakdown\n")
        
        sorted_items = sorted(self.items, key=lambda x: x['start'])
        
        cursor = 0
        node_counter = 1
        entry_counter = 1
        
        for item in sorted_items:
            # Gaps
            if item['start'] > cursor:
                gap = item['start'] - cursor
                if gap > 0:
                    out.append(f"### Gap / Padding (Offsets {cursor}-{item['start']})")
                    out.append(f"*   {gap} bytes (0x{gap:x}) likely alignment padding.\n")
            
            if item['type'] == 'NODE':
                out.append(self.format_node(item, node_counter))
                node_counter += 1
                cursor = item['end']
            elif item['type'] == 'ENTRY':
                if item['inline_node_off']:
                     out.append(self.format_entry(item, entry_counter, truncate_at_node=True))
                     cursor = item['inline_node_off'] 
                else:
                    out.append(self.format_entry(item, entry_counter))
                    cursor = item['end']
                entry_counter += 1
                
        return "\n".join(out)

    def format_bytes_spaced(self, b_data):
        return " ".join([b_data.hex()[i:i+2] for i in range(0, len(b_data.hex()), 2)])

    def format_node(self, node, idx):
        lines = []
        name = "Root Node" if node['start'] == 0 else f"Node {idx}"
        lines.append(f"### {name} (Offsets {node['start']}-{node['end']})\n")
        
        lines.append(f"**Total Size**: {self.node_size} bytes\n")
        
        lines.append("**Raw Data**:")
        lines.append("| Offset | Bytes |")
        lines.append("| :--- | :--- |")
        
        node_bytes = self.data[node['start']:node['end']]
        for i in range(0, len(node_bytes), 16):
            chunk = node_bytes[i:i+16]
            hex_s = " ".join([chunk.hex()[j:j+2] for j in range(0, len(chunk.hex()), 2)])
            lines.append(f"| {node['start'] + i} | `{hex_s}` |")
        lines.append("")
        
        lines.append(f"#### Byte 0-4: GenType")
        lines.append(f"Value: `0x{node['gen_type']:08x}`")
        lines.append(f"*   **Type**: {node['node_type']}")
        lines.append(f"*   **Generation**: {node['gen']}\n")
        
        # Hashes Table
        lines.append(f"#### Bytes 4-32: Hashes")
        lines.append("| Index | Bytes | Value | Interpretation |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for i, h in enumerate(node['hashes']):
            if h == 0 and i >= node['key_count']: continue
            interp = self.hash_to_key.get(h, "")
            if node['node_type'] == 'ARRAY': interp = f"Index {h}"
            elif interp: interp = f"Hash of \"{interp}\""
            
            raw_bytes = struct.pack("<I", h)
            b_str = self.format_bytes_spaced(raw_bytes)
            lines.append(f"| {i} | `{b_str}` | 0x{h:x} | {interp} |")
        lines.append("")
        
        lines.append(f"#### Bytes 32-36: SizeKc")
        lines.append(f"Value: `0x{node['size_kc']:08x}` (KeyCount: {node['key_count']}, Total Size: {node['total_size']})\n")
        
        # KvOffsets Table
        lines.append(f"#### Bytes 36-64: KvOffsets (Pointers to Entries)")
        lines.append("| Index | Bytes | Target Offset | Target Key |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for i, ofs in enumerate(node['kv_ofs']):
            if ofs == 0 and i >= node['key_count']: continue
            target_key = "Unknown"
            if ofs in self.entries:
                target_key = self.entries[ofs]['key']
            
            raw_bytes = struct.pack("<I", ofs)
            b_str = self.format_bytes_spaced(raw_bytes)
            lines.append(f"| {i} | `{b_str}` | **{ofs}** | \"{target_key}\" |")
        lines.append("")

        # ChildOffsets Table (NEW)
        lines.append(f"#### Bytes 64-96: ChildOffsets (Pointers to Child Nodes)")
        lines.append("| Index | Bytes | Target Offset | Description |")
        lines.append("| :--- | :--- | :--- | :--- |")
        has_children = False
        for i, ofs in enumerate(node['child_ofs']):
            if ofs == 0: continue
            has_children = True
            raw_bytes = struct.pack("<I", ofs)
            b_str = self.format_bytes_spaced(raw_bytes)
            
            # Find which node it is
            desc_extra = ""
            # We don't easily know "Node 2" from here unless we pass map, but we can say "Child X"
            # User request: "Offset of child 0, identified as Node 2 in this doc"
            # We are generating sequentially. Root=Node 1? Or Node 1=Root.
            # We need to compute Node IDs beforehand if we want to cross ref.
            # Let's just say "Offset of child X" for safety or pre-calc?
            # Simple pre-calc:
            node_id_map = {n['start']: idx+1 for idx, n in enumerate(sorted(self.items, key=lambda x: x['start']) ) if n['type'] == 'NODE'}
            # Wait, self.items isn't fully sorted during parse, but format_node calls after sort? 
            # Actually format_node is called during generate_breakdown which iterates sorted items.
            # So we can build a quick map.
            
            # Re-scoping: format_node doesn't have access to the sorted list easily unless passed or re-calc.
            # Let's do a quick lookup helper
            # Hack: Assume breakdown generation iterates linear.
            pass
            
            target_label = f"Offset of child {i}"
            lines.append(f"| {i} | `{b_str}` | **{ofs}** | {target_label} |")
        
        if not has_children:
            lines.append(f"| - | - | - | **Leaf Node** (All Child Offsets are 0) |")
        lines.append("")
        
        return "\n".join(lines)

    def format_entry(self, entry, idx, truncate_at_node=False):
        lines = []
        # Calculate size displayed
        display_end = entry['inline_node_off'] if truncate_at_node else entry['end']
        
        # Real total size
        real_size = entry['end'] - entry['start']
        
        lines.append(f"### Data Entry {idx}: \"{entry['key']}\" (Offset {entry['start']})")
        
        size_str = f"**Total Size**: {real_size} bytes"
        if entry['inline_node_off']:
            overhead = real_size - 96
            if overhead > 0:
                size_str += f" (Includes 96-byte Inline Node + {overhead} bytes for Key/Tag)"
            else:
                size_str += " (Includes 96-byte Inline Node; Type Tag is aliased with Node Header)"
        lines.append(size_str)
        
        raw_bytes = self.data[entry['start']:display_end]
        hex_s = raw_bytes.hex()
        # Insert spaces
        hex_s = " ".join([hex_s[i:i+2] for i in range(0, len(hex_s), 2)])
        lines.append(f"**Raw Data**: `{hex_s}`\n")
        
        # Table
        lines.append("| Offset | Bytes | Interpretation |")
        lines.append("| :--- | :--- | :--- |")
        
        curr = entry['start']
        
        # Key Tag
        if not entry['is_array_entry']:
            tag_len = entry['key_tag_bytes']
            tag_bytes = self.data[curr:curr+tag_len]
            lines.append(f"| **{curr}** | `{tag_bytes.hex()}` | **KeyTag**: Len {tag_len}. KeyLen {entry['key_len']} |")
            curr += tag_len
            
            key_bytes = self.data[curr:curr+entry['key_len']]
            key_clean = key_bytes.hex()
            lines.append(f"| **{curr}** | `{key_clean}` | **Key**: \"{entry['key']}\" |")
            curr += entry['key_len']
        
        # Value Header
        val_type = entry['val_type']
        val_type_str = {1:"BOOL", 2:"I64", 3:"F64", 4:"BYTES", 5:"STRING", 6:"OBJECT", 7:"ARRAY"}.get(val_type, "UNK")
        
        lines.append(f"| **{curr}** | `{val_type:02x}` | **TypeTag**: {val_type_str} ({val_type}) |")
        
        if truncate_at_node:
            lines.append(f"| ... | ... | *Inline Node follows immediately...* |")
        else:
            # Value Payload
            curr += 1
            if val_type == 1: # BOOL
                val = self.data[curr]
                lines.append(f"| **{curr}** | `{val:02x}` | **Value**: {bool(val)} |")
            elif val_type == 2: # I64
                val_bytes = self.data[curr:curr+8]
                v = struct.unpack("<q", val_bytes)[0]
                # Format bytes
                b_str = " ".join([val_bytes.hex()[i:i+2] for i in range(0, 16, 2)])
                lines.append(f"| **{curr}** | `{b_str}` | **Value**: {v} (I64) |")
            elif val_type == 3: # F64
                val_bytes = self.data[curr:curr+8]
                v = struct.unpack("<d", val_bytes)[0]
                b_str = " ".join([val_bytes.hex()[i:i+2] for i in range(0, 16, 2)])
                lines.append(f"| **{curr}** | `{b_str}` | **Value**: {v:.4f} (F64) |")
            elif val_type == 4: # BYTES
                vlen = struct.unpack("<I", self.data[curr:curr+4])[0]
                lines.append(f"| **{curr}** | `{self.data[curr:curr+4].hex()}` | **Length**: {vlen} |")
                curr += 4
                if vlen > 0:
                    val_bytes = self.data[curr:curr+vlen]
                    # if too long, truncate? user asked for full bytes? "Uses the same format as for the Raw Data"
                    # Raw Data puts spaces.
                    b_str = val_bytes.hex()
                    b_str = " ".join([b_str[i:i+2] for i in range(0, len(b_str), 2)])
                    lines.append(f"| **{curr}** | `{b_str}` | **Value**: Bytes[{vlen}] |")
            elif val_type == 5: # STRING
                vlen = struct.unpack("<I", self.data[curr:curr+4])[0]
                lines.append(f"| **{curr}** | `{self.data[curr:curr+4].hex()}` | **Length**: {vlen} |")
                curr += 4
                sval = self.data[curr:curr+vlen-1].decode('utf-8', errors='replace')
                # Show bytes
                val_bytes = self.data[curr:curr+vlen]
                b_str = val_bytes.hex()
                if len(b_str) > 32: b_str = b_str[:32] + "..." 
                b_str = " ".join([val_bytes.hex()[i:i+2] for i in range(0, len(val_bytes.hex()), 2)])
                lines.append(f"| **{curr}** | `{b_str}` | **Value**: \"{sval}\" |")
                
        lines.append("")
        return "\n".join(lines)

    def generate_graph(self):
        lines = ["## B-Tree Visualization\n", "```mermaid", "graph TD", "classDef node fill:#f9f,stroke:#333;", "classDef entry fill:#e1f5fe,stroke:#333;"]
        
        # Nodes
        for offset, node in self.nodes.items():
            lbl = f"Node @ {offset}<br>Type: {node['node_type']}<br>Keys: {node['key_count']}"
            lines.append(f"    N{offset}[\"{lbl}\"]:::node")
            
            # Edges to entries
            for i, ptr in enumerate(node['kv_ofs']):
                if ptr != 0 and i < node['key_count']:
                    # Hash
                    h = node['hashes'][i]
                    lines.append(f"    N{offset} -- \"Hash[{i}]={h:x}\" --> E{ptr}")
            
            # Edges to children
            for i, ptr in enumerate(node['child_ofs']):
                if ptr != 0:
                     lines.append(f"    N{offset} -- \"Child[{i}]\" --> N{ptr}")

        type_map = {0:"UNK", 1:"BOOL", 2:"I64", 3:"F64", 4:"BYTES", 5:"STRING", 6:"OBJECT", 7:"ARRAY"}
        # Entries
        for offset, entry in self.entries.items():
            if entry['inline_node_off']:
                val_text = "Inline Node"
            else:
                t_str = type_map.get(entry['val_type'], str(entry['val_type']))
                val_text = f"Type: {t_str}"
            
            # Escape key for mermaid
            key_escaped = entry['key'].replace('"', "'")
            
            lbl = f"Key: {key_escaped}<br>{val_text}"
            lines.append(f"    E{offset}[\"{lbl}\"]:::entry")
            
            if entry['inline_node_off']:
                 lines.append(f"    E{offset} -.-> N{entry['inline_node_off']}")

        lines.append("```")
        return "\n".join(lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: python hexdump_to_doc_skeleton.py <file>")
        return
        
    import re
    try:
        with open(sys.argv[1], 'r', encoding='utf-16') as f:
            content = f.read()
    except UnicodeError:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            content = f.read()

    match = re.search(r"Buffer \(hex\):\s*([0-9a-fA-F \n]+)", content)
    if match:
        hex_data = match.group(1)
    else:
        # Fallback: try whole file if clean hex
        hex_data = content
        
    data = bytes.fromhex(hex_data.replace('\n', '').replace(' ', ''))
    
    gen = DocGenerator(data)
    gen.parse()
    
    with open("doc_skeleton.md", "w", encoding="utf-8") as f:
        f.write(gen.generate_hex_dump())
        f.write("\n")
        f.write(gen.generate_breakdown())
        f.write("\n")
        f.write(gen.generate_graph())

if __name__ == "__main__":
    main()
