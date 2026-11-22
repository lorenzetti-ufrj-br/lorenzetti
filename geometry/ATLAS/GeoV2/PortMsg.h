// Lorenzetti port (F41 conserto 29): the ATH_MSG_* macros of the ported LArG4EC code, without the Gaudi message service.
// INFO goes to std::cout, WARNING, ERROR and FATAL to std::cerr, DEBUG and VERBOSE are dropped. As in Athena, FATAL only prints.
#ifndef LARG4EC_PORTMSG_H
#define LARG4EC_PORTMSG_H
#include <iostream>
#define ATH_MSG_VERBOSE(x) do {} while(0)
#define ATH_MSG_DEBUG(x)   do {} while(0)
#define ATH_MSG_INFO(x)    do { std::cout << "LArG4::EC INFO " << x << std::endl; } while(0)
#define ATH_MSG_WARNING(x) do { std::cerr << "LArG4::EC WARNING " << x << std::endl; } while(0)
#define ATH_MSG_ERROR(x)   do { std::cerr << "LArG4::EC ERROR " << x << std::endl; } while(0)
#define ATH_MSG_FATAL(x)   do { std::cerr << "LArG4::EC FATAL " << x << std::endl; } while(0)
#endif
