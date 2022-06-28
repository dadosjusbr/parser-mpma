import sys
import os

from pandas import notnull
import number

from coleta import coleta_pb2 as Coleta

from headers_keys import (REMUNERACAOBASICA, EVENTUALTEMP, OBRIGATORIOS, HEADERS)


def parse_employees(file, colect_key):
    employees = {}
    counter = 1
    for row in file:
        if not number.is_nan(row[0]):
            registration = str(row[0])[:-2] # Precisamos disso pois o pandas entende que a matrícula é um número float.
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
                    create_contracheque(row)
                )

                employees[registration] = member
                counter += 1

    return employees

def remunerations(file_indenizatorias):
    dict_remuneracoes = {}
    for row in file_indenizatorias:
        mat = str(row[0])
        remuneracoes = dict_remuneracoes.get(mat, Coleta.Remuneracoes())
        rem = Coleta.Remuneracao()
        rem.natureza = Coleta.Remuneracao.Natureza.Value("R")
        rem.categoria = str(row[4])
        rem.item = str(row[5])
        rem.valor = float(number.format_value(row[6]))
        rem.tipo_receita = Coleta.Remuneracao.TipoReceita.Value("O")
        remuneracoes.remuneracao.append(rem)
        dict_remuneracoes[mat] = remuneracoes
    return dict_remuneracoes

def create_indenizacoes(employee, remuneracoes):
    if employee in remuneracoes.keys():
        return remuneracoes[employee]


def create_contracheque(row):
    # REMUNERAÇÃO BÁSICA
    remuneration_array = Coleta.Remuneracoes()
    items = list(HEADERS[REMUNERACAOBASICA].items())
    for i in range(len(items)):
        key, value = items[i][0], items[i][1]
        remuneration = Coleta.Remuneracao()
        remuneration.natureza = Coleta.Remuneracao.Natureza.Value("R")
        remuneration.categoria = REMUNERACAOBASICA
        remuneration.item = key
        remuneration.valor = float(number.format_value(row[value]))
        remuneration.tipo_receita = Coleta.Remuneracao.TipoReceita.Value("B") 
        remuneration_array.remuneracao.append(remuneration)

    # REMUNERAÇÃO EVENTUAL OU TEMPORÁRIA
    items = list(HEADERS[EVENTUALTEMP].items())
    for i in range(len(items)):
        key, value = items[i][0], items[i][1]
        remuneration = Coleta.Remuneracao()
        remuneration.natureza = Coleta.Remuneracao.Natureza.Value("R")
        remuneration.categoria = EVENTUALTEMP
        remuneration.item = key
        remuneration.valor = float(number.format_value(row[value]))
        remuneration.tipo_receita = Coleta.Remuneracao.TipoReceita.Value("B")
        remuneration_array.remuneracao.append(remuneration)

    # OBRIGATÓRIOS / LEGAIS
    items = list(HEADERS[OBRIGATORIOS].items())
    for i in range(len(items)):
        key, value = items[i][0], items[i][1]
        remuneration = Coleta.Remuneracao()
        remuneration.natureza = Coleta.Remuneracao.Natureza.Value("R")
        remuneration.categoria = OBRIGATORIOS
        remuneration.item = key
        remuneration.valor = float(number.format_value(row[value]))
        remuneration.natureza = Coleta.Remuneracao.Natureza.Value("D")
        remuneration_array.remuneracao.append(remuneration)

    return remuneration_array

def update_employees(file_indenizatorias, employees):
    remuneracoes = remunerations(file_indenizatorias)
    for employee in employees:
        emp = employees[employee]
        remu = create_indenizacoes(employee, remuneracoes)
        emp.remuneracoes.MergeFrom(remu)
        employees[employee] = emp
    return employees 

def parse(data, colect_key):
    employees = {}
    payroll = Coleta.FolhaDePagamento()

    employees.update(parse_employees(data.contracheque, colect_key))
    update_employees(data.indenizatorias, employees)

    for i in employees.values():
        payroll.contra_cheque.append(i)

    return payroll
