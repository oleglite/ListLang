#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Oleg Beloglazov'

import jcodemaker

LOG_STR = ''

def log(string):
    global LOG_STR
    LOG_STR += str(string) + '\n'

class Scope:

    total_scopes_number = 0

    def __init__(self, global_scope=None):
        """ global_scope - scope that global for this scope, None if this scope is global """

        self.scope_number = self.total_scopes_number
        log('init scope %i' % Scope.total_scopes_number)
        Scope.total_scopes_number += 1

        self.vars = []
        self.var_types = {}      # dict {var_id: var_type}
        self.funcs = {}     # {function_id: (function_type, function_params_types, function_scope, ...)}
        self.code_maker = jcodemaker.JCodeMaker()
        if global_scope:
            self.global_scope = global_scope
            self.global_vars = []
        else:
            self.global_scope = self
            self.global_vars = None

    def is_global(self):
        return self.global_scope is self

    def add_function(self, f_id, f_type, f_params, f_scope):
        log('%i function' % f_scope.scope_number)
        f_params_types = [param[1] for param in f_params]
        self.funcs[f_id] = (f_type, f_params_types, f_scope)

    def add_var(self, var_id, var_type):
        self.vars.append(var_id)
        self.var_types[var_id] = var_type

    def add_global_var(self, var_id):
        self.global_vars.append(var_id)

    def get_function_code_name(self, name):
        return 's%i_%s' % (self.scope_number, name)

    def contains_var(self, var_id):
        return var_id in self.vars or (not self.is_global() and var_id in self.global_vars)