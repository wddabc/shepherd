#!/usr/bin/python
# coding=utf-8
# --------------------------------------- 
# File Name : fabfile.py
# Creation Date : 02-05-2016
# Last Modified : Thu Sep  1 23:06:54 2016
# Created By : wdd 
# --------------------------------------- 
from __future__ import with_statement

import os
from fabric.api import env, run
from fabric.context_managers import cd
from shepherd import shepherd, init, post, grid_search, basic_func, load_conf


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


@shepherd(before=[init], after=[post])
def exp2():
    header_pattern = 'python %(u_python_dir)s/example.py --param1 123'
    search_list = [
        ('param2', '64 128 256 512 1024'),
        ('param3', '0.1 0.01 0.001 0.0001'),
        ('param4', 'relu tanh sigmoid'),
    ]
    grid_search(lambda map: basic_func(header_pattern % env, map), search_list)


@shepherd(before=[load_conf])
def sync():
    env.u_workspace = os.getcwd()
    with cd(env.u_workspace):
        for rmt in env.u_remote.split(';'):
            run('rsync -av *.py src %s' % rmt)
