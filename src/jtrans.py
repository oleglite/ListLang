#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Oleg Beloglazov'

ELEMENT = 'Element'
LIST = 'List'

# JTYPES
VOID_JTYPE = 'V'
INTEGER_JTYPE = 'I'

INTEGER_LIST_CLASS = 'listlang/objects/List'
INTEGER_LIST_JTYPE = 'L%s;' % INTEGER_LIST_CLASS

_type_map = {ELEMENT: INTEGER_JTYPE, LIST: INTEGER_LIST_JTYPE}


class SemanticException(Exception): pass

class UndefinedIDException(SemanticException): pass
class UnsupportedOperation(SemanticException): pass


class JTranslator:

    DEFAULT_STACK_SIZE = 100

    def __init__(self):
        self.functions_jcode = []
        self.scopes_stack = []
        self.walker = None

    def enter_scope(self, scope):
        self.scopes_stack.append(scope)
        self.scope = scope

    def leave_scope(self):
        self.scopes_stack.pop()
        self.scope = self.scopes_stack[-1] if self.scopes_stack else None

    def get_rule_position(self):
        """ Return (line, position_in_line) of begin of current rule """
        symbol = self.walker.input.LT(-1).parent.children[0]
        return symbol.getLine(), symbol.getCharPositionInLine()

    # RULES

    def program(self):
        return self.scope.code_maker.make_class(self.DEFAULT_STACK_SIZE, len(self.scope.vars), ''.join(self.functions_jcode))

    def set_function_return_type(self, return_type):
        self.scope.code_maker.return_jtype = _type_map[return_type]

    def function(self, f_id, f_params, f_scope):
        f_translated_params = [_type_map[type] for id, type in f_params]
        f_jcode = f_scope.code_maker.make_method(
            self.scope.get_function_code_name(f_id), f_translated_params, self.DEFAULT_STACK_SIZE, len(f_scope.vars)
        )
        self.functions_jcode.append(f_jcode)

    def return_operation(self):
        self.scope.code_maker.command_return()

    def assignment_expr(self, var_id, value_type):
        self.scope.add_var(var_id, value_type)
        var_number = self.scope.vars.index(var_id)
        self.scope.code_maker.command_store(_type_map[value_type], var_number)

    # RVALUES (returns value type)

    def list_maker_begin(self):
        """ Calls first for list_maker rule, before args """
        self.scope.code_maker.command_new(INTEGER_LIST_CLASS)
        self.scope.code_maker.command_dup()
        self.scope.code_maker.command_invokespecial(INTEGER_LIST_CLASS, '<init>', [], VOID_JTYPE)
        self.scope.code_maker.command_dup()  # additional copy for args

    def list_maker_arg(self, arg_type):
        """ Calls for every arg """
        if arg_type != ELEMENT:
            raise UnsupportedOperation('Making list of lists is unsupported. (%s:%s)' % self.get_rule_position())

        self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'addLast', [INTEGER_JTYPE], VOID_JTYPE)
        self.scope.code_maker.command_dup()

    def list_maker(self):
        """ Calls last for list_maker rule, return type """
        self.scope.code_maker.command_pop()
        return LIST

    def element_literal(self, value):
        self.scope.code_maker.command_ldc(value)
        return ELEMENT

    def var_identifier(self, id):
        try:
            var_number = self.scope.vars.index(id)
        except ValueError:
            raise UndefinedIDException('Undefined ID "%s" at (%s:%s)' % ((id,) + self.get_rule_position()))

        value_type = self.scope.var_types[id]
        self.scope.code_maker.command_load(_type_map[value_type], var_number)
        return value_type


class JCodeMaker:

    CLASS_HEADER = '''.class public LLMain
.super java/lang/Object
.method public <init>()V
    aload_0
    invokespecial java/lang/Object/<init>()V
    return
.end method
'''

    JMETHOD_TEMPLATE = '''.method public static %s(%s)%s
\t.limit stack %i
\t.limit locals %i
\t%s
.end method

'''  # args: name, params, return_jtype, stack_size, locals_number, code

    INVOKE_TEMPLATE = '%s %s/%s(%s)%s'  # args: invoke_instruction, full_class_name, method, params, return_type


    def __init__(self):
        self.commands = []
        self.return_jtype = 'V'
        self.return_added = False

    def make_class(self, stack_size, locals_number, methods_code):
        """ Make Jasmin class with using commands of this maker for main method """
        return (self.CLASS_HEADER +
                self.make_method('main', ['[Ljava/lang/String;'], stack_size, locals_number) +
                methods_code)

    def make_method(self, name, params, stack_size, locals_number):
        """ Returns code of method with code maked by this maker """
        if not self.return_added:
            self.command_return()
        code = '\n\t'.join(self.commands)
        return self.JMETHOD_TEMPLATE % (name, ''.join(params), self.return_jtype, stack_size, locals_number, code)

    # COMMANDS

    def command_ldc(self, value):
        """ Jasmin command to load constant on stack """
        command =  'ldc %s' % value
        self.commands.append(command)

    def command_store(self, value_jtype, var_number):
        """ Jasmin command to pop from stack var and store it in variable """
        instruction = 'istore' if value_jtype == INTEGER_JTYPE else 'astore'
        command =  '%s %s' % (instruction, var_number)
        self.commands.append(command)

    def command_load(self, value_jtype, var_number):
        """ Jasmin command to push variable to stack """
        instruction =  'iload' if value_jtype == INTEGER_JTYPE else 'aload'
        command = '%s %s' % (instruction, var_number)
        self.commands.append(command)


    def command_return(self):
        """ Jasmin method return command """
        if self.return_jtype == INTEGER_JTYPE:
            instruction = 'ireturn'
        elif self.return_jtype == INTEGER_LIST_JTYPE:
            instruction = 'areturn'
        else:
            instruction = 'return'
        command = instruction
        self.commands.append(command)
        self.return_added = True

    def command_new(self, full_class_name):
        """ Jasmin command new """
        command = 'new ' + full_class_name
        self.commands.append(command)

    def command_dup(self):
        """ Jasmin command to duplicate top value on stack """
        self.commands.append('dup')

    def command_pop(self):
        """ Jasmin command to pop top value from stack """
        self.commands.append('pop')

    def command_invokespecial(self, full_class_name, method, jparams, return_jtype):
        """ Jasmin command to invoke special methods of objects (constructors, ...) """
        command = self.INVOKE_TEMPLATE % ('invokespecial', full_class_name, method, ''.join(jparams), return_jtype)
        self.commands.append(command)

    def command_invokevirtual(self, full_class_name, method, jparams, return_jtype):
        """ Jasmin command to invoke virtual methods of objects """
        command = self.INVOKE_TEMPLATE % ('invokevirtual', full_class_name, method, ''.join(jparams), return_jtype)
        self.commands.append(command)
