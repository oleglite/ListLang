@ECHO OFF

SET JASMIN_JAR_FILE=tmp\jasmin.jar

python src\listlang.py %1 tmp\target.j
java -jar %JASMIN_JAR_FILE% -d tmp\ tmp\target.j
java -cp tmp\ LLMain