template = """#!/bin/bash

set -eu

cd $(dirname $0)

threads=${1:-1}

cd ..
mkdir -p salmon_index

cat ./fastas/exon.fa ./fastas/genome.fa > ./fastas/gentome.fa
grep '^>' ./fastas/genome.fa | cut -d ' ' -f 1 > ./fastas/decoys.txt
sed -i.bak -e 's/>//g' ./fastas/decoys.txt

salmon index -t ./fastas/gentome.fa \\
    -d ./fastas/decoys.txt \\
    -i ./bowtie2_index/genome \\
    -p ${threads}
"""
