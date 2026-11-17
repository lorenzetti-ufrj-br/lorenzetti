/*
  Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes/src) for --atlas-emec-charge-collection (F41 conserto 29); changes: messages to PortableMsgStream instead of the Gaudi message service; include paths; GeoModel units from GeoSpecialShapes/GeoModelKernelUnits.h (same values). Compiled with -DNDEBUG -O2 as in the Athena release.

#if 0 // Lorenzetti port: no Gaudi message service, the messages go to PortableMsgStream
  #include "GaudiKernel/MsgStream.h"
  #include "GaudiKernel/ISvcLocator.h"
  #include "GaudiKernel/Bootstrap.h"
#else
  #include "PortableMsgStream/PortableMsgStream.h"
#endif
#include "GeoSpecialShapes/LArWheelCalculator_Impl/DistanceCalculatorSaggingOn.h"
#include "CLHEP/Vector/ThreeVector.h"

#include <vector>
#include <stdexcept>

#include "GeoSpecialShapes/LArWheelCalculator.h"

#include "GeoSpecialShapes/GeoModelKernelUnits.h" // Lorenzetti port: same units, without GeoModel

using GeoModelKernelUnits::mm;


namespace LArWheelCalculator_Impl
{
  DistanceCalculatorSaggingOn::DistanceCalculatorSaggingOn(const std::string& saggingOptions,
                                                           LArWheelCalculator* lwc)
    : parent(lwc),
      m_saggingOptions(saggingOptions)

  {
    init_sagging_parameters();
  }
	
  void DistanceCalculatorSaggingOn::init_sagging_parameters()
  {

    // Get pointer to the message service
#if 0 // Lorenzetti port: no Gaudi message service, the messages go to PortableMsgStream
    ISvcLocator* svcLocator = Gaudi::svcLocator();
    IMessageSvc* msgSvc;
    StatusCode status = svcLocator->service("MessageSvc", msgSvc);
    if(status.isFailure()){
      throw std::runtime_error("LArWheelCalculator constructor: \
          cannot initialze message service");
    }
    MsgStream msg(msgSvc, "LArWheelCalculator_Impl::DistanceCalculatorSaggingOn");
#else
    PortableMsgStream msg("LArWheelCalculator_Impl::DistanceCalculatorSaggingOn");
#endif
    std::string sagging_opt_value = m_saggingOptions;
    m_sagging_parameter.resize (lwc()->m_NumberOfFans, std::vector<double> (5, 0.));
    //	if(m_SaggingOn) {
    if(sagging_opt_value.substr(0, 4) == "file"){
      std::string sag_file = sagging_opt_value.substr(5);
      msg << MSG::DEBUG
        << "geting sagging parameters from file "
        << sag_file << " ..." << endmsg;
      FILE *F = fopen(sag_file.c_str(), "r");
      if(F == 0){
        msg << MSG::FATAL
          << "cannot open EMEC sagging parameters file "
          << sag_file
          << endmsg;
        throw std::runtime_error("LArWheelCalculator: read sagging parameters from file");
      }
      int s, w, t, n;
      double p0, p1, p2, p3, p4;
      while(!feof(F) &&
            fscanf(F, "%80d %80d %80d %80d %80le %80le %80le %80le %80le",
                   &s, &w, &t, &n, &p0, &p1, &p2, &p3, &p4) == 9)
      {
        if(s == lwc()->m_AtlasZside &&
           ((w == 0 && lwc()->m_isInner) || (w == 1 && !lwc()->m_isInner)) &&
           ((t == 0 && !lwc()->m_isElectrode) || (t == 1 && lwc()->m_isElectrode)) &&
           (n >= 0 && n < lwc()->m_NumberOfFans))
        {
          m_sagging_parameter[n][0] = p0;
          m_sagging_parameter[n][1] = p1;
          m_sagging_parameter[n][2] = p2;
          m_sagging_parameter[n][3] = p3;
          m_sagging_parameter[n][4] = p4;
          msg << MSG::VERBOSE
              << "sagging for " << s << " " << w << " " << t
              << " " << n << ": " << p0 << " " << p1 << " "
              << p2 << " " << p3 << endmsg;
        }
      }
      fclose(F);
    } else {
      double a, b, c, d;
      if(sscanf(sagging_opt_value.c_str(), "%80le %80le %80le %80le", &a, &b, &c, &d) != 4){
        msg << MSG::ERROR
            << "wrong value(s) "
            << " for EMEC sagging parameters: "
            << sagging_opt_value << ", defaults are used" << endmsg;
      } else {
        for(int j = 0; j < lwc()->m_NumberOfFans; j ++){
          if(lwc()->m_isInner){
            m_sagging_parameter[j][1] = a;
            m_sagging_parameter[j][0] = b * mm;
          } else {
            m_sagging_parameter[j][1] = c;
            m_sagging_parameter[j][0] = d * mm;
          }
        }
      }
    }
    //	}
    msg << MSG::INFO  << "Sagging parameters        : " << m_sagging_parameter[0][0] << " " << m_sagging_parameter[0][1] << endmsg
        << "Sagging parameters        : " << m_sagging_parameter[1][0] << " " << m_sagging_parameter[1][1] << endmsg;
  }

  // Represents aproximate, probably underestimate, distance to the
  // neutral fibre of the vertical fan. Sign of return value means
  // side of the fan; negative - lower phi.
  //
  // Uses m_fan_number to compute sagging.
  double DistanceCalculatorSaggingOn::DistanceToTheNeutralFibre(const CLHEP::Hep3Vector &p, int fan_number) const {
    CLHEP::Hep3Vector sagging_corrected( p.x()+get_sagging(p, fan_number), p.y(), p.z() );
    return parent::DistanceToTheNeutralFibre(sagging_corrected, fan_number);
  }

  CLHEP::Hep3Vector DistanceCalculatorSaggingOn::NearestPointOnNeutralFibre(const CLHEP::Hep3Vector &p, int fan_number) const {
    CLHEP::Hep3Vector sagging_corrected( p.x()+get_sagging(p, fan_number), p.y(), p.z() );
    return parent::NearestPointOnNeutralFibre(sagging_corrected, fan_number);
  }

  double DistanceCalculatorSaggingOn::AmplitudeOfSurface(const CLHEP::Hep3Vector& p, int side, int fan_number) const {
    return parent::AmplitudeOfSurface(p, side, fan_number) - get_sagging(p, fan_number);
  }


  // the function uses m_fan_number for phi-dependent sagging computation
  double DistanceCalculatorSaggingOn::get_sagging(const CLHEP::Hep3Vector &P, int fan_number) const {
#ifdef HARDDEBUG
    std::cout << "get_sagging: MFN = " << fan_number << std::endl;
#endif
    double dx = P.z() / lwc()->m_HalfWheelThickness - 1.;
    dx *= dx;
    dx = 1. - dx;
    //dx *= SaggingAmplitude * sin(FanStepOnPhi * m_fan_number + ZeroFanPhi);
    //int n = m_fan_number;
    //if(n < 0) n += m_NumberOfFans;
    //n += m_ZeroGapNumber;
    //if(n >= m_NumberOfFans) n -= m_NumberOfFans;
    //const std::vector<double>& sp = m_sagging_parameter[n];
    const std::vector<double>& sp = m_sagging_parameter[fan_number];
    double R = P.r() / mm;
    double r = R;
    double result = sp[0];
    result += R * sp[1];
    R *= r;
    result += R * sp[2];
    R *= r;
    result += R * sp[3];
    R *= r;
    result += R * sp[4];

#ifdef HARDDEBUG
    /*printf("get_sagging: (%6.3f, %6.3f, %6.3f) %6.3f; MFN %4d;"
      "n %3d; sp %6.4f %6.4f; dx %6.3f; %.6f\n", P.x()/mm, P.y()/mm, P.z()/mm,
      r, m_fan_number, n, sp[0], sp[1], dx, result*dx);*/
    printf("get_sagging: (%6.3f, %6.3f, %6.3f) %6.3f;"
           " sp %6.4f %6.4f; dx %6.3f; %.6f\n", P.x()/mm, P.y()/mm, P.z()/mm,
           r, sp[0], sp[1], dx, result*dx);
#endif //HARDDEBUG

    return result * dx;
  }

}
