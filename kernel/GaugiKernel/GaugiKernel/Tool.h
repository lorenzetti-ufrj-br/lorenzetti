#ifndef Tool_h
#define Tool_h

#include "GaugiKernel/ITool.h"
#include "GaugiKernel/DataHandle.h"
#include "GaugiKernel/StoreGate.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/Property.h"
#include "GaugiKernel/MsgStream.h"

namespace Gaugi{

  class Tool : public ITool, 
               public MsgService, 
               public PropertyService
  {
    public:

      /*! Constructor */
      Tool();

      virtual ~Tool() {};

      const std::string& name() const;

    protected:
      
      /*! Output level message */
      int m_outputLevel;

  };

} // namespace Gaugi

#endif
