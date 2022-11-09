from genome_loader.config import ConfigModel

example_config = """{
  "tools": ["blast", "salmon", "hisat2", "bowtie2", "STAR"],
  "genomes": [
    {
      "name": "mpolymorpha",
      "data": [
        {
          "version": "v6.1",
          "genome": {
            "gzip": true,
            "url": "https://marchantia.info/download/MpTak_v6.1/MpTak_v6.1.genome.fasta.gz"
          },
          "annotation": {
            "gzip": true,
            "format": "gff",
            "url": "https://marchantia.info/download/MpTak_v6.1/MpTak_v6.1r1.gff.gz"
          }
        }
      ]
    }
  ]
}"""


def test_parse_example():
    config = ConfigModel.parse_raw(example_config.encode("utf-8"))
