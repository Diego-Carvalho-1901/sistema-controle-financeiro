"""Datas de início e fim de períodos usados nos resumos e nas metas."""

import calendar
from datetime import date, timedelta


def mes_de(dia: date) -> tuple[date, date]:
    """Primeiro e último dia do mês de `dia`."""
    ultimo = calendar.monthrange(dia.year, dia.month)[1]
    return dia.replace(day=1), dia.replace(day=ultimo)


def semana_de(dia: date) -> tuple[date, date]:
    """Segunda-feira e domingo da semana de `dia`."""
    segunda = dia - timedelta(days=dia.weekday())
    return segunda, segunda + timedelta(days=6)
