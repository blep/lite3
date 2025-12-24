# Python Lite3 Implementation Plan

## Objective
Implement a pure Python version of the Lite3 library capable of creating, updating, and reading binary buffers fully compatible with the existing C implementation.

## Key Information and Context

### Core Binary Structure
*   **Nodes**: Fixed size (96 bytes), 4-byte aligned. Contains `gen_type` (generation + type), `hashes[7]` (32-bit DJB2 hashes), `size_kc` (key count + total size), `kv_ofs[7]` (offsets to entries), `child_ofs[8]` (offsets to child nodes).
*   **Entries**: Variable length. Structure: `[KeyTag] [Key Bytes] [Value Type Tag] [Value Payload]`.
*   **KeyTag Encoding**: A variable-length integer (1-4 bytes). The lowest 2 bits indicate its own byte length (minus 1). The full integer value, right-shifted by 2 (`>> 2`) gives the length of the key string (including NULL terminator).
*   **Value Type Tag**: A single byte indicating the data type (`0=NULL`, `1=BOOL`, `2=I64`, `3=F64`, `4=BYTES`, `5=STRING`, `6=OBJECT`, `7=ARRAY`).
*   **Value Payload**:
    *   Primitives (BOOL, I64, F64) have fixed sizes.
    *   Variable-length types (BYTES, STRING) store a `u32` length followed by the raw bytes.
    *   Nested Objects/Arrays are implemented as **Inline Nodes**.
*   **Inline Nodes & Aliasing**: When a value is a nested object/array, a full 96-byte Node structure is written directly at that position. The Entry's Value Type Tag (`0x06` or `0x07`) *aliases* the first byte of the Inline Node's `GenType` field, which also contains the type. This is a crucial optimization.
*   **Padding**: Due to 4-byte alignment requirements for nodes, small padding bytes (1-3) may be inserted before inline nodes or child nodes.

### Algorithms
*   **Hashing**: Lite3 uses a custom DJB2 hash function with a seed of `5381`.
    *   `hash = ((hash << 5) + hash) + char`.
    *   Collision handling involves "hash probing" (quadratic: `hash + attempt * attempt`) and subsequent string comparison of keys at the target offset.
*   **B-Tree Traversal (Read)**: Involves binary searching `node.hashes`, following `kv_ofs` to entries, verifying key strings, and recursing into `child_ofs` as needed.
*   **B-Tree Insertion (Write/Update)**: Involves traversing to the correct leaf node, shifting existing entries if space is available, or performing a "node split" (creating a new sibling node, moving half the keys, and promoting a median key to the parent) if the node is full. A root split involves creating a new root.

## Relevant Source Code and Documentation
*   **`d:\prg\prj\lite3\src\lite3.c`**: Authoritative C implementation.
    *   `struct node` definition.
    *   `lite3_get_impl` (read logic).
    *   `lite3_set_impl` (write/split logic).
*   **`d:\prg\prj\lite3\include\lite3.h`**: Header constants (`enum lite3_type`, `LITE3_NODE_ALIGNMENT`=4, `LITE3_NODE_SIZE`=96).
*   **`d:\prg\prj\lite3\decompilers\hexdump_to_doc_skeleton.py`**: Existing Python parser logic.

## Next Steps

1.  **Define Python Structures**: Define Python equivalents for `struct node` and other layouts (using `struct` or `ctypes`).
2.  **Implement `Lite3Reader`**: Adapt parsing logic from `hexdump_to_doc_skeleton.py` into a `Lite3Reader` class.
3.  **Implement Basic `Lite3Writer`**: Initialize empty buffers and append simple key-value entries (no splitting).
4.  **Implement B-Tree Logic**: Implement insertion, node splitting, and key promotion algorithms.
