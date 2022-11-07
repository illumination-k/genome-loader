import dataclasses
import gzip
import io
import os
import subprocess
from typing import Literal

import requests

from _io import Genome


@dataclasses.dataclass
class DlResult:
    filename: str
    content: bytes

    def write_to_file(self, dir_path: str):
        path = os.path.join(dir_path, self.filename)

        with open(path, mode="wb") as wb:
            wb.write(self.content)


def dl(url: str, gzipped: bool) -> DlResult:
    filename = os.path.basename(url).replace(".gz", "")

    r = requests.get(url)
    if gzipped:
        with gzip.open(io.BytesIO(r.content), mode="rb") as gzip_content:
            content = gzip_content.read()
    else:
        content = r.content

    return DlResult(filename=filename, content=content)


def download_genome_fasta(url: str, gzip: bool, genome: Genome):
    res = dl(url, gzip)
    res.filename = "genome.fa"
    res.write_to_file(genome.fasta_path())


def gff2gtf(gff_path: str, genome_fasta_path: str):
    # Not basename!
    filename = os.path.splitext(gff_path)[0]
    command = [
        "gffread",
        "-E",
        gff_path,
        "-g",
        genome_fasta_path,
        "-o",
        f"{filename}.gtf",
    ]
    subprocess.run(command)


def annotaion(
    url: str, gzip: bool, format: Literal["gff3", "gtf"], genome: Genome
) -> bytes:
    res = dl(url, gzip)
    res.write_to_file(genome.annotation_path())

    if format == "gff3":
        gff2gtf(
            os.path.join(genome.annotation_path(), res.filename),
            os.path.join(genome.fasta_path(), "genome.fa"),
        )
