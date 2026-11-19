#ifndef CaloHitTypes_h
#define CaloHitTypes_h

#include <string>
#include <cstdint>

struct CellIdentification {
  bool isValid = false;
  unsigned long int hashId = 0;
  int cell = -1;
  int etaBin = -1;
  int phiBin = -1;
  float eta = 0.0f;
  float phi = 0.0f;
  float dEta = 0.0f;
  float dPhi = 0.0f;
  int sampling = 0;
  int detector = 0;
  bool isReplaced = false;
  unsigned long int replaceHash = 0;
  std::string replaceCollectionKey = "";
  // ATLAS-specific and Free-Running identification fields
  long long atlasCellID = 0;
  int atlasSubdet = 0; // 0=Tile, 1=EMB, 2=EMEC, 3=HEC, 4=FCAL
  int atlasSide = 0;
  int atlasSampling = 0;
  int atlasRegion = 0;
  int atlasModule = 0;
  int atlasTower = 0;
  int atlasTimeBin = -1;
  int atlasSource = 0;
  // Dual readout fields
  bool hasDualReadout = false;
  float pmtWeight0 = 1.0f;
  float pmtWeight1 = 0.0f;
  int tileNPmt = 2;
};

struct CellTiming {
  float hitTime = 0.0f;
  float globalTime = 0.0f;
  float time0 = 0.0f;
  float time1 = 0.0f;
  bool hasDualReadoutTime = false;
};

#endif
