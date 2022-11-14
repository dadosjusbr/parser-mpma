from coleta import coleta_pb2 as Coleta


def catch(month, year):
    metadata = Coleta.Metadados()
    metadata.acesso = Coleta.Metadados.FormaDeAcesso.NECESSITA_SIMULACAO_USUARIO
    metadata.extensao = Coleta.Metadados.Extensao.XLS
    metadata.estritamente_tabular = True
    metadata.tem_matricula = True
    metadata.tem_lotacao = True
    metadata.tem_cargo = True
    metadata.receita_base = Coleta.Metadados.OpcoesDetalhamento.DETALHADO
    metadata.despesas = Coleta.Metadados.OpcoesDetalhamento.DETALHADO
    metadata.outras_receitas = Coleta.Metadados.OpcoesDetalhamento.DETALHADO
    metadata.formato_consistente = True

    return metadata
