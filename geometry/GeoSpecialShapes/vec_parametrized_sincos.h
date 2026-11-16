/*
  Copyright (C) 2002-2021 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes) for --atlas-emec-charge-collection (F41 conserto 29); changes: none (verbatim copy).

/**
  * @brief vectorized version of parametrized sincos
  * see ATLASSIM-4753 for details
  * @author Miha Muskinja, Chistos Anastopoulos
*/
#ifndef VEC_PARAMETRIZED_SINCOS_H
#define VEC_PARAMETRIZED_SINCOS_H

#include "CxxUtils/restrict.h"
#include "CxxUtils/vec.h"
struct vsincos_par
{

    CxxUtils::vec<double, 4> param_0 = {};
    CxxUtils::vec<double, 4> param_1 = {};
    CxxUtils::vec<double, 4> param_2 = {};

#if HAVE_FUNCTION_MULTIVERSIONING
#if defined(__x86_64__)

    __attribute__((target("avx2,fma")))

    void
    evaluate(const double r,
             double &ATH_RESTRICT sin_a,
             double &ATH_RESTRICT cos_a) const ATH_RESTRICT
    {
        const double r2 = r * r;
        CxxUtils::vec<double, 4> P = r2 * param_0 + param_1;
        P = r2 * P + param_2;
        CxxUtils::vec<double, 4> P2 = {P[1], P[0], P[3], P[2]};
        CxxUtils::vec<double, 4> res = r * P2 + P;
        sin_a = res[0];
        cos_a = res[2];
    }

    __attribute__((target("avx2")))

    void
    eval(const double r,
         double &ATH_RESTRICT sin_a,
         double &ATH_RESTRICT cos_a) const ATH_RESTRICT
    {
        const double r2 = r * r;
        CxxUtils::vec<double, 4> P = r2 * param_0 + param_1;
        P = r2 * P + param_2;
        CxxUtils::vec<double, 4> P2 = {P[1], P[0], P[3], P[2]};
        CxxUtils::vec<double, 4> res = r * P2 + P;
        sin_a = res[0];
        cos_a = res[2];
    }

    __attribute__((target("default")))

#endif // x86
#endif // FMV

    void
    eval(const double r,
         double &ATH_RESTRICT sin_a,
         double &ATH_RESTRICT cos_a) const ATH_RESTRICT
    {
        const double r2 = r * r;
        CxxUtils::vec<double, 4> P = r2 * param_0 + param_1;
        P = r2 * P + param_2;
        sin_a = r * P[1] + P[0];
        cos_a = r * P[3] + P[2];
    }
};

#endif
