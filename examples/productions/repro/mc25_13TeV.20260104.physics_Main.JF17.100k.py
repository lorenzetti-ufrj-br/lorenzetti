

import os, json
from maestro_lightning import Flow, Task, Dataset, Image

#run_number       = 20260502
run_number       = 20260104
basename = f'mc25_13TeV.{run_number}.physics_Main.JF17.100k'


basepath         = os.getcwd()
input_path       = f"{basepath}/{basename}.jobs.json"
number_of_events = 100000
number_of_jobs   = 500
image_path       = '/mnt/shared/storage03/projects/cern/data/images/lorenzetti_latest.sif'
repo_build_path  = '/home/joao.pinto/git_repos/lorenzetti/build'
binds            = {"/mnt/shared/storage03" : "/mnt/shared/storage03"}
events_per_job   = int( (number_of_events / number_of_jobs) / 10 )
events_per_job   = events_per_job if events_per_job > 1 else 1

#seed_offset = 16 # 20260502
seed_offset = 8 # 20260104

os.makedirs(input_path, exist_ok=True)
for job_id in range(number_of_jobs):
    with open(f"{input_path}/job_{job_id}.json", 'w') as f:
        nov = int(number_of_events / number_of_jobs)
        d = {
            'run_number'        : run_number,
            'seed'              : int(seed_offset * (1+job_id)),
            'number_of_events'  : nov,
            'event_per_job'     : events_per_job,
            'number_of_threads' : 10,
        }
        json.dump(d,f)

virtualenv = os.environ['VIRTUALENV_PATH']

with Flow(name=f"{basename}", 
          path=f"{basepath}/{basename}",
          virtualenv = virtualenv,
          partition = 'cpu') as session:


    input_dataset    = Dataset(name="jobs", path=input_path)
    image            = Image(name="lorenzetti", path=image_path)
    partitions       = 'cpu'

    pre_exec = f"source {repo_build_path}/lzt_setup.sh"

    command = f"{pre_exec} && gen_jets.py -o %OUT --job-file %IN -m"

    task_1 = Task(name=f"{basename}.EVT",
                  image=image,
                  command=command,
                  input_data=input_dataset,
                  outputs={'OUT':'JF17.EVT.root'},
                  partition=partitions,
                  binds=binds)
    
    
    command = f"{pre_exec} && simu_trf.py -i %IN -o %OUT -nt $OMP_NUM_THREADS"
    task_2 = Task(name=f"{basename}.HIT",
                  image=image,
                  command=command,
                  input_data=task_1.output('OUT'),
                  outputs= {'OUT':'JF17.HIT.root'},
                  partition=partitions,
                  binds=binds)
    
    
    command = f"{pre_exec} && digit_trf.py -i %IN -o %OUT -nt $OMP_NUM_THREADS --events-per-job {events_per_job} -m"
    task_3 = Task(name=f"{basename}.ESD",
                  image=image,
                  command=command,
                  input_data=task_2.output('OUT'),
                  outputs= {'OUT':'JF17.ESD.root'},
                  partition=partitions,
                  binds=binds)
    
    command = f"{pre_exec} && reco_trf.py -i %IN -o %OUT -nt $OMP_NUM_THREADS --events-per-job {events_per_job} -m"
    task_4 = Task(name=f"{basename}.AOD",
                  image=image,
                  command=command,
                  input_data=task_3.output('OUT'),
                  outputs= {'OUT':'JF17.AOD.root'},
                  partition=partitions,
                  binds=binds)
    
    command = f"{pre_exec} && ntuple_trf.py -i %IN -o %OUT -nt $OMP_NUM_THREADS --events-per-job {events_per_job} -m"
    task_5 = Task(name=f"{basename}.NTUPLE",
                  image=image,
                  command=command,
                  input_data=task_4.output('OUT'),
                  outputs= {'OUT':'JF17.NTUPLE.root'},
                  partition=partitions,
                  binds=binds)
   
   
    session.run()
    
