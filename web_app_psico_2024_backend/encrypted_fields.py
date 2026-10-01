from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


# RNF-05 (B-2): campos que se guardan cifrados en la BD y se leen
# descifrados en Python. Vistas, serializers y PDFs no cambian: siempre
# reciben el texto normal. Ojo: un campo cifrado no se puede filtrar ni
# ordenar en la BD (el mismo texto se cifra distinto cada vez).
def _fernet():
    return Fernet(settings.FIELD_ENCRYPTION_KEY)


class EncryptedTextField(models.TextField):
    def get_prep_value(self, value):
        # Python -> BD: cifra antes de guardar.
        value = super().get_prep_value(value)
        if value is None:
            return value
        return _fernet().encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        # BD -> Python: descifra al leer.
        if value is None:
            return value
        return _fernet().decrypt(value.encode()).decode()


class EncryptedBinaryField(models.BinaryField):
    # Igual que EncryptedTextField, pero para archivos (bytes). Postgres
    # devuelve un memoryview, por eso se convierte con bytes().
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        return _fernet().encrypt(bytes(value))

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return _fernet().decrypt(bytes(value))
