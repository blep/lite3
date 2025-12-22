#ifndef MSVC_COMPAT_H
#define MSVC_COMPAT_H

/* MSVC does not support __attribute__((...)) syntax */
#define __attribute__(x)

/* GCC builtins shims */
#define __builtin_expect(x, y) (x)
#define __builtin_assume_aligned(x, y) (x)
#define __builtin_prefetch(...) /* Ignore prefetch */
#define __builtin_constant_p(x) 0

/* C99 restrict support */
#define restrict __restrict

#endif // MSVC_COMPAT_H
