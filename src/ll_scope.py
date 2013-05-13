#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Oleg Beloglazov'

import jtrans

LOG_STR = ''

def log(string):
    global LOG_STR
    LOG_STR += str(string) + '\n'

class Scope:

    count = 0

    def __init__(self):
        self.num = self.count
        log('init scope %i' % Scope.count)
        Scope.count += 1

        self.vars = []
        self.var_types = {}      # dict {var_id: var_type}
        self.funcs = []     # list of tuples (function_id, function_type, function_params_types, function_scope, ...)
        self.code_maker = jtrans.JCodeMaker()

    def add_function(self, f_id, f_type, f_params, f_scope):
        log('%i function' % f_scope.num)
        self.funcs.append((f_id, f_type, f_params, f_scope))

    def add_var(self, var_id, var_type):
        if var_id in self.var_types: log('warning: var replacement "%i"' % var_id)

        self.vars.append(var_id)

        self.var_types[var_id] = var_type

    def get_function_code_name(self, name):
        return 's%i_%s' % (self.num, name)



    def __contains__(self, item):
        return item in [var[0] for var in self.vars] + [func[0] for func in self.funcs]

