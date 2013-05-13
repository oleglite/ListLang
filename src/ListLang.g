grammar ListLang;

options {
	language = Python;
	output = AST;
}

tokens {
	SLIST;		// statement list
	FUNCTION;	// function definition
	PARAM;		// parameter definiiton
	CALL;		// call function expression
	CAST;		// cast expression
	SLICE;		// slice expression
	LIST_MAKER;	// list maker expression
	PRE_INCR;	// prefix increment expression
	PRE_DECR;	// prefix decrement expression
}

@header {
	import antlr3
}

@members {
	errors = 0
	
	def emitErrorMessage(self, msg):
		self.errors += 1
		sys.stderr.write(msg + '\n')
	
	#antlr3.BaseRecognizer.emitErrorMessage = emitErrorMessage
}

program
	:	 slist
	;
	
slist
	:	NEWLINE? ( statement ( NEWLINE+ | EOF ) )+ -> ^( SLIST statement+ )
	;

statement
	:	function
	|	operation
	;

function
	:	TYPE ID L_BRACKET params_list R_BRACKET block -> ^( FUNCTION TYPE ID params_list? block )
	;

params_list
	:	( param ( COMMA param )* )? -> param*
	;

param
	:	TYPE ID -> ^( PARAM TYPE ID )
	;

block
	:	L_CURLY_BRACKET NEWLINE slist R_CURLY_BRACKET -> slist
	;

operation
	:	iter_operation | if_operation | print_operation | return_operation | global_operation | expr
	;

print_operation
	:	PRINT^ args_list
	;

return_operation
	:	RETURN^ rvalue
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
	:	FOR^ ID IN! rvalue block
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
	:	assignment_expr
	| 	rvalue
	;

assignment_expr
	:	ID ASS_OP^ rvalue
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
	:	INCR_OP prefix_expr -> ^( PRE_INCR prefix_expr )
	|	DECR_OP prefix_expr -> ^( PRE_DECR prefix_expr )
	|	unary_expr
	;

unary_expr
	: 	NOT_OP^ unary_expr
	|	postfix_expr
	;

postfix_expr
	:	primary_expr ( ( INCR_OP | DECR_OP )^ )*
	;

primary_expr
	:	call_expr
	|	cast_expr
	|	slice_expr
	|	element_literal
	|	list_maker
	|	L_BRACKET rvalue R_BRACKET -> rvalue
	|	ID
	;

call_expr
	:	ID  L_BRACKET args_list R_BRACKET -> ^( CALL ID args_list? )
	;

cast_expr
	:	TYPE L_BRACKET rvalue R_BRACKET -> ^( CAST TYPE rvalue )
	;

args_list
	:	( rvalue ( COMMA rvalue )* )? -> rvalue*
	;

slice_expr
	:	ID L_SQUARE_BRACKET rvalue ( COLON rvalue? )? R_SQUARE_BRACKET -> ^( SLICE ID rvalue rvalue? )
	;

element_literal
	:	INT
	;

list_maker
	:	L_SQUARE_BRACKET args_list R_SQUARE_BRACKET -> ^( LIST_MAKER args_list? )
	;	
	

L_BRACKET
	:	'('
	;
	
R_BRACKET
	:	')'
	;
	
L_CURLY_BRACKET
	:	'{'
	;
	
R_CURLY_BRACKET
	:	'}'
	;
	
L_SQUARE_BRACKET
	:	'['
	;
	
R_SQUARE_BRACKET
	:	']'
	;
	
COMMA
	:	','
	;
	
COLON	:	':'
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
	
IN	:	'in'
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

INCR_OP	:	'++'
	;

DECR_OP	:	'--'
	;

NOT_OP	:	'not'
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

WS 	: ('\ufeff' | ' ' | '\t')+ {$channel=HIDDEN;}
	;

NEWLINE : (('\r')? '\n' )+
	;

