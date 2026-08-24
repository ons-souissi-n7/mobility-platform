from app.recommendation.services.model import (
    MIN_OBSERVATIONS,
    score_destinations,
    train_model,
)


class TestScoreDestinationsColdStart:
    def test_returns_none_scores_without_pipeline(self):
        scores = score_destinations(
            gpa=12.0,
            department_code="SN",
            agreement_ids=[1, 2, 3],
            pipeline=None,
            rates={},
        )
        assert scores == [None, None, None]


class TestTrainModel:
    def test_returns_none_below_min_observations(self, monkeypatch):
        monkeypatch.setattr(
            "app.recommendation.services.model.build_training_dataset",
            lambda rates=None: ([[14.0, "SN", 0.5, 0]] * 5, [1, 0, 1, 0, 1]),
        )
        assert train_model() is None

    def test_returns_none_with_a_single_class(self, monkeypatch):
        rows = [[14.0, "SN", 0.5, 0]] * (MIN_OBSERVATIONS + 5)
        targets = [1] * len(rows)
        monkeypatch.setattr(
            "app.recommendation.services.model.build_training_dataset",
            lambda rates=None: (rows, targets),
        )
        assert train_model() is None

    def test_returns_none_when_minority_class_too_small_for_cv(self, monkeypatch):
        """1 seule observation positive : pas assez pour un k-fold stratifié
        fiable (n_splits >= 2 impossible), doit dégrader vers le fallback."""
        rows = [[14.0, "SN", 0.5, 0]] * (MIN_OBSERVATIONS + 5)
        targets = [0] * (len(rows) - 1) + [1]
        monkeypatch.setattr(
            "app.recommendation.services.model.build_training_dataset",
            lambda rates=None: (rows, targets),
        )
        assert train_model() is None

    def test_returns_none_when_auc_below_threshold(self, monkeypatch):
        """Cible qui alterne sans lien avec les features : aucun signal
        apprenable linéairement, l'AUC en validation croisée doit être trop
        faible pour passer le seuil MIN_AUC."""
        rows = [[10.0 + (i % 8), "SN", 0.5, 0] for i in range(MIN_OBSERVATIONS + 10)]
        targets = [i % 2 for i in range(len(rows))]
        monkeypatch.setattr(
            "app.recommendation.services.model.build_training_dataset",
            lambda rates=None: (rows, targets),
        )
        assert train_model() is None

    def test_trains_with_sufficient_mixed_data(self, monkeypatch):
        rows = [
            [
                10.0 + (i % 10),
                "SN" if i % 2 == 0 else "3EA",
                0.3 + (i % 5) / 10,
                1 if i % 2 == 0 else 0,
            ]
            for i in range(MIN_OBSERVATIONS + 10)
        ]
        targets = [1 if i % 2 == 0 else 0 for i in range(len(rows))]
        monkeypatch.setattr(
            "app.recommendation.services.model.build_training_dataset",
            lambda rates=None: (rows, targets),
        )

        pipeline = train_model()
        assert pipeline is not None

        scores = score_destinations(
            gpa=15.0,
            department_code="SN",
            agreement_ids=[1, 2],
            pipeline=pipeline,
            rates={1: 0.6, 2: 0.2},
            is_french=True,
        )
        assert len(scores) == 2
        assert all(0.0 <= s <= 1.0 for s in scores)
