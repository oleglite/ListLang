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

import error_processor

TEMPORARY_STORE_VAR_1 = 0
TEMPORARY_STORE_VAR_2 = 1


class JTranslator:

    DEFAULT_STACK_SIZE = 100

    def __init__(self):
        self.functions_jcode = []
        self.scopes_stack = []
        self.walker = None
        
        self.while_labels_stack = []
        self.for_labels_stack = []
        self.if_labels_stack = []

    def enter_scope(self, scope):
        self.scopes_stack.append(scope)
        self.scope = scope
        self.code_maker = self.scope.code_maker

    def leave_scope(self):
        self.scopes_stack.pop()
        if self.scopes_stack:
            self.scope = self.scopes_stack[-1]
            self.code_maker = self.scope.code_maker
        else:
            self.scope = None
            self.code_maker = None

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
            raise error_processor.UnsupportedOperation(
                self.get_rule_position(),
                'Undefined ID "%s".' % var_id
            )
        return RESERVED_LOCALS + var_number

    # RULES

    def program(self):
        return self.code_maker.make_class(
            self.DEFAULT_STACK_SIZE, RESERVED_LOCALS + len(self.scope.vars), ''.join(self.functions_jcode)
        )

    def set_function_return_type(self, return_type):
        self.code_maker.return_jtype = _type_map[return_type]

    def function(self, f_id, f_params, f_scope):
        f_translated_params = [_type_map[type] for id, type in f_params]
        f_jcode = f_scope.code_maker.make_method(
            self.scope.get_function_code_name(f_id), f_translated_params,
            self.DEFAULT_STACK_SIZE, RESERVED_LOCALS + len(f_scope.vars)
        )
        self.functions_jcode.append(f_jcode)

    def for_operation_begin(self, iter_id, value_type):
        if value_type != LIST:
            line, pos = self.get_rule_position()
            raise error_processor.UnsupportedOperation(
                line, pos, '"for" operation with "in" type %s is unsupported' % value_type
            )

        for_begin_label = self.code_maker.make_label(self.scope.scope_number, 'FOR_BEGIN')
        for_end_label = self.code_maker.make_label(self.scope.scope_number, 'FOR_END')
        current_stack_size = self.code_maker.stack_size

        self.for_labels_stack.append((for_begin_label, for_end_label, current_stack_size + 1))

        self.code_maker.command_comment('for_operation_begin')

        self.code_maker.command_ldc(0)  # iterator
        self.code_maker.command_label(for_begin_label)
        self.code_maker.command_store(INTEGER_JTYPE, TEMPORARY_STORE_VAR_1)  # save iterator
        self.code_maker.command_dup()  # duplicate list
        self.code_maker.list.len()
        self.code_maker.command_load(INTEGER_JTYPE, TEMPORARY_STORE_VAR_1)
        self.code_maker.command_if_icmple(for_end_label)
        self.code_maker.command_dup()  # duplicate list
        self.code_maker.command_load(INTEGER_JTYPE, TEMPORARY_STORE_VAR_1)
        self.code_maker.list.get()
        self.code_maker.command_load(INTEGER_JTYPE, TEMPORARY_STORE_VAR_1)
        self.code_maker.command_swap()
        self.assignment_expr(iter_id, ELEMENT)

    def for_operation(self):
        for_begin_label, for_end_label, stack_size = self.for_labels_stack.pop()

        self.code_maker.command_comment('for_operation_end')

        while self.code_maker.stack_size > stack_size:
            self.code_maker.command_pop()

        self.code_maker.command_ldc(1)
        self.code_maker.command_iadd()
        self.code_maker.command_goto(for_begin_label)
        self.code_maker.command_label(for_end_label)

    def while_operation_begin(self):        
        while_begin_label = self.code_maker.make_label(self.scope.scope_number, 'WHILE_BEGIN')
        while_end_label = self.code_maker.make_label(self.scope.scope_number, 'WHILE_END')
        current_stack_size = self.code_maker.stack_size
        self.while_labels_stack.append((while_begin_label, while_end_label, current_stack_size))

        self.code_maker.command_comment('while_operation_begin')
        self.code_maker.command_label(while_begin_label)
        
    def while_operation_value(self, value_type):
        while_end_label = self.while_labels_stack[-1][1]

        self.code_maker.command_comment('while_operation_value')
        if value_type == LIST:
            self.code_maker.list.to_int()
            
        self.code_maker.command_ifeq(while_end_label)
        
    def while_operation(self):
        while_begin_label, while_end_label, stack_size = self.while_labels_stack.pop()

        while self.code_maker.stack_size > stack_size:
            self.code_maker.command_pop()

        self.code_maker.command_comment('while_operation')
        self.code_maker.command_goto(while_begin_label)
        self.code_maker.command_label(while_end_label)
        
    def if_operation_value(self, value_type, is_elif=False):
        else_label = self.code_maker.make_label(self.scope.scope_number, 'ELSE')
        if is_elif:
            self.if_labels_stack[-1][1] = else_label
        else:
            if_end_label = self.code_maker.make_label(self.scope.scope_number, 'IF_END')
            current_stack_size = self.code_maker.stack_size
            self.if_labels_stack.append([if_end_label, else_label, current_stack_size - 1])

        self.code_maker.command_comment('if_operation_value')
        if value_type == LIST:
            self.code_maker.list.to_int()
            
        self.code_maker.command_ifeq(else_label)
        
    def if_operation_else(self):
        if_end_label, else_label, stack_size = self.if_labels_stack[-1]

        while self.code_maker.stack_size > stack_size:
            self.code_maker.command_pop()

        self.code_maker.command_comment('if_operation_else')
        self.code_maker.command_goto(if_end_label)
        self.code_maker.command_label(else_label)

    def if_operation(self):
        if_end_label, else_label, stack_size = self.if_labels_stack.pop()

        while self.code_maker.stack_size > stack_size:
            self.code_maker.command_pop()

        self.code_maker.command_comment('if_operation')
        self.code_maker.command_label(if_end_label)

    def print_value(self, value_type):
        self.code_maker.command_comment('print_value ' + value_type)
        if value_type == ELEMENT:
            self.code_maker.command_invokestatic(JCodeMaker.CLASS_NAME, 'print', [INTEGER_JTYPE], VOID_JTYPE)
        elif value_type == LIST:
            self.code_maker.list.print_list()
        self.code_maker.command_ldc('" "')
        self.code_maker.command_invokestatic(JCodeMaker.CLASS_NAME, 'print', [STRING_JTYPE], VOID_JTYPE)

    def print_operation(self):
        self.code_maker.command_comment('print_operation')
        self.code_maker.command_ldc('"\\n"')
        self.code_maker.command_invokestatic(JCodeMaker.CLASS_NAME, 'print', [STRING_JTYPE], VOID_JTYPE)

    def return_operation(self):
        while self.code_maker.stack_size > 1:
            self.code_maker.command_pop()
        return_label = self.code_maker.return_label
        self.code_maker.command_goto(return_label)

    def global_operation(self, var_id):
        self.scope.add_global_var(var_id)

    def assignment_expr(self, var_id, value_type):
        if self.scope.is_global():
            field_name = self.code_maker.make_field_name(var_id)
            field_jtype = _type_map[value_type]

            if not var_id in self.scope.vars:
                self.code_maker.add_static_field(field_name, field_jtype)
                self.scope.add_var(var_id, value_type)

            self.code_maker.command_putstatic(self.code_maker.CLASS_NAME, field_name, field_jtype)

        else:
            if not var_id in self.scope.vars:
                self.scope.add_var(var_id, value_type)

            if var_id in self.scope.global_vars:
                field_name = self.code_maker.make_field_name(var_id)
                field_jtype = _type_map[value_type]

                self.code_maker.command_comment('assignment global %s = %s' % (var_id, value_type))
                self.code_maker.command_putstatic(self.code_maker.CLASS_NAME, field_name, field_jtype)
            else:
                self.code_maker.command_comment('assignment %s = %s' % (var_id, value_type))
                self.code_maker.command_store(_type_map[value_type], self.get_var_number(var_id))

    # RVALUES (returns value type)

    def or_expr(self, type1, type2):
        self.code_maker.command_comment('or_expr %s or %s' % (type1, type2))
        if type2 == LIST:
            self.code_maker.list.to_int()
        if type1 == LIST:
            self.code_maker.command_swap()
            self.code_maker.list.to_int()
            self.code_maker.command_swap()

        true1_label = self.code_maker.make_label(self.scope.scope_number, 'OR_TRUE1')
        true2_label = self.code_maker.make_label(self.scope.scope_number, 'OR_TRUE2')
        or_end_label = self.code_maker.make_label(self.scope.scope_number, 'OR_END')

        self.code_maker.command_swap()
        self.code_maker.command_ifne(true1_label)
        self.code_maker.command_ifne(true2_label)
        self.code_maker.command_ldc(0)
        self.code_maker.command_goto(or_end_label)
        self.code_maker.command_label(true1_label)
        self.code_maker.command_pop()
        self.code_maker.command_label(true2_label)
        self.code_maker.command_ldc(1)
        self.code_maker.command_label(or_end_label)

        return ELEMENT

    def and_expr(self, type1, type2):
        self.code_maker.command_comment('and_expr %s and %s' % (type1, type2))
        if type2 == LIST:
            self.code_maker.list.to_int()
        if type1 == LIST:
            self.code_maker.command_swap()
            self.code_maker.list.to_int()
            self.code_maker.command_swap()

        false1_label = self.code_maker.make_label(self.scope.scope_number, 'AND_FALSE1')
        false2_label = self.code_maker.make_label(self.scope.scope_number, 'AND_FALSE')
        and_end_label = self.code_maker.make_label(self.scope.scope_number, 'AND_END')

        self.code_maker.command_swap()
        self.code_maker.command_ifeq(false1_label)
        self.code_maker.command_ifeq(false2_label)
        self.code_maker.command_ldc(1)
        self.code_maker.command_goto(and_end_label)
        self.code_maker.command_label(false1_label)
        self.code_maker.command_pop()
        self.code_maker.command_label(false2_label)
        self.code_maker.command_ldc(0)
        self.code_maker.command_label(and_end_label)

        return ELEMENT

    def equality_expr(self, operator, type1, type2):
        self.code_maker.command_comment('equality_expr %s %s %s' % (type1, operator, type2))
        if type1 == type2 == ELEMENT:
            eq_true_label = self.code_maker.make_label(self.scope.scope_number, 'EQ_TRUE')
            eq_end_label = self.code_maker.make_label(self.scope.scope_number, 'EQ_END')

            self.code_maker.command_if_icmpeq(eq_true_label)
            self.code_maker.command_ldc(0)
            self.code_maker.command_goto(eq_end_label)
            self.code_maker.command_label(eq_true_label)
            self.code_maker.command_ldc(1)
            self.code_maker.command_label(eq_end_label)

            self.code_maker.stack_size -= 1

        elif type1 == type2 == LIST:
            self.code_maker.list.equal()

        else:
            self.code_maker.command_pop()
            self.code_maker.command_pop()
            self.code_maker.command_ldc(0)

        if operator == '!=':
            self.not_expr(ELEMENT)

        return ELEMENT

    def relational_expr(self, operator, type1, type2):
        self.code_maker.command_comment('relational_expr %s %s %s' % (type1, operator, type2))
        if type1 == LIST or type2 == LIST:
            raise error_processor.UnsupportedOperation(
                self.get_rule_position(),
                'Relational operation (%s) for lists is unsupported.' % operator
            )

        rel_true_label = self.code_maker.make_label(self.scope.scope_number, 'REL_TRUE')
        rel_end_label = self.code_maker.make_label(self.scope.scope_number, 'REL_END')

        if operator == '<': self.code_maker.command_if_icmplt(rel_true_label)
        elif operator == '<=': self.code_maker.command_if_icmple(rel_true_label)
        elif operator == '>': self.code_maker.command_if_icmpgt(rel_true_label)
        elif operator == '>=': self.code_maker.command_if_icmpge(rel_true_label)

        self.code_maker.command_ldc(0)
        self.code_maker.command_goto(rel_end_label)
        self.code_maker.command_label(rel_true_label)
        self.code_maker.command_ldc(1)
        self.code_maker.command_label(rel_end_label)

        self.code_maker.stack_size -= 1

        return ELEMENT

    def additive_expr(self, operator, type1, type2):
        self.code_maker.command_comment('additive_expr %s %s %s' % (type1, operator, type2))
        if operator == '+':
            if type1 == type2 == ELEMENT:
                self.code_maker.command_iadd()
                return ELEMENT
            elif type1 == type2 == LIST:
                self.code_maker.list.concat()
                return LIST
            elif type1 == ELEMENT and type2 == LIST:
                self.code_maker.command_dup()
                self.code_maker.command_store(INTEGER_LIST_JTYPE, 0)
                self.code_maker.command_swap()
                self.code_maker.list.addFirst()
                self.code_maker.command_load(INTEGER_LIST_JTYPE, 0)
                return LIST
            elif type1 == LIST and  type2 == ELEMENT:
                self.code_maker.command_swap()
                self.code_maker.command_dup()
                self.code_maker.command_store(INTEGER_LIST_JTYPE, 0)
                self.code_maker.command_swap()
                self.code_maker.list.addLast()
                self.code_maker.command_load(INTEGER_LIST_JTYPE, 0)
                return LIST
        elif operator == '-':
            if type1 == type2 == ELEMENT:
                self.code_maker.command_isub()
                return ELEMENT
            else:
                raise error_processor.UnsupportedOperation(
                    self.get_rule_position(),
                    'Additive expression (%s %s %s) is unsupported.' % (type1, operator, type2)
                )

    def multiplicative_expr(self, operator, type1, type2):
        self.code_maker.command_comment('multiplicative_expr %s %s %s' % (type1, operator, type2))
        if operator == '*':
            if type1 == type2 == ELEMENT:
                self.code_maker.command_imul()
                return ELEMENT
            elif type1 == LIST and type2 == ELEMENT:
                self.code_maker.list.multiply()
                return LIST

        elif operator == '/':
            if type1 == type2 == ELEMENT:
                self.code_maker.command_idiv()
                return ELEMENT
            elif type1 == LIST and type2 == ELEMENT:
                self.code_maker.list.removeEvery()
                return LIST

        elif operator == '%':
            if type1 == type2 == ELEMENT:
                self.code_maker.command_irem()
                return ELEMENT
            elif type1 == LIST and type2 == ELEMENT:
                self.code_maker.command_swap()
                self.code_maker.command_dup()
                self.code_maker.command_store(INTEGER_LIST_JTYPE, 0)
                self.code_maker.command_swap()
                self.code_maker.list.delete()
                self.code_maker.command_load(INTEGER_LIST_JTYPE, 0)
                return LIST

        raise error_processor.UnsupportedOperation(
            self.get_rule_position(),
            'Multiplicative expression (%s %s %s) is unsupported.' % (type1, operator, type2)
        )
                                   
    def pre_incr_expr(self, value_type):
        self.code_maker.command_comment('pre_incr_expr ++%s' % value_type)
        if value_type == LIST:
            self.code_maker.command_dup()
            self.code_maker.command_ldc(0)
            self.code_maker.list.addFirst()
            return LIST
        else:
            raise error_processor.UnsupportedOperation(
                self.get_rule_position(),
                'Prefix increment operation for type "%s" is unsupported.' % (value_type)
            )
            
    def pre_decr_expr(self, value_type):
        self.code_maker.command_comment('pre_decr_expr --%s' % value_type)
        if value_type == LIST:
            self.code_maker.command_dup()
            self.code_maker.list.removeFirst()
            return LIST
        raise error_processor.UnsupportedOperation(
            self.get_rule_position(),
            'Prefix decrement operation for type "%s" is unsupported.' % (value_type)
        )
            
    def post_incr_expr(self, value_type):
        self.code_maker.command_comment('post_incr_expr %s++' % value_type)
        if value_type == LIST:
            self.code_maker.command_dup()
            self.code_maker.command_ldc(0)
            self.code_maker.list.addLast()
            return LIST
        raise error_processor.UnsupportedOperation(
            self.get_rule_position(),
            'Postfix increment operation for type "%s" is unsupported.' % (value_type)
        )
            
    def post_decr_expr(self, value_type):
        self.code_maker.command_comment('post_decr_expr %s--' % value_type)
        if value_type == LIST:
            self.code_maker.command_dup()
            self.code_maker.list.removeLast()
            return LIST
        raise error_processor.UnsupportedOperation(
            self.get_rule_position(),
            'Postfix decrement operation for type "%s" is unsupported.' % (value_type)
        )

    def not_expr(self, value_type):
        self.code_maker.command_comment('not_expr not %s' % value_type)
        if value_type == LIST:
            self.code_maker.list.to_int()

        false_label = self.code_maker.make_label(self.scope.scope_number, 'BOOL_FALSE')
        end_label = self.code_maker.make_label(self.scope.scope_number, 'BOOL_END')

        self.code_maker.command_invokestatic(JCodeMaker.CLASS_NAME, 'neg', [INTEGER_JTYPE], INTEGER_JTYPE)

        return ELEMENT

    def call_expr(self, func_id, types):
        self.code_maker.command_comment('call_expr %s(%s)' % (func_id, ', '.join(types)))

        func_description = self.scope.funcs.get(func_id)

        if func_description and func_description[1] == types:
            func_type = func_description[0]
            jmethod_id = self.scope.get_function_code_name(func_id)
            f_translated_params = [_type_map[type] for type in types]
            self.code_maker.command_invokestatic(
                JCodeMaker.CLASS_NAME, jmethod_id, f_translated_params, _type_map[func_type]
            )
            return func_type  # function return type
        else:
            raise error_processor.FunctionUnfoundException(
                self.get_rule_position(),
                "Can't found function with sugnature %s(%s)." % (func_id, ', '.join(types))
            )



    def cast_expr(self, value_type, target_type):
        self.code_maker.command_comment('cast_expr %s(%s)' % (target_type, value_type))

        if value_type == target_type:
            return target_type
        elif value_type == ELEMENT and target_type == LIST:
            # temporary store value to var 0
            self.code_maker.command_store(INTEGER_JTYPE, 0)

            # create list
            self.code_maker.list.new()

            # load value and call add method
            self.code_maker.command_dup()
            self.code_maker.command_load(INTEGER_JTYPE, 0)
            self.code_maker.list.addLast()
            return LIST
        elif value_type == LIST and target_type == ELEMENT:
            self.code_maker.list.to_int()
            return ELEMENT

    def slice_expr(self, list_type, value_type1, value_type2):
        if list_type == LIST:
            self.code_maker.command_comment('slice_expr [%s:%s]' % (value_type1, value_type2))
            if value_type1 == ELEMENT and not value_type2:
                self.code_maker.list.get()
                return ELEMENT
            elif value_type1 == ELEMENT and value_type2 == ELEMENT:
                self.code_maker.list.slice()
                return LIST

        raise error_processor.UnsupportedOperation(
            self.get_rule_position(),
            'Slice expression %s[%s:%s] is unsupported.' % ( list_type, value_type1, value_type2)
        )


    def list_maker_begin(self):
        """ Calls first for list_maker rule, before args """
        self.code_maker.command_comment('list_maker_begin')

        self.code_maker.list.new()
        self.code_maker.command_dup()  # additional copy for args

    def list_maker_arg(self, arg_type):
        """ Calls for every arg """
        self.code_maker.command_comment('list_maker_arg')

        if arg_type != ELEMENT:
            raise error_processor.UnsupportedOperation(
                self.get_rule_position(),
                'Making list of lists is unsupported.'
            )

        self.code_maker.list.addLast()
        self.code_maker.command_dup()

    def list_maker(self):
        """ Calls last for list_maker rule, return type """
        self.code_maker.command_comment('list_maker')

        self.code_maker.command_pop()
        return LIST

    def element_literal(self, value):
        self.code_maker.command_ldc(value)
        return ELEMENT

    def var_identifier(self, id):
        if self.scope.is_global() or id in self.scope.global_vars:
            field_name = self.code_maker.make_field_name(id)
            value_type = self.scope.global_scope.var_types[id]
            field_jtype = _type_map[value_type]
            self.code_maker.command_getstatic(self.code_maker.CLASS_NAME, field_name, field_jtype)
        else:
            var_number = self.get_var_number(id)
            value_type = self.scope.var_types[id]
            self.code_maker.command_load(_type_map[value_type], var_number)
        return value_type


class ListJavaMediator:

    def __init__(self, code_maker):
        self.code_maker = code_maker

    def len(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'len', [], INTEGER_JTYPE)

    def get(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'get', [INTEGER_JTYPE], INTEGER_JTYPE)

    def to_int(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'to_int', [], INTEGER_JTYPE)

    def print_list(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'print', [], VOID_JTYPE)

    def equal(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'equal', [INTEGER_LIST_JTYPE], INTEGER_JTYPE)

    def concat(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'concat', [INTEGER_LIST_JTYPE], INTEGER_LIST_JTYPE)

    def addFirst(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'addFirst', [INTEGER_JTYPE], VOID_JTYPE)

    def addLast(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'addLast', [INTEGER_JTYPE], VOID_JTYPE)

    def multiply(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'multiply', [INTEGER_JTYPE], INTEGER_LIST_JTYPE)

    def removeEvery(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'removeEvery', [INTEGER_JTYPE], INTEGER_LIST_JTYPE)

    def delete(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'delete', [INTEGER_JTYPE], VOID_JTYPE)

    def removeFirst(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'removeFirst', [], VOID_JTYPE)

    def removeLast(self):
        self.code_maker.command_invokevirtual(INTEGER_LIST_CLASS, 'removeLast', [], VOID_JTYPE)

    def new(self):
        self.code_maker.command_new(INTEGER_LIST_CLASS)
        self.code_maker.command_dup()
        self.code_maker.command_invokespecial(INTEGER_LIST_CLASS, '<init>', [], VOID_JTYPE)

    def slice(self):
        self.code_maker.command_invokevirtual(
            INTEGER_LIST_CLASS, 'slice', [INTEGER_JTYPE, INTEGER_JTYPE], INTEGER_LIST_JTYPE
        )

class JCodeMaker:

    CLASS_NAME = 'LLMain'

    CLASS_HEADER = '''.class public %s
.super java/lang/Object
''' % CLASS_NAME

    CLASS_INIT = '''.method public <init>()V
    aload_0
    invokespecial java/lang/Object/<init>()V
    return
.end method
'''

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

; int neg(int)
.method public static neg(I)I
    .limit locals 5
    .limit stack 5
    iload 0
    ifeq RET_1
    ldc 0
    ireturn
    RET_1:
    ldc 1
    ireturn
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
        self.list = ListJavaMediator(self)

        self.commands = []
        self.return_jtype = VOID_JTYPE
        self.return_label = 'RETURN_LABEL'
        self.label_counter = 0
        self.fields = []
        self.stack_size = 0

    def make_class(self, stack_size, locals_number, methods_code):
        """ Make Jasmin class with using commands of this maker for main method """
        fields = '\n'.join(self.fields) + '\n'
        return (self.CLASS_HEADER +
                fields +
                self.CLASS_INIT +
                self.make_method('main', ['[Ljava/lang/String;'], stack_size, locals_number) +
                methods_code +
                self.BUILTIN_METHODS)

    def make_method(self, name, params_jtypes, stack_size, locals_number):
        """ Returns code of method with code maked by this maker """
        # add return
        self.command_label(self.return_label)
        if self.stack_size == 0 and self.return_jtype != VOID_JTYPE:
            if self.return_jtype == INTEGER_JTYPE:
                self.command_ldc(0)
            elif self.return_jtype == INTEGER_LIST_JTYPE:
                self.command_new(INTEGER_LIST_CLASS)
                self.command_dup()
                self.command_invokespecial(INTEGER_LIST_CLASS, '<init>', [], VOID_JTYPE)

        self.command_return()

        # move locals of method args
        self.add_command('', add_first=True)
        for i, param_jtype in enumerate(params_jtypes):
            # reverse order of calls since adding first
            self.command_store(param_jtype, RESERVED_LOCALS + i, add_first=True)
            self.command_load(param_jtype, i, add_first=True)


        code = '\n\t'.join(self.commands)
        return self.JMETHOD_TEMPLATE % (name, ''.join(params_jtypes), self.return_jtype, stack_size, locals_number+1, code)

    def make_label(self, scope_number, name):
        self.label_counter += 1
        return 'S%iL%i_%s' % (scope_number, self.label_counter, name)

    def add_static_field(self, name, jtype):
        field = '.field static %s %s' % (name, jtype)
        self.fields.append(field)

    def make_field_name(self, name):
        return 'global__' + name

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
        self.stack_size += 1

    def command_store(self, value_jtype, var_number, add_first=False):
        """ Jasmin command to pop from stack var and store it in variable """
        instruction = 'istore' if value_jtype == INTEGER_JTYPE else 'astore'
        command =  '%s %s' % (instruction, var_number)
        self.add_command(command, add_first=add_first)
        self.stack_size -= 1

    def command_load(self, value_jtype, var_number, add_first=False):
        """ Jasmin command to push variable to stack """
        instruction =  'iload' if value_jtype == INTEGER_JTYPE else 'aload'
        command = '%s %s' % (instruction, var_number)
        self.add_command(command, add_first=add_first)
        self.stack_size += 1

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
        self.stack_size -= 1
        self.return_added = True

    def command_new(self, full_class_name):
        """ Jasmin command new """
        command = 'new ' + full_class_name
        self.add_command(command)
        self.stack_size += 1

    def command_dup(self):
        """ Jasmin command to duplicate top value on stack """
        self.add_command('dup')
        self.stack_size += 1

    def command_pop(self):
        """ Jasmin command to pop top value from stack """
        self.add_command('pop')
        self.stack_size -= 1

    def command_swap(self):
        """ Jasmin command to swap two values on top """
        self.add_command('swap')

    def command_invokespecial(self, full_class_name, method, jparams, return_jtype):
        """ Jasmin command to invoke special methods of objects (constructors, ...) """
        self.command_invoke('invokespecial', full_class_name, method, jparams, return_jtype)
        self.stack_size -= len(jparams) + 1

    def command_invokevirtual(self, full_class_name, method, jparams, return_jtype):
        """ Jasmin command to invoke virtual methods of objects """
        self.command_invoke('invokevirtual', full_class_name, method, jparams, return_jtype)
        self.stack_size -= len(jparams) + 1

    def command_invokestatic(self, full_class_name, method, jparams, return_jtype):
        """ Jasmin command to invoke static methods """
        self.command_invoke('invokestatic', full_class_name, method, jparams, return_jtype)
        self.stack_size -= len(jparams)

    def command_invoke(self, invoke_instr, full_class_name, method, jparams, return_jtype):
        command = self.INVOKE_TEMPLATE % (invoke_instr, full_class_name, method, ''.join(jparams), return_jtype)
        self.add_command(command)
        if return_jtype != VOID_JTYPE:
            self.stack_size += 1

    def command_ifgt(self, label):
        self.add_command('ifgt ' + label)
        self.stack_size -= 1

    def command_ifne(self, label):
        self.add_command('ifne ' + label)
        self.stack_size -= 1

    def command_ifeq(self, label):
        self.add_command('ifeq ' + label)
        self.stack_size -= 1

    def command_goto(self, label):
        self.add_command('goto ' + label)

    def command_if_icmpeq(self, label):
        self.add_command('if_icmpeq ' + label)
        self.stack_size -= 2

    def command_if_icmplt(self, label):
        self.add_command('if_icmplt ' + label)
        self.stack_size -= 2

    def command_if_icmpge(self, label):
        self.add_command('if_icmpge ' + label)
        self.stack_size -= 2

    def command_if_icmpgt(self, label):
        self.add_command('if_icmpgt ' + label)
        self.stack_size -= 2

    def command_if_icmple(self, label):
        self.add_command('if_icmple ' + label)
        self.stack_size -= 2

    def command_label(self, label):
        self.add_command('\n%s:' % label)

    def command_iadd(self):
        self.add_command('iadd')
        self.stack_size -= 1

    def command_isub(self):
        self.add_command('isub')
        self.stack_size -= 1

    def command_imul(self):
        self.add_command('imul')
        self.stack_size -= 1

    def command_idiv(self):
        self.add_command('idiv')
        self.stack_size -= 1

    def command_irem(self):
        self.add_command('irem')
        self.stack_size -= 1

    def command_ineg(self):
        self.add_command('ineg')

    def command_comment(self, comment):
        self.add_command('\n\t; %s; stack=%i' % (comment, self.stack_size))

    def command_putstatic(self, jclass, field, jtype):
        self.add_command('putstatic %s/%s %s' % (jclass, field, jtype))
        self.stack_size -= 1

    def command_getstatic(self, jclass, field, jtype):
        self.add_command('getstatic %s/%s %s' % (jclass, field, jtype))
        self.stack_size += 1


