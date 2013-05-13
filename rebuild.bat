@ECHO OFF

SET ANTLR_JAR_FILE=C:\antlr\antlr-3.1.3.jar
SET JDK_HOME=c:\Program Files\Java\jdk1.7.0_07\bin\

ECHO rebuild: antlr grammar
java -jar %ANTLR_JAR_FILE% -fo src\ -make src\ListLang.g
java -jar %ANTLR_JAR_FILE% -fo src\ -make src\ListLangWalker.g

ECHO rebuild: java List
CALL "%JDK_HOME%javac.exe" -d tmp\ src\List.java