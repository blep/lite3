
import argparse
import random
import sys

# Constants
DJB2_INIT = 5381
MOD_MASK = 0xFFFFFFFF

def djb2(s: bytes) -> int:
    """Standard DJB2 hash matching the behavior of Lite3."""
    h = DJB2_INIT
    for b in s:
        # Lite3: ((hash << 5) + hash) + char
        h = ((h << 5) + h) + b
        h &= MOD_MASK
    return h

def djb2_poly(s: bytes) -> int:
    """Calculates the Polynomial(S) part of the collision equation (DJB2 with seed 0)."""
    h = 0
    for b in s:
        h = ((h << 5) + h) + b
        h &= MOD_MASK
    return h

def mod_inv(a, m):
    """Calculates modular inverse of a modulo m."""
    return pow(a, -1, m)

def generate_collisions(target_key, count, verbose=False):
    target_bytes = target_key.encode('utf-8')
    target_hash = djb2(target_bytes)
    
    if verbose:
        print(f"Target Key: '{target_key}'")
        print(f"Target Hash: {target_hash} (0x{target_hash:08x})")
        print(f"Generating optimized lookup table (~65k entries)...")
    
    # --- Meet-in-the-Middle Logic ---
    # Hash(P + S) = Hash(P) * 33^len(S) + Poly(S)
    # We want: Hash(P) * 33^len(S) + Poly(S) = TargetHash
    # Leading to: Hash(P) = (TargetHash - Poly(S)) * inv(33^len(S))
    
    # We use fixed lengths for simplicity and robustness
    len_p = 6
    len_s = 6
    
    # Constant multiplier for the suffix length
    suffix_multiplier = pow(33, len_s, 2**32)
    inv_multiplier = mod_inv(suffix_multiplier, 2**32)
    
    prefix_map = {} # Map Hash(P) -> List[Prefix]
    found = set()
    found.add(target_key) # Don't output the key itself if we stumble upon it
    
    # 1. Fill Lookup Table (Prefixes)
    # 65536 is sqrt(2^32), statistically likely to find collisions with another set of 65536
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    # We generate a bit more than 65k to increase hit rate
    for _ in range(80000):
        p = "".join(random.choices(chars, k=len_p))
        h_p = djb2(p.encode('utf-8'))
        
        if h_p not in prefix_map:
            # We only store one prefix per hash to save memory, 
            # collisions in prefixes don't help us find *different* final hashes.
            prefix_map[h_p] = []
        prefix_map[h_p].append(p)
            
    if verbose:
        print(f"Table built. Searching for suffixes...")
    
    generated_count = 0
    
    # 2. Search (Suffixes)
    while generated_count < count:
        s = "".join(random.choices(chars, k=len_s))
        poly_s = djb2_poly(s.encode('utf-8'))
        
        # Calculate what prefix hash we need
        # result = (Target - Poly(S)) * inv_mult
        required_h_p = ((target_hash - poly_s) * inv_multiplier) & MOD_MASK
        
        if required_h_p in prefix_map:
            for p in prefix_map[required_h_p]:
                collision = p + s
                if collision not in found:
                    found.add(collision)
                    print(collision)
                    generated_count += 1
                    if generated_count >= count:
                        return

def main():
    parser = argparse.ArgumentParser(description="Generate DJB2 hash collisions for a target key.")
    parser.add_argument("key", help="The target key string")
    parser.add_argument("N", type=int, help="Number of colliding keys to generate")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print debug info")
    
    args = parser.parse_args()
    
    generate_collisions(args.key, args.N, args.verbose)

if __name__ == "__main__":
    main()
