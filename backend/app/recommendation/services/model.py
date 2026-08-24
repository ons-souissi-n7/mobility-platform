"""
Entraînement et scoring du moteur de recommandation (régression logistique,
cf. chapitre 4 du rapport). Entraîné à la volée à chaque appel — aucune
persistance : le volume de données (quelques milliers de vœux au plus) rend
le ré-entraînement systématique instantané, ce qui évite tout risque de
modèle figé sur des données périmées.
"""

from collections import Counter

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.recommendation.services.dataset import build_training_dataset

# En dessous de ce nombre d'observations (ou s'il manque une des deux classes
# affecté/non-affecté), le modèle n'est pas fiable : on retombe sur le GPA
# seul (cf. "risque de démarrage à froid", chapitre 4).
MIN_OBSERVATIONS = 30

# AUC minimal (validation croisée) en dessous duquel le modèle n'est pas
# significativement meilleur qu'un tirage aléatoire (0.5) : on retombe sur
# le fallback GPA plutôt que de servir un classement peu fiable.
MIN_AUC = 0.65

_CV_FOLDS = 5

# Colonnes de la matrice de features :
# [gpa, department_code, historical_rate, is_french]
_NUMERIC_COLUMNS = [0, 2, 3]
_CATEGORICAL_COLUMNS = [1]


def _build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        [
            ("num", StandardScaler(), _NUMERIC_COLUMNS),
            ("dept", OneHotEncoder(handle_unknown="ignore"), _CATEGORICAL_COLUMNS),
        ]
    )
    return Pipeline([("preprocess", preprocessor), ("clf", LogisticRegression())])


def train_model(rates: dict[int, float] | None = None) -> Pipeline | None:
    """`rates` peut être fourni par l'appelant pour éviter de recalculer les
    taux historiques une deuxième fois (déjà fait pour le scoring).

    Avant d'entraîner le modèle final (sur 100% des données, à chaque appel —
    aucune persistance), une validation croisée stratifiée estime son AUC sur
    les données du moment. Si l'AUC est sous MIN_AUC, ou si une classe est
    trop petite pour un k-fold fiable, on retombe sur le fallback GPA plutôt
    que de servir un modèle dont la capacité prédictive n'est pas démontrée
    (cf. `evaluate_recommendation_model` pour l'évaluation détaillée hors-ligne).
    """
    rows, targets = build_training_dataset(rates)
    if len(rows) < MIN_OBSERVATIONS or len(set(targets)) < 2:
        return None

    x = np.array(rows, dtype=object)
    y = np.array(targets)

    min_class_count = min(Counter(targets).values())
    n_splits = min(_CV_FOLDS, min_class_count)
    if n_splits < 2:
        return None

    pipeline = _build_pipeline()
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    auc_scores = cross_val_score(pipeline, x, y, cv=cv, scoring="roc_auc")
    if auc_scores.mean() < MIN_AUC:
        return None

    pipeline.fit(x, y)
    return pipeline


def score_destinations(
    gpa: float | None,
    department_code: str,
    agreement_ids: list[int],
    pipeline: Pipeline | None,
    rates: dict[int, float],
    is_french: bool = False,
) -> list[float | None]:
    """Retourne un score par agreement_id, dans l'ordre fourni.

    Sans modèle entraîné (démarrage à froid), retourne None pour chaque
    entrée : ce n'est pas une probabilité, l'appelant doit alors classer
    autrement (GPA seul, cf. chapitre 4)."""
    if pipeline is None:
        return [None] * len(agreement_ids)

    gpa_value = float(gpa) if gpa is not None else 0.0
    is_french_value = 1 if is_french else 0
    x = np.array(
        [
            [gpa_value, department_code, rates.get(aid, 0.0), is_french_value]
            for aid in agreement_ids
        ],
        dtype=object,
    )
    # classes_ triées par ordre croissant par LogisticRegression (garanti par
    # sklearn) : la cible étant binaire {0, 1}, la colonne 1 est P(affecté=1).
    probabilities = pipeline.predict_proba(x)
    return [float(p) for p in probabilities[:, 1]]
