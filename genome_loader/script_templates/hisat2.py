template = """#!/bin/bash

set -eu

cd $(dirname $0)

threads=${1:-1}

cd ..
mkdir -p ./hisat2_index

hisat2-build -p ${threads} ./fastas/genome.fa \\
    ./hisat2_index/genome
"""
