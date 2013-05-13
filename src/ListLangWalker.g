tree grammar ListLangWalker;

options {
	language = Python;
	tokenVocab=ListLang;	// import tokens
	ASTLabelType=CommonTree;
}

@header {
	import ll_scope
	import jtrans
	from ll_scope import Scope, log
	
	translator = jtrans.JTranslator()
}

program returns[code]
scope {
	global_scope;
}
@init {
	translator.walker = self
	$program::global_scope = Scope()
	translator.enter_scope($program::global_scope)
}
@after {
	#print '\n\n', ll_scope.LOG_STR
	$code = translator.program()
	translator.leave_scope()
}
	:	slist[$program::global_scope]
	;
	
slist[init_scope]
scope {
	local_scope;
}
@init {	
	$slist::local_scope = $slist.init_scope
}
	:	^( SLIST statement+ )
	;
	
statement
	:	function
	|	operation
	;
	
function
scope {
	params;
	function_scope;
}
@init {
	$function::params = []
	$function::function_scope = Scope()
	translator.enter_scope($function::function_scope)
}
	:	^( FUNCTION TYPE ID param* 
			{for p_id, p_type in $function::params: $function::function_scope.add_var(p_id, p_type)}
			{translator.set_function_return_type($TYPE.text)}
		function_slist ) 
			{$slist::local_scope.add_function($ID.text, $TYPE.text, $function::params, $function::function_scope)}
			{translator.leave_scope()}
			{translator.function($ID.text, $function::params, $function::function_scope)}
	;
	
function_slist
	:	slist[$function::function_scope]
	;

param
	:	^( PARAM TYPE ID ) {$function::params.append(($ID.text, $TYPE.text))}
	;
	
block_slist
	:	slist[$slist::local_scope]
	;

operation
	:	/*^( WHILE rvalue block_slist) {log(str($slist::local_scope.num) + ' while')}
	|	^( FOR ID rvalue block_slist ) 
	|	^( IF rvalue  block_slist elif_operation* else_operation?) 
	|	^( PRINT rvalue* ) 
	|*/	^( RETURN rvalue ) {translator.return_operation()} /*
	|	^( GLOBAL ID ) */
	|	expr
	;
/*
elif_operation
	:	^( ELIF rvalue block_slist )
	;

else_operation
	:	^( ELSE block_slist )
	;*/

expr
	:	assignment_expr
	| 	rvalue
	;

assignment_expr
	:	^( ASS_OP ID rvalue ) {translator.assignment_expr($ID.text, $rvalue.type)}
	;
/*
rvalue returns[type]
	:	or_expr
	|	and_expr
	|	equality_expr
	|	relational_expr
	|	additive_expr
	|	multiplicative_expr
	|	prefix_incr_expr
	|	prefix_decr_expr
	|	not_expr
	|	postfix_incr_expr
	|	postfix_decr_expr
	|	call_expr
	|	cast_expr
	|	slice_expr
	|	list_maker
	|	*element_literal
	|	identifier
	;
	

or_expr
	:	^( OR_OP rvalue rvalue )
	;
	
and_expr
	:	^( AND_OP rvalue rvalue )
	;
	
equality_expr
	:	^( EQ_OP rvalue rvalue )
	;

relational_expr
	:	^( REL_OP rvalue rvalue )
	;

additive_expr
	:	^( ADD_OP rvalue rvalue )
	;

multiplicative_expr
	:	^( MUL_OP rvalue rvalue )
	;

prefix_incr_expr
	:	^( PRE_INCR rvalue )
	;
	
prefix_decr_expr
	:	^( PRE_DECR rvalue )
	;
	
not_expr
	:	^( NOT_OP rvalue )
	;

postfix_incr_expr
	:	^( INCR_OP rvalue )
	;
	
postfix_decr_expr
	:	^( DECR_OP rvalue )
	;

call_expr
	:	^( CALL ID rvalue* )
	;

cast_expr
	:	^( CAST TYPE rvalue )
	;

slice_expr
	:	^( SLICE ID rvalue rvalue? )
	;

list_maker
	:	^( LIST_MAKER rvalue* ) 
	;


element_literal returns[type]
	:	INT {$type = translator.element_literal(int($INT.text))}
	;

identifier
	:	ID {$type = translator.var_identifier($ID.text)}
	;
*/
	

rvalue returns[type]
	:/*	^( OR_OP rvalue rvalue )
	|	^( AND_OP rvalue rvalue )
	|	^( EQ_OP rvalue rvalue )
	|	^( REL_OP rvalue rvalue )
	|	^( ADD_OP rvalue rvalue )
	|	^( MUL_OP rvalue rvalue )
	|	^( PRE_INCR rvalue )
	|	^( PRE_DECR rvalue )
	|	^( NOT_OP rvalue )
	|	^( INCR_OP rvalue )
	|	^( DECR_OP rvalue )
	|	^( CALL ID rvalue* )
	|	^( CAST TYPE rvalue )
	|	^( SLICE ID rvalue rvalue? )
	|*/	^( LIST_MAKER
			{translator.list_maker_begin()}
		(t = rvalue 
			{translator.list_maker_arg($t.type)} 
		)* ) 
			{$type = translator.list_maker()}
	|	INT {$type = translator.element_literal(int($INT.text))}
	|	ID {$type = translator.var_identifier($ID.text)}
	;