#!/usr/bin/python
# --------------------------------------- 
# File Name :
# Creation Date : 28-04-2017
# Last Modified : Fri Apr 28 18:45:38 2017
# Created By : wdd 
# --------------------------------------- 
import sys, re, string, pickle, theano, argparse
import theano.tensor as T
import numpy as np
from itertools import *

_arg_parser = argparse.ArgumentParser()
_arg_parser.add_argument('--task', default='main', type=str, action='store', help='')
_arg_parser.add_argument('--x', default=0, type=int, action='store', help='')
_args = _arg_parser.parse_args()

def _config(args_dict=vars(_args)):
    return '\n'.join("{0}:{1}".format(key, val) for (key, val) in args_dict.items())


def main():
    pass

if __name__ == "__main__": locals()[_args.task]()
