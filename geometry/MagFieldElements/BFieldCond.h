/*
  Copyright (C) 2002-2020 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: Eigen (EventPrimitives/EventPrimitives.h) replaced by the minimal local 3-vector BFieldCondMath::Vector3d below, which reproduces the Eigen 3.3.7 arithmetic used here (element-wise ops, cross, dot and squaredNorm summed as (x0+x1)+x2, norm = sqrt(squaredNorm), normalized = v/sqrt(squaredNorm)); <algorithm> added for std::max (previously reached through Eigen).

//
// BFieldCond.h
//
// Current conductors used in BFieldZone.
// It may be finite : p1 to p2.
// It may be infinite : passing p1 and direction parallel to p2.
//
// Masahiro Morii, Harvard University
//
#ifndef BFIELDCOND_H
#define BFIELDCOND_H

#include <algorithm>
#include <cmath>

// Minimal replacement for the Eigen types used by BFieldCond (port to
// Lorenzetti, no Eigen dependency). Every operation is evaluated element by
// element exactly as Eigen 3.3.7 (the version of Athena 23.0.14) evaluates it
// for fixed-size 3-vectors of double with SSE2: the reductions (dot,
// squaredNorm) are computed as (x0 + x1) + x2, i.e. one 2-wide packet for
// elements 0,1 followed by the scalar tail element 2.
namespace BFieldCondMath {

struct Vector3d
{
  double m_v[3];

  Vector3d() = default;
  Vector3d(double x, double y, double z)
    : m_v{ x, y, z }
  {}
  // equivalent of Eigen::Map<const Eigen::Vector3d>(p)
  explicit Vector3d(const double* p)
    : m_v{ p[0], p[1], p[2] }
  {}

  double operator()(int i) const { return m_v[i]; }
  double operator[](int i) const { return m_v[i]; }

  // Eigen::MatrixBase::squaredNorm (cwiseAbs2().sum())
  double squaredNorm() const
  {
    return (m_v[0] * m_v[0] + m_v[1] * m_v[1]) + m_v[2] * m_v[2];
  }
  // Eigen::MatrixBase::norm = sqrt(squaredNorm())
  double norm() const { return std::sqrt(squaredNorm()); }
  // Eigen::MatrixBase::normalized
  Vector3d normalized() const
  {
    const double z = squaredNorm();
    if (z > 0.0) {
      const double n = std::sqrt(z);
      return Vector3d(m_v[0] / n, m_v[1] / n, m_v[2] / n);
    }
    return *this;
  }
  // Eigen::MatrixBase::dot (binaryExpr<conj_prod>().sum())
  double dot(const Vector3d& o) const
  {
    return (m_v[0] * o.m_v[0] + m_v[1] * o.m_v[1]) + m_v[2] * o.m_v[2];
  }
  // Eigen::MatrixBase::cross (Eigen/src/Geometry/OrthoMethods.h)
  Vector3d cross(const Vector3d& o) const
  {
    return Vector3d(m_v[1] * o.m_v[2] - m_v[2] * o.m_v[1],
                    m_v[2] * o.m_v[0] - m_v[0] * o.m_v[2],
                    m_v[0] * o.m_v[1] - m_v[1] * o.m_v[0]);
  }
  Vector3d& operator+=(const Vector3d& o)
  {
    m_v[0] += o.m_v[0];
    m_v[1] += o.m_v[1];
    m_v[2] += o.m_v[2];
    return *this;
  }
};

inline Vector3d
operator+(const Vector3d& a, const Vector3d& b)
{
  return Vector3d(a.m_v[0] + b.m_v[0], a.m_v[1] + b.m_v[1], a.m_v[2] + b.m_v[2]);
}
inline Vector3d
operator-(const Vector3d& a, const Vector3d& b)
{
  return Vector3d(a.m_v[0] - b.m_v[0], a.m_v[1] - b.m_v[1], a.m_v[2] - b.m_v[2]);
}
// scalar * vector (Eigen: scalar_product_op, s * v_i)
inline Vector3d
operator*(double s, const Vector3d& a)
{
  return Vector3d(s * a.m_v[0], s * a.m_v[1], s * a.m_v[2]);
}
// vector * scalar (Eigen: v_i * s)
inline Vector3d
operator*(const Vector3d& a, double s)
{
  return Vector3d(a.m_v[0] * s, a.m_v[1] * s, a.m_v[2] * s);
}
// vector / scalar (Eigen: scalar_quotient_op, v_i / s, no reciprocal)
inline Vector3d
operator/(const Vector3d& a, double s)
{
  return Vector3d(a.m_v[0] / s, a.m_v[1] / s, a.m_v[2] / s);
}

// equivalent of Eigen::Map<Eigen::Vector3d>(p): writes through to p
struct Vector3dMap
{
  double* m_p;
  explicit Vector3dMap(double* p)
    : m_p(p)
  {}
  Vector3dMap& operator+=(const Vector3d& o)
  {
    m_p[0] += o.m_v[0];
    m_p[1] += o.m_v[1];
    m_p[2] += o.m_v[2];
    return *this;
  }
};

// equivalent of Eigen::Map<Eigen::Matrix<double, 3, 3, Eigen::RowMajor>>(p)
struct RowMajorMatrix3Map
{
  double* m_p;
  explicit RowMajorMatrix3Map(double* p)
    : m_p(p)
  {}
  double& operator()(int i, int j) { return m_p[3 * i + j]; }
  // equivalent of D += v * w.transpose(): D(i,j) += v(i) * w(j)
  void addOuterProduct(const Vector3d& v, const Vector3d& w)
  {
    for (int i = 0; i < 3; ++i) {
      for (int j = 0; j < 3; ++j) {
        m_p[3 * i + j] += v.m_v[i] * w.m_v[j];
      }
    }
  }
};

} // namespace BFieldCondMath

class BFieldCond
{
public:
  // constructor
  BFieldCond(bool finite,
             const double* p1,
             const double* p2,
             double curr)
    : m_finite(finite)
    , m_p1(BFieldCondMath::Vector3d(p1))
    , m_p2(BFieldCondMath::Vector3d(p2))
    , m_u(finite ? (m_p2 - m_p1).normalized() : m_p2)
    , m_curr(curr)
    , m_nomCurr(curr)
  {}

  // compute magnetic field, plus derivatives if requested, and add
  void addBiotSavart(double scaleFactor,
                     const double* ATH_RESTRICT xyz,
                     double* ATH_RESTRICT B,
                     double* ATH_RESTRICT deriv = nullptr) const;
  // scale the current wrt the nominal current
  void scaleCurrent(double factor) { m_curr = factor * m_nomCurr; }
  // accessors
  bool finite() const { return m_finite; }
  double p1(int i) const { return m_p1[i]; }
  double p2(int i) const { return m_p2[i]; }
  double curr() const { return m_curr; }

private:
  bool m_finite; // true if the conductor is finite in length

  /*
   * m_p1: One end of a finite conductor, or one point on an infinite conductor
   * m_p2: The other end of a finite conductor, or the direction vector of an
   * infinite conductor m_u : Direction vector (= m_p2 if infinite)
   */
  const BFieldCondMath::Vector3d m_p1, m_p2, m_u;
  double m_curr;    // current (in A) flowing through the conductor
  double m_nomCurr; // nominal current (in A) read from the map file
};
#include "BFieldCond.icc"
#endif
