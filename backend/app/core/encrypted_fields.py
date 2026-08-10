"""
Custom Django field that encrypts values at rest using PostgreSQL pgcrypto
(pgp_sym_encrypt / pgp_sym_decrypt with a symmetric passphrase key).

The key is never stored in code — it is read from settings.PGCRYPTO_KEY,
which must be set via the PGCRYPTO_KEY environment variable.

Prerequisites:
  - PostgreSQL extension pgcrypto enabled (see migration 0018_enable_pgcrypto)
  - settings.PGCRYPTO_KEY non-vide
"""

from django.conf import settings
from django.db import models


def _key() -> str:
    return settings.PGCRYPTO_KEY


class PgEncryptedTextField(models.BinaryField):
    """
    TextField chiffré en base via pgcrypto (pgp_sym_encrypt / pgp_sym_decrypt).
    Stocké en bytea ; déchiffré de manière transparente à la lecture.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("editable", True)
        kwargs.setdefault("blank", True)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs.pop("editable", None)
        return name, "app.core.encrypted_fields.PgEncryptedTextField", args, kwargs

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None if self.null else ""
        raw = bytes(value)
        if not raw:
            return ""
        with connection.cursor() as c:
            c.execute("SELECT pgp_sym_decrypt(%s::bytea, %s)", [raw, _key()])
            row = c.fetchone()
        return (row[0] if row else None) or ""

    def to_python(self, value):
        if isinstance(value, bytes | memoryview):
            return value
        return value or ""

    def get_db_prep_save(self, value, connection):
        if value is None or value == "":
            return None
        with connection.cursor() as c:
            c.execute("SELECT pgp_sym_encrypt(%s, %s)", [str(value), _key()])
            return c.fetchone()[0]
