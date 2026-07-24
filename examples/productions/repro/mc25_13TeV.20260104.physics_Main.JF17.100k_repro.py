

import os, json
from maestro_lightning import Flow, Task, Dataset, Image


basepath         = os.getcwd()

basename        = 'mc25_13TeV.20260104.physics_Main.JF17.100k'
input_path       = f"/mnt/shared/storage03/projects/cern/lorenzetti/{basename}.HIT.JF17.HIT.root"

image_path       = '/mnt/shared/storage03/projects/cern/data/images/lorenzetti_latest.sif'
repo_build_path  = '/home/joao.pinto/git_repos/lorenzetti/build'
binds            = {"/mnt/shared/storage03" : "/mnt/shared/storage03"}

recon = 1



with Flow(name=f"{basename}.r{recon}", path=f"{basepath}/{basename}.r{recon}") as session:


    input_dataset    = Dataset(name=f"{basename}.HIT.JF17.HIT.root", path=input_path)
    image            = Image(name="lorenzetti", path=image_path)
    partitions       = 'gpu,cpu'

    pre_exec = f"source {repo_build_path}/lzt_setup.sh"

    
    command = f"{pre_exec} && digit_trf.py -i %IN -o %OUT -nt 10 --events-per-job 100 -m"
    task_3 = Task(name=f"{basename}.ESD.r{recon}",
                  image=image,
                  command=command,
                  input_data=input_dataset,
                  outputs= {'OUT':'JF17.ESD.root'},
                  partition=partitions,
                  binds=binds)
    
    command = f"{pre_exec} && reco_trf.py -i %IN -o %OUT -nt 10 --events-per-job 100 -m"
    task_4 = Task(name=f"{basename}.AOD.r{recon}",
                  image=image,
                  command=command,
                  input_data=task_3.output('OUT'),
                  outputs= {'OUT':'JF17.AOD.root'},
                  partition=partitions,
                  binds=binds)
    
    command = f"{pre_exec} && ntuple_trf.py -i %IN -o %OUT -nt 10 --events-per-job 100 -m"
    task_5 = Task(name=f"{basename}.NTUPLE.r{recon}",
                  image=image,
                  command=command,
                  input_data=task_4.output('OUT'),
                  outputs= {'OUT':'JF17.NTUPLE.root'},
                  partition=partitions,
                  binds=binds)
   
   
    session.run()
    
