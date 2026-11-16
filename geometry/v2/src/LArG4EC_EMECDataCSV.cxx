// Lorenzetti port (F41 conserto 29): see LArG4EC/EMECDataCSV.h. The numbers are read with strtod from the text that
// emec_tables_from_geomdb.py writes (Python repr, the shortest decimal that gives back the same double).
#include "LArG4EC/EMECDataCSV.h"
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <vector>

EMECData readEMECDataCSV(const std::string &path)
{
  std::ifstream in(path);
  if(!in) throw std::runtime_error("readEMECDataCSV: cannot open " + path);
  EMECData data;
  std::string line;
  std::getline(in, line); // header
  while(std::getline(in, line)){
    if(!line.empty() && line.back() == '\r') line.pop_back(); // the csv module of Python ends the lines with CR LF
    if(line.empty()) continue;
    std::vector<std::string> f;
    std::stringstream ss(line); std::string item;
    while(std::getline(ss, item, ',')) f.push_back(item);
    if(f.size() != 5) throw std::runtime_error("readEMECDataCSV: bad line " + line);
    const std::string &table = f[0], &column = f[3], &value = f[4];
    const int row = std::atoi(f[2].c_str());
    if(table == "EmecGeometry"){
      auto &v = data.emecgeometry; if((int)v.size() <= row) v.resize(row + 1);
      if(column == "EFIELD") { v[row].EFIELD = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "MLGAP") { v[row].MLGAP = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "SABL") { v[row].SABL = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "SBAR") { v[row].SBAR = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "SBRN") { v[row].SBRN = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "SCRB") { v[row].SCRB = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "Z1") { v[row].Z1 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "Z0") { v[row].Z0 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DCF") { v[row].DCF = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "RLIMIT") { v[row].RLIMIT = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "EPS") { v[row].EPS = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "RHOIN") { v[row].RHOIN = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "RCKP") { v[row].RCKP = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ETOT") { v[row].ETOT = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "EKAP") { v[row].EKAP = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ECU") { v[row].ECU = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "EPREP") { v[row].EPREP = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "EINOX") { v[row].EINOX = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "NLAYER") { v[row].NLAYER = std::atoi(value.c_str()); continue; }
      if(column == "RMIN") { v[row].RMIN = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "RMAX") { v[row].RMAX = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DZENDE") { v[row].DZENDE = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ZORIG") { v[row].ZORIG = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DCRACK") { v[row].DCRACK = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DZPLA") { v[row].DZPLA = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DZDSE") { v[row].DZDSE = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DZDSM") { v[row].DZDSM = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DZDSI") { v[row].DZDSI = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "NUREG") { v[row].NUREG = std::atoi(value.c_str()); continue; }
      if(column == "DETA_0") { v[row].DETA_0 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DETA_1") { v[row].DETA_1 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DETA_2") { v[row].DETA_2 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DETA_3") { v[row].DETA_3 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DETA_4") { v[row].DETA_4 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DETA_5") { v[row].DETA_5 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DETA_6") { v[row].DETA_6 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DETA_7") { v[row].DETA_7 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DETA_8") { v[row].DETA_8 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DETA_9") { v[row].DETA_9 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DETA_10") { v[row].DETA_10 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DPHI_0") { v[row].DPHI_0 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DPHI_1") { v[row].DPHI_1 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DPHI_2") { v[row].DPHI_2 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DPHI_3") { v[row].DPHI_3 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DPHI_4") { v[row].DPHI_4 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DPHI_5") { v[row].DPHI_5 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DPHI_6") { v[row].DPHI_6 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DPHI_7") { v[row].DPHI_7 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DPHI_8") { v[row].DPHI_8 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DPHI_9") { v[row].DPHI_9 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "DPHI_10") { v[row].DPHI_10 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ETASTR_0") { v[row].ETASTR_0 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ETASTR_1") { v[row].ETASTR_1 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ETASTR_2") { v[row].ETASTR_2 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ETASTR_3") { v[row].ETASTR_3 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ETASTR_4") { v[row].ETASTR_4 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ETASTR_5") { v[row].ETASTR_5 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ETASTR_6") { v[row].ETASTR_6 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "EMHIT") { v[row].EMHIT = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "EMDIGI") { v[row].EMDIGI = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "GAP0") { v[row].GAP0 = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ZSHIFT") { v[row].ZSHIFT = std::strtod(value.c_str(), nullptr); continue; }
      continue;
    }
    if(table == "EmecParams"){
      auto &v = data.emecparams; if((int)v.size() <= row) v.resize(row + 1);
      if(column == "PHIROTATION") { v[row].PHIROTATION = value; continue; }
      if(column == "SAGGING") { v[row].SAGGING = value; continue; }
      if(column == "INNERSLANTPARAM") { v[row].INNERSLANTPARAM = value; continue; }
      if(column == "OUTERSLANTPARAM") { v[row].OUTERSLANTPARAM = value; continue; }
      continue;
    }
    if(table == "EmecWheelParameters"){
      auto &v = data.emecwheelparameters; if((int)v.size() <= row) v.resize(row + 1);
      if(column == "IWHEEL") { v[row].IWHEEL = std::atoi(value.c_str()); continue; }
      if(column == "NABS") { v[row].NABS = std::atoi(value.c_str()); continue; }
      if(column == "NACC") { v[row].NACC = std::atoi(value.c_str()); continue; }
      if(column == "ETAINT") { v[row].ETAINT = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ETAEXT") { v[row].ETAEXT = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "NWSAMP") { v[row].NWSAMP = std::atoi(value.c_str()); continue; }
      continue;
    }
    if(table == "EmecMagicNumbers"){
      auto &v = data.emecmagicnumbers; if((int)v.size() <= row) v.resize(row + 1);
      if(column == "STRAIGHTSTARTSECTION") { v[row].STRAIGHTSTARTSECTION = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "FOCALTOREF") { v[row].FOCALTOREF = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "REFTOACTIVE") { v[row].REFTOACTIVE = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ACTIVELENGTH") { v[row].ACTIVELENGTH = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "REFTOPRESAMPLER") { v[row].REFTOPRESAMPLER = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "PRESAMPLERLENGTH") { v[row].PRESAMPLERLENGTH = std::strtod(value.c_str(), nullptr); continue; }
      continue;
    }
    if(table == "ColdContraction"){
      auto &v = data.coldcontraction; if((int)v.size() <= row) v.resize(row + 1);
      if(column == "ABSORBERCONTRACTION") { v[row].ABSORBERCONTRACTION = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "G10RINGCONTRACTION") { v[row].G10RINGCONTRACTION = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "MOTHERBOARDCONTRACTION") { v[row].MOTHERBOARDCONTRACTION = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "CABLECONTRACTION") { v[row].CABLECONTRACTION = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "COLDWINDOWCONTRACTION") { v[row].COLDWINDOWCONTRACTION = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ELECTRODEINVCONTRACTION") { v[row].ELECTRODEINVCONTRACTION = std::strtod(value.c_str(), nullptr); continue; }
      continue;
    }
    if(table == "EmecFan"){
      auto &v = data.emecfan; if((int)v.size() <= row) v.resize(row + 1);
      if(column == "LEADTHICKNESSINNER") { v[row].LEADTHICKNESSINNER = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "LEADTHICKNESSOUTER") { v[row].LEADTHICKNESSOUTER = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "STEELTHICKNESS") { v[row].STEELTHICKNESS = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "GLUETHICKNESS") { v[row].GLUETHICKNESS = std::strtod(value.c_str(), nullptr); continue; }
      if(column == "ELECTRODETOTALTHICKNESS") { v[row].ELECTRODETOTALTHICKNESS = std::strtod(value.c_str(), nullptr); continue; }
      continue;
    }
  }
  if(data.emecgeometry.size() != 1 || data.emecparams.size() != 1 || data.emecwheelparameters.size() != 2 ||
     data.emecmagicnumbers.size() != 1 || data.coldcontraction.size() != 1 || data.emecfan.size() != 1)
    throw std::runtime_error("readEMECDataCSV: incomplete tables in " + path);
  return data;
}
