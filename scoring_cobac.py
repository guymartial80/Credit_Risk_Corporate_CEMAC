# scoring_cobac.py - Version corrigée
"""
Système de scoring conforme COBAC pour l'analyse du risque de crédit
"""

import pandas as pd
from regulations_cobac import REGLEMENTATION_COBAC

class ScoringSystemCOBAC:
    def __init__(self):
        self.categories = {
            'A': {'score_min': 60, 'libelle': 'Excellent - Risque faible', 'couleur': 'green'},
            'B': {'score_min': 50, 'libelle': 'Bon - Risque modéré', 'couleur': 'blue'}, 
            'C': {'score_min': 40, 'libelle': 'Moyen - Risque acceptable', 'couleur': 'orange'},
            'D': {'score_min': 30, 'libelle': 'Médiocre - Risque élevé', 'couleur': 'red'},
            'E': {'score_min': 0, 'libelle': 'Mauvais - Risque très élevé', 'couleur': 'darkred'}
        }
        
        self.poids_criteres = {
            'rentabilite': 0.25,
            'structure': 0.25, 
            'liquidite': 0.20,
            'tresorerie': 0.15,
            'croissance': 0.15
        }
    
    def calculer_score_global(self, sig_results, ratios_results, working_capital_results):
        """Calcule le score global selon méthodologie COBAC"""
        try:
            if not sig_results or not ratios_results or not working_capital_results:
                return self._create_default_score()
            
            dernier_annee = max(sig_results.keys())
            scores = {}
            
            # 1. Rentabilité (25 points)
            scores['rentabilite'] = self._score_rentabilite(ratios_results, dernier_annee)
            
            # 2. Structure financière (25 points)
            scores['structure'] = self._score_structure(ratios_results, dernier_annee)
            
            # 3. Liquidité (20 points)
            scores['liquidite'] = self._score_liquidite(ratios_results, dernier_annee)
            
            # 4. Trésorerie (15 points)
            scores['tresorerie'] = self._score_tresorerie(working_capital_results, dernier_annee)
            
            # 5. Croissance (15 points)
            scores['croissance'] = self._score_croissance(sig_results, ratios_results)
            
            # Score pondéré
            score_total = sum(scores[critere] * poids for critere, poids in self.poids_criteres.items())
            score_total = max(0, min(100, score_total))  # S'assurer que le score est entre 0 et 100
            
            # Détermination catégorie
            categorie = self._determiner_categorie(score_total)
            
            return {
                'score_total': round(score_total, 1),
                'categorie': categorie,
                'libelle_categorie': self.categories[categorie]['libelle'],
                'couleur_categorie': self.categories[categorie]['couleur'],
                'scores_detailles': scores,
                'conformite_cobac': self._verifier_conformite_cobac(ratios_results, dernier_annee)
            }
            
        except Exception as e:
            print(f"Erreur dans calculer_score_global: {e}")
            return self._create_default_score()
    
    def _create_default_score(self):
        """Crée un score par défaut en cas d'erreur"""
        return {
            'score_total': 0,
            'categorie': 'E',
            'libelle_categorie': 'Données insuffisantes',
            'couleur_categorie': 'gray',
            'scores_detailles': {
                'rentabilite': 0,
                'structure': 0,
                'liquidite': 0,
                'tresorerie': 0,
                'croissance': 0
            },
            'conformite_cobac': {
                'rentabilite': False,
                'endettement': False,
                'liquidite': False,
                'autonomie': False,
                'global': False
            }
        }
    
    def _score_rentabilite(self, ratios_results, annee):
        """Score rentabilité (0-25 points)"""
        try:
            if annee not in ratios_results:
                return 0
                
            rentabilite_str = ratios_results[annee].get('rentabilite_nette', '0%')
            rentabilite = float(rentabilite_str.replace('%', '').replace(',', '.'))
            
            if rentabilite >= 15: return 25
            elif rentabilite >= 10: return 20
            elif rentabilite >= 7: return 16
            elif rentabilite >= 5: return 12
            elif rentabilite >= 3: return 8
            elif rentabilite >= 0: return 4
            else: return 0
        except:
            return 0
    
    def _score_structure(self, ratios_results, annee):
        """Score structure financière (0-25 points)"""
        try:
            if annee not in ratios_results:
                return 0
                
            endettement_str = ratios_results[annee].get('ratio_endettement', '0')
            autonomie_str = ratios_results[annee].get('ratio_autonomie', '0%')
            
            endettement = float(endettement_str.replace(',', '.'))
            autonomie = float(autonomie_str.replace('%', '').replace(',', '.'))
            
            score_endettement = 0
            if endettement <= 0.5: score_endettement = 15
            elif endettement <= 1.0: score_endettement = 12
            elif endettement <= 1.5: score_endettement = 9
            elif endettement <= 2.0: score_endettement = 6
            else: score_endettement = 3
            
            score_autonomie = 0
            if autonomie >= 50: score_autonomie = 10
            elif autonomie >= 40: score_autonomie = 8
            elif autonomie >= 30: score_autonomie = 6
            elif autonomie >= 20: score_autonomie = 4
            else: score_autonomie = 2
            
            return score_endettement + score_autonomie
        except:
            return 0
    
    def _score_liquidite(self, ratios_results, annee):
        """Score liquidité (0-20 points)"""
        try:
            if annee not in ratios_results:
                return 0
                
            liquidite_str = ratios_results[annee].get('ratio_liquidite', '0')
            liquidite = float(liquidite_str.replace(',', '.'))
            
            if liquidite >= 2.0: return 20
            elif liquidite >= 1.5: return 16
            elif liquidite >= 1.2: return 12
            elif liquidite >= 1.0: return 8
            elif liquidite >= 0.8: return 4
            else: return 0
        except:
            return 0
    
    def _score_tresorerie(self, working_capital_results, annee):
        """Score trésorerie (0-15 points)"""
        try:
            if annee not in working_capital_results:
                return 0
                
            tn = working_capital_results[annee].get('tn', 0)
            caf = working_capital_results[annee].get('caf', 0)
            bfr = working_capital_results[annee].get('bfr', 0)
            
            if tn > 0 and caf > 0 and caf > abs(bfr): return 15
            elif tn > 0 and caf > 0: return 12
            elif tn > 0 or caf > 0: return 8
            elif tn >= -caf: return 4
            else: return 0
        except:
            return 0
    
    def _score_croissance(self, sig_results, ratios_results):
        """Score croissance (0-15 points)"""
        try:
            if len(sig_results) < 2:
                return 7  # Score neutre si pas d'historique
                
            annees = sorted(sig_results.keys())
            derniere_annee = annees[-1]
            annee_precedente = annees[-2]
            
            # Croissance CA
            ca_actuel = sig_results[derniere_annee].get('chiffre_affaires', 0)
            ca_precedent = sig_results[annee_precedente].get('chiffre_affaires', 0)
            
            if ca_precedent > 0:
                croissance_ca = ((ca_actuel - ca_precedent) / ca_precedent * 100)
            else:
                croissance_ca = 0
            
            # Croissance rentabilité
            renta_actuelle_str = ratios_results[derniere_annee].get('rentabilite_nette', '0%')
            renta_precedente_str = ratios_results[annee_precedente].get('rentabilite_nette', '0%')
            
            renta_actuelle = float(renta_actuelle_str.replace('%', '').replace(',', '.'))
            renta_precedente = float(renta_precedente_str.replace('%', '').replace(',', '.'))
            
            croissance_renta = renta_actuelle - renta_precedente
            
            if croissance_ca > 10 and croissance_renta > 2: return 15
            elif croissance_ca > 5 and croissance_renta > 0: return 12
            elif croissance_ca > 0: return 9
            elif croissance_ca >= -5: return 6
            else: return 3
        except:
            return 5  # Score moyen en cas d'erreur
    
    def _determiner_categorie(self, score_total):
        """Détermine la catégorie COBAC basée sur le score"""
        try:
            for categorie, infos in self.categories.items():
                if score_total >= infos['score_min']:
                    return categorie
            return 'E'
        except:
            return 'E'
    
    def _verifier_conformite_cobac(self, ratios_results, annee):
        """Vérifie la conformité aux normes COBAC"""
        try:
            if annee not in ratios_results:
                return self._create_default_conformite()
                
            seuils = REGLEMENTATION_COBAC['seuils_alertes']
            ratios = ratios_results[annee]
            
            rentabilite_str = ratios.get('rentabilite_nette', '0%')
            endettement_str = ratios.get('ratio_endettement', '0')
            liquidite_str = ratios.get('ratio_liquidite', '0')
            autonomie_str = ratios.get('ratio_autonomie', '0%')
            
            rentabilite = float(rentabilite_str.replace('%', '').replace(',', '.'))
            endettement = float(endettement_str.replace(',', '.'))
            liquidite = float(liquidite_str.replace(',', '.'))
            autonomie = float(autonomie_str.replace('%', '').replace(',', '.'))
            
            conformite = {
                'rentabilite': rentabilite >= seuils['rentabilite_min'],
                'endettement': endettement <= seuils['endettement_max'],
                'liquidite': liquidite >= seuils['liquidite_min'],
                'autonomie': autonomie >= seuils['autonomie_min']
            }
            
            conformite['global'] = all(conformite.values())
            
            return conformite
        except:
            return self._create_default_conformite()
    
    def _create_default_conformite(self):
        """Crée une conformité par défaut en cas d'erreur"""
        return {
            'rentabilite': False,
            'endettement': False,
            'liquidite': False,
            'autonomie': False,
            'global': False
        }
    
    def calculer_provisionnement(self, montant_pret, categorie):
        """Calcule le provisionnement requis selon COBAC"""
        try:
            taux = REGLEMENTATION_COBAC['classification_creances'][categorie]['provision']
            provision = montant_pret * taux
            
            return {
                'montant_pret': montant_pret,
                'categorie': categorie,
                'taux_provision': taux,
                'provision_requise': provision,
                'montant_net': montant_pret - provision
            }
        except:
            # Fallback en cas d'erreur
            return {
                'montant_pret': montant_pret,
                'categorie': 'E',
                'taux_provision': 1.0,
                'provision_requise': montant_pret,
                'montant_net': 0
            }