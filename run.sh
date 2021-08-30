#!/bin/bash


# remove old data file
#rm little-league.db



for i in $(seq 403 403); do
    date
    rm little-league.db

    # create new data file
    ./create-database-2021-fall.py


    date 
    # apply schedule
    ./run-sched.py $i
    retVal=$?
    if [ $retVal -ne 0 ]; then
        echo "Error - ${retVal}"
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