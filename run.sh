#!/bin/bash


# remove old data file
#rm little-league.db



for i in `seq 241 241`; do
    rm little-league.db

    # create new data file
    ./create-database.py

    # apply schedule
    ./run-sched.py $i
    retVal=$?
    if [ $retVal -ne 0 ]; then
        echo "Error"
    else
        echo "Good"
        break
    fi

done





echo "Posting results"
# save schedule to html and csv
./dump-sched.py

# tidy the html
#tidy -quiet output.html > output2.html
#mv output2.html output.html

tput bel