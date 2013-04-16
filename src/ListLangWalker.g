tree grammar ListLangWalker;

options {
	language = Python;
	tokenVocab=ListLang;	// import tokens
	ASTLabelType=CommonTree;
}

program
	:	slist
	;
	
slist
	:	^( SLIST statement+ )
	;

statement
	:	^( FUNCTION TYPE ID param* block )
	|	operation
	;

param
	:	^( PARAM TYPE ID )
	;
		
block
	:	slist
	;

operation
	:	^( WHILE rvalue  block)
	|	^( FOR ID rvalue block ) 
	|	^( IF rvalue  block elif_operation* else_operation?) 
	|	^( PRINT rvalue* ) 
	|	^( RETURN rvalue ) 
	|	^( GLOBAL ID ) 
	|	expr
	;

elif_operation
	:	^( ELIF rvalue block )
	;

else_operation
	:	^( ELSE block )
	;

expr
	:	assignment_expr
	| 	rvalue
	;

assignment_expr
	:	^( ASS_OP ID rvalue ) {print 'assign', $ID.text, '=', $rvalue.text}
	;

rvalue
	:	^( OR_OP rvalue rvalue )
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
	|	^( LIST_MAKER rvalue* )
	|	INT
	|	ID
	;
