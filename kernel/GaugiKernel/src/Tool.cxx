#include "GaugiKernel/Tool.h"

using namespace Gaugi;

Tool::Tool(): 
  IMsgService()
{;}

const std::string& Tool::name() const
{
  return getLogName();
}
