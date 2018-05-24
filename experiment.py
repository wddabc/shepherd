from shepherd import shepherd,SPD, init, post, grid_search, basic_func
from shepherd import SYS


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


@shepherd(before=[init], after=[post])
def exp2():
    command_base = 'python %(python_dir)s/example.py --param1 123' % SYS
    search_list = [
        ('param2', '64 128 256 512 1024'),
        ('param3', '0.1 0.01 0.001 0.0001'),
        ('param4', 'relu tanh sigmoid'),
    ]
    grid_search(lambda map: basic_func(command_base, map), search_list)
