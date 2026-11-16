// This file's extension implies that it's C, but it's really -*- C++ -*-.

/*
// Ported to Lorenzetti from Athena release 23.0.14 (Control/CxxUtils) for --atlas-emec-charge-collection (F41 conserto 29); changes: none (verbatim copy).
  Copyright (C) 2002-2019 CERN for the benefit of the ATLAS collaboration
*/

// $Id: sincos.h,v 1.1 2008-11-24 04:34:07 ssnyder Exp $

/**
 * @file CxxUtils/sincos.h
 * @author scott snyder
 * @date Nov 2008, from older D0 code.
 * @brief Helper to simultaneously calculate sin and cos of the same angle.
 */


#ifndef CXXUTILS_SINCOS_H
#define CXXUTILS_SINCOS_H


#include <cmath>


namespace CxxUtils {


/**
 * @brief Helper to simultaneously calculate sin and cos of the same angle.
 *
 * Instantiate an instance of this object, passing the angle to the
 * constructor.  The sin and cos are then available as the sn and cs
 * members.  In addition, the apply() method may be used to calculate
 * a*sin(x) + b*cos(x).
 *
 * Implementation notes:
 * 
 * The i386/x87 architecture has an instruction to do this.
 * So, on that platform, we use that instruction directly.
 * It seems to be a win to use it even if we're using SSE math,
 * so we'll use it for x86_64 too.
 * Otherwise, we'll use sincos() if it's available (it's a GNU extension).
 * Otherwise, just call sin() and cos() separately.
 *
 * Note that the fsincos instruction only works correctly
 * if the input angle is in the range -2^63 ... 2^63.
 * This is not likely to be an issue for us.
 *
 * Why prefer using the fsincos instruction directly to calling
 * the sincos() library function?
 *
 * - It turns out to be a little difficult to ensure that
 *   sincos()  actually gets inlined.  In general, one needs -ffast-math
 *   (which isn't on for standard Atlas builds), but even that's not always
 *   sufficient.
 *
 * - The library version includes extra code that we
 *   don't really need to handle the case where
 *   abs(angle) > 2^63.  (Runtime penalty, though, is
 *   moving the FPU status word to $eax and one
 *   taken branch.)
 *
 * - Most importantly, though, the library function
 *   takes pointers into which the results are stored.
 *   Playing with this, i was unable to prevent the
 *   calculated values from being spilled to memory.
 *   With the definition used below, we don't necessarily
 *   spill to memory.  A sequence like
 *
 *      sincos sc (ang);
 *      double a = sc.apply (x, y)
 *
 *   can be calculated entirely in the FPU register file,
 *   with no spills.
 */
struct sincos
{
  // cppcheck-suppress uninitMemberVar  ; false positive
  /// Calculate sine and cosine of x.
  sincos (double x)
#if defined(__GNUC__) && (defined(__i386__) || defined(__x86_64__))
  // Inline assembly version.  Uses x87 FPU.
  { __asm __volatile__ ("fsincos\n\t" : "=t" (cs), "=u" (sn) : "0" (x)); }
#elif defined(__USE_GNU)
  // Version using the GNU sincos() function.
  { ::sincos(x, &sn, &cs); }
#else
  // Generic version.
  : sn (std::sin (x)), cs (std::cos (x)) {}
#endif

  /// @f$\sin(x)@f$
  double sn;

  /// @f$\cos(x)@f$
  double cs;

  /// @f$a\sin(x) + b\cos(x)@f$
  double apply (double a, double b) const { return a*sn + b*cs; }

  /// @f$a\sin^2(x) + b\sin(x)\cos(x) + c\cos^2(x)@f$
  double apply2 (double a, double b, double c) const
  { return a*sn*sn + b*sn*cs + c*cs*cs; }
};


} // namespace CxxUtils


#endif //not CXXUTILS_SINCOS_H
