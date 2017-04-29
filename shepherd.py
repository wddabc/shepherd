from __future__ import with_statement
import math
from fabric.api import task, hide, show, run, local, env, settings, hosts
from functools import wraps
from fabric.context_managers import cd
import numpy.random as rnd
import os, re, sys
import json

try:
    import cPickle as pickle
except:
    import pickle

maxint = 65535
line_splitter = re.compile('\s+')


# A function wrapper
def shepherd(before=[], after=[]):
    def decorator(func):
        @task
        @hosts('localhost')
        @wraps(func)
        def decorated(*args, **kwargs):
            env.u_func_name = func.__name__
            for bfr in before: bfr()
            try:
                func(*args, **kwargs)
            except KeyboardInterrupt:
                pass
            for afr in after: afr()

        return decorated

    return decorator


def grid_search(func, search_list):
    gs(func, remained=map(lambda x: (x[0], env.get('u_' + x[0], x[1]).split()), search_list))


def gs(func, remained=None, searched=None):
    if searched is None:
        if int(env.get('u_est_total', 0)) == 1:
            total = 1
            for _, lst in remained:
                total *= len(lst)
            print 'Total Jobs:%i' % total
            return
        gs(func, remained=remained, searched=[])
    elif len(remained) == 0:
        env.u_job_handler.submit(*func(searched))
    else:
        name, candidates = remained[0]
        for val in candidates:
            gs(func, remained=remained[1:], searched=searched + [(name, val)])


def arg_conf(val_map):
    return ' '.join('--{0} {1}'.format(k, v) for k, v in val_map), '-'.join(
        '{0}={1}'.format(k[0], v) for k, v in val_map)


def basic_func(header, val_map,
               param_func=lambda x: 'job_' + x,
               jobid_func=lambda x: 'job_' + x):
    args, config = arg_conf(val_map)
    command = header.format(config=param_func(config)) + ' ' + args
    return [command], jobid_func(config)


def _dry_run(command):
    print 'dry_run:', command
    return 'dry_run'


class JobHandler(object):
    def __init__(self, batch_size, dry_run):
        self.__task_counter = 0
        self.__job_counter = 0
        self.__job_queue = []
        self.__batch_size = batch_size
        self._dry_run = dry_run
        self._bash_prfx = ''

    def _valid(self, command, config):
        return True

    def _before(self, id):
        self.script = env.u_scripts + '/' + id + '.sh'
        with open(self.script, 'w') as f:
            print >> f, self._bash_prfx.format(id=id)
            for cmd_list, config in self.__job_queue:
                for cmd in cmd_list:
                    if type(cmd) == tuple and not cmd[1]:
                        print >> f, cmd[0]
                    else:
                        print >> f, cmd + ' | tee -a %(u_std)s/{config}.log'.format(config=config) % env

    def _after(self, id):
        pass

    def _run(self):
        pass

    def __submit_queue(self, id):
        self._before(id)
        self._run()
        self._after(id)
        self.__job_queue = []
        self.__job_counter += 1

    def _finish(self):
        pass

    def submit(self, command, config='TEST'):
        if not self._valid(command, config):
            local('echo skip: ' + config, capture=True)
            return
        self.__task_counter += 1
        self.__job_queue += [(command, config)]
        if len(self.__job_queue) == self.__batch_size:
            self.__submit_queue(config)

    def finish(self):
        if len(self.__job_queue) > 0:
            self.__submit_queue(self.__job_queue[-1][1])
        self._finish()
        print '%i tasks submitted!' % self.__task_counter
        print '%i jobs submitted!' % self.__job_counter


class LocalJobHandler(JobHandler):
    def __init__(self, batch_size=1, dry_run=False):
        super(LocalJobHandler, self).__init__(batch_size, dry_run)
        self._bash_prfx = '#!/bin/bash -l\n' \
                          '#--job-name=%(u_task_name)s_{id}\n' % env
        self._my_run = _dry_run if self._dry_run else local

    def _run(self):
        self._my_run('bash {script}'.format(script=self.script))


class CLSPJobHandler(JobHandler):
    def __init__(self, batch_size=1, dry_run=False):
        super(CLSPJobHandler, self).__init__(batch_size, dry_run)
        env.u_gpu = env.get('u_gpu', '0')
        env.u_cpus = env.get('u_cpus', '1')
        dev_flag = '#$ -pe smp %(u_cpus)s\n' % env
        if int(env.u_gpu) > 0:
            dev_flag += '#$ -l gpu=%(u_gpu)s,h=b1[1-8]*\n' \
                        '#$ -q g.q\n' % env
            env.u_device = 'gpu'
        self._bash_prfx = \
            '#!/bin/bash -l\n' \
            '#$ -N %(u_task_name)s_{id}\n' \
            '#$ -cwd\n' \
            '#$ -l mem_free=%(u_mem)s,ram_free=%(u_mem)s,arch=*64*\n' \
            '#$ -o %(u_std)s/{id}.o\n' \
            '#$ -e %(u_std)s/{id}.e\n' % env + dev_flag

        def _run_grid(message):
            submit_message = local(message, capture=True)
            lines = submit_message.split('\n')
            submit_message = lines[len(lines) - 1]
            return line_splitter.split(submit_message)[2]

        self._my_run = _dry_run if self._dry_run else _run_grid

    def _valid(self, command, id):
        with hide('output', 'running', 'warnings'), settings(warn_only=True):
            ret = local("qstat -u $(whoami) -r | grep 'Full jobname'", capture=True)
            jid = '%(u_task_name)s_{id}'.format(id=id) % env
            return not len(ret) or jid not in [line.split()[2] for line in ret.split('\n')]

    def _run(self):
        self.job_id = self._my_run('qsub {script}'.format(script=self.script))

    def _after(self, id):
        with open(env.u_task_dir + '/.tmp', "a") as f:
            print >> f, "qdel {job_id} #{id}".format(job_id=self.job_id, id=id)

    def _finish(self):
        tmpfile = env.u_task_dir + '/.tmp'
        if os.path.isfile(tmpfile):
            os.rename(tmpfile, env.u_task_dir + '/kill_' + env.u_time + '.sh')


class MarccJobHandler(JobHandler):
    def __init__(self, batch_size=1, dry_run=False):
        super(MarccJobHandler, self).__init__(batch_size, dry_run)
        env.u_queue = env.get('u_queue', 'shared')
        env.u_duration = env.get('u_duration', '12:0:0')
        mem = float(re.compile('(\d+)g').match(env.u_mem).group(1))
        memory_per_cpu = 21.1 if 'mem' in env.u_queue else 5.3
        default_ncpus = int(math.ceil(mem / memory_per_cpu))
        if 'gpu' in env.u_queue:
            cpu_per_gpu = 6
            default_ngpus = int(math.ceil(mem / (memory_per_cpu * cpu_per_gpu)))
            env.u_gpus = int(env.get('u_gpus', default_ngpus))
            env.u_cpus = env.get('u_cpus', env.u_gpus * cpu_per_gpu)
            env.u_device = 'gpu'
            dev_flag = '#SBATCH --gres=gpu:%(u_gpus)s\n' \
                       '#SBATCH --cpus-per-task=%(u_cpus)s\n' % env
        else:
            env.u_cpus = env.get('u_cpus', default_ncpus)
            dev_flag = '#SBATCH --cpus-per-task=%(u_cpus)s\n' % env
        if 'scav' in env.u_queue:
            dev_flag += '#SBATCH --qos=scavenger\n' % env
        self._bash_prfx = \
            '#!/bin/bash -l\n' \
            '#SBATCH --job-name=%(u_task_name)s_{id}\n' \
            '#SBATCH --mem=%(u_mem)s\n' \
            '#SBATCH --ntasks-per-node=1\n' \
            '#SBATCH --time=%(u_duration)s\n' \
            '#SBATCH --requeue\n' \
            '#SBATCH --partition=%(u_queue)s\n' \
            '#SBATCH --output=%(u_std)s/{id}.o\n' \
            '#SBATCH --error=%(u_std)s/{id}.e\n' % env + dev_flag

        #            '#SBATCH --mail-type=ALL\n' \
        #            '#SBATCH --mail-user=%(u_email)s\n' \
        def _run_grid(message):
            submit_message = local(message, capture=True)
            lines = submit_message.split('\n')
            submit_message = lines[len(lines) - 1]
            return line_splitter.split(submit_message)[3]

        self._my_run = _dry_run if self._dry_run else _run_grid

    def _valid(self, command, id):
        with hide('output', 'running', 'warnings'), settings(warn_only=True):
            ret = local("squeue -u $(whoami) -o %j", capture=True)
            jid = '%(u_task_name)s_{id}'.format(id=id) % env
            return jid not in ret.split('\n')

    def _run(self):
        self.job_id = self._my_run('sbatch {script}'.format(script=self.script))

    def _after(self, id):
        with open(env.u_task_dir + '/.tmp', "a") as f:
            print >> f, "scancel {job_id} #{id}".format(job_id=self.job_id, id=id)

    def _finish(self):
        tmpfile = env.u_task_dir + '/.tmp'
        if os.path.isfile(tmpfile):
            os.rename(tmpfile, env.u_task_dir + '/kill_' + env.u_time + '.sh')


class MarccInteractJobHandler(MarccJobHandler):
    def __init__(self, batch_size=1, dry_run=False):
        super(MarccInteractJobHandler, self).__init__(batch_size, dry_run)
        self.runner = 'srun'
        self._my_run = _dry_run if self._dry_run else run

    def _run(self):
        self._my_run('{runner} {script}'.format(runner=self.runner,
                                                script=self.script))


def make_dirs():
    env.u_jobs = '%(u_out)s/jobs' % env
    env.u_task_dir = '%(u_jobs)s/%(u_task_name)s' % env
    env.u_std = '%(u_task_dir)s/std' % env
    env.u_tmp = '%(u_task_dir)s/tmp' % env
    env.u_log = '%(u_task_dir)s/log' % env
    env.u_model = '%(u_task_dir)s/model' % env
    env.u_src = '%(u_task_dir)s/src' % env
    env.u_scripts = '%(u_task_dir)s/scripts' % env
    env.u_output = '%(u_task_dir)s/output' % env
    env.u_evaluation = '%(u_task_dir)s/eval' % env
    env.u_test_evaluation = '%(u_evaluation)s/test' % env
    for dir in [env.u_jobs,
                env.u_task_dir,
                env.u_std, env.u_tmp, env.u_log,
                env.u_model,
                env.u_src,
                env.u_scripts,
                env.u_output,
                env.u_evaluation,
                env.u_test_evaluation]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def init_laptop(batch_size=1, dry_run=False):
    env.u_host = 'laptop'
    make_dirs()
    with show('output', 'running', 'warnings'), cd(env.u_workspace):
        run('cp -r -n %(u_workspace)s/src/* %(u_src)s' % env)
    env.u_job_handler = LocalJobHandler(batch_size, dry_run)
    env.u_verbose = int(env.get('u_verbose', 1))


def init_clsp_grid(batch_size=1, dry_run=False):
    env.u_host = 'clsp'
    make_dirs()
    env.u_job_handler = LocalJobHandler(batch_size, dry_run) if env.u_local else  CLSPJobHandler(batch_size, dry_run)


def init_marcc(batch_size=1, dry_run=False):
    env.u_host = 'marcc'
    make_dirs()
    if env.u_local:
        env.u_job_handler = LocalJobHandler(batch_size, dry_run)
    else:
        env.u_interact = int(env.get('u_interact', 0))
        env.u_job_handler = MarccInteractJobHandler(batch_size, dry_run) \
            if env.u_debug == 1 or env.u_interact == 1 else MarccJobHandler(batch_size, dry_run)


def init_cluster(batch_size=1, dry_run=False):
    env.u_job_number = env.get('u_job_number', 100000)
    env.u_domainname = local('domainname', capture=True)
    env.u_wait = env.get('u_wait', '24:00:00')
    if env.u_domainname == 'clsp':
        init_clsp_grid(batch_size, dry_run)
    elif env.u_domainname == '(none)':
        init_marcc(batch_size, dry_run)
    with show('output', 'running', 'warnings'), cd(env.u_workspace):
        local('cp -r -n %(u_workspace)s/src/* %(u_src)s' % env)
    env.u_verbose = int(env.get('u_verbose', 0))


def load_conf():
    if os.path.isfile('.shepherd.config'):
        with open('.shepherd.config') as json_data:
            env_default = json.load(json_data)
            for name, val in env_default.items():
                if name not in env:
                    env[name] = val


def init():
    with hide('output', 'running', 'warnings'), settings(warn_only=True):
        load_conf()
        env.u_task_spec = env.get('u_task_spec', 'TEST')
        env.u_task_prfx = env.get('u_task_prfx', '')
        env.u_task_name = '%(u_task_prfx)s%(u_func_name)s_%(u_task_spec)s' % env
        env.u_time = env.get('u_time', local('date +%Y_%m_%d_%H_%M_%S', capture=True))
        env.u_device = env.get('u_device', 'cpu')
        env.u_seed = int(env.get('u_seed', 345))
        env.u_debug = int(env.get('u_debug', 0))
        env.u_local = int(env.get('u_local', 0))
        rnd.seed(int(env.get('u_random', 123)))
        env.u_mem = env.get('u_mem', '5g')
        env.u_python = env.get('u_python', 'python')
        env.u_th_mode = env.get('u_theano_mode', 'FAST_RUN')
        env.u_java = env.get('u_java', 'java')
        env.u_hostname = local('hostname', capture=True)
        bs, dry = int(env.get('u_bs', 1)), False if int(env.get('u_dry', 0)) == 0 else True
        env.u_workspace = env.get('u_workspace', os.getcwd())
        env.u_data = env.get('u_data', os.path.join('%(u_workspace)s' % env, 'data'))
        env.u_out = env.get('u_out', os.getcwd())
        if env.u_hostname.startswith('ous'):
            init_laptop(bs, dry)
        else:
            init_cluster(bs, dry)
        env.u_latest = int(env.get('u_latest', 0))
        env.u_python_dir = '%(u_workspace)s/src/python' % env if env.u_latest else '%(u_src)s/python' % env
        env.u_exe_dir = '%(u_workspace)s/exe' % env
        print 'task name: %(u_task_name)s' % env


def post():
    env.u_job_handler.finish()
