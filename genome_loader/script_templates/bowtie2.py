template = """#!/bin/bash

set -eu

cd $(dirname $0)

threads=${1:-1}

cd ..
mkdir -p bowtie2_index

bowtie2-build -f ./fastas/genome.fa \\
    ./bowtie2_index/genome
"""
