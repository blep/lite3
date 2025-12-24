# Hashing Algorithm

The B-tree implementation in `lite3` uses the **DJB2** hash algorithm for hashing keys.

## Implementation

The hashing logic is implemented in `include/lite3.h` as an inline function `lite3_get_key_data`.

```c
#define LITE3_DJB2_HASH_SEED ((uint32_t)5381)

static inline lite3_key_data lite3_get_key_data(const char *key) {
        lite3_key_data key_data;
        const char *key_cursor = key;
        key_data.hash = LITE3_DJB2_HASH_SEED;
        while (*key_cursor)
                key_data.hash = ((key_data.hash << 5) + key_data.hash) + (uint8_t)(*key_cursor++);
        key_data.size = (uint32_t)(key_cursor - key) + 1;
        return key_data;
}
```

## Formal Representation

The algorithm can be described as a state update function, where $H_i$ is the hash state after processing the $i$-th byte $m_i$ of the message $M$.

**Initialization:**
$$
H_0 = 5381
$$

**Compression Function:**
For each byte $m_i$ in the message:
$$
H_i = ((H_{i-1} \ll 5) + H_{i-1}) + m_i \pmod{2^{32}}
$$

Which is algebraically equivalent to:
$$
H_i = (33 \cdot H_{i-1} + m_i) \pmod{2^{32}}
$$

**Finalization:**
The final hash value is the state $H_n$ after processing all $n$ bytes of the key string (excluding the null terminator for the hash calculation loop in the provided code, though `size` includes it).

*Note: The implementation uses `uint32_t` arithmetic, implicitly enforcing the modulo $2^{32}$ operation.*

## Security Analysis

**DJB2 is not a cryptographic hash function.**

In security terminology, this function lacks **Preimage Resistance**, **Second-Preimage Resistance**, and **Collision Resistance**:

1.  **Preimage Vulnerability**: Given a hash value $h$, it is trivial to compute a string $s$ such that $H(s) = h$. Since the function is linear ($H(m) \approx 33 \cdot H + c$), the state is easily reversible for short inputs or calculable via algebra.
2.  **Collision Vulnerability**: It is computationally trivial to find two different strings $s_1$ and $s_2$ such that $H(s_1) = H(s_2)$.

Because the entire state is only 32 bits wide, the "Birthday Paradox" implies that you only need to hash approximately $\sqrt{2^{32}} \approx 65,536$ random keys to have a 50% chance of a collision. Targeted collisions can be generated even faster.

**Implication for Lite3**:
This hash function is designed for speed in a B-tree lookup, not for security. Usage with untrusted input keys could technically lead to **HashDos** (Hash Denial of Service) attacks, where an attacker intentionally provides keys that collide to degrade B-tree performance to $O(n)$ or fill hash buckets linearly. However, Lite3 mitigates this by handling collisions via linear probing or B-tree node splits, simply treating them as "full" nodes.

## Birthday Paradox Analysis

The vulnerability of a 32-bit hash function can be understood through the "Birthday Paradox". **This statistical probability applies to ANY 32-bit hash function, regardless of its quality or cryptographic strength.**

The question is effectively: *"How many keys must we hash before there is a 50% chance that two of them share the same hash?"*

We can approximate the probability of a collision $P(n)$ for $n$ random keys and $H$ possible hash values ($2^{32}$) using the following derivative:
$$
P(n) \approx 1 - e^{-\frac{n^2}{2H}}
$$

To find the number of keys $n$ required for a 50% probability ($P(n) = 0.5$):

$$
0.5 = 1 - e^{-\frac{n^2}{2 \cdot 2^{32}}}
$$
$$
0.5 = e^{-\frac{n^2}{2^{33}}}
$$
$$
\ln(0.5) = -\frac{n^2}{2^{33}}
$$
$$
0.693 \approx \frac{n^2}{8,589,934,592}
$$
$$
n \approx \sqrt{0.693 \times 8,589,934,592} \approx \sqrt{5,952,824,672} \approx 77,154
$$

Often in security research, the rough approximation $\sqrt{H}$ is used for the "birthday bound", as it represents the order of magnitude where collisions become likely.
$$
\sqrt{2^{32}} = \sqrt{4,294,967,296} = 65,536
$$

This explains why ~65,536 is cited as the threshold. At exactly 65,536 keys, the probability of collision is already substantial ($\approx 39\%$).

### Comparison with 64-bit Hashes
For comparison, a **64-bit** hash function would require approximately $\sqrt{2^{64}} = 2^{32} \approx 4.29$ billion keys to reach the same 50% collision probability.
*   **Computation**: rigorous hashing of 4 billion keys takes only seconds to minutes on a modern CPU.
*   **Storage**: Detecting these collisions requires storing the hashes, which takes approximately 32-64 GB of RAM.

While significantly stronger than 32-bit, a 64-bit hash is still considered vulnerable to collision attacks on modern hardware, which is why cryptographic standards typically use 256-bit or larger hashes (where the bound is $2^{128}$, an astronomically large number).

## Generating Targeted Collisions

A more severe vulnerability is the ease of generating **targeted collisions** (finding a *different* key that produces the *same* hash as a specific target key). This is often called a "Second Preimage Attack".

While brute-forcing a 32-bit integer is feasible (taking a few minutes on modern hardware), we can achieve this almost instantaneously using a **Meet-in-the-Middle** approach that exploits the linear nature of the DJB2 algorithm.

The hash function state update is: `h_next = (33 * h_prev) + char`. Thus, the hash of a concatenated string `Prefix + Suffix` can be expressed as:

$$
Hash(P + S) = Hash(P) \cdot 33^{len(S)} + Polynomial(S) \pmod{2^{32}}
$$

Where $Polynomial(S)$ is the hash of the suffix calculated with a starting seed of 0.

**Algorithm:**
1.  **Generate Prefixes**: Generate $2^{16}$ (~65k) random prefixes. Store their hashes in a lookup table: `{ Hash(P) : P }`.
2.  **Generate Suffixes**: Generate random suffixes $S$. For each, calculate the $RequiredPrefixHash$ that would result in the `TargetHash`:
    $$
    RequiredHash(P) = (TargetHash - Polynomial(S)) \cdot (33^{len(S)})^{-1} \pmod{2^{32}}
    $$
3.  **Match**: Check if $RequiredHash(P)$ exists in our lookup table. If it does, `P + S` is a valid collision.

This reduces the complexity from $2^{32}$ operations to roughly $\sqrt{2^{32}} = 2^{16}$ operations, making it instant.
