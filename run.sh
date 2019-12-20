#!/bin/bash

rm little-league.db

./create-database.py

./run-sched.py

./dump-sched.py

tidy docs/output.html > docs/output2.html
mv docs/output2.html docs/output.html

