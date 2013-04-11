grammar ListLang;

options {
	language = Python;
	output = AST;
}

tokens {
	PROGRAM; FUNCTION; PARAM; CALL; CAST; PRE_INC; PRE_DECR; SLICE; LIST_MAKER;
}

program 
	:	statement+ -> ^(PROGRAM statement+)
	;

statement
	:	function
	|	operation
	|	NEWLINE!
	;
	
function
	:	type ID '(' params_list ')' block -> ^(FUNCTION type ID params_list? block)
	;
	
params_list
	:	( param ( ',' param )* )? -> param*
	;
	
param
	:	type ID -> ^(PARAM type ID)
	;
	
block
	:	'{' NEWLINE statement+ '}' -> ^(PROGRAM statement+)
	;
	
	
operation
	:	iter_operation | if_operation | print_operation | return_operation | global_operation | expr
	;
	
print_operation
	:	'print'^ args_list NEWLINE!
	;

return_operation
	:	'return'^ rvalue NEWLINE!
	;
	
global_operation
	:	'global'^ ID
	;
	
iter_operation
	:	while_operation | for_operation
	;
	
while_operation
	:	'while'^ rvalue  block
	;
	
for_operation
	:	'for'^ ID 'in' ID block
	;
	
if_operation
	:	'if'^ rvalue  block elif_operation* else_operation?
	;
	
elif_operation
	:	'elif'^ rvalue block
	;

else_operation
	:	'else'^ block
	;
	
expr
	:	assignment_expr NEWLINE -> assignment_expr
	| 	rvalue NEWLINE -> rvalue
	;
	
assignment_expr
	:	type? ID '='^ rvalue
	;
	
rvalue
	:	or_expr
	;
	
or_expr
	:	and_expr ('or'^ and_expr)*
	;

and_expr
	:	equality_expr ('and'^ equality_expr)*
	;
	
equality_expr
	:	relational_expr (('=='|'!=')^ relational_expr)*
	;

relational_expr
	:	additive_expr (('<'|'>'|'<='|'>=')^ additive_expr)*
	;
	
additive_expr
	:	multiplicative_expr (('+' | '-')^ multiplicative_expr)*
	;
	
multiplicative_expr
	:	prefix_expr (('*' | '/' | '%')^ prefix_expr)*
	;
	
prefix_expr
	:	'++' prefix_expr -> ^(PRE_INC prefix_expr)
	|	'--' prefix_expr -> ^(PRE_DECR prefix_expr)
	|	unary_expr
	;
	
unary_expr
	: 	'not'^ unary_expr
	|	postfix_expr
	;

postfix_expr
	:	primary_expr ( ( '++' | '--' )^ )*
	;
	
primary_expr
	:	call_expr
	|	cast_expr
	|	slice_expr
	|	element_literal
	|	list_maker
	|	'(' rvalue ')' -> rvalue
	|	ID
	;
	
call_expr
	:	ID  '(' args_list ')' -> ^( CALL ID args_list? )
	;
	
cast_expr
	:	type '(' rvalue ')' -> ^( CAST type rvalue )
	;
	
args_list
	:	( rvalue ( ',' rvalue )* )? -> rvalue*
	;
	
slice_expr
	:	ID '[' rvalue ( ':' rvalue? )? ']' -> ^( SLICE ID rvalue ':'? rvalue? )
	;
	
element_literal
	:	INT
	;
	
list_maker
	:	'[' args_list ']' -> ^( LIST_MAKER args_list? )
	;
	
type
	:	'List' | 'Element'
	;

ID  :	('a'..'z'|'A'..'Z'|'_') ('a'..'z'|'A'..'Z'|'0'..'9'|'_')*
    ;

INT :	'0'..'9'+
    ;

COMMENT
    :   '//' ~('\n'|'\r')* ('\r')? '\n' {$channel=HIDDEN;}
    |   '/*' ( options {greedy=false;} : . )* '*/' {$channel=HIDDEN;}
    ;
    
WS 	: (' ' | '\t')+ {$channel=HIDDEN;}
	;
    
NEWLINE : (('\u000C')?('\r')? '\n' )+
	;

