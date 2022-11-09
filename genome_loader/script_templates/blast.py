template = """#!/bin/bash

set -eu

cd $(dirname $0)

cd ..
mkdir -p blastdb

for nucl for 'genome' 'exon' 'cds'; do
    makeblastdb -in ./fasta/${nucl}.fa -out ./blastdb/${nucl} \\
        -dbtype nucl -parse_seqids -hash_index
done

makeblastdb -in ./fasta/protein.fa -out ./blastdb/protein \\
    -dbtype prot -parse_seqids -hash_index
"""
