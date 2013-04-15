grammar ListLang;

options {
	language = Python;
	output = AST;
}

tokens {
	PROGRAM; FUNCTION; PARAM; CALL; CAST; SLICE; LIST_MAKER;
	PRE_INCR; PRE_DECR;
}

program
	:	statement+ -> ^( PROGRAM statement+ )
	;

statement
	:	function
	|	operation
	|	NEWLINE!
	;

function
	:	TYPE ID '(' params_list ')' block -> ^( FUNCTION TYPE ID params_list? block )
	;

params_list
	:	( param ( ',' param )* )? -> param*
	;

param
	:	TYPE ID -> ^( PARAM TYPE ID )
	;

block
	:	'{' NEWLINE statement+ '}' -> ^( PROGRAM statement+ )
	;

operation
	:	iter_operation | if_operation | print_operation | return_operation | global_operation | expr
	;

print_operation
	:	PRINT^ args_list NEWLINE!
	;

return_operation
	:	RETURN^ rvalue NEWLINE!
	;

global_operation
	:	GLOBAL^ ID
	;

iter_operation
	:	while_operation | for_operation
	;

while_operation
	:	WHILE^ rvalue  block
	;

for_operation
	:	FOR^ ID 'in' ID block
	;

if_operation
	:	IF^ rvalue  block elif_operation* else_operation?
	;

elif_operation
	:	ELIF^ rvalue block
	;

else_operation
	:	ELSE^ block
	;

expr
	:	assignment_expr NEWLINE -> assignment_expr
	| 	rvalue NEWLINE -> rvalue
	;

assignment_expr
	:	TYPE? ID ASS_OP^ rvalue
	;

rvalue
	:	or_expr
	;

or_expr
	:	and_expr ( OR_OP^ and_expr )*
	;

and_expr
	:	equality_expr ( AND_OP^ equality_expr )*
	;

equality_expr
	:	relational_expr ( EQ_OP^ relational_expr )*
	;

relational_expr
	:	additive_expr ( REL_OP^ additive_expr )*
	;

additive_expr
	:	multiplicative_expr ( ADD_OP^ multiplicative_expr )*
	;

multiplicative_expr
	:	prefix_expr ( MUL_OP^ prefix_expr )*
	;

prefix_expr
	:	INCR prefix_expr -> ^( PRE_INCR prefix_expr )
	|	DECR prefix_expr -> ^( PRE_DECR prefix_expr )
	|	unary_expr
	;

unary_expr
	: 	NOT^ unary_expr
	|	postfix_expr
	;

postfix_expr
	:	primary_expr ( ( INCR | DECR )^ )*
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
	:	TYPE '(' rvalue ')' -> ^( CAST TYPE rvalue )
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


PRINT	:	'print'
	;

RETURN	:	'return'
	;

GLOBAL	:	'global'
	;

WHILE	:	'while'
	;

FOR	:	'for'
	;

IF	:	'if'
	;

ELIF	:	'elif'
	;

ELSE	:	'else'
	;

ASS_OP	:	'='
	;

AND_OP	:	'and'
	;

OR_OP	:	'or'
	;

EQ_OP	:	'==' | '!='
	;

REL_OP	:	'<' | '>' | '<=' | '>='
	;

ADD_OP	:	'+' | '-'
	;

MUL_OP	:	'*' | '/' | '%'
	;

INCR	:	'++'
	;

DECR	:	'--'
	;

NOT	:	'not'
	;

TYPE
	:	'List' | 'Element'
	;

ID	:	('a'..'z'|'A'..'Z'|'_') ('a'..'z'|'A'..'Z'|'0'..'9'|'_')*
	;

INT	:	'0'..'9'+
	;

COMMENT	:   '//' ~('\n'|'\r')* ('\r')? '\n' {$channel=HIDDEN;}
	|   '/*' ( options {greedy=false;} : . )* '*/' {$channel=HIDDEN;}
	;

WS 	: (' ' | '\t')+ {$channel=HIDDEN;}
	;

NEWLINE : (('\r')? '\n' )+
	;

