"""
Custom Django field that encrypts values at rest using PostgreSQL pgcrypto
(pgp_sym_encrypt / pgp_sym_decrypt with a symmetric passphrase key).

The key is never stored in code — it is read from settings.PGCRYPTO_KEY,
which must be set via the PGCRYPTO_KEY environment variable.

Prerequisites:
  - PostgreSQL extension pgcrypto enabled (see migration 0018_enable_pgcrypto)
  - settings.PGCRYPTO_KEY non-vide

Lecture : déchiffrée en ligne dans la requête SELECT elle-même via get_col()
(pgp_sym_decrypt(colonne, clé) inséré directement dans le SQL généré par
l'ORM), et non via une requête séparée par valeur. Avant ce correctif,
from_db_value() faisait un aller-retour SQL individuel PAR CHAMP PAR LIGNE
(confirmé : 31 requêtes de déchiffrement supplémentaires pour 25 étudiants),
ce qui dominait la latence sous charge concurrente (BNF04). Vérifié qu'aucun
filter()/exclude()/order_by()/annotate()/Q() du projet ne porte sur ces
champs — get_col() n'affecte donc que la liste SELECT, jamais un WHERE
existant. Le chiffrement à l'écriture (get_db_prep_save) garde son aller-
retour séparé : chemin peu fréquent (création/import), hors du chemin chaud
mesuré, et moins sûr à inliner sans tests dédiés supplémentaires.
"""

from django.conf import settings
from django.db import models
from django.db.models.expressions import Col


def _key() -> str:
    return settings.PGCRYPTO_KEY


class _DecryptedCol(Col):
    """
    Col standard, sauf que son SQL est enveloppé en pgp_sym_decrypt(..., clé).
    Garder un vrai sous-classe de Col (plutôt qu'une expression généraliste
    comme Func) est nécessaire : ModelIterable._iter() lit .target.attname
    sur les colonnes du SELECT pour savoir quel attribut d'instance remplir,
    et seul Col porte cet attribut.
    """

    def as_sql(self, compiler, connection):
        sql, params = super().as_sql(compiler, connection)
        return f"pgp_sym_decrypt({sql}::bytea, %s)", [*params, _key()]


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
        name, _path, args, kwargs = super().deconstruct()
        kwargs.pop("editable", None)
        return name, "app.core.encrypted_fields.PgEncryptedTextField", args, kwargs

    def get_col(self, alias, output_field=None):
        if output_field is None:
            output_field = self
        return _DecryptedCol(alias, self, output_field)

    def from_db_value(self, value, expression, connection):
        # Appelée normalement : get_col() garde ce champ comme target ET
        # output_field du Col, donc get_db_converters() route toujours ici.
        # La valeur reçue est déjà déchiffrée en texte par pgp_sym_decrypt()
        # dans le SQL (via _DecryptedCol.as_sql) — cette méthode ne fait donc
        # plus qu'un passthrough. Le repli bytes bruts n'est qu'un filet de
        # sécurité pour un chemin qui ne devrait plus jamais se produire.
        if value is None:
            return None if self.null else ""
        if isinstance(value, bytes | memoryview):
            raw = bytes(value)
            if not raw:
                return ""
            with connection.cursor() as c:
                c.execute("SELECT pgp_sym_decrypt(%s::bytea, %s)", [raw, _key()])
                row = c.fetchone()
            return (row[0] if row else None) or ""
        return value or ""

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
