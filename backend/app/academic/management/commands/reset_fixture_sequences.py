from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connection


class Command(BaseCommand):
    """
    Réinitialise les séquences PostgreSQL des apps données.

    `loaddata` insère les lignes des fixtures avec des PK explicites (ex.
    countries.json, agreements.json) — Postgres ne fait avancer une séquence
    que via nextval(), jamais par un INSERT à valeur explicite. Résultat : le
    premier objet créé ensuite par l'ORM/l'API (un accord ajouté par un test
    E2E, une année créée depuis l'interface…) retente la PK 1 et lève une
    IntegrityError.

    Équivalent programmatique de `manage.py sqlsequencereset <apps> | psql`,
    sans dépendre du binaire psql (absent de l'image backend de dev).
    """

    help = (
        "Réinitialise les séquences des apps données après un loaddata à PK explicites."
    )

    def add_arguments(self, parser):
        parser.add_argument("app_labels", nargs="+")

    def handle(self, *_args, **options):
        models = []
        for label in options["app_labels"]:
            try:
                models.extend(apps.get_app_config(label).get_models())
            except LookupError as exc:
                raise CommandError(str(exc)) from exc

        statements = connection.ops.sequence_reset_sql(no_style(), models)
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)

        self.stdout.write(
            self.style.SUCCESS(f"{len(statements)} séquence(s) réinitialisée(s).")
        )
