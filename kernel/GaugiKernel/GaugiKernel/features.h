/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
  Adapted for Lorenzetti / GaugiKernel
*/
#ifndef GAUGI_FEATURES_H
#define GAUGI_FEATURES_H

#include <features.h>

/// Do we support the compatible set of GCC and clang extensions
#if (defined(__GNUC__) || defined(__clang__)) &&      \
     !(defined(__ICC) || defined(__COVERITY__) ||     \
       defined(__CUDACC__) || defined(__CLING__))
# define HAVE_GCC_CLANG_EXTENSIONS 1
#else
# define HAVE_GCC_CLANG_EXTENSIONS 0
#endif

/// Do we have function multiversioning?
#if HAVE_GCC_CLANG_EXTENSIONS &&                                     \
  (defined(__i386__) || defined(__x86_64__)) && defined(__ELF__) &&  \
  !defined(__HIP__) && !defined(CL_SYCL_LANGUAGE_VERSION) &&         \
  !defined(SYCL_LANGUAGE_VERSION)
#define HAVE_FUNCTION_MULTIVERSIONING 1
#else
# define HAVE_FUNCTION_MULTIVERSIONING 0
#endif

/// Do we additionally have the target_clones attribute?
#if HAVE_FUNCTION_MULTIVERSIONING && !(defined(__clang__) && __clang_major__ < 14)
# define HAVE_TARGET_CLONES 1
#else
# define HAVE_TARGET_CLONES 0
#endif

/// Do we have support for all GCC intrinsics?
#if HAVE_GCC_CLANG_EXTENSIONS && !defined(__clang__)
# define HAVE_GCC_INTRINSICS 1
#else
# define HAVE_GCC_INTRINSICS 0
#endif

/// Do we have the bit-counting intrinsics?
#if HAVE_GCC_CLANG_EXTENSIONS
# define HAVE_BITCOUNT_INTRINSICS 1
#else
# define HAVE_BITCOUNT_INTRINSICS 0
#endif

// Do we have the vector_size attribute for writing explicitly vectorized code?
#if HAVE_GCC_CLANG_EXTENSIONS || defined(__CLING__)
# define HAVE_VECTOR_SIZE_ATTRIBUTE 1
#else
# define HAVE_VECTOR_SIZE_ATTRIBUTE 0
#endif

// Do we additionally support the clang __builtin_convertvector
#if HAVE_VECTOR_SIZE_ATTRIBUTE && (defined(__clang__) || (__GNUC__ >= 9))
# define HAVE_CONVERT_VECTOR 1
#else
# define HAVE_CONVERT_VECTOR 0
#endif

// Do we have mallinfo2?
#if defined(__GLIBC__) && __GLIBC_PREREQ(2, 33)
# define HAVE_MALLINFO2 1
#else
# define HAVE_MALLINFO2 0
#endif

// Do we have malloc hooks?
#if defined(__GLIBC__) && !__GLIBC_PREREQ(2, 34)
# define HAVE_MALLOC_HOOKS 1
#else
# define HAVE_MALLOC_HOOKS 0
#endif

#endif // not GAUGI_FEATURES_H
