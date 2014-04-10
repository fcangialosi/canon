Canon
=====

Canon is a tool that automates the process of checking student tests against your code for CMSC420 MeeshQuest, providing a quick and easy way to test your code without making a trip to the submit server.
It scrapes Piazza for new student tests, downloads both the input and canonical output files, runs the input through your code, and then diffs your output with the expected (canonical) output.

***

JAR
===
Before running Canon, you must export your code as an executable JAR file in eclipse.

1. File > Export...
2. Java > Runnable JAR file, then click "Next"
3. Change export destination to the same directory as canon (or just move it later)
4. Select "Package required libraries into generated JAR" under Library handling
5. Finish

Usage
=====
Run Canon with:

	python canon.py -e EMAIL -p PASSWORD -j JAR

- `-e EMAIL` : the e-mail address for your Piazza account
- `-p PASSWORD` : the password to your Piazza acount
- `-j JAR`: the location of your executable JAR file


