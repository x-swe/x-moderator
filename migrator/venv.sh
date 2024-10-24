#!/bin/bash

. .venv/bin/activate

cd migrator/

python3 migrator.py $@
