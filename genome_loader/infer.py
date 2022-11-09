from typing import Literal


def is_gzip(uri: str) -> bool:
    if "gz" in uri:
        return True
    else:
        return False


def annotation_format(uri: str) -> Literal["gff", "gtf"]:
    if "gtf" in uri:
        return "gtf"
    else:
        return "gff"
