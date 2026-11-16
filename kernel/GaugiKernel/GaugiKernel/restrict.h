/*
 * Copyright (C) 2002-2019 CERN for the benefit of the ATLAS collaboration.
 * Adapted for Lorenzetti / GaugiKernel
 */
#ifndef GAUGI_RESTRICT_H
#define GAUGI_RESTRICT_H

#ifndef GAUGI_HAS_RESTRICT
# if defined(__GNUC__) || defined(__clang__)
#  define GAUGI_HAS_RESTRICT 1
# else
#  define GAUGI_HAS_RESTRICT 0
# endif
#endif

#if GAUGI_HAS_RESTRICT
# define GAUGI_RESTRICT __restrict__
#else
# define GAUGI_RESTRICT
#endif

// Backward-compatibility macro for Athena ported components
#ifndef ATH_RESTRICT
# define ATH_RESTRICT GAUGI_RESTRICT
#endif

#endif // not GAUGI_RESTRICT_H
