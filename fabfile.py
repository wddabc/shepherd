#!/usr/bin/python
# coding=utf-8
# --------------------------------------- 
# File Name : fabfile.py
# Creation Date : 02-05-2016
# Last Modified : Thu Sep  1 23:06:54 2016
# Created By : wdd 
# --------------------------------------- 
from __future__ import with_statement

import os, re
from subprocess import call
from fabric.api import task, hosts, env, run
from fabric.context_managers import cd
from shepherd import wraper, init, post, grid_search, basic_func, load_conf
import numpy as np

@task
@hosts('localhost')
@wraper(before=[compile])
def git():
    info = env.get('u_msg', 'minor')
    env.u_workspace = os.getcwd()
    with cd(env.u_workspace):
        call('git pull;git commit -am "SYNC:{}";git push'.format(info), shell=True)
        call('git describe > src/version.txt', shell=True)


@task
@hosts('localhost')
@wraper(before=[load_conf, compile, git])
def sync():
    env.u_workspace = os.getcwd()
    with cd(env.u_workspace):
        for rmt in env.u_remote.split(';'):
            run('rsync -av *.py src %s' % rmt)
