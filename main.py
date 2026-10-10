###################################################################
################## SISTEMA DE CONTROLE FINANCEIRO #################
###################################################################
### NOME: Diego Carvalho Louzada Viveiros                       ###
###################################################################


###############################################
########## Importação de bibliotecas ##########
###############################################

import csv # importa a biblioteca CSV para manipulação de arquivos CSV
import sys

from analise import (
    ErroLeitura,
    calcular_media,
    calcular_percentual,
    encontrar_maior_e_menor,
    ler_movimentacoes,
    nome_do_mes,
    somar_por_mes,
)

try:
    arquivo = open('dados/movimentacoes.csv')
    # L> abre o arquivo CSV com os dados de movimentações
except FileNotFoundError:
    print("\nErro: O arquivo inserido não foi encontrado!!\n")
    sys.exit()

leitor = csv.reader(arquivo) # permite a leitura do arquivo CSV


##################################################################
########## Definição de variáveis e estruturas de dados ##########
##################################################################

receita = 0 # inicializa a variável receita com valor 0
despesa = 0 # inicializa a variável despesa com valor 0
saldo = 0 # inicializa a variável saldo com valor 0

despesas_categorias = {} 
# L> inicializa um dicionário para armazenar as despesas por categoria
maior_despesas_categorias = 0 # inicializa a variável maior_despesas_categorias com valor 0
categoria_maior_despesa = "" # inicializa a variável categoria_maior_despesa com uma string vazia

receitas_categorias = {} # inicializa um dicionário para armazenar as receitas por categoria
maior_receitas_categorias = 0 # inicializa a variável maior_receitas_categorias com valor 0
categoria_maior_receita = "" # inicializa a variável categoria_maior_receita com uma string vazia

percentuais_categorias = {} # inicializa um dicionário para armazenar os percentuais de cada categoria
percentuais_receitas = {} # inicializa um dicionário para armazenar os percentuais de cada categoria de receitas

valores_mes = {} # inicializa um dicionário para armazenar os valores de cada mês



##########################################
########## Definição de funções ##########
##########################################

   
def processar_movimentacao(receita, despesa, tipo, valor, categoria, receitas_categorias, despesas_categorias):
        if tipo == 'receita': # verifica se o tipo é receita
            receita, receitas_categorias[categoria] = atualizar_movimentacao(valor, categoria, receita, receitas_categorias)
        elif tipo == 'despesa': # verifica se o tipo é despesa
            despesa, despesas_categorias[categoria] = atualizar_movimentacao(valor, categoria, despesa, despesas_categorias)
        else:
            print("Erro: O tipo de movimentação inserido é inválido!!")
            sys.exit()
        return receita, despesa # retorna as variáveis receita e despesa atualizadas
#L> função responsável por decidir se aquela movimentação é uma receita ou despesa e encaminhar os dados corretamente.


def atualizar_movimentacao(valor, categoria, total, categorias): # declaração da função
    total = total + valor # calculo do total depois da entrada de uma movimentação

    if categoria in categorias: # verifica se a categoria já existe no dicionário de categorias
        categorias[categoria] = categorias[categoria] + valor # se existir, adiciona o valor da movimentação
    else:
        categorias[categoria] = valor # se não existir, cria a categoria e adiciona o valor da movimentação

    return total, categorias[categoria]
#L> função generica que pega os valores trazidos por processar_movimentacao e
#   e atualiza as variáveis total e categorias com os valores das movimentações;



limite_percentual = 20
def analisar_concentracao(percentual_categorias, limite_percentual):
    return percentual_categorias >= limite_percentual



######################################################
########### Processamento das movimentações ##########
######################################################


try:
    movimentacoes = ler_movimentacoes(leitor)
except ErroLeitura as erro:
    print(f"\nErro: {erro}\n")
    sys.exit(1)

for data, valor, tipo, categoria, descricao in movimentacoes:
    receita, despesa = processar_movimentacao(receita, despesa, tipo, valor, categoria, receitas_categorias, despesas_categorias)
    # L> armazena a movimentação e atualiza as variáveis receita e despesa

valores_receitas_mes = somar_por_mes(movimentacoes, "receita")
valores_despesas_mes = somar_por_mes(movimentacoes, "despesa")



#########################################
########### Funções auxiliares ##########
#########################################    

def mostrar_categorias(categorias): # função mostra as categorias e seus respectivos valores
    for categoria in categorias:
        print(f"= > {categoria} : R$ {categorias[categoria]:.2f}")

def maior_categoria(categorias): # função retorna a categoria com maior valor e o valor correspondente
    maior_valor_categorias = 0
    categoria_maior = ""

    for categoria in categorias:
        if categorias[categoria] > maior_valor_categorias:
            maior_valor_categorias = categorias[categoria]
            categoria_maior = categoria

    return categoria_maior, maior_valor_categorias # retorna a categoria com maior valor e o valor correspondente


saldo = receita - despesa # calculo do saldo


armaz_maior_movimentacao, armaz_menor_movimentacao = encontrar_maior_e_menor(movimentacoes)


qtd_receitas = 0
qtd_despesas = 0
for movimentacao in movimentacoes:
    data, valor, tipo, categoria, descricao = movimentacao  

    if tipo == "receita":
        qtd_receitas = qtd_receitas + 1
    elif tipo == "despesa":
        qtd_despesas = qtd_despesas + 1



######################################
########### Relatório final ##########
######################################

print ('\n====================================================')
print ('================ ANALISE FINANCEIRA ================')
print ('====================================================\n')
resultado_comprometido = calcular_percentual(despesa, receita)
resultado_disponivel = calcular_percentual(saldo, receita)
print(f'Total de Receitas: R$ {receita:.2f}')
print(f'Total de Despesas: R$ {despesa:.2f}')
print(f'Saldo: R$ {saldo:.2f}')
print('\n >>> ANALISE PERCENTUAL DE RECEITA COMPROMETIDA E RECEITA DISPONIVEL <<< \n')
print(f'Receita Comprometida: {resultado_comprometido:.2f} %')
print(f'Receita Disponível: {resultado_disponivel:.2f} %')

print ('\n====================================================')
print ('================== ANALISE MENSAL ==================')
print ('====================================================\n')
meses = set(valores_receitas_mes.keys()) | set(valores_despesas_mes.keys())
meses_ordenados = sorted (meses)
for ano, mes in meses_ordenados:
    nome_mes = f"{nome_do_mes(mes)}/{ano}"

    receita_mes = valores_receitas_mes.get((ano, mes), 0)
    despesa_mes = valores_despesas_mes.get((ano, mes), 0)

    saldo_mes = receita_mes - despesa_mes

    print(f'\nMês: {nome_mes}')
    print(f'Valor de receita: R$ {receita_mes:.2f}')
    print(f'Valor de despesa: R$ {despesa_mes:.2f}')
    print(f'Valor do saldo: R$ {saldo_mes:.2f}')

print ('\n====================================================')
print ('=========== HISTÓRICO DE MOVIMENTAÇÕES =============')
print ('====================================================\n')
movimentacoes_ordenadas = sorted(movimentacoes, key=lambda item: item[0])
for movimentacao in movimentacoes_ordenadas:
    data, valor, tipo, categoria, descricao = movimentacao
    data_formatada = data.strftime("%d/%m/%Y") # formatando data, pois na analise mensal ela deixou de ser uma string
    print (f"data: {data_formatada} | valor: {valor:10.2f} | Tipo: {tipo: <10} | Categoria: {categoria: <15} | Descricao: {descricao: <15}")

print ('\n===============================================')
print ('============= MAIOR MOVIMENTAÇÃO ==============')
print ('===============================================\n')
data, valor, tipo, categoria, descricao = armaz_maior_movimentacao
data_formatada = data.strftime("%d/%m/%Y") # formatando data, pois na analise mensal ela deixou de ser uma string
print(f'= > Data: {data_formatada} \n= > Valor: R$ {valor:.2f} \n= > Tipo: {tipo} \n= > Categoria: {categoria} \n= > Descricao: {descricao}')

print ('\n===============================================')
print ('============= MENOR MOVIMENTAÇÃO ==============')
print ('===============================================\n')
data, valor, tipo, categoria, descricao = armaz_menor_movimentacao
data_formatada = data.strftime("%d/%m/%Y") # formatando data, pois na analise mensal ela deixou de ser uma string
print(f'= > Data: {data_formatada} \n= > Valor: R$ {valor:.2f} \n= > Tipo: {tipo} \n= > Categoria: {categoria} \n= > Descricao: {descricao}')

print ('\n====================================================')
print ('============= MEDIAS DE MOVIMENTAÇÕES ==============')
print ('====================================================\n')

media_receitas = calcular_media(receita, qtd_receitas)
media_despesas = calcular_media(despesa, qtd_despesas)

print(f'Média de Receitas: R$ {media_receitas:.2f}')
print(f'Média de Despesas: R$ {media_despesas:.2f}')

print ('\n=================================================================')
print ('============= PERCENTUAIS DE DESPESAS POR CATEGORIA =============')
print ('=================================================================\n')
for categoria in despesas_categorias:
    resultado = calcular_percentual(despesas_categorias[categoria], despesa)
    percentuais_categorias[categoria] = resultado    
    print(f"= > {categoria: <15} | R$ {despesas_categorias[categoria]:10.2f} | {percentuais_categorias[categoria]:10.2f} %")

print ('\n=================================================================')
print ('============= PERCENTUAIS DE RECEITAS POR CATEGORIA =============')
print ('=================================================================\n')
for categoria in receitas_categorias:
    resultado = calcular_percentual(receitas_categorias[categoria], receita)
    percentuais_receitas[categoria] = resultado    
    print(f"= > {categoria: <15} | R$ {receitas_categorias[categoria]:10.2f} | {percentuais_receitas[categoria]:10.2f} %")

print ('\n=================================================================')
print ('============== ANÁLISE DE CONCENTRAÇÃO DAS DESPESAS =============')
print ('=================================================================\n')
for categoria in percentuais_categorias:
    percentual = percentuais_categorias[categoria]
    concentracao = analisar_concentracao(percentual, limite_percentual)

    if concentracao:
        print(f'Categoria: {categoria:<15} | Percentual: {percentual:15.2f} % | alta concentracao')
    else:
        print(f'Categoria: {categoria:<15} | Percentual: {percentual:15.2f} % | baixa concentracao')

print ('\n====================================================')
print ('============= DESPESAS POR CATEGORIA ===============')
print ('====================================================\n')
mostrar_categorias(despesas_categorias)

print ('\n====================================================')
print ('========= CATEGORIA COM MAIOR DESPESA ==============')
print ('====================================================\n')
categoria_maior_despesa, maior_despesas_categorias = maior_categoria(despesas_categorias)
print(f"= > Categoria com maior despesa: {categoria_maior_despesa}")
print(f"= > Valor da maior despesa: R$ {maior_despesas_categorias:.2f}")

print ('\n====================================================')
print ('============== RECEITAS POR CATEGORIA ==============')
print ('====================================================\n')
mostrar_categorias(receitas_categorias)

print ('\n====================================================')
print ('========= CATEGORIA COM MAIOR RECEITA ==============')
print ('====================================================\n')
categoria_maior_receita, maior_receitas_categorias = maior_categoria(receitas_categorias)
print(f"= > Categoria com maior receita: {categoria_maior_receita}")
print(f"= > Valor da maior receita: R$ {maior_receitas_categorias:.2f}")

print ('\n=======================================================')
print ('================= RANKING DE DESPESAS =================')
print ('=======================================================\n')
ranking_despesas = sorted(despesas_categorias.items(), key=lambda item: item[1], reverse=True)

for posicao, item in enumerate(ranking_despesas, 1):
    categoria, valor = item

    print(f'{posicao}º | Categoria: {categoria: <15} | Valor: R$ {valor: 10.2f} | Percentual: {percentuais_categorias[categoria]: 10.2f} %')

print ('\n====================================================\n')
