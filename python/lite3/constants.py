from enum import IntEnum

# General Configuration
LITE3_NODE_ALIGNMENT = 4
LITE3_NODE_SIZE = 96
LITE3_DJB2_HASH_SEED = 5381
LITE3_HASH_PROBE_MAX = 128

# Struct Node Offsets & Sizes
OFS_GEN_TYPE = 0
OFS_HASHES = 4
OFS_SIZE_KC = 32
OFS_KV_OFS = 36
OFS_CHILD_OFS = 64

MAX_KEYS = 7
MAX_CHILDREN = 8

# Type constants
class Lite3Type(IntEnum):
    NULL = 0
    BOOL = 1
    I64 = 2
    F64 = 3
    BYTES = 4
    STRING = 5
    OBJECT = 6
    ARRAY = 7
    INVALID = 8
    COUNT = 9

# GenType Bitfields
# u32 gen_type; // upper 24 bits: gen lower 8 bits: lite3_type
# Bits:
# 0-7: Type (8 bits)
# 8-12: NodeN (5 bits)
# 13-31: Gen (19 bits)

NODE_TYPE_MASK = 0xFF
NODE_N_SHIFT = 8
NODE_N_MASK = 0x1F
GEN_SHIFT = 8
GEN_MASK = 0xFFFFFF

# SizeKC Bitfields
NODE_KC_MASK = 0x3F # 6 bits
NODE_SIZE_SHIFT = 6

# Constants
DEFAULT_NODE_N = 3
