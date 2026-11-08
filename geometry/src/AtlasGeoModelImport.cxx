// F41 conserto 27: volumes of the ATLAS geometry of the simulation imported from its GeoModel SQLite dump (see AtlasGeoModelImport.h).
#include "AtlasGeoModelImport.h"

#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4RotationMatrix.hh"
#include "G4ThreeVector.hh"
#include "G4UnionSolid.hh"
#include <map>
#include <stdexcept>
#include <functional>

#ifdef LORENZETTI_WITH_GEOMODEL

#include "GeoModelDBManager/GMDBManager.h"
#include "GeoModelRead/ReadGeoModel.h"
#include "GeoModel2G4/ExtParameterisedVolumeBuilder.h"
#include "GeoModel2G4/Geo2G4SolidFactory.h"
#include "GeoMaterial2G4/Geo2G4MaterialFactory.h"
#include "GeoModelKernel/GeoVPhysVol.h"
#include "GeoModelKernel/GeoLogVol.h"
#include "G4DisplacedSolid.hh"

namespace {
  G4Transform3D toG4( const GeoTrf::Transform3D &x )
  {
    const auto &r = x.linear(); const auto &t = x.translation();
    const CLHEP::HepRep3x3 rep( r(0,0), r(0,1), r(0,2), r(1,0), r(1,1), r(1,2), r(2,0), r(2,1), r(2,2) );
    return G4Transform3D( G4RotationMatrix( rep ), G4ThreeVector( t.x(), t.y(), t.z() ) );
  }

  bool startsWithAny( const std::string &name, const std::vector<std::string> &prefixes )
  {
    for( const auto &p : prefixes ) if( name.rfind( p, 0 ) == 0 ) return true;
    return false;
  }
}

struct AtlasGeoModelImport::Impl {
  std::unique_ptr<GMDBManager> db;
  std::unique_ptr<GeoModelIO::ReadGeoModel> reader;
  PVConstLink world;
  Geo2G4SolidFactory solids;
  Geo2G4MaterialFactory materials;
  std::map<const GeoVPhysVol*, bool> hasDropped;
  // logical volumes converted, by "<subdetector>::<name>" (the names of the ATLAS regions)
  std::map<std::string, std::set<G4LogicalVolume*>> byName;

  void collect( const std::string &top, G4LogicalVolume *lv, std::set<G4LogicalVolume*> &seen )
  {
    if( !seen.insert( lv ).second ) return;
    byName[ top + "::" + lv->GetName() ].insert( lv );
    for( size_t k = 0; k < lv->GetNoDaughters(); ++k ) collect( top, lv->GetDaughter(k)->GetLogicalVolume(), seen );
  }

  bool dropsBelow( const PVConstLink &pv, const std::vector<std::string> &dropped )
  {
    auto it = hasDropped.find( pv.get() );
    if( it != hasDropped.end() ) return it->second;
    bool found = false;
    for( unsigned int i = 0; i < pv->getNChildVols() && !found; ++i ){
      PVConstLink child = pv->getChildVol( i );
      found = startsWithAny( child->getLogVol()->getName(), dropped ) || dropsBelow( child, dropped );
    }
    hasDropped[ pv.get() ] = found;
    return found;
  }
};


AtlasGeoModelImport::AtlasGeoModelImport( const std::string &dbFile ) : m_impl( new Impl )
{
  m_impl->db.reset( new GMDBManager( dbFile ) );
  if( !m_impl->db->checkIsDBOpen() ) throw std::runtime_error( "AtlasGeoModelImport: cannot open " + dbFile );
  m_impl->reader.reset( new GeoModelIO::ReadGeoModel( m_impl->db.get() ) );
  m_impl->world = m_impl->reader->buildGeoModel();
}

AtlasGeoModelImport::~AtlasGeoModelImport() = default;

bool AtlasGeoModelImport::available() { return true; }


void AtlasGeoModelImport::placeWorldChildren( G4LogicalVolume *mother, const std::set<std::string> &names, bool checkOverlaps )
{
  const PVConstLink &world = m_impl->world;
  for( unsigned int i = 0; i < world->getNChildVols(); ++i ){
    PVConstLink child = world->getChildVol( i );
    const std::string name = child->getLogVol()->getName();
    if( !names.count( name ) ) continue;
    ExtParameterisedVolumeBuilder builder( name );
    G4LogicalVolume *lv = builder.Build( child );
    new G4PVPlacement( toG4( world->getXToChildVol( i ) ), lv, name, mother, false, i, checkOverlaps );
    std::set<G4LogicalVolume*> seen;
    m_impl->collect( name, lv, seen );
  }
}


G4LogicalVolume* AtlasGeoModelImport::placeWorldChildrenInEnvelope( G4LogicalVolume *mother, const std::string &envelope,
                                                                    const std::set<std::string> &names, bool checkOverlaps )
{
  const PVConstLink &world = m_impl->world;
  std::vector<unsigned int> kids;
  for( unsigned int i = 0; i < world->getNChildVols(); ++i )
    if( names.count( world->getChildVol( i )->getLogVol()->getName() ) ) kids.push_back( i );
  if( kids.empty() ) return nullptr;
  // the union of the shapes with their transformations, in the material of the first one (Geo2G4Builder::BuildTree)
  G4VSolid *shape = nullptr;
  for( unsigned int i : kids ){
    const GeoLogVol *glv = world->getChildVol( i )->getLogVol();
    G4VSolid *s = m_impl->solids.Build( glv->getShape(), glv->getName() );
    const G4Transform3D x = toG4( world->getXToChildVol( i ) );
    if( !shape ) shape = new G4DisplacedSolid( envelope, s, x );
    else         shape = new G4UnionSolid( envelope, shape, s, x );
  }
  G4LogicalVolume *env = new G4LogicalVolume( shape, m_impl->materials.Build( world->getChildVol( kids[0] )->getLogVol()->getMaterial() ),
                                              envelope );
  new G4PVPlacement( G4Transform3D(), env, envelope, mother, false, 0, checkOverlaps );
  m_impl->byName[ envelope + "::" + envelope ].insert( env );
  for( unsigned int i : kids ){
    PVConstLink child = world->getChildVol( i );
    const std::string name = child->getLogVol()->getName();
    ExtParameterisedVolumeBuilder builder( name );
    G4LogicalVolume *lv = builder.Build( child );
    new G4PVPlacement( toG4( world->getXToChildVol( i ) ), lv, name, env, false, i, checkOverlaps );
    std::set<G4LogicalVolume*> seen;
    m_impl->collect( name, lv, seen );
  }
  return env;
}


std::vector<AtlasGeoModelImport::Container> AtlasGeoModelImport::placeUnwrapped( G4LogicalVolume *mother, const std::string &name,
                                                                                 const std::vector<std::string> &dropped, bool checkOverlaps )
{
  std::vector<Container> containers;
  ExtParameterisedVolumeBuilder builder( name );
  // places pv (transformation xLocal in its mother, xGlobal in the world): cloned when something below it is dropped
  std::function<void(const PVConstLink&, const G4Transform3D&, const G4Transform3D&, G4LogicalVolume*, int, int)> place =
    [&]( const PVConstLink &pv, const G4Transform3D &xGlobal, const G4Transform3D &xLocal, G4LogicalVolume *motherLV, int depth, int copy ){
      const GeoLogVol *glv = pv->getLogVol();
      const std::string lvName = glv->getName();
      // an envelope of special::Ether (the transparent material of ATLAS) is not a volume: as the assemblies of GeoModel2G4, its children
      // go to its mother with the composed transformation (F41 conserto 32: the containers of the MuonSys, ECT_Toroids and others)
      if( glv->getMaterial()->getName() == "special::Ether" ){
        for( unsigned int k = 0; k < pv->getNChildVols(); ++k ){
          PVConstLink child = pv->getChildVol( k );
          if( startsWithAny( child->getLogVol()->getName(), dropped ) ) continue;
          const G4Transform3D xk = toG4( pv->getXToChildVol( k ) );
          place( child, xGlobal * xk, xLocal * xk, motherLV, depth, copy * 1000 + (int)k );
        }
        return;
      }
      if( m_impl->dropsBelow( pv, dropped ) ){
        G4LogicalVolume *lv = new G4LogicalVolume( m_impl->solids.Build( glv->getShape(), lvName ),
                                                   m_impl->materials.Build( glv->getMaterial() ), lvName );
        new G4PVPlacement( xLocal, lv, lvName, motherLV, false, copy, checkOverlaps );
        containers.push_back( Container{ lv, xGlobal, depth, lvName } );
        m_impl->byName[ name + "::" + lvName ].insert( lv );
        for( unsigned int k = 0; k < pv->getNChildVols(); ++k ){
          PVConstLink child = pv->getChildVol( k );
          if( startsWithAny( child->getLogVol()->getName(), dropped ) ) continue;
          const G4Transform3D xk = toG4( pv->getXToChildVol( k ) );
          place( child, xGlobal * xk, xk, lv, depth + 1, k );
        }
      }else{
        G4LogicalVolume *lv = builder.Build( pv );
        new G4PVPlacement( xLocal, lv, lvName, motherLV, false, copy, checkOverlaps );
        std::set<G4LogicalVolume*> seen;
        m_impl->collect( name, lv, seen );
      }
    };

  const PVConstLink &world = m_impl->world;
  for( unsigned int i = 0; i < world->getNChildVols(); ++i ){
    PVConstLink top = world->getChildVol( i );
    if( top->getLogVol()->getName() != name ) continue;
    const G4Transform3D xTop = toG4( world->getXToChildVol( i ) );
    for( unsigned int k = 0; k < top->getNChildVols(); ++k ){
      PVConstLink child = top->getChildVol( k );
      if( startsWithAny( child->getLogVol()->getName(), dropped ) ) continue;
      const G4Transform3D x = xTop * toG4( top->getXToChildVol( k ) );
      place( child, x, x, mother, 0, k );
    }
  }
  return containers;
}


int AtlasGeoModelImport::placeDescendants( G4LogicalVolume *mother, const std::set<std::string> &tops, const std::set<std::string> &names,
                                           bool checkOverlaps )
{
  int n = 0;
  std::map<const GeoVPhysVol*, G4LogicalVolume*> built;   // one Geant4 logical volume per GeoModel volume (shared placements)
  // a pattern ending in '*' is a prefix; "!name" leaves the volume out (not placed, not searched below); ">name" searches below it without
  // placing it (its own material is the air of the world)
  auto has = [&]( const std::string &name, char mark ){
    for( const auto &p : names ){
      if( p.empty() || p[0] != mark ) continue;
      const std::string q = p.substr( 1 );
      if( q == name || ( !q.empty() && q.back() == '*' && name.compare( 0, q.size() - 1, q, 0, q.size() - 1 ) == 0 ) ) return true;
    }
    return false;
  };
  auto matches = [&]( const std::string &name ){
    if( names.count( name ) ) return true;
    for( const auto &p : names )
      if( !p.empty() && p[0] != '!' && p[0] != '>' && p.back() == '*' && name.compare( 0, p.size() - 1, p, 0, p.size() - 1 ) == 0 ) return true;
    return false;
  };
  std::function<void(const PVConstLink&, const GeoTrf::Transform3D&, const std::string&)> search =
    [&]( const PVConstLink &pv, const GeoTrf::Transform3D &x, const std::string &top ){
      for( unsigned int k = 0; k < pv->getNChildVols(); ++k ){
        PVConstLink child = pv->getChildVol( k );
        const std::string name = child->getLogVol()->getName();
        const GeoTrf::Transform3D xc = x * pv->getXToChildVol( k );
        if( has( name, '!' ) ) continue;
        if( has( name, '>' ) || !matches( name ) ){ search( child, xc, top ); continue; }
        G4LogicalVolume *&lv = built[ child.get() ];
        if( !lv ){
          ExtParameterisedVolumeBuilder builder( top );
          lv = builder.Build( child );
          std::set<G4LogicalVolume*> seen;
          m_impl->collect( top, lv, seen );
        }
        new G4PVPlacement( toG4( xc ), lv, name, mother, false, n, checkOverlaps );
        ++n;
      }
    };
  const PVConstLink &world = m_impl->world;
  for( unsigned int i = 0; i < world->getNChildVols(); ++i ){
    PVConstLink top = world->getChildVol( i );
    const std::string t = top->getLogVol()->getName();
    if( tops.count( t ) ) search( top, world->getXToChildVol( i ), t );
  }
  return n;
}


std::vector<G4LogicalVolume*> AtlasGeoModelImport::logicalVolumes( const std::set<std::string> &names ) const
{
  std::vector<G4LogicalVolume*> out;
  for( const auto &n : names ){
    auto it = m_impl->byName.find( n );
    if( it != m_impl->byName.end() ) out.insert( out.end(), it->second.begin(), it->second.end() );
  }
  return out;
}

#else

struct AtlasGeoModelImport::Impl {};

AtlasGeoModelImport::AtlasGeoModelImport( const std::string & )
{
  throw std::runtime_error( "AtlasGeoModelImport: Lorenzetti was built without the GeoModel libraries (set GEOMODEL_DIR and run cmake)" );
}
AtlasGeoModelImport::~AtlasGeoModelImport() = default;
bool AtlasGeoModelImport::available() { return false; }
void AtlasGeoModelImport::placeWorldChildren( G4LogicalVolume *, const std::set<std::string> &, bool ) {}
int AtlasGeoModelImport::placeDescendants( G4LogicalVolume *, const std::set<std::string> &, const std::set<std::string> &, bool ) { return 0; }
G4LogicalVolume* AtlasGeoModelImport::placeWorldChildrenInEnvelope( G4LogicalVolume *, const std::string &, const std::set<std::string> &,
                                                                    bool ) { return nullptr; }
std::vector<AtlasGeoModelImport::Container> AtlasGeoModelImport::placeUnwrapped( G4LogicalVolume *, const std::string &,
                                                                                 const std::vector<std::string> &, bool ) { return {}; }
std::vector<G4LogicalVolume*> AtlasGeoModelImport::logicalVolumes( const std::set<std::string> & ) const { return {}; }

#endif
