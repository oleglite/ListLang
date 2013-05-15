#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Oleg Beloglazov'

ELEMENT = 'Element'
LIST = 'List'

# JTYPES
VOID_JTYPE = 'V'
INTEGER_JTYPE = 'I'
STRING_JTYPE = 'Ljava/lang/String;'

INTEGER_LIST_CLASS = 'listlang/objects/List'
INTEGER_LIST_JTYPE = 'L%s;' % INTEGER_LIST_CLASS

_type_map = {ELEMENT: INTEGER_JTYPE, LIST: INTEGER_LIST_JTYPE}

RESERVED_LOCALS = 10


class SemanticException(Exception):
    def __init__(self, line, pos_in_line, message):
        self.line = line
        self.pos_in_line = pos_in_line
        self.message = message
        
    def __str__(self):
        return '%i:%i %s' % (self.line, self.pos_in_line, self.message)

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
        symbol = self.walker.input.LT(-1)
        if symbol.parent:
            symbol = symbol.parent.children[0]
        return symbol.getLine(), symbol.getCharPositionInLine()

    def get_var_number(self, var_id):
        try:
            var_number = self.scope.vars.index(var_id)
        except ValueError:
            line, pos = self.get_rule_position()
            raise UnsupportedOperation(line, pos, 'Undefined ID "%s".' % var_id)
        return RESERVED_LOCALS + var_number

    # RULES

    def program(self):
        return self.scope.code_maker.make_class(self.DEFAULT_STACK_SIZE, RESERVED_LOCALS + len(self.scope.vars),
                                                ''.join(self.functions_jcode))

    def set_function_return_type(self, return_type):
        self.scope.code_maker.return_jtype = _type_map[return_type]

    def function(self, f_id, f_params, f_scope):
        f_translated_params = [_type_map[type] for id, type in f_params]
        f_jcode = f_scope.code_maker.make_method(
            self.scope.get_function_code_name(f_id), f_translated_params,
            self.DEFAULT_STACK_SIZE, RESERVED_LOCALS + len(f_scope.vars)
        )
        self.functions_jcode.append(f_jcode)

    def print_value(self, value_type):
        if value_type == ELEMENT:
            self.scope.code_maker.command_invokestatic(JCodeMaker.CLASS_NAME, 'print', [INTEGER_JTYPE], VOID_JTYPE)
        elif value_type == LIST:
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'print', [], VOID_JTYPE)
        self.scope.code_maker.command_ldc('" "')
        self.scope.code_maker.command_invokestatic(JCodeMaker.CLASS_NAME, 'print', [STRING_JTYPE], VOID_JTYPE)

    def print_operation(self):
        self.scope.code_maker.command_ldc('"\\n"')
        self.scope.code_maker.command_invokestatic(JCodeMaker.CLASS_NAME, 'print', [STRING_JTYPE], VOID_JTYPE)

    def return_operation(self):
        self.scope.code_maker.command_return()

    def assignment_expr(self, var_id, value_type):
        self.scope.add_var(var_id, value_type)
        self.scope.code_maker.command_store(_type_map[value_type], self.get_var_number(var_id))

    # RVALUES (returns value type)

    def or_expr(self, type1, type2):
        if type2 == LIST:
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'to_int', [], INTEGER_JTYPE)
        if type1 == LIST:
            self.scope.code_maker.command_swap()
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'to_int', [], INTEGER_JTYPE)
            self.scope.code_maker.command_swap()

        true1_label = self.scope.code_maker.make_label('OR_TRUE1')
        true2_label = self.scope.code_maker.make_label('OR_TRUE2')
        or_end_label = self.scope.code_maker.make_label('OR_END')

        self.scope.code_maker.command_swap()
        self.scope.code_maker.command_ifne(true1_label)
        self.scope.code_maker.command_ifne(true2_label)
        self.scope.code_maker.command_ldc(0)
        self.scope.code_maker.command_goto(or_end_label)
        self.scope.code_maker.command_label(true1_label)
        self.scope.code_maker.command_pop()
        self.scope.code_maker.command_label(true2_label)
        self.scope.code_maker.command_ldc(1)
        self.scope.code_maker.command_label(or_end_label)

        return ELEMENT

    def and_expr(self, type1, type2):
        if type2 == LIST:
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'to_int', [], INTEGER_JTYPE)
        if type1 == LIST:
            self.scope.code_maker.command_swap()
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'to_int', [], INTEGER_JTYPE)
            self.scope.code_maker.command_swap()

        false1_label = self.scope.code_maker.make_label('AND_FALSE1')
        false2_label = self.scope.code_maker.make_label('AND_FALSE')
        and_end_label = self.scope.code_maker.make_label('AND_END')

        self.scope.code_maker.command_swap()
        self.scope.code_maker.command_ifeq(false1_label)
        self.scope.code_maker.command_ifeq(false2_label)
        self.scope.code_maker.command_ldc(1)
        self.scope.code_maker.command_goto(and_end_label)
        self.scope.code_maker.command_label(false1_label)
        self.scope.code_maker.command_pop()
        self.scope.code_maker.command_label(false2_label)
        self.scope.code_maker.command_ldc(0)
        self.scope.code_maker.command_label(and_end_label)

        return ELEMENT

    def equality_expr(self, operator, type1, type2):
        if type1 == type2 == ELEMENT:
            eq_true_label = self.scope.code_maker.make_label('EQ_TRUE')
            eq_end_label = self.scope.code_maker.make_label('EQ_END')

            self.scope.code_maker.command_if_icmpeq(eq_true_label)
            self.scope.code_maker.command_ldc(0)
            self.scope.code_maker.command_goto(eq_end_label)
            self.scope.code_maker.command_label(eq_true_label)
            self.scope.code_maker.command_ldc(1)
            self.scope.code_maker.command_label(eq_end_label)

        elif type1 == type2 == LIST:
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'equal', [INTEGER_LIST_JTYPE], INTEGER_JTYPE)

        else:
            self.scope.code_maker.command_pop()
            self.scope.code_maker.command_pop()
            self.scope.code_maker.command_ldc(0)

        if operator == '!=':
            self.not_expr(ELEMENT)

        return ELEMENT

    def relational_expr(self, operator, type1, type2):
        if type1 == LIST or type2 == LIST:
            line, pos = self.get_rule_position()
            raise UnsupportedOperation(line, pos, 'Relational operation (%s) for lists is unsupported.' % operator)

        rel_true_label = self.scope.code_maker.make_label('REL_TRUE')
        rel_end_label = self.scope.code_maker.make_label('REL_END')

        if operator == '<': self.scope.code_maker.command_if_icmplt(rel_true_label)
        elif operator == '<=': self.scope.code_maker.command_if_icmple(rel_true_label)
        elif operator == '>': self.scope.code_maker.command_if_icmpgt(rel_true_label)
        elif operator == '>=': self.scope.code_maker.command_if_icmpge(rel_true_label)

        self.scope.code_maker.command_ldc(0)
        self.scope.code_maker.command_goto(rel_end_label)
        self.scope.code_maker.command_label(rel_true_label)
        self.scope.code_maker.command_ldc(1)
        self.scope.code_maker.command_label(rel_end_label)

        return ELEMENT

    def additive_expr(self, operator, type1, type2):
        if operator == '+':
            if type1 == type2 == ELEMENT:
                self.scope.code_maker.command_iadd()
                return ELEMENT
            elif type1 == type2 == LIST:
                self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'concat', [INTEGER_LIST_JTYPE], INTEGER_LIST_JTYPE)
                return LIST
            elif type1 == ELEMENT and type2 == LIST:
                self.scope.code_maker.command_dup()
                self.scope.code_maker.command_store(INTEGER_LIST_JTYPE, 0)
                self.scope.code_maker.command_swap()
                self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'addFirst', [INTEGER_JTYPE], VOID_JTYPE)
                self.scope.code_maker.command_load(INTEGER_LIST_JTYPE, 0)
                return LIST
            elif type1 == LIST and  type2 == ELEMENT:
                self.scope.code_maker.command_swap()
                self.scope.code_maker.command_dup()
                self.scope.code_maker.command_store(INTEGER_LIST_JTYPE, 0)
                self.scope.code_maker.command_swap()
                self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'addLast', [INTEGER_JTYPE], VOID_JTYPE)
                self.scope.code_maker.command_load(INTEGER_LIST_JTYPE, 0)
                return LIST
        elif operator == '-':
            if type1 == type2 == ELEMENT:
                self.scope.code_maker.command_isub()
                return ELEMENT
            else:
                line, pos = self.get_rule_position()
                raise UnsupportedOperation(line, pos,
                                           'Additive expression (%s %s %s) is unsupported.' % (type1, operator, type2))

    def multiplicative_expr(self, operator, type1, type2):
        if operator == '*':
            if type1 == type2 == ELEMENT:
                self.scope.code_maker.command_imul()
                return ELEMENT
            elif type1 == LIST and type2 == ELEMENT:
                self.scope.code_maker.command_invokevirtual(
                    INTEGER_LIST_CLASS, 'multiply', [INTEGER_JTYPE], INTEGER_LIST_JTYPE
                )
                return LIST

        elif operator == '/':
            if type1 == type2 == ELEMENT:
                self.scope.code_maker.command_idiv()
                return ELEMENT
            elif type1 == LIST and type2 == ELEMENT:
                self.scope.code_maker.command_invokevirtual(
                    INTEGER_LIST_CLASS, 'removeEvery', [INTEGER_JTYPE], INTEGER_LIST_JTYPE
                )
                return LIST

        elif operator == '%':
            if type1 == type2 == ELEMENT:
                self.scope.code_maker.command_irem()
                return ELEMENT
            elif type1 == LIST and type2 == ELEMENT:
                self.scope.code_maker.command_swap()
                self.scope.code_maker.command_dup()
                self.scope.code_maker.command_store(INTEGER_LIST_JTYPE, 0)
                self.scope.code_maker.command_swap()
                self.scope.code_maker.command_invokevirtual(
                    INTEGER_LIST_CLASS, 'del', [INTEGER_JTYPE], VOID_JTYPE
                )
                self.scope.code_maker.command_load(INTEGER_LIST_JTYPE, 0)
                return LIST

        line, pos = self.get_rule_position()
        raise UnsupportedOperation(line, pos,
                                   'Multiplicative expression (%s %s %s) is unsupported.' % (type1, operator, type2))
                                   
    def pre_incr_expr(self, value_type):
        if value_type == ELEMENT:
            self.scope.code_maker.command_ldc(1)
            self.scope.code_maker.command_iadd()
            return ELEMENT
        elif value_type == LIST:
            self.scope.code_maker.command_dup()
            self.scope.code_maker.command_ldc(0)
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'addFirst', [INTEGER_JTYPE], VOID_JTYPE)
            return LIST
            
    def pre_decr_expr(self, value_type):
        if value_type == ELEMENT:
            self.scope.code_maker.command_ldc(1)
            self.scope.code_maker.command_isub()
            return ELEMENT
        elif value_type == LIST:
            self.scope.code_maker.command_dup()
            self.scope.code_maker.command_ldc(0)
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'del', [INTEGER_JTYPE], VOID_JTYPE)
            return LIST
            
    def post_incr_expr(self, value_type):
        if value_type == ELEMENT:
            self.scope.code_maker.command_ldc(1)
            self.scope.code_maker.command_iadd()
            return ELEMENT
        elif value_type == LIST:
            self.scope.code_maker.command_dup()
            self.scope.code_maker.command_ldc(0)
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'addLast', [INTEGER_JTYPE], VOID_JTYPE)
            return LIST
            
    def post_decr_expr(self, value_type):
        if value_type == ELEMENT:
            self.scope.code_maker.command_ldc(1)
            self.scope.code_maker.command_isub()
            return ELEMENT
        elif value_type == LIST:
            self.scope.code_maker.command_dup()
            self.scope.code_maker.command_dup()
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'len', [], INTEGER_JTYPE)
            self.scope.code_maker.command_ldc(1)
            self.scope.code_maker.command_isub()
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'del', [INTEGER_JTYPE], VOID_JTYPE)
            return LIST

    def not_expr(self, value_type):
        if value_type == LIST:
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'to_int', [], INTEGER_JTYPE)

        false_label = self.scope.code_maker.make_label('BOOL_FALSE')
        end_label = self.scope.code_maker.make_label('BOOL_END')

        self.scope.code_maker.command_ifeq(false_label)
        self.scope.code_maker.command_ldc(0)
        self.scope.code_maker.command_goto(end_label)
        self.scope.code_maker.command_label(false_label)
        self.scope.code_maker.command_ldc(1)
        self.scope.code_maker.command_label(end_label)

        return ELEMENT




    def cast_expr(self, value_type, target_type):
        if value_type == target_type:
            return target_type
        elif value_type == ELEMENT and target_type == LIST:
            # temporary store value to var 0
            self.scope.code_maker.command_store(INTEGER_JTYPE, 0)

            # create list
            self.scope.code_maker.command_new(INTEGER_LIST_CLASS)
            self.scope.code_maker.command_dup()
            self.scope.code_maker.command_invokespecial(INTEGER_LIST_CLASS, '<init>', [], VOID_JTYPE)

            # load value and call add method
            self.scope.code_maker.command_dup()
            self.scope.code_maker.command_load(INTEGER_JTYPE, 0)
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'addLast', [INTEGER_JTYPE], VOID_JTYPE)
            return LIST
        elif value_type == LIST and target_type == ELEMENT:
            self.scope.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'to_int', [], INTEGER_JTYPE)
            return ELEMENT

    def list_maker_begin(self):
        """ Calls first for list_maker rule, before args """
        self.scope.code_maker.command_new(INTEGER_LIST_CLASS)
        self.scope.code_maker.command_dup()
        self.scope.code_maker.command_invokespecial(INTEGER_LIST_CLASS, '<init>', [], VOID_JTYPE)
        self.scope.code_maker.command_dup()  # additional copy for args

    def list_maker_arg(self, arg_type):
        """ Calls for every arg """
        if arg_type != ELEMENT:
            line, pos = self.get_rule_position()
            raise UnsupportedOperation(line, pos, 'Making list of lists is unsupported.')

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
        var_number = self.get_var_number(id)
        value_type = self.scope.var_types[id]
        self.scope.code_maker.command_load(_type_map[value_type], var_number)
        return value_type


class JCodeMaker:

    CLASS_NAME = 'LLMain'

    CLASS_HEADER = '''.class public %s
.super java/lang/Object
.method public <init>()V
    aload_0
    invokespecial java/lang/Object/<init>()V
    return
.end method
''' % CLASS_NAME

    BUILTIN_METHODS = '''; void print(int)
.method public static print(I)V
    .limit locals 5
    .limit stack 5
    iload 0
    getstatic java/lang/System/out Ljava/io/PrintStream;
    swap
    invokevirtual java/io/PrintStream/print(I)V
    return
.end method

; void print(string)
.method public static print(Ljava/lang/String;)V
    .limit locals 5
    .limit stack 5
    aload 0
    getstatic java/lang/System/out Ljava/io/PrintStream;
    swap
    invokevirtual java/io/PrintStream/print(Ljava/lang/String;)V
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
        self.label_counter = 0

    def make_class(self, stack_size, locals_number, methods_code):
        """ Make Jasmin class with using commands of this maker for main method """
        return (self.CLASS_HEADER +
                self.make_method('main', ['[Ljava/lang/String;'], stack_size, locals_number) +
                methods_code +
                self.BUILTIN_METHODS)

    def make_method(self, name, params_jtypes, stack_size, locals_number):
        """ Returns code of method with code maked by this maker """
        # add return
        if not self.return_added:
            self.command_return()

        # move locals of method args
        for i, param_jtype in enumerate(params_jtypes):
            # reverse order of calls since adding first
            self.command_store(param_jtype, RESERVED_LOCALS + i, add_first=True)
            self.command_load(param_jtype, i, add_first=True)

        code = '\n\t'.join(self.commands)
        return self.JMETHOD_TEMPLATE % (name, ''.join(params_jtypes), self.return_jtype, stack_size, locals_number+1, code)

    def make_label(self, name):
        self.label_counter += 1
        return 'L%i_%s' % (self.label_counter, name)

    def add_command(self, command, add_first=False):
        if add_first:
            self.commands.insert(0, command)
        else:
            self.commands.append(command)

    # COMMANDS

    def command_ldc(self, value):
        """ Jasmin command to load constant on stack """
        command =  'ldc %s' % value
        self.add_command(command)

    def command_store(self, value_jtype, var_number, add_first=False):
        """ Jasmin command to pop from stack var and store it in variable """
        instruction = 'istore' if value_jtype == INTEGER_JTYPE else 'astore'
        command =  '%s %s' % (instruction, var_number)
        self.add_command(command, add_first=add_first)

    def command_load(self, value_jtype, var_number, add_first=False):
        """ Jasmin command to push variable to stack """
        instruction =  'iload' if value_jtype == INTEGER_JTYPE else 'aload'
        command = '%s %s' % (instruction, var_number)
        self.add_command(command, add_first=add_first)


    def command_return(self):
        """ Jasmin method return command """
        if self.return_jtype == INTEGER_JTYPE:
            instruction = 'ireturn'
        elif self.return_jtype == INTEGER_LIST_JTYPE:
            instruction = 'areturn'
        else:
            instruction = 'return'
        command = instruction
        self.add_command(command)
        self.return_added = True

    def command_new(self, full_class_name):
        """ Jasmin command new """
        command = 'new ' + full_class_name
        self.add_command(command)

    def command_dup(self):
        """ Jasmin command to duplicate top value on stack """
        self.add_command('dup')

    def command_pop(self):
        """ Jasmin command to pop top value from stack """
        self.add_command('pop')

    def command_swap(self):
        """ Jasmin command to swap two values on top """
        self.add_command('swap')

    def command_invokespecial(self, full_class_name, method, jparams, return_jtype):
        """ Jasmin command to invoke special methods of objects (constructors, ...) """
        command = self.INVOKE_TEMPLATE % ('invokespecial', full_class_name, method, ''.join(jparams), return_jtype)
        self.add_command(command)

    def command_invokevirtual(self, full_class_name, method, jparams, return_jtype):
        """ Jasmin command to invoke virtual methods of objects """
        command = self.INVOKE_TEMPLATE % ('invokevirtual', full_class_name, method, ''.join(jparams), return_jtype)
        self.add_command(command)

    def command_invokestatic(self, full_class_name, method, jparams, return_jtype):
        command = self.INVOKE_TEMPLATE % ('invokestatic', full_class_name, method, ''.join(jparams), return_jtype)
        self.add_command(command)

    def command_ifgt(self, label):
        self.add_command('ifgt ' + label)

    def command_ifne(self, label):
        self.add_command('ifne ' + label)

    def command_ifeq(self, label):
        self.add_command('ifeq ' + label)

    def command_goto(self, label):
        self.add_command('goto ' + label)

    def command_if_icmpeq(self, label):
        self.add_command('if_icmpeq ' + label)

    def command_if_icmplt(self, label):
        self.add_command('if_icmplt ' + label)

    def command_if_icmpge(self, label):
        self.add_command('if_icmpge ' + label)

    def command_if_icmpgt(self, label):
        self.add_command('if_icmpgt ' + label)

    def command_if_icmple(self, label):
        self.add_command('if_icmple ' + label)

    def command_label(self, label):
        self.add_command('\t%s:' % label)

    def command_iadd(self):
        self.add_command('iadd')

    def command_isub(self):
        self.add_command('isub')

    def command_imul(self):
        self.add_command('imul')

    def command_idiv(self):
        self.add_command('idiv')

    def command_irem(self):
        self.add_command('irem')

    def command_ineg(self):
        self.add_command('ineg')


