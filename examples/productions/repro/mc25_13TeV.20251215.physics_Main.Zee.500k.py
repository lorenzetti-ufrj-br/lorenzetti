

import os, json
from maestro_lightning import Flow, Task, Dataset, Image


basepath         = os.getcwd()
input_path       = f"{basepath}/mc25_13TeV.20251215.physics_Main.Zee.500k.jobs.json"
number_of_events = 500000
number_of_jobs   = 100
run_number       = 20251215
image_path       = '/mnt/shared/storage03/projects/cern/data/images/lorenzetti_latest.sif'
repo_build_path  = '/home/joao.pinto/git_repos/lorenzetti/build'
binds            = {"/mnt/shared/storage03" : "/mnt/shared/storage03"}


os.makedirs(input_path, exist_ok=True)
for job_id in range(number_of_jobs):
    with open(f"{input_path}/job_{job_id}.json", 'w') as f:
        nov = int(number_of_events / number_of_jobs)
        number_of_threads = 10
        d = {
            'run_number'        : run_number,
            'seed'              : int(16 * (1+job_id)),
            'number_of_events'  : nov,
            'events_per_job'    : int(nov/number_of_threads),
            'number_of_threads' : number_of_threads
        }
        json.dump(d,f)



with Flow(name="mc25_13TeV.20251215.physics_Main.Zee.500k", path=f"{basepath}/mc25_13TeV.20251215.physics_Main.Zee.500k") as session:


    input_dataset    = Dataset(name="mc25_13TeV.20251215.physics_Main.Zee.500k.jobs.json", path=input_path)
    image            = Image(name="lorenzetti", path=image_path)
    partitions       = 'gpu,cpu-large,gpu-large'

    pre_exec = f"source {repo_build_path}/lzt_setup.sh"

    command = f"{pre_exec} && gen_zee.py -o %OUT --job-file %IN -m"

    task_1 = Task(name="mc25_13TeV.20251215.physics_Main.Zee.500k.EVT",
                  image=image,
                  command=command,
                  input_data=input_dataset,
                  outputs={'OUT':'Zee.EVT.root'},
                  partition=partitions,
                  binds=binds)
    
    
    command = f"{pre_exec} && simu_trf.py -i %IN -o %OUT -nt 40"
    task_2 = Task(name="mc25_13TeV.20251215.physics_Main.Zee.500k.HIT",
                  image=image,
                  command=command,
                  input_data=task_1.output('OUT'),
                  outputs= {'OUT':'Zee.HIT.root'},
                  partition=partitions,
                  binds=binds)
    
    
    command = f"{pre_exec} && digit_trf.py -i %IN -o %OUT -nt 10 --events-per-job 100 -m"
    task_3 = Task(name="mc25_13TeV.20251215.physics_Main.Zee.500k.ESD",
                  image=image,
                  command=command,
                  input_data=task_2.output('OUT'),
                  outputs= {'OUT':'Zee.ESD.root'},
                  partition=partitions,
                  binds=binds)
    
    command = f"{pre_exec} && reco_trf.py -i %IN -o %OUT -nt 10 --events-per-job 100 -m"
    task_4 = Task(name="mc25_13TeV.20251215.physics_Main.Zee.500k.AOD",
                  image=image,
                  command=command,
                  input_data=task_3.output('OUT'),
                  outputs= {'OUT':'Zee.AOD.root'},
                  partition=partitions,
                  binds=binds)
    
    command = f"{pre_exec} && ntuple_trf.py -i %IN -o %OUT -nt 10 --events-per-job 100 -m"
    task_5 = Task(name="mc25_13TeV.20251215.physics_Main.Zee.500k.NTUPLE",
                  image=image,
                  command=command,
                  input_data=task_4.output('OUT'),
                  outputs= {'OUT':'Zee.NTUPLE.root'},
                  partition=partitions,
                  binds=binds)
   
   
    session.run()
    
