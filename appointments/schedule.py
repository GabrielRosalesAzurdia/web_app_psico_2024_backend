"""Esquema de horario compartido por Appointment y Activity.

La jornada se divide en bloques de 40 minutos desde las 08:00 hasta las
12:40. Ademas de esos bloques fijos, se admite "hora libre": el usuario
escribe cualquier hora a mano en el TimeField y deja `time_block` vacio.
"""
from datetime import date as date_cls, datetime, time, timedelta

from django.db import models
from django.utils.translation import gettext_lazy as _

BLOCK_MINUTES = 40

# La jornada de atencion: primer bloque inicia 08:00, el ultimo (12:40)
# termina 13:20. Toda hora (bloque u hora libre) debe caer en este rango.
DAY_START = time(8, 0)
DAY_END = time(13, 20)


class TimeBlock(models.TextChoices):
    B_0800 = '08:00', '08:00 - 08:40'
    B_0840 = '08:40', '08:40 - 09:20'
    B_0920 = '09:20', '09:20 - 10:00'
    B_1000 = '10:00', '10:00 - 10:40'
    B_1040 = '10:40', '10:40 - 11:20'
    B_1120 = '11:20', '11:20 - 12:00'
    B_1200 = '12:00', '12:00 - 12:40'
    B_1240 = '12:40', '12:40 - 13:20'


# Hora de inicio (datetime.time) por cada valor de bloque.
BLOCK_START = {
    choice.value: time(*map(int, choice.value.split(':')))
    for choice in TimeBlock
}


def block_to_time(value):
    """Devuelve la hora de inicio de un bloque, o None si viene vacio
    (hora libre)."""
    if not value:
        return None
    return BLOCK_START[value]


def block_end(value):
    """Hora de fin del bloque (inicio + 40 min)."""
    start = BLOCK_START[value]
    return (datetime.combine(date_cls.min, start)
            + timedelta(minutes=BLOCK_MINUTES)).time()


def in_working_day(hour):
    return DAY_START <= hour <= DAY_END


class ScheduleError(ValueError):
    """Error de validacion de horario; el campo afectado va en `field`."""

    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(message)


def resolve_hour(time_block, hour):
    """Normaliza (time_block, hour) para una cita.

    - Con bloque: la hora se deriva del bloque; si ademas mandan `hour`
      y no coincide, es un error.
    - Sin bloque (hora libre): `hour` es obligatoria.
    En ambos casos la hora debe caer dentro de la jornada.
    Devuelve la hora final (datetime.time).
    """
    if time_block:
        block_hour = BLOCK_START[time_block]
        if hour is not None and hour != block_hour:
            raise ScheduleError(
                'hour',
                f'La hora {hour:%H:%M} no coincide con el bloque '
                f'seleccionado ({block_hour:%H:%M}). Deje la hora vacia '
                f'o mande la del bloque.',
            )
        return block_hour

    if hour is None:
        raise ScheduleError('hour', 'Indique un bloque o una hora libre.')
    if not in_working_day(hour):
        raise ScheduleError(
            'hour',
            f'La hora debe estar entre {DAY_START:%H:%M} y {DAY_END:%H:%M}.',
        )
    return hour


def resolve_activity_hours(time_block, start_hour, end_hour):
    """Igual que resolve_hour pero para actividades (inicio + fin).

    Con bloque: start = inicio del bloque, end = fin del bloque.
    Sin bloque: se exigen ambas, dentro de la jornada y end > start.
    Devuelve (start_hour, end_hour).
    """
    if time_block:
        return BLOCK_START[time_block], block_end(time_block)

    if start_hour is None:
        raise ScheduleError('start_hour', 'Indique un bloque o una hora de inicio.')
    if end_hour is None:
        raise ScheduleError('end_hour', 'La hora de fin es obligatoria.')
    if end_hour <= start_hour:
        raise ScheduleError(
            'end_hour', 'La hora de fin debe ser posterior a la hora de inicio.'
        )
    for field, value in (('start_hour', start_hour), ('end_hour', end_hour)):
        if not in_working_day(value):
            raise ScheduleError(
                field,
                f'El horario debe estar entre {DAY_START:%H:%M} y {DAY_END:%H:%M}.',
            )
    return start_hour, end_hour
