// This file's extension implies that it's C, but it's really -*- C++ -*-.
/*
 * Copyright (C) 2002-2019 CERN for the benefit of the ATLAS collaboration.
 */
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: none (verbatim copy).
/**
 * @file CxxUtils/restrict.h
 * @author scott snyder <snyder@bnl.gov>
 * @date May, 2019
 * @brief Macro wrapping the nonstandard restrict keyword.
 *
 * Use the @c ATH_RESTRICT macro for the non-standard __restrict__ keyword.
 */


#ifndef CXXUTILS_RESTRICT_H
#define CXXUTILS_RESTRICT_H


#ifndef ATH_HAS_RESTRICT
# if defined(__GNUC__) || defined(__clang__)
#  define ATH_HAS_RESTRICT 1
# else
#  define ATH_HAS_RESTRICT 0
# endif
#endif


#if ATH_HAS_RESTRICT
# define ATH_RESTRICT __restrict__
#else
# define ATH_RESTRICT
#endif


#endif // not CXXUTILS_RESTRICT_H
