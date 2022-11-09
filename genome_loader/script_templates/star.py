template = """#!/bin/bash

set -eu

cd $(dirname $0)

cd ..
mkdir -p star_index

threads=${1:-1}

STAR --runMode genomeGenerate \\
    --runThreadN ${threads} \\
    --genomeDir ./star_index \\
    --genomeFastaFiles ./fastas/genome.fa \\
    --sjdbGTFfile ./annotations/genome.gtf \\
    --genomeSAindexNbases 12
"""
