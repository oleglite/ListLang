@ECHO OFF

SET JASMIN_JAR_FILE=tmp\jasmin.jar


python src\listlang.py %1 tmp\target.j
IF ERRORLEVEL 1 GOTO EXIT
java -jar %JASMIN_JAR_FILE% -d tmp\ tmp\target.j
IF ERRORLEVEL 1 GOTO EXIT
java -cp tmp\ LLMain
IF ERRORLEVEL 1 GOTO EXIT
:EXIT