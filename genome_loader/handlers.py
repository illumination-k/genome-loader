import dataclasses
import gzip as gz
import io
import logging
import os
import subprocess
from pathlib import Path
from typing import Literal

import requests

from genome_loader import infer
from genome_loader.config import (
    ConfigModel,
    GenomeAnnotationModel,
    GenomeFastaModel,
    GenomeModel,
    GenomeVersionModel,
)

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

    def meta_path(self) -> Path:
        return Path(os.path.join(self.root_path(), "meta.json"))

    def create_dirs(self):
        os.makedirs(self.fasta_path(), exist_ok=True)
        os.makedirs(self.annotation_path(), exist_ok=True)
        os.makedirs(self.scripts_path(), exist_ok=True)


def gff2gtf(gff_path: str, genome_fasta_path: str):
    # Not basename!
    dir_path = os.path.dirname(gff_path)
    command = [
        "gffread",
        "-E",
        gff_path,
        "-g",
        genome_fasta_path,
        "-o",
        f"{os.path.join(dir_path, 'genome')}.gtf",
    ]
    logger.debug(f"command of gff2gtf: f{' '.join(command)}")
    subprocess.run(command)


def extract_features(annotation_path: str, genome_fasta_path: str, util: GenomeIOUtil):
    # extract cds, exon, protein
    cds_path = os.path.join(util.fasta_path(), "cds.fa")
    exon_path = os.path.join(util.fasta_path(), "exon.fa")
    protein_path = os.path.join(util.fasta_path(), "protein.fa")

    base_command = [
        "gffread",
        "-E",
        annotation_path,
        "-g",
        genome_fasta_path,
    ]

    extend_command = []

    if not os.path.exists(cds_path):
        extend_command += [
            "-x",
            cds_path,
        ]

    if not os.path.exists(exon_path):
        extend_command += [
            "-w",
            exon_path,
        ]

    if not os.path.exists(protein_path):
        extend_command += [
            "-y",
            protein_path,
        ]

    if len(extend_command) != 0:
        command = base_command + extend_command
        logger.debug(f"command of extract features by gffread: f{' '.join(command)}")
        subprocess.run(command)


def check_update(url: str, util: GenomeIOUtil, file_type: Literal["genome", "annotation"]) -> bool:
    # check uri is the same as previous and file exists or not
    meta_path = util.meta_path()

    # generate file path corresponding to file type
    file_name = "genome.fa" if file_type == "genome" else "genome.gtf"
    file_dir = util.fasta_path() if file_type == "genome" else util.annotation_path()
    file_path = Path(os.path.join(file_dir, file_name))

    if os.path.exists(meta_path):
        meta = GenomeVersionModel.parse_file(meta_path)
        prev_url = meta.genome.url if file_type == "genome" else meta.annotation.url

        if prev_url == url and file_path.exists() and file_path.stat().st_size >= 10:
            logger.debug(f"{str(file_path)} already exists! skip updating...")
            return False

    return True


def dl_and_write(url: str, path: Path, gzip: bool):
    r = requests.get(url)
    if gzip:
        with gz.open(io.BytesIO(r.content), "rb") as gf:
            with open(path, "wb") as wb:
                wb.write(gf.read())
    else:
        with open(path, "wb") as wb:
            wb.write(r.content)


def sync(config: ConfigModel):
    tools = config.tools

    for genome in config.genomes:
        genome_name = genome.name
        data = genome.data

        for d in data:
            util = GenomeIOUtil(genome_name, d.version)
            util.create_dirs()

            # download fasta
            genome_fasta_path = Path(os.path.join(util.fasta_path(), "genome.fa"))

            is_genome_updated = check_update(
                url=d.genome.url,
                util=util,
                file_type="genome",
            )

            if is_genome_updated:
                dl_and_write(url=d.genome.url, path=genome_fasta_path, gzip=d.genome.gzip)

            # download annotation (and convert to gtf)
            annotation_path = Path(
                os.path.join(
                    util.annotation_path(),
                    f"genome.{d.annotation.format}",
                )
            )

            is_annotation_updated = check_update(
                url=d.annotation.url,
                util=util,
                file_type="annotation",
            )

            if is_annotation_updated:
                dl_and_write(url=d.annotation.url, path=annotation_path, gzip=d.annotation.gzip)
                if d.annotation.format == "gff":
                    # convert gff to gtf for more machine freindly format
                    gff2gtf(str(annotation_path), genome_fasta_path=str(genome_fasta_path))

                extract_features(
                    annotation_path=str(annotation_path),
                    genome_fasta_path=str(genome_fasta_path),
                    util=util,
                )

            # generate scripts if any update occured
            if is_annotation_updated or is_genome_updated:
                from genome_loader import script_templates

                tools_map = {
                    "blast": script_templates.blast_template,
                    "hisat2": script_templates.hisat2_template,
                    "bowtie2": script_templates.bowtie2_template,
                    "STAR": script_templates.star_template,
                    "salmon": script_templates.salmon_template,
                }

                for k, v in tools_map.items():
                    if k in tools:
                        with open(os.path.join(util.scripts_path(), f"{k}.sh"), "w") as w:
                            w.write(v)
            else:
                logger.debug("No update!")

            # save meta file
            with open(util.meta_path(), "w") as w:
                w.write(d.json(indent=2))


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

    new_genome_version = GenomeVersionModel(
        version=genome_version,
        genome=GenomeFastaModel(url=genomic_fasta_url, gzip=genomic_fasta_is_gzip),
        annotation=GenomeAnnotationModel(
            url=annotation_url, gzip=annotation_url_is_gzip, format=annotation_format
        ),
    )

    if genome_name in genome_names:
        idx = genome_names.index(genome_name)
        config.genomes[idx].data.append(new_genome_version)
    else:
        config.genomes.append(GenomeModel(name=genome_name, data=[new_genome_version]))

    with open(config_path, "w") as w:
        w.write(config.json(indent=2))


def init():
    init_config = ConfigModel(tools=["blast", "salmon", "hisat2", "bowtie2", "STAR"], genomes=[])

    with open("genomes.json", "w") as w:
        w.write(init_config.json(indent=2))
