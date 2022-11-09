template = """#!/bin/bash

set -eu

cd $(dirname $0)

threads=${1:-1}

cd ..
mkdir -p ./hisat2_index

hisat2-build -f ./fastas/genome.fa \\
    ./hisat2_index/genome
"""
