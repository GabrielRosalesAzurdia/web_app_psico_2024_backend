from enum import Enum


class GroupName(Enum):
    # RNF-02 (B-1): roles del sistema, guardados como grupos de Django.
    # Un usuario puede tener varios (ej. profesional y administrador).
    PROFESSIONAL = 'profesional'
    RECEPTION = 'recepcion'
    ADMINISTRATOR = 'administrador'