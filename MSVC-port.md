# MSVC Portability Report

This document details the source code modifications applied to the `lite3` library to enable native compilation with Microsoft Visual C++ (MSVC). The changes are listed from most complex to trivial.

## 1. Removing GCC Statement Expressions (Complex)

### The Problem
The original codebase relied heavily on **GCC statement expressions** (a GNU extension) in its public API macros. This feature allows compound statements to be used as expressions, returning the value of the last statement.

**Original Code (incompatible with MSVC):**
```c
#define lite3_set_str_n(buf, ..., str, str_len) ({ \
    const char *__lite3_key__ = (key); \
    _lite3_set_str_n_impl(buf, ..., __lite3_key__, ...); \
})
```

MSVC does not support this extension, causing syntax errors.

### The Solution
We refactored these macros into standard C `static inline` functions. This required two distinct approaches depending on the macro's complexity:

**A. Simple Macros (Direct Replacement)**
For macros that simply wrapped an implementation call, we essentially replaced the statement expression with a direct inline function call or a standard C macro expansion.

**B. Complex Macros with Validation (Wrapper Functions)**
For macros that performed inline verification (e.g., checking return values before proceeding), we introduced a compatibility wrapper function.

**New Code (Portable):**
```c
#if defined(__GNUC__) || defined(__clang__)
    // Original GCC implementation preserved for backward compatibility/optimization
    #define lite3_set_str_n(...) ({ ... })
#else
    // MSVC / Standard C fallback
    #define lite3_set_str_n(buf, ..., key, ...) \
        _lite3_set_str_n_impl(buf, ..., key, lite3_get_key_data(key), ...)
#endif
```
For more complex control flow (like `lite3_set_obj`), we created static inline `_compat` functions to encapsulate the logic that was previously inside the statement expression.

---

## 2. Variable Declarations in Switch Cases (Moderate)

### The Problem
In `src/json_dec.c`, several `switch` statements declared variables immediately after a `case` label.

**Original Code:**
```c
switch (type) {
    case LITE3_TYPE_STRING:
        const char *str = ...; // Error in C89 / MSVC
        // ...
        break;
]
```

According to the C standard (specifically C89/C90, which MSVC historically adhered to strictly), declarations are not allowed immediately after a label; they must be the start of a compound statement (block).

### The Solution
We enclosed the logic of these cases within braces `{}` to create a new scope.

**New Code:**
```c
switch (type) {
    case LITE3_TYPE_STRING: { 
        const char *str = ...; // OK
        // ...
        break;
    }
}
```

---

## 3. Forward Declarations (Trivial)

### The Problem
The refactoring in Step 1 introduced new inline functions in `lite3.h` that made calls to internal implementation functions (e.g., `lite3_set_obj_impl`). With the structural changes, these implementation functions were being called before they were explicitly declared in the compilation unit (or the implicit declaration warning was triggered).

### The Solution
We added explicit forward declarations for these internal verification and implementation functions at the point of use or correctly ordered in the header file.

```c
extern int lite3_set_obj_impl(...); // Forward declaration added
return lite3_set_obj_impl(...);
```

---

## 4. Compiler Builtins and Attributes (Trivial)

### The Problem
The codebase used GCC-specific attributes and builtins not present in MSVC:
*   `__attribute__((always_inline))`
*   `__builtin_expect`
*   `__restrict` (MSVC uses `__restrict` but context varies)
*   `__builtin_constant_p`

### The Solution
We added a compatibility block at the top of `include/lite3.h` to shim these macros when compiling with MSVC (`_MSC_VER`).

```c
#if defined(_MSC_VER) && !defined(__clang__)
#define __attribute__(x)          /* No-op */
#define __builtin_expect(x, v)    (x)
#define __restrict                __restrict
#define __builtin_constant_p(x)   0
#endif
```
