import logging
import shutil
from typing import List, Literal

logger = logging.getLogger(__name__)

OptionalCommand = Literal["blast", "hisat2", "salmon", "bowtie2"]


def run(optional_commands: List[str]):
    if (path := shutil.which("gffread")) is not None:
        logger.debug(f"gffread path: {path}")
    else:
        logger.error("gffread is required!")

    for cmd in optional_commands:
        if shutil.which(cmd) is None:
            logger.error(f"{cmd} is required!")
