# Shepherd 

Shepherd is a simple python framework for managing experimental jobs locally and on clusters. Although the target users are originally the [CLSP](https://www.clsp.jhu.edu/) students at [JHU](https://www.clsp.jhu.edu/), people from other places are welcome to use since the changes should be trivial. 

The key features of Shepherd include:

* Keep track of all the experiments, including scripts, models, outputs, logs, code backups. 

* Auto-detects the system and decides the behavior, for example, when doing grid search on local computers, it will run jobs serially. When on clusters, it will submit jobs instead.

* The current version supports the basic commands of two workload managers: [Sun Grid Engine](http://gridscheduler.sourceforge.net/htmlman/manuals.html) and [Slurm](https://slurm.schedmd.com/). For CLSPers they are CLSP grid and MARCC respectively.

### Requirements 

* [fabric](http://www.fabfile.org/)


### Usage

Easy, first copy the `shepherd.py` into your working directory, then create and edit your own `shepherd.py` and enjoy. This repository just give a working example.

