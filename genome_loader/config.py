from typing import Literal

from pydantic import BaseModel


class GenomeFastaModel(BaseModel):
    url: str
    gzip: bool


class GenomeAnnotationModel(BaseModel):
    gzip: bool
    format: Literal["gff", "gtf"]
    url: str


class GenomeVersionModel(BaseModel):
    version: str
    genome: GenomeFastaModel
    annotation: GenomeAnnotationModel


class GenomeModel(BaseModel):
    name: str
    data: list[GenomeVersionModel]


class ConfigModel(BaseModel):
    tools: list[str]
    genomes: list[GenomeModel]
