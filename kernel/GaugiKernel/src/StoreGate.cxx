#include <boost/algorithm/string/replace.hpp>
#include "GaugiKernel/StoreGate.h"
#include "TROOT.h"
#include <sstream>
#include <algorithm>

using namespace SG;


StoreGate::StoreGate( std::string outputfile): 
  IMsgService("StoreGate"),
  m_currentPath("")
{
  // This must be used for multithreading root reader 
  ROOT::EnableThreadSafety();
  if (!outputfile.empty() && outputfile != "/dev/null" && outputfile.rfind(".parquet") == std::string::npos)
  {
    m_file = std::unique_ptr<TFile>(new TFile( outputfile.c_str(), "recreate"));
  }
}



void StoreGate::save()
{
  MSG_INFO("Saving StoreGate...");
  
  for( auto& it : m_decorators)
  {
    delete it.second;
  }

  if (!m_file)
  {
    MSG_INFO("StoreGate running in fileless mode; skipping ROOT file save.");
    return;
  }

  MSG_INFO( "Writing all root objects into the file and delete all decorators" ); 
  MSG_INFO( "Decorators will no be saved into the root file.");
  for( auto it : m_objs)
  {
    MSG_DEBUG( it.first  << " " << it.second);
    if (it.second) {
      std::string fullpath = it.first;
      size_t lastSlash = fullpath.rfind('/');
      std::string dirPath = "";
      if (lastSlash != std::string::npos && lastSlash > 0) {
        dirPath = fullpath.substr(0, lastSlash);
        while (!dirPath.empty() && dirPath.front() == '/') {
          dirPath.erase(0, 1);
        }
      }
      cd(dirPath);
      it.second->Write(0, TObject::kOverwrite);
    }
  }

  cd();
  m_file->Write(0, TObject::kOverwrite);
  m_file->Close();
}


void StoreGate::mkdir( std::string path ){
  MSG_DEBUG( "Creating a directory with name " << path );
  if (m_file && !m_file->GetDirectory(path.c_str())){
    m_file->mkdir(path.c_str());
    m_file->cd(path.c_str());
  }
  m_currentPath = path;
}


void StoreGate::cd( std::string path ){
  m_currentPath = path;
  if (m_file)
  {
    m_file->cd(path.c_str());
  }
}


bool StoreGate::add( TObject* obj, bool force){  
  std::string feature(obj->GetName());
  std::string fullpath = m_currentPath + "/" + feature;
  auto it = m_objs.find( fullpath );
  if( (it != m_objs.end()) && it->second != nullptr && !force ) 
  {
    MSG_WARNING("It's not possible to attach the histogram with name " << feature << " into this path " << m_currentPath);
    return false;
  }
  m_objs[fullpath] = obj;
  return true;
}


TH1F* StoreGate::hist1( std::string name )
{
  std::string path = m_currentPath+"/"+name;
  auto it = m_objs.find(path);
  return (it != m_objs.end()) ? ((TH1F*)it->second) : nullptr;
}


TH2F* StoreGate::hist2( std::string name )
{
  std::string path = m_currentPath+"/"+name;
  auto it = m_objs.find(path);
  return (it != m_objs.end()) ? ((TH2F*)it->second) : nullptr;
}


TH1I* StoreGate::histI( std::string name )
{
  std::string path = m_currentPath+"/"+name;
  auto it = m_objs.find(path);
  return (it != m_objs.end()) ? ((TH1I*)it->second) : nullptr;
}


TH2Poly* StoreGate::hist2P( std::string name )
{
  std::string path = m_currentPath+"/"+name;
  auto it = m_objs.find(path);
  return (it != m_objs.end()) ? ((TH2Poly*)it->second) : nullptr;
}


TTree* StoreGate::tree( std::string name )
{
  std::string path = m_currentPath+"/"+name;
  auto it = m_objs.find(path);
  return (it != m_objs.end()) ? ((TTree*)it->second) : nullptr;
}


void StoreGate::setLabels(TH1* histo, const std::vector<std::string>& labels) {
    if ( ! labels.empty() ){
        for ( int i = 0; i < std::min( (int)labels.size(), (int)histo->GetNbinsX() ); ++i ) {
            int bin = i+1;
            histo->GetXaxis()->SetBinLabel(bin, labels[i].c_str());
            MSG_DEBUG("setting label X" <<  labels[i] << " for bin " << bin);
        }

        for ( int i = (int)histo->GetNbinsX(); i < std::min( (int)labels.size(), (int)histo->GetNbinsX()+(int)histo->GetNbinsY() ); ++i ) {
            int bin = i+1-(int)histo->GetNbinsX();
            histo->GetYaxis()->SetBinLabel(bin, labels[i].c_str());
            MSG_DEBUG("setting label Y" <<  labels[i] << " for bin " << bin);
        }
    }
}


bool StoreGate::decorate( std::string name, TObject* obj){  
  auto it = m_decorators.find( name );
  if( it != m_decorators.end() && it->second != nullptr ) 
  {
    MSG_WARNING("It's not possible decorate with name " << name);
		return false;
  }
  m_decorators[name] = obj;
  return true;
}


TObject* StoreGate::decorator( std::string name )
{
  auto it = m_decorators.find(name);
  return (it != m_decorators.end()) ? it->second : nullptr;
}