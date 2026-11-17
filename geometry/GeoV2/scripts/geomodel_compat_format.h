// <format> for building GeoModel 6.29 and the import of --atlas-run4 with gcc 11 (no std::format): std::format from the {fmt} library
// 10.2.1, headers only (F41 conserto 27). Installed as <prefix>/include/format by build_geomodel.sh.
#pragma once
#define FMT_HEADER_ONLY
#include <fmt/format.h>
namespace std { using fmt::format; using fmt::vformat; using fmt::make_format_args; using fmt::format_to; }
