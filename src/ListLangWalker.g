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
	|*/	^( PRINT (val=rvalue
			{translator.print_value($val.type)}
		)* ) 
			{translator.print_operation()}
	|	^( RETURN rvalue ) {translator.return_operation()} /*
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

rvalue returns[type]
	:	^( OR_OP val1=rvalue val2=rvalue )
			{$type = translator.or_expr($val1.type, $val2.type)}
			
	|	^( AND_OP val1=rvalue val2=rvalue )
			{$type = translator.and_expr($val1.type, $val2.type)}
			
	|	^( EQ_OP val1=rvalue val2=rvalue )
			{$type = translator.equality_expr($EQ_OP.text, $val1.type, $val2.type)}
			
	|	^( REL_OP val1=rvalue val2=rvalue )
			{$type = translator.relational_expr($REL_OP.text, $val1.type, $val2.type)}
	
	|	^( ADD_OP val1=rvalue val2=rvalue )
			{$type = translator.additive_expr($ADD_OP.text, $val1.type, $val2.type)}
			
	|	^( MUL_OP val1=rvalue val2=rvalue )
			{$type = translator.multiplicative_expr($MUL_OP.text, $val1.type, $val2.type)}
	|/*	^( PRE_INCR rvalue )
	|	^( PRE_DECR rvalue )
	
	|*/	^( NOT_OP val=rvalue )		{$type = translator.not_expr($val.type)}
	
	|/*	^( INCR_OP rvalue )
	
	|	^( DECR_OP rvalue )
	
	|	^( CALL ID rvalue* )
	
	|*/	^( CAST TYPE val=rvalue ) 	{$type = translator.cast_expr($val.type, $TYPE.text)}
	
	//|	^( SLICE ID rvalue rvalue? )
	
	|	^( LIST_MAKER			{translator.list_maker_begin()}
		(val = rvalue 			{translator.list_maker_arg($val.type)} 
		)* )				{$type = translator.list_maker()}
		
	|	INT 				{$type = translator.element_literal(int($INT.text))}
	
	|	ID 				{$type = translator.var_identifier($ID.text)}
	;