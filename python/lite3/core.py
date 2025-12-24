from typing import Optional, Union, Any, Iterator, Tuple, TYPE_CHECKING
import json
import struct

from .constants import *

# ... (rest of imports)


if TYPE_CHECKING:
    # Forward declarations for type hints
    from .core import Lite3Object, Lite3Array

class Lite3Ref:
    """
    Base class for references into the Lite3 buffer.
    Using __slots__ for memory efficiency and fast attribute access.
    """
    __slots__ = ('_buffer', '_offset')

    def __init__(self, buffer: 'Lite3Buffer', offset: int):
        self._buffer = buffer
        self._offset = offset

    @property
    def offset(self) -> int:
        return self._offset

class Lite3Object(Lite3Ref):
    """
    Reference to a Lite3 Object node.
    Allows dictionary-like access and modification.
    """
    __slots__ = ()

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set a value using Python type inference.
        """
        self._buffer._set_auto(self._offset, key, value)

    def __getitem__(self, key: str) -> Any:
        """
        Get a value by key.
        """
        return self._buffer._get_auto(self._offset, key)

    def get_i64(self, key: str) -> int:
        # return self._buffer._get_i64(self._offset, key)
        return 0

    def get_f64(self, key: str) -> float:
        # return self._buffer._get_f64(self._offset, key)
        return 0.0
    
    def get_str(self, key: str) -> str:
        # return self._buffer._get_str(self._offset, key)
        return ""

    def get_bool(self, key: str) -> bool:
        # return self._buffer._get_bool(self._offset, key)
        return False
    
    def get_object(self, key: str) -> 'Lite3Object':
        # ofs = self._buffer._get_obj_ofs(self._offset, key)
        # return Lite3Object(self._buffer, ofs)
        return Lite3Object(self._buffer, 0)

    def exists(self, key: str) -> bool:
        return False

    def get(self, key: str, default: Any = None) -> Any:
        # if self.exists(key): return self[key]
        return default

    def keys(self) -> Iterator[str]:
        # return self._buffer._iter_keys(self._offset)
        return iter([])

    def values(self) -> Iterator[Any]:
        # return self._buffer._iter_values(self._offset)
        return iter([])

    def items(self) -> Iterator[Tuple[str, Any]]:
        # return self._buffer._iter_items(self._offset)
        return iter([])

    def __iter__(self) -> Iterator[str]:
        return self.keys()
    
    def __contains__(self, key: str) -> bool:
        return self.exists(key)

    def set_i64(self, key: str, value: int) -> None:
        self._buffer._set_i64(self._offset, key, value)
    
    def set_f64(self, key: str, value: float) -> None:
        self._buffer._set_f64(self._offset, key, value)

    def create_object(self, key: str) -> 'Lite3Object':
        """Create and return a nested object."""
        new_ofs = self._buffer._set_obj(self._offset, key)
        return Lite3Object(self._buffer, new_ofs)

    def create_array(self, key: str) -> 'Lite3Array':
        """Create and return a nested array."""
        new_ofs = self._buffer._set_arr(self._offset, key)
        return Lite3Array(self._buffer, new_ofs)

class Lite3Array(Lite3Ref):
    """
    Reference to a Lite3 Array node.
    Allows list-like appending.
    """
    __slots__ = ()

    def __setitem__(self, index: int, value: Any) -> None:
        """Set value by index."""
        # self._buffer._arr_set_auto(self._offset, index, value)
        pass

    def __getitem__(self, index: int) -> Any:
        """Get value by index."""
        return None

    def __iter__(self):
        """Iterate over elements."""
        return iter([])

    def __len__(self) -> int:
        return 0

    def append(self, value: Any) -> None:
        """
        Append a value using Python type inference.
        """
        self._buffer._arr_append_auto(self._offset, value)

    def append_i64(self, value: int) -> None:
        self._buffer._arr_append_i64(self._offset, value)

    def append_object(self) -> 'Lite3Object':
        """Append a new object to this array and return its reference."""
        new_ofs = self._buffer._arr_append_obj(self._offset)
        return Lite3Object(self._buffer, new_ofs)
    
    def append_array(self) -> 'Lite3Array':
        """Append a new array to this array and return its reference."""
        new_ofs = self._buffer._arr_append_arr(self._offset)
        return Lite3Array(self._buffer, new_ofs)


class Lite3Buffer:
    """
    A Python implementation of the Lite3 binary data format.
    """

    def __init__(self, initial_capacity: int = 1024, data: Optional[Union[bytes, bytearray, memoryview]] = None):
        if data is not None:
            self._buffer = bytearray(data)
            self._buflen = len(data)
            if len(self._buffer) < initial_capacity:
                self._buffer.extend(b'\x00' * (initial_capacity - len(self._buffer)))
        else:
            self._buffer = bytearray(initial_capacity)
            self._buflen = 0

    @property
    def memory(self) -> memoryview:
        """Get a zero-copy memoryview of the used portion of the buffer."""
        return memoryview(self._buffer)[:self._buflen]

    def init_obj(self) -> Lite3Object:
        """Initialize the root as an Object."""
        self._init_node(Lite3Type.OBJECT)
        return Lite3Object(self, 0)

    def init_arr(self) -> Lite3Array:
        """Initialize the root as an Array."""
        self._init_node(Lite3Type.ARRAY)
        return Lite3Array(self, 0)

    def _init_node(self, type_tag: Lite3Type):
        # Ensure capacity for root node
        needed = LITE3_NODE_SIZE
        if len(self._buffer) < needed:
            self._buffer.extend(b'\x00' * (needed - len(self._buffer)))
        
        # Zero out the node range
        self._buffer[0:LITE3_NODE_SIZE] = b'\x00' * LITE3_NODE_SIZE
        
        # Write GenType: (Gen(0) << 13) | (NodeN(3) << 8) | type
        gen_type = (0 << GEN_SHIFT) | (DEFAULT_NODE_N << NODE_N_SHIFT) | (type_tag & NODE_TYPE_MASK)
        struct.pack_into('<I', self._buffer, OFS_GEN_TYPE, gen_type)
        
        # Write SizeKC: (0 << 6) | 0 -> 0
        struct.pack_into('<I', self._buffer, OFS_SIZE_KC, 0)
        
        self._buflen = LITE3_NODE_SIZE

    def _set_auto(self, ofs: int, key: str, value: Any) -> None:
        if value is None:
            self._set_null(ofs, key)
        elif isinstance(value, bool):
            self._set_bool(ofs, key, value)
        elif isinstance(value, int):
            self._set_i64(ofs, key, value)
        elif isinstance(value, float):
            self._set_f64(ofs, key, value)
        elif isinstance(value, (bytes, bytearray)):
            self._set_bytes(ofs, key, value)
        elif isinstance(value, str):
            self._set_str(ofs, key, value)
        else:
            raise TypeError(f"Unsupported type: {type(value)}")

    def _set_i64(self, ofs: int, key: str, value: int) -> None:
        # Tag: LITE3_TYPE_I64 (2)
        payload = struct.pack('<Bq', Lite3Type.I64, value)
        self._set_impl(ofs, key, payload)

    def _set_f64(self, ofs: int, key: str, value: float) -> None:
        # Tag: LITE3_TYPE_F64 (3)
        payload = struct.pack('<Bd', Lite3Type.F64, value)
        self._set_impl(ofs, key, payload)

    def _set_bool(self, ofs: int, key: str, value: bool) -> None:
        # LITE3_TYPE_BOOL (1). Value is NOT in tag.
        # Wait, C hex check?
        # Example 02 or 08 needed.
        # Assuming payload follows: [Tag] [Value(1 byte)].
        payload = struct.pack('<BB', Lite3Type.BOOL, 1 if value else 0)
        self._set_impl(ofs, key, payload)

    def _set_null(self, ofs: int, key: str) -> None:
        # Tag: LITE3_TYPE_NULL (0)
        payload = struct.pack('<B', Lite3Type.NULL)
        self._set_impl(ofs, key, payload)
        
    def _set_str(self, ofs: int, key: str, value: str) -> None:
        # Tag: LITE3_TYPE_STRING (5)
        # Length: 4 bytes (u32) based on observed hex
        encoded = value.encode('utf-8') + b'\x00'
        length = len(encoded)
        payload = struct.pack('<BI', Lite3Type.STRING, length) + encoded
        self._set_impl(ofs, key, payload)

    def _set_bytes(self, ofs: int, key: str, value: bytes) -> None:
        # Tag: LITE3_TYPE_BYTES (4)
        length = len(value)
        payload = struct.pack('<BI', Lite3Type.BYTES, length) + value
        self._set_impl(ofs, key, payload)

    def _encode_var_len(self, tag_base: int, data: bytes) -> bytes:
        # Deprecated logic removed
        return b''

    def _calc_hash(self, key: str) -> int:
        h = LITE3_DJB2_HASH_SEED
        for c in key.encode('utf-8'):
            h = ((h << 5) + h) + c
            h &= 0xFFFFFFFF # Keep 32-bit
        return h

    def _set_impl(self, root_ofs: int, key: str, val_payload: bytes) -> int:
        # 1. Hashing
        key_hash = self._calc_hash(key)
        
        # Increment Generation Count (C Compatibility)
        gen_type = struct.unpack_from('<I', self._buffer, root_ofs + OFS_GEN_TYPE)[0]
        gen = (gen_type >> GEN_SHIFT) + 1
        new_gen_type = (gen_type & NODE_TYPE_MASK) | (gen << GEN_SHIFT)
        struct.pack_into('<I', self._buffer, root_ofs + OFS_GEN_TYPE, new_gen_type)
        
        node_ofs = root_ofs
        parent_ofs = None
        child_idx_in_parent = -1

        hashes = []
        kv_ofs = []
        child_ofs = []
        size_kc = 0
        key_count = 0
        
        while True:
            # Read Node Data
            hashes = [struct.unpack_from('<I', self._buffer, node_ofs + OFS_HASHES + i*4)[0] for i in range(MAX_KEYS)]
            size_kc = struct.unpack_from('<I', self._buffer, node_ofs + OFS_SIZE_KC)[0]
            key_count = size_kc & NODE_KC_MASK
            kv_ofs = [struct.unpack_from('<I', self._buffer, node_ofs + OFS_KV_OFS + i*4)[0] for i in range(MAX_KEYS)]
            child_ofs = [struct.unpack_from('<I', self._buffer, node_ofs + OFS_CHILD_OFS + i*4)[0] for i in range(MAX_CHILDREN)]
            
            # Check Full -> Split
            if key_count >= MAX_KEYS:
                 done_ofs, next_node, next_parent, next_idx = self._split_node(
                     node_ofs, parent_ofs, child_idx_in_parent, root_ofs, 
                     key, val_payload, key_hash
                 )
                 if done_ofs is not None:
                     return done_ofs
                 
                 node_ofs = next_node
                 parent_ofs = next_parent
                 child_idx_in_parent = next_idx
                 continue

            # Check Keys in Node
            idx = 0
            while idx < key_count:
                 h = hashes[idx]
                 if h == key_hash:
                     # Match Found
                     entry_ofs = self._append_entry(key, val_payload)
                     struct.pack_into('<I', self._buffer, node_ofs + OFS_KV_OFS + idx*4, entry_ofs)
                     return entry_ofs
                 if h > key_hash:
                     break
                 idx += 1
            
            # Check Children
            next_child = child_ofs[idx]
            if next_child != 0:
                 # Traverse Down
                 parent_ofs = node_ofs
                 child_idx_in_parent = idx
                 node_ofs = next_child
                 continue
            
            # Insert at Leaf (idx)
            entry_ofs = self._append_entry(key, val_payload)
            
            # Shift
            for i in range(key_count, idx, -1):
                 struct.pack_into('<I', self._buffer, node_ofs + OFS_HASHES + i*4, hashes[i-1])
                 struct.pack_into('<I', self._buffer, node_ofs + OFS_KV_OFS + i*4, kv_ofs[i-1])
            
            struct.pack_into('<I', self._buffer, node_ofs + OFS_HASHES + idx*4, key_hash)
            struct.pack_into('<I', self._buffer, node_ofs + OFS_KV_OFS + idx*4, entry_ofs)
            
            # Update SizeKC
            key_count += 1
            size = (size_kc >> NODE_SIZE_SHIFT) + 1
            new_size_kc = (size << NODE_SIZE_SHIFT) | key_count
            struct.pack_into('<I', self._buffer, node_ofs + OFS_SIZE_KC, new_size_kc)
            
            return entry_ofs

    def _split_node(self, node_ofs: int, parent_ofs: Optional[int], child_idx: int, root_ofs: int, 
                    key: str, val_payload: bytes, key_hash: int) -> Tuple[Optional[int], int, Optional[int], int]:
        
        # 1. Align Buffer
        current_len = self._buflen
        aligned_len = (current_len + 3) & ~3
        if aligned_len > current_len:
             self._buffer.extend(b'\x00' * (aligned_len - current_len))
             self._buflen = aligned_len
             
        # 2. Handle Root Split
        if parent_ofs is None and node_ofs == root_ofs:
             new_child_ofs = self._buflen
             self._buffer.extend(self._buffer[root_ofs : root_ofs + LITE3_NODE_SIZE])
             self._buflen += LITE3_NODE_SIZE
             
             # Re-init Root
             self._buffer[root_ofs + 8 : root_ofs + LITE3_NODE_SIZE] = b'\x00' * (LITE3_NODE_SIZE - 8)
             struct.pack_into('<I', self._buffer, root_ofs + OFS_CHILD_OFS, new_child_ofs)
             old_size_kc = struct.unpack_from('<I', self._buffer, root_ofs + OFS_SIZE_KC)[0]
             struct.pack_into('<I', self._buffer, root_ofs + OFS_SIZE_KC, old_size_kc & ~NODE_KC_MASK)
             
             parent_ofs = root_ofs
             node_ofs = new_child_ofs
             child_idx = 0
        
        # 3. Standard Split
        # Alloc Sibling
        sibling_ofs = self._buflen
        self._buffer.extend(b'\x00' * LITE3_NODE_SIZE)
        self._buflen += LITE3_NODE_SIZE
        
        median_idx = 3
        
        # Shift Parent
        p_size_kc = struct.unpack_from('<I', self._buffer, parent_ofs + OFS_SIZE_KC)[0]
        p_kc = p_size_kc & NODE_KC_MASK
        
        for j in range(p_kc, child_idx, -1):
             h_val = struct.unpack_from('<I', self._buffer, parent_ofs + OFS_HASHES + (j-1)*4)[0]
             struct.pack_into('<I', self._buffer, parent_ofs + OFS_HASHES + j*4, h_val)
             k_val = struct.unpack_from('<I', self._buffer, parent_ofs + OFS_KV_OFS + (j-1)*4)[0]
             struct.pack_into('<I', self._buffer, parent_ofs + OFS_KV_OFS + j*4, k_val)
             c_val = struct.unpack_from('<I', self._buffer, parent_ofs + OFS_CHILD_OFS + j*4)[0]
             struct.pack_into('<I', self._buffer, parent_ofs + OFS_CHILD_OFS + (j+1)*4, c_val)
             
        # Promote Median
        m_hash = struct.unpack_from('<I', self._buffer, node_ofs + OFS_HASHES + median_idx*4)[0]
        m_kv = struct.unpack_from('<I', self._buffer, node_ofs + OFS_KV_OFS + median_idx*4)[0]
        
        struct.pack_into('<I', self._buffer, parent_ofs + OFS_HASHES + child_idx*4, m_hash)
        struct.pack_into('<I', self._buffer, parent_ofs + OFS_KV_OFS + child_idx*4, m_kv)
        struct.pack_into('<I', self._buffer, parent_ofs + OFS_CHILD_OFS + (child_idx+1)*4, sibling_ofs)
        
        struct.pack_into('<I', self._buffer, parent_ofs + OFS_SIZE_KC, (p_size_kc & ~NODE_KC_MASK) | (p_kc + 1))
        
        # Init Sibling
        ntype = struct.unpack_from('<I', self._buffer, node_ofs + OFS_GEN_TYPE)[0]
        struct.pack_into('<I', self._buffer, sibling_ofs + OFS_GEN_TYPE, ntype)
        struct.pack_into('<I', self._buffer, sibling_ofs + OFS_SIZE_KC, median_idx)
        struct.pack_into('<I', self._buffer, node_ofs + OFS_SIZE_KC, median_idx)
        
        # Move Keys
        c_m1 = struct.unpack_from('<I', self._buffer, node_ofs + OFS_CHILD_OFS + (median_idx+1)*4)[0]
        struct.pack_into('<I', self._buffer, sibling_ofs + OFS_CHILD_OFS, c_m1)
        struct.pack_into('<I', self._buffer, node_ofs + OFS_CHILD_OFS + (median_idx+1)*4, 0)
        
        for j in range(median_idx):
             src_idx = j + median_idx + 1
             h = struct.unpack_from('<I', self._buffer, node_ofs + OFS_HASHES + src_idx*4)[0]
             kv = struct.unpack_from('<I', self._buffer, node_ofs + OFS_KV_OFS + src_idx*4)[0]
             c = struct.unpack_from('<I', self._buffer, node_ofs + OFS_CHILD_OFS + (src_idx+1)*4)[0]
             
             struct.pack_into('<I', self._buffer, sibling_ofs + OFS_HASHES + j*4, h)
             struct.pack_into('<I', self._buffer, sibling_ofs + OFS_KV_OFS + j*4, kv)
             struct.pack_into('<I', self._buffer, sibling_ofs + OFS_CHILD_OFS + (j+1)*4, c)
             
             struct.pack_into('<I', self._buffer, node_ofs + OFS_HASHES + src_idx*4, 0)
             struct.pack_into('<I', self._buffer, node_ofs + OFS_KV_OFS + src_idx*4, 0)
             struct.pack_into('<I', self._buffer, node_ofs + OFS_CHILD_OFS + (src_idx+1)*4, 0)
             
        struct.pack_into('<I', self._buffer, node_ofs + OFS_HASHES + median_idx*4, 0)
        struct.pack_into('<I', self._buffer, node_ofs + OFS_KV_OFS + median_idx*4, 0)
        
        # Determine Next Node (Left/Right/Parent)
        if key_hash > m_hash:
             return None, sibling_ofs, parent_ofs, child_idx + 1
        elif key_hash == m_hash:
             # Match in Parent
             entry_ofs = self._append_entry(key, val_payload)
             struct.pack_into('<I', self._buffer, parent_ofs + OFS_KV_OFS + child_idx*4, entry_ofs)
             return entry_ofs, node_ofs, parent_ofs, child_idx # Loop will return
        else:
             return None, node_ofs, parent_ofs, child_idx

    def _append_entry(self, key: str, val_payload: bytes) -> int:
        
        # Check if payload requires alignment (Object/Array nodes)
        align_payload = False
        if len(val_payload) > 0:
            type_tag = val_payload[0]
            if type_tag == Lite3Type.OBJECT or type_tag == Lite3Type.ARRAY:
                align_payload = True
        
        # 1. Key Tag & Bytes
        base_key_bytes = key.encode('utf-8') + b'\x00'
        
        # Iterative padding calculation (because tag size might change)
        padding = 0
        while True:
            key_bytes = base_key_bytes + (b'\x00' * padding)
            key_len = len(key_bytes)
            
            # Calc Tag Size (1..4)
            if key_len < 64: tag_size = 1
            elif key_len < 16384: tag_size = 2
            else: tag_size = 4
            
            if not align_payload:
                break
                
            offset = self._buflen
            payload_start = offset + tag_size + key_len
            needed_padding = (4 - (payload_start % 4)) % 4
            
            if needed_padding == 0:
                break
            
            padding += needed_padding
            
        tag_val = (key_len << 2) | (tag_size - 1)
        tag_bytes = tag_val.to_bytes(tag_size, 'little')
        
        data = tag_bytes + key_bytes + val_payload
        needed = len(data)
        
        # Ensure capacity
        offset = self._buflen
        if offset + needed > len(self._buffer):
            self._buffer.extend(b'\x00' * max(32, needed)) # Smart resize later
            
        # Write
        self._buffer[offset:offset+needed] = data
        self._buflen += needed
        
        return offset

    def _arr_append_auto(self, arr_ofs: int, val: Any) -> None:
        # Similar logic for arrays
        if isinstance(val, int):
            self._arr_append_i64(arr_ofs, val)
        elif isinstance(val, str):
            self._arr_append_str(arr_ofs, val)
        # ... others
        else:
             raise TypeError(f"Unsupported type for Lite3 append: {type(val)}")
    
    def _create_node_bytes(self, type_tag: Lite3Type) -> bytearray:
        """Create a new node bytearray (96 bytes)."""
        node_bytes = bytearray(LITE3_NODE_SIZE)
        
        # Write GenType
        gen_type = (0 << GEN_SHIFT) | (DEFAULT_NODE_N << NODE_N_SHIFT) | (type_tag & NODE_TYPE_MASK)
        struct.pack_into('<I', node_bytes, OFS_GEN_TYPE, gen_type)
        
        # Write SizeKC: 0
        struct.pack_into('<I', node_bytes, OFS_SIZE_KC, 0)
        
        return node_bytes

    def _set_obj(self, ofs: int, key: str) -> int: 
        """Returns new object offset"""
        # 1. Create Node Bytes
        node_bytes = self._create_node_bytes(Lite3Type.OBJECT)
        return self._insert_node_entry(ofs, key, node_bytes)

    def _set_arr(self, ofs: int, key: str) -> int:
        """Returns new array offset"""
        node_bytes = self._create_node_bytes(Lite3Type.ARRAY)
        return self._insert_node_entry(ofs, key, node_bytes)
        
    def _insert_node_entry(self, parent_ofs: int, key: str, node_bytes: bytearray) -> int:
        entry_ofs = self._set_impl(parent_ofs, key, node_bytes)
        # Read entry to find correct value offset (skipping padded key)
        _, val_ofs, _ = self._read_entry_header(entry_ofs, Lite3Type.OBJECT)
        return val_ofs

    def _get_auto(self, node_ofs: int, key: str) -> Any:
        # 1. Calculate Hash
        key_hash = self._calc_hash(key)
        
        # 2. Find Key
        hashes = [struct.unpack_from('<I', self._buffer, node_ofs + OFS_HASHES + i*4)[0] for i in range(MAX_KEYS)]
        size_kc = struct.unpack_from('<I', self._buffer, node_ofs + OFS_SIZE_KC)[0]
        key_count = size_kc & NODE_KC_MASK
        kv_ofs = [struct.unpack_from('<I', self._buffer, node_ofs + OFS_KV_OFS + i*4)[0] for i in range(MAX_KEYS)]
        
        child_ofs = [struct.unpack_from('<I', self._buffer, node_ofs + OFS_CHILD_OFS + i*4)[0] for i in range(MAX_CHILDREN)]
        
        idx = 0
        while idx < key_count:
            h = hashes[idx]
            if h == key_hash:
                # Found Candidate? Hash collision possible?
                # Need to verify Key String match if hashes match.
                # Lite3 relies on 32-bit hashes. Collisions handled?
                # Spec doesn't describe collision handling explicit scan.
                # But typically verify key.
                # Let's verify key.
                k_ofs = kv_ofs[idx]
                found_key, val_ofs, val_type = self._read_entry_header(k_ofs, Lite3Type.OBJECT) # Root is Object
                if found_key == key:
                    return self._read_recursive(val_ofs, val_type)
                    
                # If collision but not key match? Lite3 B-Tree likely handles it by open addressing or chaining?
                # Or just traversing?
                # If hashes are sorted, we might scan forward?
                pass
            
            if h > key_hash:
                # Check child[idx]
                c_ofs = child_ofs[idx]
                if c_ofs != 0:
                    return self._get_auto(c_ofs, key) # Recurse
                return None # Not found
                
            idx += 1
            
        # Check last child (rightmost)
        c_ofs = child_ofs[idx]
        if c_ofs != 0:
             return self._get_auto(c_ofs, key)
             
        return None

    def _read_entry_header(self, k_ofs: int, node_type: int) -> Tuple[Optional[str], int, int]:
        # Helper extracted from _iter_node logic
        if node_type == Lite3Type.ARRAY:
             curr = k_ofs
             key_str = None
        else:
             tag_byte = self._buffer[k_ofs]
             tag_size = (tag_byte & 0x03) + 1
             if tag_size == 1: tag_val = self._buffer[k_ofs]
             elif tag_size == 2: tag_val = struct.unpack_from('<H', self._buffer, k_ofs)[0]
             else: tag_val = struct.unpack_from('<I', self._buffer, k_ofs)[0]
             
             key_len = tag_val >> 2
             key_ptr = k_ofs + tag_size
             key_raw = self._buffer[key_ptr : key_ptr + key_len]
             key_str = key_raw.decode('utf-8').rstrip('\x00')
             curr = key_ptr + key_len
             
        val_type = self._buffer[curr]
        
        if val_type == Lite3Type.OBJECT or val_type == Lite3Type.ARRAY:
             pass_ofs = curr
        else:
             pass_ofs = curr + 1
             
        return key_str, pass_ofs, val_type

    def _arr_append_i64(self, ofs: int, val: int) -> None: ...
    def _arr_append_str(self, ofs: int, val: str) -> None: ...
    
    def _arr_append_obj(self, ofs: int) -> int:
        """Returns new nested object offset"""
        ...
        return 0
    
    def _arr_append_arr(self, ofs: int) -> int:
        """Returns new nested array offset"""
        ...
        return 0

    def hex_dump(self) -> str:
        return self.memory.hex()


    def to_json_string(self, indent: int = 4) -> str:
        # Root is always at offset 0
        if self._buflen < LITE3_NODE_SIZE:
             return "{}" # Empty or uninitialized
             
        root_type = self._get_node_type(0)
        data = self._read_recursive(0, root_type)
        return json.dumps(data, indent=indent, sort_keys=True)

    def _get_node_type(self, node_ofs: int) -> int:
        gen_type = struct.unpack_from('<I', self._buffer, node_ofs + OFS_GEN_TYPE)[0]
        return gen_type & NODE_TYPE_MASK
        
    def _read_recursive(self, offset: int, type_tag: int) -> Any:
        if type_tag == Lite3Type.NULL:
            return None
        elif type_tag == Lite3Type.BOOL:
            # Value in payload? Or if it was a node type?
            # Reads from VALUE payload location?
            pass
            
        # Dispatch
        if type_tag == Lite3Type.OBJECT:
             return self._read_object(offset)
        elif type_tag == Lite3Type.ARRAY:
             return self._read_array(offset)
        elif type_tag == Lite3Type.STRING:
             return self._read_str_val(offset) # offset points to [Len][Bytes]
        elif type_tag == Lite3Type.BYTES:
             return self._read_bytes_val(offset)
        elif type_tag == Lite3Type.I64:
             return struct.unpack_from('<q', self._buffer, offset)[0]
        elif type_tag == Lite3Type.F64:
             return struct.unpack_from('<d', self._buffer, offset)[0]
        elif type_tag == Lite3Type.BOOL:
             # For bool, value is in byte after tag. 
             # Callers of _read_recursive typically pass offset AFTER the tag.
             # In my set_bool: [Tag] [Val].
             return bool(self._buffer[offset])
        elif type_tag == Lite3Type.NULL:
             return None
        else:
             return f"<Unknown Type {type_tag}>"

    def _read_str_val(self, offset: int) -> str:
        length = struct.unpack_from('<I', self._buffer, offset)[0]
        s_bytes = self._buffer[offset+4 : offset+4+length]
        return s_bytes.decode('utf-8').rstrip('\x00')

    def _read_bytes_val(self, offset: int) -> str:
        length = struct.unpack_from('<I', self._buffer, offset)[0]
        b_val = self._buffer[offset+4 : offset+4+length]
        import base64
        return base64.b64encode(b_val).decode('ascii')

    def _read_object(self, node_ofs: int) -> dict:
        result = {}
        for key, val_ofs, val_type in self._iter_node(node_ofs):
            val = self._read_recursive(val_ofs, val_type)
            result[key] = val
        return result

    def _read_array(self, node_ofs: int) -> list:
        # Arrays in Lite3 are B-Trees where keys are omitted (hashes=index).
        # We need to iterate and collect.
        # However, indices might be sparse? Or B-tree order?
        # Standard iterator should yield in stored order (hash order)?
        # For Arrays, hash is index. So iterating yields sorted by index.
        result = []
        for _, val_ofs, val_type in self._iter_node(node_ofs):
             val = self._read_recursive(val_ofs, val_type)
             result.append(val)
        return result

    def _iter_node(self, node_ofs: int) -> Iterator[Tuple[Optional[str], int, int]]:
        """
        Traverses B-Tree rooted at node_ofs.
        Yields (key, value_payload_offset, value_type_tag)
        """
        # Read Node Header
        gen_type = struct.unpack_from('<I', self._buffer, node_ofs + OFS_GEN_TYPE)[0]
        node_type = gen_type & NODE_TYPE_MASK
        
        # We need recursive traversal of children + local keys
        # Arrays: child pointers are interleaving keys.
        # Layout: C0, K0, C1, K1 ...
        
        # Read arrays
        hashes = [struct.unpack_from('<I', self._buffer, node_ofs + OFS_HASHES + i*4)[0] for i in range(MAX_KEYS)]
        size_kc = struct.unpack_from('<I', self._buffer, node_ofs + OFS_SIZE_KC)[0]
        key_count = size_kc & NODE_KC_MASK
        kv_ofs = [struct.unpack_from('<I', self._buffer, node_ofs + OFS_KV_OFS + i*4)[0] for i in range(MAX_KEYS)]
        child_ofs = [struct.unpack_from('<I', self._buffer, node_ofs + OFS_CHILD_OFS + i*4)[0] for i in range(MAX_CHILDREN)]

        # In-order traversal
        for i in range(key_count + 1):
             # Visit Child[i]
             c_ofs = child_ofs[i]
             if c_ofs != 0:
                 yield from self._iter_node(c_ofs)
             
             # Visit Key[i] (if i < key_count)
             if i < key_count:
                 k_ofs = kv_ofs[i]
                 
                 # Decode Entry at k_ofs
                 # Entry: [Tag] [Key] [ValTag] [ValPayload]
                 # If Array, Key is skipped?
                 # Lite3 Spec: "Array entries omit the key entirely".
                 if node_type == Lite3Type.ARRAY:
                     # For Arrays, we can assume no keys needed to be parsed
                     curr = k_ofs
                     key_str = None
                 else:
                     # Object Entry: [KeyTag] [Key] ...
                     # Read Key Tag
                     tag_byte = self._buffer[k_ofs]
                     tag_size = (tag_byte & 0x03) + 1
                     key_len = struct.unpack_from('<I', self._buffer, k_ofs)[0] >> 2 # Read 4 bytes for tag value calc? 
                     # Wait, my logic: tag_val = (key_len << 2) | (TagSize - 1)
                     # Tag is 1..4 bytes.
                     # C Spec: "TagValue = ReadLeBytes...".
                     if tag_size == 1:
                         tag_val = self._buffer[k_ofs]
                     elif tag_size == 2:
                         tag_val = struct.unpack_from('<H', self._buffer, k_ofs)[0]
                     else:
                         tag_val = struct.unpack_from('<I', self._buffer, k_ofs)[0]
                         
                     key_len = tag_val >> 2
                     
                     # Read Key
                     key_ptr = k_ofs + tag_size
                     # key includes null? Spec: "KeySize = number of key bytes, including null terminator"
                     key_raw = self._buffer[key_ptr : key_ptr + key_len]
                     key_str = key_raw.decode('utf-8').rstrip('\x00')
                     
                     curr = key_ptr + key_len
                 
                 # Read Value Type Tag
                 val_type = self._buffer[curr]
                 val_payload_ofs = curr + 1
                 
                 # Special handling for Nested Nodes (Object/Array)
                 if val_type == Lite3Type.OBJECT or val_type == Lite3Type.ARRAY:
                     # The Node starts exactly where TypeTag is (Aliasing)
                     # But alignment logic from C means there might be padding BEFORE `curr`
                     # However, for reading, if we trust `kv_ofs` points to [KeyTag], and we iterated over Key...
                     # If there was padding, it should be between Key and Value.
                     # Where is it?
                     # My simple reader assumes NO padding for now (which matches my Writer).
                     # Only Test 8 (complex) likely has it.
                     pass_ofs = curr
                 else:
                     pass_ofs = curr + 1
                     
                 yield (key_str, pass_ofs, val_type)
