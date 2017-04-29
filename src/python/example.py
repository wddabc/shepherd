#!/usr/bin/python
# --------------------------------------- 
# File Name :
# Creation Date : 28-04-2017
# Last Modified : Fri Apr 28 18:45:38 2017
# Created By : wdd 
# --------------------------------------- 
import argparse

_arg_parser = argparse.ArgumentParser()
_arg_parser.add_argument('--param1', default=0, type=int, action='store', help='')
_arg_parser.add_argument('--param2', default=0, type=int, action='store', help='')
_arg_parser.add_argument('--param3', default=0, type=float, action='store', help='')
_arg_parser.add_argument('--param4', default='', type=str, action='store', help='')
_args = _arg_parser.parse_args()

if __name__ == "__main__":
    print 'Running with: param1=%i, param2=%i, param3=%.f, param4=%s' % (
        _args.fixed_param, _args.param1, _args.param2, _args.param3)
