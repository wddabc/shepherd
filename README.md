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

### Example 1 

This repository just gives a working example. After checking out this repo, there is an implementation of your brilliant idea, say, `src/python/example.py`. Running so you need: 

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


in the command line, where `u_task_spec=example` sets the name of the task. It will run all the experiments and store everything into a new creates folder named `job/exp1_example`, which includes 8 folders. In this example, only 3 of them are used, `script` stores the all the scripts generated, `std` stores all the system outputs, `src` is a copy of the current code you are running. 

If this command is executed on the cluster, it will submit 60 jobs to the cluster instead. In  `job/exp1_example`, there will be an additional script starts with `kill_` in case you submit these jobs by mistake and want kill all of them. 

### Example 2 

The above example should be good enough so far. If you want a life even easier, try out `exp2()`, which does exactly the same thing as `exp1()`, with fewer lines of code:

```python
@shepherd(before=[init], after=[post])
def exp2():
    header_pattern = 'python %(u_python_dir)s/example.py --param1 123'
    search_list = [
        ('param2', '64 128 256 512 1024'),
        ('param3', '0.1 0.01 0.001 0.0001'),
        ('param4', 'relu tanh sigmoid'),
    ]
    grid_search(lambda map: basic_func(header_pattern % env, map), search_list)
```

Try


		fab --set=u_task_spec=example exp2

and see what's in `job/exp2_example`. In this example, if you are not happy with the hardcoded hyperparameter candidates, for instance, `param2` you can do:

		fab --set=u_task_spec=example,u_param2="100 200 300" exp2

. It will use `100 200 300` instead of the default `64 128 256 512 1024`.


### Useful Tips

**Dry run** (`u_dry=1`): This will just generate the script without running (submitting) in the `script` folder.  

**Run the lastest version** (`u_latest=1`): Run the latest version of the source code. See [IMPORTANT](#IMPORTANT) for details.

**Submit job batches** (`u_bs=tasks per job`): Numbers of tasks per job. The example commands so far generate 60 tasks with 60 jobs (scripts). If you are trying thousands of combinations with one combination (task) per job, you are probably killing the cluster's job scheduler or blocking other users, then your cluster administrators will probably put you into the Death Note, so don't do that. Try to add `u_bs`, for example. `fab --set=u_task_spec=example,u_bs=20 exp1` will submit 3 scripts with 20 jobs for each, where these 20 jobs will be executed serially. 

**Set queue to run the jobs** (`u_queue`): This is only for MARCC users
 
### IMPORTANT

When you running the same command twice, the following behaviors should be keep in mind.

**`src` folder**: By default, Shepherd will run the copied code in `job/exp1_example/src` instead of the source code in your workspace. This means, if do the following:

1. Run `fab --set=u_task_spec=example exp1`

2. Make changes of the source code in your workspace

3. Run `fab --set=u_task_spec=example exp1` again 

It won't work as you might want. This will still use the old code in `job/exp1_example/src`. To get away with this, you can. 

1. Delete `job/exp1_example` before run the command again 

2. Directly change the code in `job/exp1_example/src`

3. Try `fab --set=u_task_spec=example_v2 exp1`, which will create a new `job/exp1_example_v2/src` and the code is up-to-date.

4. Use `fab --set=u_task_spec=example,u_latest=1 exp1`, as suggested in the [Useful Tips](#Useful-Tips) This will run the code in your workspace, although the code in `job/exp1_example/src` is still the old version.

**`std` folder** : `.log` files will be appended rather than overwritten.

**others**: Will be overwritten if the same file name encountered.

**Runing on the cluster**: A job will be skipped if there is a job with the same job name already running.

