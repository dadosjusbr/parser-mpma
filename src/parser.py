import sys
import os

from pandas import notnull
import number

from coleta import coleta_pb2 as Coleta

from headers_keys import MES13, REMUNERACAOBASICA, EVENTUALTEMP, OBRIGATORIOS, HEADERS


# Listando os membros da folha de contracheque
def parse_employees(file, colect_key, file_cq13, month):
    employees = {}
    counter = 1
    if month == "12":
        cq13 = contracheque13(file_cq13)
    for row in file:
        if not number.is_nan(row[0]):
            # Precisamos disso pois o pandas entende que a matrícula é um número float.
            registration = str(row[0])
            name = row[1]
            function = row[2]
            location = row[3]
            if (
                not number.is_nan(registration)
                and registration.casefold() != "matrícula"
            ):
                member = Coleta.ContraCheque()
                member.id_contra_cheque = colect_key + "/" + str(counter)
                member.chave_coleta = colect_key
                member.matricula = registration
                member.nome = str(name)
                member.funcao = str(function)
                member.local_trabalho = str(location)
                member.tipo = Coleta.ContraCheque.Tipo.Value("MEMBRO")
                member.ativo = True
                if month == "12" and row[0] in file_cq13:
                    employee = cq13.get(registration)
                    member.remuneracoes.CopyFrom(
                        create_contracheque(row, month, employee)
                    )
                else:
                    member.remuneracoes.CopyFrom(create_contracheque(row, month, ""))

                employees[registration] = member
                counter += 1

    return employees


# Listando cada rubrica da folha de indenizações e seus valores
# R = Receita; O = Outras
def remunerations(file_indenizatorias):
    dict_remuneracoes = {}
    for row in file_indenizatorias:
        if number.is_nan not in row:
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


# Listando cada rubrica do contracheque e seus valores
# Apenas a Remuneração do Cargo Efetivo é do tipo B = Base
# Os demais são O, outras remunerações, ou D, descontos
def create_contracheque(row, month, employee):
    # REMUNERAÇÃO BÁSICA
    remuneration_array = Coleta.Remuneracoes()
    for key, value in HEADERS[REMUNERACAOBASICA].items():
        remuneration = Coleta.Remuneracao()
        remuneration.natureza = Coleta.Remuneracao.Natureza.Value("R")
        remuneration.categoria = REMUNERACAOBASICA
        remuneration.item = key
        remuneration.valor = float(number.format_value(row[value]))
        if value == 4:
            remuneration.tipo_receita = Coleta.Remuneracao.TipoReceita.Value("B")
        else:
            remuneration.tipo_receita = Coleta.Remuneracao.TipoReceita.Value("O")
        remuneration_array.remuneracao.append(remuneration)

    # REMUNERAÇÃO EVENTUAL OU TEMPORÁRIA
    for key, value in HEADERS[EVENTUALTEMP].items():
        remuneration = Coleta.Remuneracao()
        remuneration.natureza = Coleta.Remuneracao.Natureza.Value("R")
        remuneration.categoria = EVENTUALTEMP
        remuneration.item = key
        if month == "12" and value in [7, 9] and employee != "":
            for emp in employee.remuneracao:
                if key in emp.item:
                    remuneration.valor = (
                        float(number.format_value(row[value])) + emp.valor
                    )
        else:
            remuneration.valor = float(number.format_value(row[value]))
        remuneration.tipo_receita = Coleta.Remuneracao.TipoReceita.Value("O")
        remuneration_array.remuneracao.append(remuneration)

    # OBRIGATÓRIOS / LEGAIS
    for key, value in HEADERS[OBRIGATORIOS].items():
        remuneration = Coleta.Remuneracao()
        remuneration.categoria = OBRIGATORIOS
        remuneration.item = key
        if month == "12" and value in [13, 14] and employee != "":
            for emp in employee.remuneracao:
                if key in emp.item:
                    remuneration.valor = (
                        float(number.format_value(row[value])) + emp.valor
                    ) * (-1)
        else:
            remuneration.valor = float(number.format_value(row[value])) * (-1)
        remuneration.natureza = Coleta.Remuneracao.Natureza.Value("D")
        remuneration_array.remuneracao.append(remuneration)

    return remuneration_array


# O MPMA possui um contracheque "a mais" referente ao 13º
# Juntamos com a folha de dezembro
def contracheque13(cq13):
    dict_cq13 = {}
    for row in cq13:
        # Para não confundir o cabeçalho da planilha de contracheque com os valores.
        if not number.is_nan(row[0]) and str(row[0]).casefold() != "matrícula":
            # Precisamos disso pois o pandas entende que a matrícula é um número float.
            mat = str(row[0])
            remuneracoes = dict_cq13.get(mat, Coleta.Remuneracoes())
            for key, value in MES13[EVENTUALTEMP].items():
                remuneration = Coleta.Remuneracao()
                remuneration.natureza = Coleta.Remuneracao.Natureza.Value("R")
                remuneration.categoria = EVENTUALTEMP
                remuneration.item = key
                remuneration.valor = float(number.format_value(row[value]))
                remuneration.tipo_receita = Coleta.Remuneracao.TipoReceita.Value("O")
                remuneracoes.remuneracao.append(remuneration)
            for key, value in MES13[OBRIGATORIOS].items():
                remuneration = Coleta.Remuneracao()
                remuneration.categoria = OBRIGATORIOS
                remuneration.item = key
                remuneration.valor = float(number.format_value(row[value]))
                remuneration.natureza = Coleta.Remuneracao.Natureza.Value("D")
                remuneracoes.remuneracao.append(remuneration)
            dict_cq13[mat] = remuneracoes
    return dict_cq13


# Mapeando as indenizações para cada membro da folha de contracheque
def update_employees(file_indenizatorias, employees):
    remuneracoes = remunerations(file_indenizatorias)
    for employee in employees:
        emp = employees[employee]
        remu = create_indenizacoes(employee, remuneracoes)
        emp.remuneracoes.MergeFrom(remu)
        employees[employee] = emp
    return employees


# Executando todas as funções,
# iterando os contracheques e indenizações e retornando a folha completa
def parse(data, colect_key):
    employees = {}
    payroll = Coleta.FolhaDePagamento()
    cq13 = contracheque13(data.contracheque13)

    employees.update(
        parse_employees(data.contracheque, colect_key, data.contracheque13, data.month)
    )
    update_employees(data.indenizatorias, employees)

    for i in employees.values():
        payroll.contra_cheque.append(i)

    return payroll
