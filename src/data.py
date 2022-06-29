import sys
import os
import subprocess
import pandas as pd

# Se for erro de não existir planilhas o retorno vai ser esse:
STATUS_DATA_UNAVAILABLE = 4
# Caso o erro for a planilha, que é invalida por algum motivo, o retorno vai ser esse:
STATUS_INVALID_FILE = 5


def _read(file):
    try:
        d = pd.read_excel(file, engine='xlrd')
        data = d.to_numpy()
    except Exception as excep:
        print(f"Erro lendo as planilhas: {excep}", file=sys.stderr)
        sys.exit(STATUS_INVALID_FILE)
    return data

def _convert_file(file, output_path):
    """
    Corrigindo arquivos XLS que estão corrompidos.
    """
    subprocess.run(
        ["libreoffice", "--headless", "--invisible", "--convert-to", "xls", file],
        capture_output=True,
        text=True,
    )  # Pega a saída para não interferir no print dos dados
    file_name = file.split(sep="/")[-1]
    file_name = f'{file_name.split(sep=".")[0]}.xls'
    # Move para o diretório passado por parâmetro
    subprocess.run(["mv", file_name, f"{output_path}/{file_name}"])
    return f"{output_path}/{file_name}"


def load(file_names, year, month, output_folder):
    """Carrega os arquivos passados como parâmetros.
       :param file_names: slice contendo os arquivos baixados pelo coletor.
      Os nomes dos arquivos devem seguir uma convenção e começar com
      Membros ativos-contracheque e Membros ativos-Verbas Indenizatorias
       :param year e month: usados para fazer a validação na planilha de controle de dados
       :return um objeto Data() pronto para operar com os arquivos
      """

    contracheque = _read(_convert_file([c for c in file_names if "contracheque" in c][0], output_folder))
    indenizatorias = _read(_convert_file([i for i in file_names if "indenizatorias" in i][0], output_folder))

    return Data(contracheque, indenizatorias, year, month, output_folder)


class Data:
    def __init__(self, contracheque, indenizatorias, year, month, output_folder):
        self.year = year
        self.month = month
        self.output_folder = output_folder
        self.contracheque = contracheque
        self.indenizatorias = indenizatorias

    def validate(self):
        """
         Validação inicial dos arquivos passados como parâmetros.
        Aborta a execução do script em caso de erro.
         Caso o validade fique pare o script na leitura da planilha 
        de controle de dados dara um erro retornando o codigo de erro 4,
        esse codigo significa que não existe dados para a data pedida.
        """

        if not (
                os.path.isfile(
                    f"{self.output_folder}/membros-ativos-contracheque-{self.month}-{self.year}.xls"
                )
                or os.path.isfile(
            f"{self.output_folder}/membros-ativos-verbas-indenizatorias-{self.month}-{self.year}.xls"
        )
        ):
            sys.stderr.write(f"Não existe planilhas para {self.month}/{self.year}.")
            sys.exit(STATUS_DATA_UNAVAILABLE)