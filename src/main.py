import sys
import os
import metadata as mt
import data as dt

from coleta import coleta_pb2 as Coleta, IDColeta
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf import text_format
from parser import parse


if "YEAR" in os.environ:
    YEAR = os.environ["YEAR"]
else:
    sys.stderr.write("YEAR environment variable not set\n")
    os._exit(1)

if "MONTH" in os.environ:
    MONTH = os.environ["MONTH"]
else:
    sys.stderr.write("MONTH environment variable not set\n")
    os._exit(1)

if "OUTPUT_FOLDER" in os.environ:
    OUTPUT_FOLDER = os.environ["OUTPUT_FOLDER"]
else:
    OUTPUT_FOLDER = "/output"

if "GIT_COMMIT" in os.environ:
    CRAWLER_VERSION = os.environ["GIT_COMMIT"]
else:
    CRAWLER_VERSION = "unspecified"


def parse_execution(data, file_names):
    # Cria objeto com dados da coleta.
    coleta = Coleta.Coleta()
    coleta.chave_coleta = IDColeta("mpma", MONTH, YEAR)
    coleta.orgao = "mpma"
    coleta.mes = int(MONTH)
    coleta.ano = int(YEAR)
    coleta.repositorio_coletor = "https://github.com/dadosjusbr/coletor-mpma"
    coleta.versao_coletor = CRAWLER_VERSION
    coleta.arquivos.extend(file_names)
    timestamp = Timestamp()
    timestamp.GetCurrentTime()
    coleta.timestamp_coleta.CopyFrom(timestamp)

    # Consolida folha de pagamento
    payroll = Coleta.FolhaDePagamento()
    payroll = parse(data, coleta.chave_coleta, MONTH, YEAR)

    # Monta resultado da coleta.
    rc = Coleta.ResultadoColeta()
    rc.folha.CopyFrom(payroll)
    rc.coleta.CopyFrom(coleta)

    metadata = mt.catch(int(MONTH), int(YEAR))
    rc.metadados.CopyFrom(metadata)

    # Imprime a versão textual na saída padrão.
    print(text_format.MessageToString(rc), flush=True, end="")


# Main execution
def main():
    file_names = [f.rstrip() for f in sys.stdin.readlines()]
    data = dt.load(file_names, YEAR, MONTH, OUTPUT_FOLDER)
    data.validate()
    parse_execution(data, file_names)


if __name__ == "__main__":
    main()