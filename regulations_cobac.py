"""
Règlementation COBAC/CEMAC pour la gestion du risque de crédit
Références: R-2015/01 à R-2015/12
"""

REGLEMENTATION_COBAC = {
    # R-2015/03 - Ratio de solvabilité
    'ratio_solvabilite': {
        'minimum': 0.08,
        'cible': 0.10,
        'reference': 'R-2015/03 Art. 4',
        'calcul': 'Fonds propres / Actifs pondérés des risques'
    },
    
    # R-2015/04 - Risque de crédit et provisionnement
    'classification_creances': {
        'standard': {
            'provision': 0.0,
            'seuil_score': 60,
            'description': 'Dossier de bonne qualité, faible risque'
        },
        'suivi_special': {
            'provision': 0.2,
            'seuil_score': 50,
            'description': 'Signaux d\'alerte, surveillance renforcée'
        },
        'douteux': {
            'provision': 0.5, 
            'seuil_score': 40,
            'description': 'Difficultés avérées, risque élevé'
        },
        'contentieux': {
            'provision': 1.0,
            'seuil_score': 30,
            'description': 'Défaut de paiement, recouvrement nécessaire'
        },
        'reference': 'R-2015/04 Art. 8-12'
    },
    
    # R-2015/04 - Concentration des risques
    'concentration_risques': {
        'max_client_unique': 0.25,  # 25% des fonds propres
        'max_groupe': 0.50,         # 50% des fonds propres
        'reference': 'R-2015/04 Art. 15',
        'penalite_depassement': 0.5  # Majoration de 50% des fonds propres requis
    },
    
    # R-2015/06 - Gestion des risques
    'seuils_alertes': {
        'rentabilite_min': 3.0,     # 3% minimum
        'endettement_max': 2.0,     # 200% maximum
        'liquidite_min': 1.0,       # Ratio de liquidité ≥ 1
        'autonomie_min': 20.0,      # 20% minimum
        'reference': 'R-2015/06 Annexe'
    },
    
    # R-2015/08 - Liquidité
    'ratios_liquidite': {
        'immediate_min': 0.8,       # 80% minimum
        'generale_min': 1.0,        # 100% minimum
        'reference': 'R-2015/08 Art. 5'
    }
}

def get_cobac_requirements():
    """Retourne les exigences réglementaires COBAC"""
    return {
        'scoring_obligatoire': True,
        'provisionnement_obligatoire': True,
        'classification_obligatoire': True,
        'reporting_trimestriel': True,
        'seuil_intervention': 0.7  # Seuil d'intervention à 70% de probabilité de défaut
    }

def get_provision_taux(categorie):
    """Retourne le taux de provision selon la catégorie COBAC"""
    categories = REGLEMENTATION_COBAC['classification_creances']
    return categories.get(categorie, {}).get('provision', 1.0)

def check_seuils_conformite(ratios):
    """Vérifie la conformité aux seuils COBAC"""
    seuils = REGLEMENTATION_COBAC['seuils_alertes']
    conformite = {}
    
    rentabilite = float(ratios.get('rentabilite_nette', '0%').replace('%', ''))
    conformite['rentabilite'] = rentabilite >= seuils['rentabilite_min']
    
    endettement = float(ratios.get('ratio_endettement', 0))
    conformite['endettement'] = endettement <= seuils['endettement_max']
    
    liquidite = float(ratios.get('ratio_liquidite', 0))
    conformite['liquidite'] = liquidite >= seuils['liquidite_min']
    
    autonomie = float(ratios.get('ratio_autonomie', '0%').replace('%', ''))
    conformite['autonomie'] = autonomie >= seuils['autonomie_min']
    
    conformite['global'] = all(conformite.values())
    
    return conformite