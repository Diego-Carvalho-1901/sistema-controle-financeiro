"""Persistência: tabelas, conexão e repositório de lançamentos.

Os cálculos (financeiro/calculos.py) não sabem que o banco existe: eles
continuam recebendo objetos Lancamento. Quem traduz entre as linhas do
banco e esses objetos é o repositório (financeiro/banco/repositorio.py).
"""
