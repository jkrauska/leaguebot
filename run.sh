#!/bin/bash

# remove old data file
rm little-league.db

# create new data file
./create-database.py

# apply schedule
./run-sched.py | tee report.log

echo "Posting results"
# save schedule to html and csv
./dump-sched.py

# tidy the html
tidy -quiet output.html > output2.html
mv output2.html output.html

