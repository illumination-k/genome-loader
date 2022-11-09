import dataclasses
import gzip as gz
import io
import logging
import os
import subprocess
from pathlib import Path

import requests

from genome_loader import infer
from genome_loader.config import ConfigModel, GenomeVersionModel, GenomeAnnotationModel, GenomeFastaModel, GenomeModel

logger = logging.getLogger(__name__)

"""
.
|- mpolymorpha
    |- v6.1
        |- fastas*
            |- genome.fa
            |- cds.fa
            |- exon.fa
            |- protein.fa
        |- annotations*
            |- annotation.gff
            |- annotation.gtf
        |- blastdb
            |- genome.db
            |- cds.db
            |- exon.db
            |- protein.db
        |- hisat2
            |- index.ht.1
            ...
        |- bowtie2
            |- index.bt.1
            ...
        |- STAR
            |- ...
        |- scripts*
            |- blastdb.sh
            |- hisat2.sh
            |- bowtie2.sh
            ...
"""


@dataclasses.dataclass
class GenomeIOUtil:
    name: str
    version: str

    def root_path(self) -> Path:
        return Path(os.path.join(self.name, self.version))

    def fasta_path(self) -> Path:
        return Path(os.path.join(self.root_path(), "fasta"))

    def annotation_path(self) -> Path:
        return Path(os.path.join(self.root_path(), "annotations"))

    def scripts_path(self) -> Path:
        return Path(os.path.join(self.root_path(), "scripts"))

    def create_dirs(self):
        os.makedirs(self.fasta_path(), exist_ok=True)
        os.makedirs(self.annotation_path(), exist_ok=True)
        os.makedirs(self.scripts_path(), exist_ok=True)


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


def sync(config: ConfigModel):
    tools = config.tools

    for genome in config.genomes:
        genome_name = genome.name
        data = genome.data

        for d in data:
            util = GenomeIOUtil(genome_name, d.version)
            util.create_dirs()

            def dl_and_write(url: str, path: Path, gzip: bool):
                if path.exists() and path.stat().st_size >= 10:
                    logger.debug(f"{str(path)} already exists! skip download...")
                    return

                r = requests.get(url)
                if gzip:
                    with gz.open(io.BytesIO(r.content), "rb") as gf:
                        with open(path, "wb") as wb:
                            wb.write(gf.read())
                else:
                    with open(path, "wb") as wb:
                        wb.write(r.content)

            # download fasta
            genome_fasta_path = Path(os.path.join(util.fasta_path(), "genome.fa"))
            dl_and_write(url=d.genome.url, path=genome_fasta_path, gzip=d.genome.gzip)

            # download annotation (and convert to gtf)
            annotation_path = Path(
                os.path.join(
                    util.annotation_path(),
                    os.path.basename(d.annotation.url.replace(".gz", "")),
                )
            )

            dl_and_write(url=d.annotation.url, path=annotation_path, gzip=d.annotation.gzip)

            if d.annotation.format == "gff":
                # convert gff to gtf for more machine freindly format
                gff2gtf(str(annotation_path), genome_fasta_path=str(genome_fasta_path))

            # extract cds, exon, protein
            cds_path = os.path.join(util.fasta_path(), "cds.fa")
            exon_path = os.path.join(util.fasta_path(), "exon.fa")
            protein_path = os.path.join(util.fasta_path(), "protein.fa")

            subprocess.run(
                [
                    "gffread",
                    "-E",
                    annotation_path,
                    "-g",
                    genome_fasta_path,
                    "-w",
                    exon_path,
                    "-x",
                    cds_path,
                    "-y",
                    protein_path,
                ]
            )

            # generate scripts
            ## Blast
            if "blast" in tools:
                blast_script_path = os.path.join(util.scripts_path(), "makeblastdb.sh")
                from genome_loader.script_templates import blast

                with open(blast_script_path, "w") as w:
                    w.write(blast.template)

            ## Hisat2

            ## Bowtie2

            ## Salmon


def genome_add(config_path: str):
    config = ConfigModel.parse_file(config_path)
    genome_names = [genome.name for genome in config.genomes]
    print("genome name?")
    print(f"current registered genome names: {' '.join(genome_names)}")
    genome_name = input()
    print("genome version?")
    genome_version = input()
    print("genomic fasta url?")
    genomic_fasta_url = input()
    genomic_fasta_is_gzip = infer.is_gzip(genomic_fasta_url)
    print("annotation url?")
    annotation_url = input()
    annotation_url_is_gzip = infer.is_gzip(annotation_url)
    annotation_format = infer.annotation_format(annotation_url)
    
    genome_version = GenomeVersionModel(
        version = genome_version,
        genome=GenomeFastaModel(url=genomic_fasta_url, gzip=genomic_fasta_is_gzip),
        annotation=GenomeAnnotationModel(url=annotation_url, gzip=annotation_url_is_gzip, format=annotation_format)
    )
    
    if genome_name in genome_names:
        idx = genome_names.index(genome_name)
        config.genomes[idx].data.append(genome_version)
    else:
        config.genomes.append(GenomeModel(name=genome_name, data=[genome_version]))
    
    print(config.json(indent=2))