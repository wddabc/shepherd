# Shepherd 

Shepherd is a simple python framework for managing experimental jobs locally and on clusters. Although the target users are originally the [CLSP](https://www.clsp.jhu.edu/) students at [JHU](https://www.clsp.jhu.edu/), people from other places are welcome to use since the changes should be trivial. 

The key features of Shepherd include:

* Keep track of all the experiments, including scripts, models, outputs, logs, code backups. 

* Auto-detects the system and decides the behavior, for example, when doing grid search on local computers, it will run jobs serially. When using clusters, it will submit jobs instead. All you need is writing exactly the same command.

* The current version supports the basic commands of two workload managers: [Sun Grid Engine](http://gridscheduler.sourceforge.net/htmlman/manuals.html) and [Slurm](https://slurm.schedmd.com/). For CLSPers they are CLSP grid and MARCC respectively.

### Requirements 

* Python3 


### Usage

Easy, first copy the `shepherd.py` into your working directory, then create and edit your own `fabfile.py` and enjoy.

### Example 1 

This repository just gives a working example. After checking out this repo, there is an implementation of your brilliant idea, say, `src/python/example.py`. Running so you need: 

       	python src/python/example.py --param1 123 --param2 64 --param3 0.1 --param4 relu 

This program takes 4 hyperparameters --param[1-4]. Now you want to try out some other hyperparameters by grid search. You can create a function in `fabfile.py` with the snippet like this:

```python
@shepherd(before=[init], after=[post])
def exp1():
    cmd_base = 'python %(python_dir)s/example.py --param1 123' % SYS
    id = 0
    for param2 in [64, 128, 256, 512, 1024]:
        param2_str = ' --param2 %s' % str(param2)
        for param3 in [0.1, 0.01, 0.001, 0.0001]:
            param3_str = ' --param3 %s' % str(param3)
            for param4 in ['relu', 'tanh', 'sigmoid']:
                param4_str = ' --param4 %s' % str(param4)
                id += 1
                command = cmd_base + param2_str + param3_str + param4_str
                SPD().submit([command], str(id))

```

This snippet is already in the `experiment.py` of this repo, the basic idea is just generating the python command strings (5 * 4  * 3 = 60 combinations) and submit to the `SPD()`. Then run:

 
		python shepherd.py exp1-foo


in the command line, where `foo`, which is after the hyphen, sets the name of the task. It will run all the experiments and store everything into a new creates folder named `job/exp1-foo`, which includes 8 folders. In this example, only 3 of them are used, `script` stores the all the scripts generated, `std` stores all the system outputs, `src` is a copy of the current code you are running. 

If this command is executed on the cluster, it will submit 60 jobs to the cluster instead. In  `job/exp1-foo`, there will be an additional script starts with `info-` which includes the metadata of the submitted jobs (such as the job name, job ids, etc.).

### Example 2 

The above example should be good enough so far. If you want a life even easier, try out `exp2()`, which does exactly the same thing as `exp1()`, with fewer lines of code:

```python
@shepherd(before=[init], after=[post])
def exp2():
    command_base = 'python %(python_dir)s/example.py --param1 123' % SYS
    search_list = [
        ('param2', '64 128 256 512 1024'),
        ('param3', '0.1 0.01 0.001 0.0001'),
        ('param4', 'relu tanh sigmoid'),
    ]
    grid_search(lambda map: basic_func(command_base, map), search_list)
```

Try

		python shepherd.py exp2-foo

and see what's in `job/exp2-example`. In this example, if you are not happy with the hardcoded hyperparameter candidates, for instance, `param2` you can do:

		python shepherd.py exp2-foo -u param2="100 200 300"

. It will use `100 200 300` instead of the default `64 128 256 512 1024`. `-u` leads the keyword arguments, which can be visited by attributes of `USR`.
For example, if we have:

```python
@shepherd(before=[init], after=[post])
def exp3():
    print(USR.bar)
```

and we run:

		python shepherd.py exp3-foo -u bar="hellow world"

it will print `hellow world`.


### Useful Tips

**Dry run** (`-d`): This will just generate the script without running (submitting) in the `script` folder.  

**Run the lastest version** (`-l`): Run the latest version of the source code. See [IMPORTANT](#IMPORTANT) for details.

**Submit job batches** (`-b`): Numbers of tasks per job. The example commands so far generate 60 tasks with 60 jobs (scripts). If you are trying thousands of combinations with one combination (task) per job, you are probably killing the cluster's job scheduler or blocking other users, so don't do that. Try to add `-b`, for example. `python shepherd.py exp2-foo -b 20` will submit 3 scripts with 20 jobs for each, where these 20 jobs will be executed serially. 

**Random search** (`-r`): Another way to reduce the number of jobs by randomly skipping the jobs with probability `1 - r`.

**System arguments** (`-s`): Set the system arguments when running on the server, which are set by keywords. For example:
 
		python shepherd.py exp2-foo -u param2="100 200 300" -s queue=shared mem=20g duration=72:00:00

submits the jobs to the `shared` queue, with memory limit 20g and time limit 72 hours. Note that these values can be visited by attributes of `SYS`.

### IMPORTANT

When you running the same command twice, the following behaviors should be keep in mind.

**`src` folder**: By default, Shepherd will run the copied code in `job/exp1-foo/src` instead of the source code in your workspace. This means, if do the following:

1. Run `python shepherd.py exp1-foo`

2. Make changes of the source code in your workspace

3. Run `python shepherd.py exp1-foo` again 

It won't work as you might want. This will still use the old code in `job/exp1-foo/src`. To get away with this, you can. 

1. Delete `job/exp1-foo` before run the command again, or 

2. Directly change the code in `job/exp1-foo/src`, or

3. Try `python shepherd.py exp1-bar`, which will create a new `job/exp1-bar/src` and the code is up-to-date.

4. Use `python shepherd.py exp1-bar -l`, as suggested in the [Useful Tips](#Useful-Tips) This will run the code in your workspace, although the code in `job/exp1-bar/src` is still the old version.

**`std` folder** : `.log` files will be appended rather than overwritten.

**others**: Will be overwritten if the same file name encountered.

**Runing on the cluster**: A job will be skipped if there is a job with the same job name already running.

