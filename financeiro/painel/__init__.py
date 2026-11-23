"""Painel web (issue [19]): gráficos do mês no navegador.

O login não tem senha: a pessoa manda /painel para o bot e recebe um link
que vale por 10 minutos. Abrir o link cria uma sessão num cookie assinado.
O navegador só desenha: todos os números vêm prontos da API.
"""
