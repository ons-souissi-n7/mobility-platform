from .moveon_transformer import (
    TransformedAgreement,
    TransformedAgreementQuota,
    TransformedMobilityCategory,
)


class ValidationError(ValueError):
    pass


def validate_mobility_category(category: TransformedMobilityCategory) -> None:
    if not category.moveon_id:
        raise ValidationError(
            "Identifiant MoveON du cadre manquant — impossible d'importer sans identifiant unique. "
            "Vérifiez que le champ 'moveon_framework_id' est bien présent dans la réponse MoveON."
        )
    if not category.name:
        raise ValidationError(
            "Nom du cadre de mobilité manquant — champ obligatoire. "
            "Vérifiez que le champ 'name' est renseigné dans MoveON."
        )


def validate_agreement(agreement: TransformedAgreement) -> None:
    if not agreement.moveon_id:
        raise ValidationError(
            "Identifiant MoveON de l'accord manquant — impossible d'importer sans identifiant unique. "
            "Vérifiez que le champ 'moveon_id' ou 'relation_id' est présent dans la réponse MoveON."
        )
    if not agreement.name:
        raise ValidationError(
            "Nom de l'accord manquant — champ obligatoire. "
            "Renseignez le nom de l'accord dans MoveON avant de relancer la synchronisation."
        )
    if not any(
        [
            agreement.partner_university_moveon_id,
            agreement.partner_university_id,
            agreement.partner_university_erasmus_code,
            agreement.partner_university_name,
        ]
    ):
        raise ValidationError(
            "Référence de l'université partenaire manquante — aucun identifiant MoveON, "
            "code Erasmus ou nom d'université trouvé dans le payload. "
            "Cliquez sur « Corriger » pour lier cet accord à une université existante du référentiel."
        )
    if (
        agreement.start_date
        and agreement.end_date
        and agreement.start_date > agreement.end_date
    ):
        raise ValidationError(
            f"Date de début ({agreement.start_date}) postérieure à la date de fin ({agreement.end_date}) — "
            "veuillez corriger les dates de validité de l'accord dans MoveON."
        )


def validate_agreement_quota(quota: TransformedAgreementQuota) -> None:
    if not quota.moveon_id and not quota.agreement_id:
        raise ValidationError(
            "Identifiant de quota MoveON manquant — impossible de rattacher ce quota à un accord."
        )
    if not quota.academic_year_label:
        raise ValidationError(
            "Année académique du quota manquante — champ obligatoire pour l'affectation temporelle."
        )
    if quota.total_places < 0:
        raise ValidationError(
            f"Nombre de places total invalide ({quota.total_places}) — la valeur ne peut pas être négative."
        )
    if quota.remaining_places < 0:
        raise ValidationError(
            f"Nombre de places restantes invalide ({quota.remaining_places}) — la valeur ne peut pas être négative."
        )
    if quota.remaining_places > quota.total_places:
        raise ValidationError(
            f"Incohérence des places : places restantes ({quota.remaining_places}) "
            f"supérieures au total ({quota.total_places})."
        )
    if quota.total_duration is not None and quota.total_duration < 0:
        raise ValidationError(
            f"Durée totale invalide ({quota.total_duration}) — la valeur ne peut pas être négative."
        )
