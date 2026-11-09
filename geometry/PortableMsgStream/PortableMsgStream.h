/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (DetectorDescription/GeoModel/GeoSpecialShapes/PortableMsgStream) for --atlas-emec-charge-collection (F41 conserto 29); changes: compiled without PORTABLE_LAR_SHAPE.

// JFB Feb 2022
// This is an ersatz message stream class. It directs messages to cout.
// This is not used within Athena. It is for portability (e.g. to FullSimLight).
// 

#ifndef __LArWheelCalculator_Impl_PortableMsgStream_H__
#define __LArWheelCalculator_Impl_PortableMsgStream_H__
#if 1 // Lorenzetti port: always available
#include <iostream>
#include <sstream>
#include <string>


namespace MSG {
  enum Level {VERBOSE, DEBUG, INFO, WARNING, ERROR, FATAL};
}

class PortableMsgStream;
PortableMsgStream& endmsg( PortableMsgStream& s ); 


class PortableMsgStream {
public:

  PortableMsgStream(const std::string  label="",MSG::Level threshold=MSG::INFO,std::ostream & stream=std::cout) :
    m_ostream(stream),
    m_label(label),
    m_threshold(threshold)
  {
  }

  template<typename T> PortableMsgStream & operator << (const T & t) {
    if (m_level>=m_threshold) m_sstream << t;
    return *this;
  }

  PortableMsgStream& operator<<( PortableMsgStream& ( *t )(PortableMsgStream&)) {
    if (t==endmsg) {
      if (m_level>=m_threshold) {
	return doOutput();
      }
      else {
	m_ostream.clear();
	return *this;
      }
    }
    return *this;
  }
  
  PortableMsgStream& operator << (MSG::Level level) {
    m_level=level;
    return *this;
  }

  PortableMsgStream & doOutput() {
    
    switch (m_level) {
    case MSG::VERBOSE:
      m_ostream << "VERBOSE: ";
      break;
    case MSG::DEBUG:
      m_ostream << "DEBUG  : ";
      break;
    case MSG::INFO:
      m_ostream << "INFO   : ";
      break;
    case MSG::WARNING:
      m_ostream << "WARNING: ";
      break;
    case MSG::ERROR:
      m_ostream << "ERROR  : ";
      break;
    case MSG::FATAL:
      m_ostream << "FATAL  : ";
      break;
    };
    m_ostream << m_label;
    m_ostream << m_sstream.str() << std::endl;
    m_sstream.str("");
    m_sstream.clear();
    return *this;
  }

  
private:

  PortableMsgStream (const PortableMsgStream &) = delete;
  PortableMsgStream & operator=(const PortableMsgStream &) = delete;
  
  std::ostringstream   m_sstream;
  std::ostream       & m_ostream;
  const std::string    m_label;
  MSG::Level           m_level;
  MSG::Level           m_threshold;
};

inline PortableMsgStream& endmsg( PortableMsgStream& s ) { return s.doOutput(); }


#endif //LAR_PORTABLE_SHAPE
#endif  // __LArWheelCalculator_Impl_PortableMsgStream_H__

