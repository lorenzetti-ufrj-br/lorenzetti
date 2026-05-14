
import os
import shutil

# mapping based on grepped output
mapping = {
    'core/G4Kernel/python' : 'G4Kernel',
    'core/GaugiKernel/python' : 'GaugiKernel',
    'events/CaloCell/python' : 'CaloCell',
    'events/CaloCluster/python' : 'CaloCluster',
    'events/CaloHit/python' : 'CaloHit',
    'events/CaloRings/python' : 'CaloRings',
    'events/Egamma/python' : 'Egamma',
    'events/EventInfo/python' : 'EventInfo',
    'events/SpacePoint/python' : 'SpacePoint',
    'generator/evtgen/python' : 'evtgen',
    'generator/filters/python' : 'filters',
    'generator/genkernel/python' : 'GenKernel',
    'geometry/python' : 'geometry',
    'reconstruction/calorimeter/CaloCellBuilder/python' : 'CaloCellBuilder',
    'reconstruction/calorimeter/CaloClusterBuilder/python' : 'CaloClusterBuilder',
    'reconstruction/calorimeter/CaloHitBuilder/python' : 'CaloHitBuilder',
    'reconstruction/calorimeter/CaloRingsBuilder/python' : 'CaloRingsBuilder',
    'reconstruction/io/RootStreamBuilder/python' : 'RootStreamBuilder',
    'reconstruction/physics/EgammaBuilder/python' : 'EgammaBuilder',
    'reconstruction/reco/python' : 'reco',
}

base_dir = os.path.abspath('.')
mock_dir = os.path.join(base_dir, 'doc/mock_site_packages')

for src_rel, pkg_name in mapping.items():
    src = os.path.join(base_dir, src_rel)
    dst = os.path.join(mock_dir, pkg_name)
    if not os.path.exists(src):
        print(f"Skipping {src} (not found)")
        continue
    
    print(f"Copying {src} -> {dst}")
    # Overwrite existing directory without deleting it first to avoid permission issues
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
