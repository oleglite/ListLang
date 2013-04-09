grammar ListLang;

options {
	language = Python;
	output = AST;
}

program 
	:	statement+
	;

statement
	:	function | operation | NEWLINE
	;
	
function
	:	type ID '(' params_list ')' block
	;
	
params_list
	:	( param ( ',' param )* )?
	;
	
param
	:	type ID
	;
	
block
	:	'{' NEWLINE statement+ '}'
	;
	
	
operation
	:	iter_operation | if_operation | print_operation | return_operation | global_operation | expr
	;
	
print_operation
	:	'print' rvalue NEWLINE
	;

return_operation
	:	'return' rvalue NEWLINE
	;
	
global_operation
	:	'global' ID
	;
	
iter_operation
	:	while_operation | for_operation
	;
	
while_operation
	:	'while' rvalue  block
	;
	
for_operation
	:	'for' ID 'in' ID block
	;
	
if_operation
	:	'if' rvalue  block ('elif' rvalue block)* ('else' block)?
	;
	
expr
	:	(assignment_expr | rvalue) NEWLINE
	;
	
assignment_expr
	:	type? ID '=' rvalue
	;
	
rvalue
	:	or_expr
	;
	
or_expr
	:	and_expr ('or' and_expr)*
	;

and_expr
	:	equality_expr ('and' equality_expr)*
	;
	
equality_expr
	:	relational_expr (('=='|'!=') relational_expr)*
	;

relational_expr
	:	additive_expr (('<'|'>'|'<='|'>=') additive_expr)*
	;
	
additive_expr
	:	multiplicative_expr ('+' multiplicative_expr | '-' multiplicative_expr)*
	;
	
multiplicative_expr
	:	prefix_expr ('*' prefix_expr | '/' prefix_expr | '%' prefix_expr)*
	;
	
prefix_expr
	:	'++' prefix_expr
	|	'--' prefix_expr
	|	unary_expr
	;
	
unary_expr
	: 	'!' unary_expr
	|	'empty' unary_expr
	|	'not' unary_expr
	|	postfix_expr
	;

postfix_expr
	:	primary_expr ( '++' | '--' )*
	;
	
primary_expr
	:	ID
	|	call_expr
	|	literal
	|	index_expr
	|	'(' rvalue ')'
	;
	
call_expr
	:	( ID | type ) '(' args_list ')'
	;
	
args_list
	:	( rvalue ( ',' rvalue )* )?
	;
	
index_expr
	:	ID '[' rvalue ']'
	;
	
literal
	:	element_literal | list_literal
	;
	
element_literal
	:	INT
	;
	
list_literal
	:	'[' args_list ']'
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

