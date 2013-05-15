#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Oleg Beloglazov'

import jtrans

LOG_STR = ''

def log(string):
    global LOG_STR
    LOG_STR += str(string) + '\n'

class Scope:

    total_scopes_number = 0

    def __init__(self):
        self.scope_number = self.total_scopes_number
        log('init scope %i' % Scope.total_scopes_number)
        Scope.total_scopes_number += 1

        self.vars = []
        self.var_types = {}      # dict {var_id: var_type}
        self.funcs = {}     # {function_id: (function_type, function_params_types, function_scope, ...)}
        self.code_maker = jtrans.JCodeMaker()

    def add_function(self, f_id, f_type, f_params, f_scope):
        log('%i function' % f_scope.scope_number)
        f_params_types = [param[1] for param in f_params]
        self.funcs[f_id] = (f_type, f_params_types, f_scope)

    def add_var(self, var_id, var_type):
        if var_id in self.var_types: log('warning: var replacement "%i"' % var_id)

        self.vars.append(var_id)
        self.var_types[var_id] = var_type

    def get_function_code_name(self, name):
        return 's%i_%s' % (self.scope_number, name)