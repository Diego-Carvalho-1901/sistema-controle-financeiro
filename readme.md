# Sistema de Controle Financeiro

## Sobre o projeto
Este projeto consiste em um sistema de controle financeiro desenvolvido em Python, capaz de ler e processar movimentações financeiras armazenadas em um arquivo CSV. A aplicação realiza o cálculo de receitas, despesas e saldo, além de gerar análises por categoria e por período. O projeto foi desenvolvido com foco na prática de manipulação de dados, criação de funções, tratamento de erros e organização de informações financeiras.

## Funcionalidades
Leitura de movimentações financeiras através de arquivo CSV;
Cálculo do total de receitas e despesas;
Cálculo do saldo financeiro;
Análise de receitas e despesas por categoria;
Cálculo de percentuais por categoria;
Identificação das maiores e menores movimentações;
Cálculo de médias financeiras;
Análise de concentração de despesas;
Ranking de despesas por categoria;
Histórico cronológico das movimentações;
Análise financeira por mês;
Tratamento de erros relacionados aos dados e ao arquivo CSV.

## Tecnologias utilizadas
- Python
- CSV
- Git e GitHub
- Visual Studio Code

## Estrutura do projeto
```text
sistema_controle_financeiro/
├── dados/
│   └── movimentacoes.csv
├── main.py
└── README.md

```
## Como executar
```markdown

1. Clone este repositório.
2. Abra a pasta do projeto no Visual Studio Code.
3. Certifique-se de que o arquivo `dados/movimentacoes.csv` está presente.
4. Execute o arquivo `main.py` através do terminal:

```bash
```

## Exemplo de execução
```text
====================================================
================ ANALISE FINANCEIRA ================
====================================================

Total de Receitas: R$ 10150.00
Total de Despesas: R$ 4522.50
Saldo: R$ 5627.50

 >>> ANALISE PERCENTUAL DE RECEITA COMPROMETIDA E RECEITA DISPONIVEL <<< 

Receita Comprometida: 44.56 %
Receita Disponível: 55.44 %

====================================================
================== ANALISE MENSAL ==================
====================================================


Mês: August
Valor de receita: R$ 2350.00
Valor de despesa: R$ 1085.40
Valor do saldo: R$ 1264.60

Mês: September
Valor de receita: R$ 2950.00
Valor de despesa: R$ 1236.30
Valor do saldo: R$ 1713.70

Mês: October
Valor de receita: R$ 2700.00
Valor de despesa: R$ 945.90
Valor do saldo: R$ 1754.10

Mês: November
Valor de receita: R$ 2150.00
Valor de despesa: R$ 1254.90
Valor do saldo: R$ 895.10

====================================================
=========== HISTÓRICO DE MOVIMENTAÇÕES =============
====================================================

data: 05/08/2026 | valor:     300.00 | Tipo: receita    | Categoria: freelance       | Descricao: Servico de programacao
data: 10/08/2026 | valor:      85.50 | Tipo: despesa    | Categoria: alimentacao     | Descricao: Supermercado   
data: 16/08/2026 | valor:    1800.00 | Tipo: receita    | Categoria: salario         | Descricao: Salario mensal 
data: 17/08/2026 | valor:     120.00 | Tipo: despesa    | Categoria: transporte      | Descricao: Combustivel    
data: 18/08/2026 | valor:     320.00 | Tipo: despesa    | Categoria: alimentacao     | Descricao: Compras do supermercado
data: 20/08/2026 | valor:     150.00 | Tipo: despesa    | Categoria: transporte      | Descricao: Combustivel    
data: 22/08/2026 | valor:     250.00 | Tipo: receita    | Categoria: freelance       | Descricao: Servico de programacao
data: 25/08/2026 | valor:      89.90 | Tipo: despesa    | Categoria: assinaturas     | Descricao: Internet       
data: 26/08/2026 | valor:     200.00 | Tipo: despesa    | Categoria: lazer           | Descricao: Restaurante    
data: 28/08/2026 | valor:     120.00 | Tipo: despesa    | Categoria: lazer           | Descricao: Restaurante    
data: 01/09/2026 | valor:    1800.00 | Tipo: receita    | Categoria: salario         | Descricao: Salario mensal 
data: 02/09/2026 | valor:      45.90 | Tipo: despesa    | Categoria: alimentacao     | Descricao: Almoco         
data: 03/09/2026 | valor:     120.00 | Tipo: despesa    | Categoria: lazer           | Descricao: Cinema e alimentacao
data: 04/09/2026 | valor:     200.00 | Tipo: despesa    | Categoria: transporte      | Descricao: Combustivel    
data: 05/09/2026 | valor:     350.00 | Tipo: receita    | Categoria: freelance       | Descricao: Servico de desenvolvimento
data: 06/09/2026 | valor:      89.90 | Tipo: despesa    | Categoria: assinaturas     | Descricao: Internet       
data: 07/09/2026 | valor:      75.50 | Tipo: despesa    | Categoria: alimentacao     | Descricao: Supermercado   
data: 08/09/2026 | valor:     150.00 | Tipo: despesa    | Categoria: educacao        | Descricao: Curso online   
data: 09/09/2026 | valor:     300.00 | Tipo: receita    | Categoria: freelance       | Descricao: Projeto de programacao
data: 10/09/2026 | valor:      60.00 | Tipo: despesa    | Categoria: lazer           | Descricao: Saida com amigos
data: 11/09/2026 | valor:     110.00 | Tipo: despesa    | Categoria: transporte      | Descricao: Manutencao do carro
data: 12/09/2026 | valor:     250.00 | Tipo: despesa    | Categoria: alimentacao     | Descricao: Compras do mes 
data: 13/09/2026 | valor:     500.00 | Tipo: receita    | Categoria: outros          | Descricao: Venda de equipamento usado
data: 14/09/2026 | valor:      35.00 | Tipo: despesa    | Categoria: saude           | Descricao: Farmacia       
data: 15/09/2026 | valor:     100.00 | Tipo: despesa    | Categoria: educacao        | Descricao: Livros         
data: 02/10/2026 | valor:    1800.00 | Tipo: receita    | Categoria: salario         | Descricao: Salario mensal 
data: 04/10/2026 | valor:     500.00 | Tipo: receita    | Categoria: freelance       | Descricao: Projeto de programacao
data: 05/10/2026 | valor:     200.00 | Tipo: despesa    | Categoria: alimentacao     | Descricao: Supermercado   
data: 08/10/2026 | valor:     180.00 | Tipo: despesa    | Categoria: transporte      | Descricao: Combustivel    
data: 09/10/2026 | valor:      75.90 | Tipo: despesa    | Categoria: alimentacao     | Descricao: Supermercado   
data: 12/10/2026 | valor:     400.00 | Tipo: receita    | Categoria: freelance       | Descricao: Projeto de programacao
data: 15/10/2026 | valor:      90.00 | Tipo: despesa    | Categoria: assinaturas     | Descricao: Internet       
data: 18/10/2026 | valor:     150.00 | Tipo: despesa    | Categoria: transporte      | Descricao: Combustivel    
data: 20/10/2026 | valor:     150.00 | Tipo: despesa    | Categoria: lazer           | Descricao: Cinema e jantar
data: 27/10/2026 | valor:     100.00 | Tipo: despesa    | Categoria: educacao        | Descricao: Livro tecnico  
data: 03/11/2026 | valor:    1800.00 | Tipo: receita    | Categoria: salario         | Descricao: Salario mensal 
data: 06/11/2026 | valor:     350.00 | Tipo: receita    | Categoria: freelance       | Descricao: Servico de desenvolvimento
data: 07/11/2026 | valor:     350.00 | Tipo: despesa    | Categoria: educacao        | Descricao: Curso online   
data: 08/11/2026 | valor:      95.00 | Tipo: despesa    | Categoria: alimentacao     | Descricao: Supermercado   
data: 12/11/2026 | valor:     180.00 | Tipo: despesa    | Categoria: transporte      | Descricao: Combustivel    
data: 15/11/2026 | valor:     220.00 | Tipo: despesa    | Categoria: alimentacao     | Descricao: Compras do mes 
data: 16/11/2026 | valor:     120.00 | Tipo: despesa    | Categoria: lazer           | Descricao: Cinema         
data: 20/11/2026 | valor:     200.00 | Tipo: despesa    | Categoria: educacao        | Descricao: Curso online   
data: 25/11/2026 | valor:      89.90 | Tipo: despesa    | Categoria: assinaturas     | Descricao: Internet       

===============================================
============= MAIOR MOVIMENTAÇÃO ==============
===============================================

= > Data: 01/09/2026 
= > Valor: R$ 1800.00 
= > Tipo: receita 
= > Categoria: salario 
= > Descricao: Salario mensal

===============================================
============= MENOR MOVIMENTAÇÃO ==============
===============================================

= > Data: 14/09/2026 
= > Valor: R$ 35.00 
= > Tipo: despesa 
= > Categoria: saude 
= > Descricao: Farmacia

====================================================
============= MEDIAS DE MOVIMENTAÇÕES ==============
====================================================

Média de Receitas: R$ 845.83
Média de Despesas: R$ 141.33

=================================================================
============= PERCENTUAIS DE DESPESAS POR CATEGORIA =============
=================================================================

= > alimentacao     | R$    1367.80 |      30.24 %
= > lazer           | R$     770.00 |      17.03 %
= > transporte      | R$    1090.00 |      24.10 %
= > assinaturas     | R$     359.70 |       7.95 %
= > educacao        | R$     900.00 |      19.90 %
= > saude           | R$      35.00 |       0.77 %

=================================================================
============= PERCENTUAIS DE RECEITAS POR CATEGORIA =============
=================================================================

= > salario         | R$    7200.00 |      70.94 %
= > freelance       | R$    2450.00 |      24.14 %
= > outros          | R$     500.00 |       4.93 %

=================================================================
============== ANÁLISE DE CONCENTRAÇÃO DAS DESPESAS =============
=================================================================

Categoria: alimentacao     | Percentual:           30.24 % | alta concentracao
Categoria: lazer           | Percentual:           17.03 % | baixa concentracao
Categoria: transporte      | Percentual:           24.10 % | alta concentracao
Categoria: assinaturas     | Percentual:            7.95 % | baixa concentracao
Categoria: educacao        | Percentual:           19.90 % | baixa concentracao
Categoria: saude           | Percentual:            0.77 % | baixa concentracao

====================================================
============= DESPESAS POR CATEGORIA ===============
====================================================

= > alimentacao : R$ 1367.80
= > lazer : R$ 770.00
= > transporte : R$ 1090.00
= > assinaturas : R$ 359.70
= > educacao : R$ 900.00
= > saude : R$ 35.00

====================================================
========= CATEGORIA COM MAIOR DESPESA ==============
====================================================

= > Categoria com maior despesa: alimentacao
= > Valor da maior despesa: R$ 1367.80

====================================================
============== RECEITAS POR CATEGORIA ==============
====================================================

= > salario : R$ 7200.00
= > freelance : R$ 2450.00
= > outros : R$ 500.00

====================================================
========= CATEGORIA COM MAIOR RECEITA ==============
====================================================

= > Categoria com maior receita: salario
= > Valor da maior receita: R$ 7200.00

=======================================================
================= RANKING DE DESPESAS =================
=======================================================

1º | Categoria: alimentacao     | Valor: R$    1367.80 | Percentual:      30.24 %
2º | Categoria: transporte      | Valor: R$    1090.00 | Percentual:      24.10 %
3º | Categoria: educacao        | Valor: R$     900.00 | Percentual:      19.90 %
4º | Categoria: lazer           | Valor: R$     770.00 | Percentual:      17.03 %
5º | Categoria: assinaturas     | Valor: R$     359.70 | Percentual:       7.95 %
6º | Categoria: saude           | Valor: R$      35.00 | Percentual:       0.77 %

====================================================

```

## Análises realizadas

A partir das movimentações registradas no arquivo CSV, o sistema gera um relatório financeiro contendo:

- Total de receitas e despesas;
- Saldo financeiro;
- Distribuição das despesas por categoria;
- Percentual de participação de cada categoria;
- Maior e menor movimentação registrada;
- Média dos valores movimentados;
- Ranking das categorias com maiores despesas;
- Histórico completo das movimentações em ordem cronológica;
- Comparação mensal entre receitas, despesas e saldo;
- Identificação de categorias com maior concentração de despesas.

## Tratamento e validação de dados

O sistema possui validações para evitar que informações inválidas interrompam o processamento de forma inesperada.

São tratados casos como:

- Arquivo CSV não encontrado;
- Valores financeiros inválidos;
- Datas em formato incorreto;
- Tipos de movimentação inválidos.

Quando um desses problemas é identificado, o sistema informa o erro ao usuário e encerra a execução de forma controlada.

## Conceitos praticados

Durante o desenvolvimento, foram aplicados conceitos importantes de Python, como:

- Manipulação de arquivos CSV;
- Listas, dicionários e tuplas;
- Funções e reutilização de código;
- Estruturas condicionais e de repetição;
- Conversão e validação de dados;
- Manipulação de datas com `datetime`;
- Ordenação de dados;
- Uso de `sorted()` e `lambda`;
- Cálculos e agregações de dados;
- Tratamento de exceções com `try/except`;
- Organização e refatoração de código.

## Objetivo do projeto

O objetivo deste projeto foi transformar um conjunto de movimentações financeiras armazenadas em CSV em informações organizadas e úteis para análise.

Além de praticar fundamentos de Python, o projeto foi desenvolvido pensando em uma aplicação próxima de problemas de manipulação e análise de dados, servindo como uma etapa da minha evolução em programação e na área de dados.

## Próximos passos

Este projeto faz parte de uma sequência de projetos com níveis progressivos de complexidade.

A ideia é evoluir gradualmente a forma de trabalhar com dados, passando por diferentes fontes, ferramentas e técnicas de processamento, até chegar a projetos mais próximos de aplicações utilizadas em ambientes profissionais.