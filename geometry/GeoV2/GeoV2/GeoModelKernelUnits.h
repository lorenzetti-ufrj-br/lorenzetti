// Lorenzetti port (F41 conserto 29): the units of GeoModelKernel/Units.h (GeoModel 6.29.0) that the ported LArWheelCalculator uses,
// with the same definitions, so that the port does not depend on the optional GeoModel installation.
#ifndef GEOSPECIALSHAPES_GEOMODELKERNELUNITS_H
#define GEOSPECIALSHAPES_GEOMODELKERNELUNITS_H
namespace GeoModelKernelUnits {
  static constexpr double pi = 3.14159265358979323846;
  static constexpr double millimeter = 1.;
  static constexpr double centimeter = 10.*millimeter;
  static constexpr double mm = millimeter;
  static constexpr double cm = centimeter;
  static constexpr double radian = 1.;
  static constexpr double degree = (pi/180.0)*radian;
  static constexpr double deg = degree;
}
#endif
