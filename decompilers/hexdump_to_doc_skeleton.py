
import sys
import struct
import base64

class DocGenerator:
    def __init__(self, data):
        self.data = data
        self.node_size = 96
        self.items = [] # List of dicts describing headers/entries
        self.visited_offsets = set()
        self.nodes = {} # Offset -> Node Info
        self.entries = {} # Offset -> Entry Info
        self.root_hashes = []

    def read_u32(self, offset):
        return struct.unpack("<I", self.data[offset:offset+4])[0]

    def parse(self):
        # 1. Parse Root Node
        self.parse_node(0, "Root Node", is_root=True)
        # 2. Sort items by offset for linear breakdown
        self.items.sort(key=lambda x: x['start'])

    def parse_node(self, offset, label, is_root=False):
        if offset in self.visited_offsets: return
        self.visited_offsets.add(offset)
        
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
        
        # Parse Entries
        for i, entry_off in enumerate(kv_ofs):
            if i < key_count and entry_off != 0:
                self.parse_entry(entry_off, type_tag == 7, i) # 7 is Array

    def parse_entry(self, offset, is_array_entry, index_in_node):
        if offset in self.visited_offsets: return
        self.visited_offsets.add(offset)
        
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
            key_str = key_bytes[:-1].decode('utf-8', errors='replace')
            curr += key_len
        else:
            # Array entries have no key stored
            key_str = f"Index {index_in_node}"

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
             # Recurse into inline node
             # Special case: Inline node is logically a value, but physically a node.
             # We should generate a NODE item for it too, overlapping or modifying parsing?
             # Let's say we call parse_node. It will add a NODE item.
             # But we also have an ENTRY item covering the same Bytes? 
             # Yes. Entry covers Key + Node. Node covers Node.
             # For visualization, we want to split. 
             # Let's adjust Entry 'end' to NOT include the inline node for the sake of the list?
             # OR, we mark the Entry as containing an Inline Node.
             pass
             
        if inline_node_off is not None:
            self.parse_node(inline_node_off, f"Inline {key_str}")

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
        
        # Sort items by start. Filter out visited inline nodes if they were added twice?
        # parse_node adds header. parse_entry adds entry.
        # If entry has inline node, the node header starts at entry.val_start.
        # So we have overlap.
        # Logic: Iterate sorted. If we hit an Entry with Inline Node, print the "Entry Header" details,
        # then let the Node logic print the "Node" details (which will come next in sorted list).
        
        sorted_items = sorted(self.items, key=lambda x: x['start'])
        
        # Filter: If logic works, Entry starts before Node (Key bytes).
        # Except if Array Entry? Array Entry has no key. So Entry Start == Node Start.
        # In Array case, Entry is just logic wrapper. 
        # Let's handle overlap.
        
        cursor = 0
        node_counter = 1
        entry_counter = 1
        
        for item in sorted_items:
            if item['start'] < cursor:
                # Overlap!
                # If Array Entry (Start=NodeStart), skip Entry item and just show Node?
                # Or show "Entry X (Array Index)" then Node.
                pass
            
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
                # If this entry contains an inline node, its 'end' includes the node.
                # But we want to print the Node separately.
                # So we only print the Key part here?
                if item['inline_node_off']:
                     out.append(self.format_entry(item, entry_counter, truncate_at_node=True))
                     cursor = item['inline_node_off'] # Next item should be the Node
                else:
                    out.append(self.format_entry(item, entry_counter))
                    cursor = item['end']
                entry_counter += 1
                
        return "\n".join(out)

    def format_node(self, node, idx):
        lines = []
        name = "Root Node" if node['start'] == 0 else f"Node {idx}"
        lines.append(f"### {name} (Offsets {node['start']}-{node['end']})\n")
        
        # Excerpt
        excerpt = self.data[node['start']:node['start']+32] # First 32 bytes
        lines.append(f"**Header Excerpt**: `{excerpt.hex()[:16]}...`\n")
        
        lines.append(f"#### Byte 0-4: GenType")
        lines.append(f"Value: `0x{node['gen_type']:08x}`")
        lines.append(f"*   **Type**: {node['node_type']}")
        lines.append(f"*   **Generation**: {node['gen']}\n")
        
        lines.append(f"#### Bytes 4-32: Hashes")
        hashes_str = ", ".join([f"0x{h:x}" for h in node['hashes'] if h!=0])
        lines.append(f"Active Hashes: {hashes_str}\n")
        
        lines.append(f"#### Bytes 32-36: SizeKc")
        lines.append(f"Value: `0x{node['size_kc']:08x}` (KeyCount: {node['key_count']}, Total Size: {node['total_size']})\n")
        
        lines.append(f"#### Bytes 36-64: KvOffsets")
        kv_str = ", ".join([str(o) for o in node['kv_ofs'] if o!=0])
        lines.append(f"Pointers to Entries: {kv_str}\n")
        
        return "\n".join(lines)

    def format_entry(self, entry, idx, truncate_at_node=False):
        lines = []
        # Calculate size displayed
        end = entry['inline_node_off'] if truncate_at_node else entry['end']
        size = end - entry['start']
        
        lines.append(f"### Data Entry {idx}: \"{entry['key']}\" (Offset {entry['start']})")
        lines.append(f"**Total Size**: {size} bytes")
        
        raw_bytes = self.data[entry['start']:end]
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
            if val_type == 1:
                val = self.data[curr]
                lines.append(f"| **{curr}** | `{val:02x}` | **Value**: {bool(val)} |")
            elif val_type == 2:
                v = struct.unpack("<q", self.data[curr:curr+8])[0]
                lines.append(f"| **{curr}** | ... | **Value**: {v} (I64) |")
            elif val_type == 3:
                v = struct.unpack("<d", self.data[curr:curr+8])[0]
                lines.append(f"| **{curr}** | ... | **Value**: {v:.4f} (F64) |")
            elif val_type == 5:
                vlen = struct.unpack("<I", self.data[curr:curr+4])[0]
                curr += 4
                sval = self.data[curr:curr+vlen-1].decode('utf-8', errors='replace')
                lines.append(f"| **{curr}** | ... | **Value**: \"{sval}\" |")
                
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

        # Entries
        for offset, entry in self.entries.items():
            val_text = f"Type: {entry['val_type']}"
            if entry['inline_node_off']:
                val_text = "Inline Node"
            
            lbl = f"Key: {entry['key']}<br>{val_text}"
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
