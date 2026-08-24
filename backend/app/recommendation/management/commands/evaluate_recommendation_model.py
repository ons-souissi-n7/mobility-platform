from collections import Counter

import numpy as np
from django.core.management.base import BaseCommand
from sklearn.model_selection import StratifiedKFold, cross_validate

from app.recommendation.services.dataset import build_training_dataset
from app.recommendation.services.model import MIN_AUC, MIN_OBSERVATIONS, _build_pipeline

_METRICS = ["roc_auc", "accuracy", "precision", "recall", "f1"]


class Command(BaseCommand):
    help = (
        "Evalue hors-ligne la qualite predictive du modele de recommandation "
        "(validation croisee stratifiee) sans impacter le chemin d'entrainement "
        "live, qui continue de s'entrainer sur 100% des donnees a chaque requete."
    )

    def handle(self, *args, **options):
        rows, targets = build_training_dataset()
        class_counts = Counter(targets)

        self.stdout.write(f"Observations : {len(rows)}")
        self.stdout.write(f"Repartition classes : {dict(class_counts)}")

        if len(rows) < MIN_OBSERVATIONS or len(class_counts) < 2:
            self.stdout.write(
                self.style.WARNING(
                    "Donnees insuffisantes pour entrainer ou evaluer le modele "
                    "(fallback GPA utilise en production)."
                )
            )
            return

        n_splits = min(5, min(class_counts.values()))
        if n_splits < 2:
            self.stdout.write(
                self.style.WARNING(
                    "Classe minoritaire trop petite pour une validation croisee "
                    "fiable (fallback GPA utilise en production)."
                )
            )
            return

        x = np.array(rows, dtype=object)
        y = np.array(targets)
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        results = cross_validate(_build_pipeline(), x, y, cv=cv, scoring=_METRICS)

        self.stdout.write(f"Folds : {n_splits}")
        for metric in _METRICS:
            scores = results[f"test_{metric}"]
            self.stdout.write(
                f"{metric:>10s} : {scores.mean():.3f} (+/- {scores.std():.3f})"
            )

        auc_mean = results["test_roc_auc"].mean()
        if auc_mean < MIN_AUC:
            self.stdout.write(
                self.style.ERROR(
                    f"AUC moyen ({auc_mean:.3f}) sous le seuil MIN_AUC={MIN_AUC} : "
                    "le modele live basculerait sur le fallback GPA."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"AUC moyen ({auc_mean:.3f}) au-dessus du seuil "
                    f"MIN_AUC={MIN_AUC}."
                )
            )
