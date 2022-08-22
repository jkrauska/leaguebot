#!/bin/bash


# remove old data file
#rm little-league.db



date
rm little-league.db
./create-database-2022-fall.py
date 

./run-sched.py



echo "Posting results"
# save schedule to html and csv
./dump-sched.py

# tidy the html
#tidy -quiet output.html > output2.html
#mv output2.html output.html

tput bel
tput bel