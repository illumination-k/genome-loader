import dataclasses
import os

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
class Genome:
    name: str
    version: str

    def root_path(self) -> str:
        return os.path.join(self.name, self.version)

    def fasta_path(self) -> str:
        return os.path.join(self.root_path(), "fasta")

    def annotation_path(self) -> str:
        return os.path.join(self.root_path(), "annotations")

    def scripts_path(self) -> str:
        return os.path.join(self.root_path(), "scripts")


def create_dirs(root_dir, genome_name, version):
    dir_path = os.path.join(root_dir, genome_name, version)
