/*
  Copyright (C) 2002-2022 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (Simulation/G4Atlas/G4AtlasServices, StandardFieldSvc.cxx) for --atlas-run4 (F41 conserto 27); changes: createFieldMap turned into the static helper AtlasMagneticField::loadMap; ATH_MSG_* replaced by std::cerr/std::cout; PathResolver dropped (explicit path); an IsZombie() check added after opening the file.

#include "AtlasMagneticField.h"

// Field map
#include "MagFieldElements/AtlasFieldMap.h"

// ROOT
#include "TFile.h"
#include "TTree.h"

#include <iostream>

//-----------------------------------------------------------------------------
// Create field map (StandardFieldSvc::createFieldMap)
//-----------------------------------------------------------------------------
std::shared_ptr<MagField::AtlasFieldMap>
AtlasMagneticField::loadMap(const std::string& rootFile, double soleCurrent, double toroCurrent)
{
    // Do checks and extract root file to initialize the map
    if ( rootFile.find(".root") == std::string::npos ) {
        std::cerr << "AtlasMagneticField::loadMap: input file name '" << rootFile << "' does not end with .root" << std::endl;
        return nullptr;
    }

    std::unique_ptr<TFile> rootfile = std::make_unique<TFile>(rootFile.c_str(), "OLD");
    if ( ! rootfile.get() || rootfile->IsZombie() ) {
        std::cerr << "AtlasMagneticField::loadMap: failed to open " << rootFile << std::endl;
        return nullptr;
    }
    if ( !rootfile->cd() ) {
        // could not make it current directory
        std::cerr << "AtlasMagneticField::loadMap: unable to cd() into the ROOT field map TFile" << std::endl;
        rootfile->Close();
        return nullptr;
    }
    // open the tree
    TTree* tree = (TTree*)rootfile->Get("BFieldMap");
    if ( tree == nullptr ) {
        // no tree
        std::cerr << "AtlasMagneticField::loadMap: TTree 'BFieldMap' does not exist in ROOT field map" << std::endl;
        rootfile->Close();
        return nullptr;
    }

    // create map
    auto fieldMap = std::make_shared<MagField::AtlasFieldMap>();

    // initialize map
    if (!fieldMap->initializeMap( rootfile.get(), soleCurrent , toroCurrent) ) {
        // failed to initialize the map
        std::cerr << "AtlasMagneticField::loadMap: unable to initialize the map for AtlasFieldMap for file " << rootFile << std::endl;
        rootfile->Close();
        return nullptr;
    }

    rootfile->Close();

    std::cout << "AtlasMagneticField::loadMap: Initialized the field map from " << rootFile << std::endl;
    return fieldMap;
}
