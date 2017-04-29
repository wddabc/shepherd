# Shepherd 

Shepherd is a simple python framework for managing experimental jobs locally and on clusters. Although the target users are originally the [CLSP](https://www.clsp.jhu.edu/) students at [JHU](https://www.clsp.jhu.edu/), people from other places are welcome to use since the changes should be trivial. 

The key features of Shepherd include:

* Keep track of all the experiments, including scripts, models, outputs, logs, code backups. 

* Auto-detects the system and decides the behavior, for example, when doing grid search on local computers, it will run jobs serially. When using clusters, it will submit jobs instead. All you need is writing exactly the same command.

* The current version supports the basic commands of two workload managers: [Sun Grid Engine](http://gridscheduler.sourceforge.net/htmlman/manuals.html) and [Slurm](https://slurm.schedmd.com/). For CLSPers they are CLSP grid and MARCC respectively.

### Requirements 

* [fabric](http://www.fabfile.org/)


### Usage

Easy, first copy the `shepherd.py` into your working directory, then create and edit your own `fabfile.py` and enjoy.

This repository just gives a working example. After checking out this repo. There is an implementation of your brilliant idea, say, `src/python/example.py`. Running so you need: 

       	python src/python/example.py --param1 123 --param2 64 --param3 0.1 --param4 relu 

This program takes 4 hyperparameters --param[1-4]. Now you want to try out some other hyperparameters by grid search. You can create a function in `fabfile.py` with the snippet like this:

```python
@shepherd(before=[init], after=[post])
def exp1():
    header_pattern = 'python %(u_python_dir)s/example.py --param1 123'
    id = 0
    for param2 in [64, 128, 256, 512, 1024]:
        param2_str = ' --param2 %s' % str(param2)
        for param3 in [0.1, 0.01, 0.001, 0.0001]:
            param3_str = ' --param3 %s' % str(param3)
            for param4 in ['relu', 'tanh', 'sigmoid']:
                param4_str = ' --param4 %s' % str(param4)
                id += 1
                command = header_pattern % env + param2_str + param3_str + param4_str
                env.u_job_handler.submit([command], str(id))

```

This snippet is already in the `fabfile.py` of this repo, the basic idea is just generating the python command strings (5 * 4  * 3 = 60 combinations) and submit to the `job_handler`. Then run:

 
		fab --set=u_task_spec=example exp1


in the command line, where `u_task_spec=example` sets the name of the task. It will run all the experiments and store everything into a new creates folder named `job/exp1_example`, which includes 8 folders. In this example, only 2 of them are used, `script` stores the all the scripts generated, `std` stores all the system outputs. 

If this command is executed on the cluster, it will submit 60 jobs to the cluster instead. In  `job/exp1_example`, there will be an additional script starts with `kill_` in case you submit these jobs by mistake and want kill all of them. 

