// This file's extension implies that it's C, but it's really -*- C++ -*-.
/*
 * Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration.
 */
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: none (verbatim copy).
/**
 * @file CxxUtils/vec.h
 * @author scott snyder <snyder@bnl.gov>
 * @author Christos Anastopoulos (additional helper methods)
 * @date Mar, 2020
 * @brief Vectorization helpers.
 *
 * gcc and clang provide built-in types for writing vectorized code,
 * using the vector_size attribute.  This usually results in code
 * that is much easier to read and more portable than one would get
 * using intrinsics directly.  However, it is still non-standard,
 * and there are some operations which are kind of awkward.
 *
 * This file provides some helpers for writing vectorized code
 * in C++.
 *
 * A vectorized type may be named as @c CxxUtils::vec<T, N>.  Here @c T is the
 * element type, which should be an elementary integer or floating-point type.
 * @c N is the number of elements in the vector; it should be a power of 2.
 * This will either be a built-in vector type if the @c vector_size
 * attribute is supported or a fallback C++ class intended to be
 * (mostly) functionally equivalent (see vec_fb.h)
 *
 *
 * The GCC, clang and fallback vector types support:
 * ++, --, +,-,*,/,%, =, &,|,^,~, >>,<<, !, &&, ||,
 * ==, !=, >, <, >=, <=, =, sizeof and Initialization from brace-enclosed lists
 *
 * Furthermore the GCC and clang vector types support the ternary operator.
 *
 * We also support some additional operations.
 *
 * Deducing useful types:
 *
 *  - @c CxxUtils::vec_type_t<VEC> is the element type of @c VEC.
 *  - @c CxxUtils::vec_mask_type_t<VEC> is the vector type return by relational
 *                                  operations.
 *
 * Deducing the num of elements in a vectorized type:
 *
 *  - @c CxxUtils::vec_size<VEC>() is the number of elements in @c VEC.
 *  - @c CxxUtils::vec_size(const VEC&) is the number of elements in @c VEC.
 *
 * Additional Helpers for common SIMD operations:
 *
 *  - @c CxxUtils::vbroadcast (VEC& v, T x) initializes each element of
 *                                          @c v with @c x.
 *  - @c CxxUtils::vload (VEC& dst, const vec_type_t<VEC>* src)
 *                                          loads elements from @c src
 *                                          to @c dst
 *  - @c CxxUtils::vstore (vec_type_t<VEC>* dst, const VEC& src)
 *                                          stores elements from @c src
 *                                          to @c dst
 *  - @c CxxUtils::vselect (VEC& dst, const VEC& a, const VEC& b, const
 *                          vec_mask_type_t<VEC>& mask) copies elements
 *                          from @c a or @c b, depending
 *                          on the value of @c  mask to @c dst.
 *                          dst[i] = mask[i] ? a[i] : b[i]
 *  - @c CxxUtils::vmin    (VEC& dst, const VEC& a, const VEC& b)
 *                         copies to @c dst[i]  the min(a[i],b[i])
 *  - @c CxxUtils::vmax    (VEC& dst, const VEC& a, const VEC& b)
 *                         copies to @c dst[i]  the max(a[i],b[i])
 *  - @c CxxUtils::vconvert (VEC1& dst, const VEC2& src)
 *                          Fills @c dst with the result  of a
 *                          static_cast of every element of @c src
 *                          to the element type of dst.
 *                          dst[i] = static_cast<vec_type_t<VEC1>>(src[i])
 *
 *  Functions that construct a permutation of elements from one or two vectors
 *  and return a vector of the same type as the input vector(s).
 *  The mask has the same element count  as the vectors.
 *  Intentionally kept compatible with gcc's _builtin_shuffle.
 *  If we move to gcc>=12 we could unify with clang's _builtin_shuffle_vector
 *  and relax some of these requirements
 *
 *  - @c CxxUtils::vpermute<mask> (VEC& dst, const VEC& src)
 *                          Fills dst with permutation of src
 *                          according to mask.
 *                          @c mask is a list of integers that specifies the elements
 *                          that should be extracted and returned in @c src.
 *                          dst[i] = src[mask[i]] where mask[i] is the ith integer
 *                          in the @c mask.
 *
 *  - @c CxxUtils::vpermute2<mask> (VEC& dst, const VEC& src1,const VEC& src2)
 *                          Fills @c dst with permutation of @c src1 and @c src2
 *                          according to @c mask.
 *                          @c mask is a list of integers that specifies the elements
 *                          that should be extracted from @c src1 and @c src2.
 *                          An index i in the interval [0,N) indicates that element number i
 *                          from the first input vector should be placed in the
 *                          corresponding position in the result vector.
 *                          An index in the interval [N,2N)
 *                          indicates that the element number i-N
 *                          from the second input vector should be placed
 *                          in the corresponding position in the result vector.
 *
 * In terms of expected performance it might be  advantageous to
 * use vector types that fit the size of the ISA.
 * e.g 128 bit wide for SSE, 256 wide for AVX.
 *
 * Specifying a combination that is not valid for the current architecture
 * causes the compiler to synthesize the instructions using a narrower mode.
 *
 * Consider using Function Multiversioning (CxxUtils/features.h)
 * if you really need to target efficiently multiple ISAs.
 */

#ifndef CXXUTILS_VEC_H
#define CXXUTILS_VEC_H

#include "CxxUtils/features.h"
#include <cstdlib>
#include <cstring>
#include <type_traits>


// Define @c WANT_VECTOR_FALLBACK prior to including this file to
// make the fallback class @c vec_fb visible, even if we support the
// built-in type.
// Intended for testing.
#ifndef WANT_VECTOR_FALLBACK
# define WANT_VECTOR_FALLBACK 0
#endif

#if (!HAVE_VECTOR_SIZE_ATTRIBUTE) || WANT_VECTOR_FALLBACK!=0
#include "CxxUtils/vec_fb.h"
#endif // !HAVE_VECTOR_SIZE_ATTRIBUTE || WANT_VECTOR_FALLBACK

namespace CxxUtils {


/**
 * @brief check the type and the size  of the vector.
 * Choose between the built-in (if available or
 * fallback type.
 */
template <typename T, size_t N>
struct vec_typedef{
   static_assert((N & (N-1)) == 0, "N must be a power of 2.");
   static_assert(std::is_arithmetic_v<T>, "T not an arithmetic type");

#if HAVE_VECTOR_SIZE_ATTRIBUTE

   using type  __attribute__ ((vector_size(N*sizeof(T)))) = T;

#else

   using type vec_fb<T, N>;

#endif
};

/**
 * @brief Define a nice alias for the vectorized type
 */
template <typename T, size_t N>
using vec = typename vec_typedef<T,N>::type;

/**
 * @brief Deduce the element type from a vectorized type.
 */
template <class VEC>
struct vec_type
{
  // Requires c++20.
  //typedef typename std::invoke_result< decltype([](const VEC& v){return v[0];}), VEC& >::type type;

  // Works in c++17.
  static auto elt (const VEC& v) -> decltype( v[0] );
  typedef typename std::invoke_result< decltype(elt), const VEC& >::type type1;
  typedef std::remove_cv_t<std::remove_reference_t<type1> > type;
};

/**
 * @brief Define a nice alias for the element type of a vectorized type
 */
template<class VEC>
using vec_type_t = typename vec_type<VEC>::type;

/**
 * @brief Deduce the type of the mask returned by relational operations,
 * for a vectorized type.
 */
template<class VEC>
struct vec_mask_type
{
  static auto maskt(const VEC& v1, const VEC& v2) -> decltype(v1 < v2);
  typedef
    typename std::invoke_result<decltype(maskt), const VEC&, const VEC&>::type type1;
  typedef std::remove_cv_t<std::remove_reference_t<type1>> type;
};

/**
 * @brief Define a nice alias for the mask type for a vectorized type.
 */
template<class VEC>
using vec_mask_type_t = typename vec_mask_type<VEC>::type;

/**
 * @brief Return the number of elements in a vectorized type.
 */
template<class VEC>
inline constexpr size_t
vec_size()
{
  typedef vec_type_t<VEC> ELT;
  return sizeof(VEC) / sizeof(ELT);
}

/**
 * @brief Return the number of elements in a vectorized type.
 */
template<class VEC>
inline constexpr size_t
vec_size(const VEC&)
{
  typedef vec_type_t<VEC> ELT;
  return sizeof(VEC) / sizeof(ELT);
}

/**
 * @brief Copy a scalar to each element of a vectorized type.
 */
template<typename VEC, typename T>
inline void
vbroadcast(VEC& v, T x)
{
#if !HAVE_VECTOR_SIZE_ATTRIBUTE || WANT_VECTOR_FALLBACK
  constexpr size_t N = CxxUtils::vec_size<VEC>();
  for (size_t i = 0; i < N; ++i) {
    v[i] = x;
  }
#else
  // using  - to avoid sign conversions.
  v = x - VEC{ 0 };
#endif
}

/*
 * @brief load elements from  memory address src (C-array)
 * to a vectorized type dst.
 * Used memcpy to avoid alignment issues
 */
template<typename VEC>
inline void
vload(VEC& dst, vec_type_t<VEC> const* src)
{
  std::memcpy(&dst, src, sizeof(VEC));
}

/*
 * @brief store elements from a vectorized type src to
 * to a memory address dst (C-array).
 * Uses memcpy to avoid alignment issues
 */
template<typename VEC>
inline void
vstore(vec_type_t<VEC>* dst, const VEC& src)
{
  std::memcpy(dst, &src, sizeof(VEC));
}

/*
 * @brief select elements based on a mask
 * Fill dst according to
 * dst[i] = mask[i] ? a[i] : b[i]
 */
template<typename VEC>
inline void
vselect(VEC& dst, const VEC& a, const VEC& b, const vec_mask_type_t<VEC>& mask)
{
#if !HAVE_VECTOR_SIZE_ATTRIBUTE || WANT_VECTOR_FALLBACK
  constexpr size_t N = vec_size<VEC>();
  for (size_t i = 0; i < N; ++i) {
    dst[i] = mask[i] ? a[i] : b[i];
  }
#else
  dst = mask ? a : b;
#endif
}

/*
 * @brief vectorized min.
 * copies to @c dst[i]  the min(a[i],b[i])
 */
template<typename VEC>
inline void
vmin(VEC& dst, const VEC& a, const VEC& b)
{
#if !HAVE_VECTOR_SIZE_ATTRIBUTE || WANT_VECTOR_FALLBACK
  constexpr size_t N = vec_size<VEC>();
  for (size_t i = 0; i < N; ++i) {
    dst[i] = a[i] < b[i] ? a[i] : b[i];
  }
#else
  dst = a < b ? a : b;
#endif
}

/*
 * @brief vectorized max.
 * copies to @c dst[i]  the max(a[i],b[i])
 */
template<typename VEC>
inline void
vmax(VEC& dst, const VEC& a, const VEC& b)
{
#if !HAVE_VECTOR_SIZE_ATTRIBUTE || WANT_VECTOR_FALLBACK
  constexpr size_t N = vec_size<VEC>();
  for (size_t i = 0; i < N; ++i) {
    dst[i] = a[i] > b[i] ? a[i] : b[i];
  }
#else
  dst = a > b ? a : b;
#endif
}

template<typename VEC1, typename VEC2>
inline void
vconvert(VEC1& dst, const VEC2& src)
{
  static_assert((vec_size<VEC1>() == vec_size<VEC2>()),
                "vconvert dst and src have different number of elements");

#if !HAVE_CONVERT_VECTOR || WANT_VECTOR_FALLBACK
  typedef vec_type_t<VEC1> ELT;
  constexpr size_t N = vec_size<VEC1>();
  for (size_t i = 0; i < N; ++i) {
    dst[i] = static_cast<ELT>(src[i]);
  }
#else
  dst = __builtin_convertvector(src, VEC1);
#endif
}

/**
 * @brief Helper for static asserts for argument packs
 */
namespace bool_pack_helper {
template<bool...>
struct bool_pack;
template<bool... bs>
using all_true = std::is_same<bool_pack<bs..., true>, bool_pack<true, bs...>>;
}
/**
 * @brief vpermute function.
 * move any element of a vector src
 * into any or multiple position inside dst.
 */
template<size_t... Indices, typename VEC>
inline void
vpermute(VEC& dst, const VEC& src)
{

  constexpr size_t N = vec_size<VEC>();
  static_assert((sizeof...(Indices) == N),
                "vpermute number of indices different than vector size");
  static_assert(
    bool_pack_helper::all_true<(Indices >= 0 && Indices < N)...>::value,
    "vpermute value of a mask index is outside the allowed range");

#if !HAVE_VECTOR_SIZE_ATTRIBUTE || WANT_VECTOR_FALLBACK
  dst = VEC{ src[Indices]... };
#elif defined(__clang__)
  dst = __builtin_shufflevector(src, src, Indices...);
#else // gcc
  dst = __builtin_shuffle(src, vec_mask_type_t<VEC>{ Indices... });
#endif
}

/**
 * @brief vpermute2 function.
 * move any element of the vectors src1, src2
 * into any or multiple position inside dst.
 */
template<size_t... Indices, typename VEC>
inline void
vpermute2(VEC& dst, const VEC& src1, const VEC& src2)
{
  constexpr size_t N = vec_size<VEC>();
  static_assert(
    (sizeof...(Indices) == N),
    "vpermute2 number of indices different than vector size");
  static_assert(
    bool_pack_helper::all_true<(Indices >= 0 && Indices < 2 * N)...>::value,
    "vpermute2 value of a mask index is outside the allowed range");

#if !HAVE_VECTOR_SIZE_ATTRIBUTE || WANT_VECTOR_FALLBACK
  VEC tmp;
  size_t pos{0};
  for (auto index: { Indices... }) {
    if (index < N) {
      tmp[pos] = src1[index];
    } else {
      tmp[pos] = src2[index - N];
    }
    ++pos;
  }
  dst = tmp;
#elif defined(__clang__)
  dst = __builtin_shufflevector(src1, src2, Indices...);
#else // gcc
  dst = __builtin_shuffle(src1, src2, vec_mask_type_t<VEC>{ Indices... });
#endif
}


} // namespace CxxUtils

#endif // not CXXUTILS_VEC_H
