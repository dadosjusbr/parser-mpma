import sys
import os
import number

from coleta import coleta_pb2 as Coleta

from headers_keys import (CONTRACHEQUE, INDENIZACOES, HEADERS)


def parse_employees(file, colect_key, category):
    employees = {}
    counter = 1
    for row in file:
        if not number.is_nan(row[0]):
            registration = str(row[0])
            name = row[1]
            function = row[2]
            location = row[3]
            if not number.is_nan(registration) and registration != "MATRÍCULA":
                member = Coleta.ContraCheque()
                member.id_contra_cheque = colect_key + "/" + str(counter)
                member.chave_coleta = colect_key
                member.matricula = registration
                member.nome = str(name)
                member.funcao = str(function)
                member.local_trabalho = str(location)
                member.tipo = Coleta.ContraCheque.Tipo.Value("MEMBRO")
                member.ativo = True

                member.remuneracoes.CopyFrom(
                    create_remuneration(row, category)
                )

                employees[registration] = member
                counter += 1

    return employees


def create_remuneration(row, category):
    remuneration_array = Coleta.Remuneracoes()
    items = list(HEADERS[category].items())
    print(row)
    for i in range(len(items)):
        key, value = items[i][0], items[i][1]
        remuneration = Coleta.Remuneracao()
        remuneration.natureza = Coleta.Remuneracao.Natureza.Value("R")
        remuneration.categoria = category
        remuneration.item = key
        # Caso o valor seja negativo, ele vai transformar em positivo:

        
        #remuneration.valor = float(abs(number.format_value(row[value])))
        remuneration.valor = float(number.format_value(row[value]))

        if (category == CONTRACHEQUE and value in [13, 14, 15]):
            remuneration.natureza = Coleta.Remuneracao.Natureza.Value("D")
        else:
            remuneration.tipo_receita = Coleta.Remuneracao.TipoReceita.Value("B")

        remuneration_array.remuneracao.append(remuneration)
        

    return remuneration_array


def update_employees(file, employees, category):
    for row in file:
        registration = str(row[0])
        if registration in employees.keys():
            emp = employees[registration]
            remu = create_remuneration(row, category)
            emp.remuneracoes.MergeFrom(remu)
            employees[registration] = emp
    return employees


def parse(data, colect_key, month, year):
    employees = {}
    payroll = Coleta.FolhaDePagamento()

    employees.update(parse_employees(data.contracheque, colect_key, CONTRACHEQUE))
    update_employees(data.indenizatorias, employees, INDENIZACOES)

    for i in employees.values():
        payroll.contra_cheque.append(i)

    return payroll
