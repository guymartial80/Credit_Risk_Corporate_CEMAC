import pandas as pd
import numpy as np

class FinancialAnalyzer:
    def __init__(self):
        self.sig_definitions = {
            'marge_commerciale': 'Ventes - Achats marchandises',
            'valeur_ajoutee': 'Marge commerciale + Production - Consommations',
            'ebe': 'VA + Subventions - Charges personnel - Impôts',
            'resultat_exploitation': 'EBE + Reprises - Dotations',
            'resultat_courant': 'Résultat exploitation + Résultat financier',
            'resultat_net': 'Résultat courant + Résultat exceptionnel - Impôts'
        }
        
        self.ratios_definitions = {
            'rentabilite': 'Résultat net / Chiffre affaires',
            'endettement': 'Dettes financières / Capitaux propres',
            'liquidite': 'Actif circulant / Passif circulant',
            'autonomie': 'Capitaux propres / Total bilan',
            'couverture_charges_financieres': 'EBE / Charges financières'
        }
    
    def calculate_soldes_intermediaires(self, df, company_id="001"):
        """Calcule les soldes intermédiaires de gestion"""
        sig_results = {}
        
        for year in df['year'].unique():
            year_data = df[df['year'] == year]
            cpc_data = year_data[year_data['source'] == 'CPC']
            bilan_data = year_data[year_data['source'] == 'BILAN']
            
            # Calcul des SIG
            ventes = cpc_data[cpc_data['nature'] == 'produit']['amount'].sum()
            achats_marchandises = cpc_data[
                (cpc_data['account_code'] == '601') | 
                (cpc_data['account_label'].str.contains('achat', case=False))
            ]['amount'].sum()
            
            # Marge commerciale
            marge_commerciale = ventes - abs(achats_marchandises)
            
            # Valeur ajoutée
            production = cpc_data[
                cpc_data['account_label'].str.contains('production', case=False)
            ]['amount'].sum()
            consommations = cpc_data[
                cpc_data['account_label'].str.contains('consommation', case=False)
            ]['amount'].sum()
            valeur_ajoutee = marge_commerciale + production - abs(consommations)
            
            # EBE (Excédent Brut d'Exploitation)
            charges_personnel = cpc_data[
                cpc_data['account_code'].isin(['641', '645'])
            ]['amount'].sum()
            ebe = valeur_ajoutee - abs(charges_personnel)
            
            # Résultat net
            charges_total = cpc_data[cpc_data['nature'] == 'charge']['amount'].sum()
            resultat_net = ventes - abs(charges_total)
            
            sig_results[year] = {
                'chiffre_affaires': ventes,
                'marge_commerciale': marge_commerciale,
                'valeur_ajoutee': valeur_ajoutee,
                'ebe': ebe,
                'charges_personnel': abs(charges_personnel),
                'resultat_net': resultat_net
            }
        
        return sig_results
    
    def calculate_financial_ratios(self, df, company_id="001"):
        """Calcule les ratios financiers"""
        ratios_results = {}
        
        for year in df['year'].unique():
            year_data = df[df['year'] == year]
            
            # Données CPC
            cpc_data = year_data[year_data['source'] == 'CPC']
            ventes = cpc_data[cpc_data['nature'] == 'produit']['amount'].sum()
            resultat_net = ventes - cpc_data[cpc_data['nature'] == 'charge']['amount'].sum()
            
            # Données Bilan
            bilan_data = year_data[year_data['source'] == 'BILAN']
            actif_total = bilan_data[bilan_data['nature'] == 'actif']['amount'].sum()
            passif_total = bilan_data[bilan_data['nature'] == 'passif']['amount'].sum()
            capitaux_propres = bilan_data[
                bilan_data['account_code'].isin(['101', '106', '109'])
            ]['amount'].sum()
            
            # Ratios
            rentabilite = (resultat_net / ventes * 100) if ventes > 0 else 0
            endettement = (passif_total / capitaux_propres) if capitaux_propres > 0 else 0
            liquidite = (actif_total / passif_total) if passif_total > 0 else 0
            autonomie = (capitaux_propres / actif_total * 100) if actif_total > 0 else 0
            
            ratios_results[year] = {
                'rentabilite_net': f"{rentabilite:.1f}%",
                'ratio_endettement': f"{endettement:.2f}",
                'ratio_liquidite': f"{liquidite:.2f}",
                'ratio_autonomie': f"{autonomie:.1f}%",
                'resultat_net': resultat_net
            }
        
        return ratios_results
    
    def calculate_working_capital_indicators(self, df, company_id="001"):
        """Calcule la CAF, BFR, TN et FR"""
        working_capital_results = {}
        
        for year in df['year'].unique():
            year_data = df[df['year'] == year]
            cpc_data = year_data[year_data['source'] == 'CPC']
            bilan_data = year_data[year_data['source'] == 'BILAN']
            
            # === CAF (Capacité d'Autofinancement) ===
            resultat_net = cpc_data[cpc_data['nature'] == 'produit']['amount'].sum() - \
                          cpc_data[cpc_data['nature'] == 'charge']['amount'].sum()
            
            # Dotations aux amortissements (approximation)
            dotations_amortissement = cpc_data[
                (cpc_data['account_code'] == '681') | 
                (cpc_data['account_label'].str.contains('amortissement', case=False))
            ]['amount'].sum()
            
            caf = resultat_net + abs(dotations_amortissement)  # CAF = Résultat net + Dotations
            
            # === Calcul du BFR (Besoin en Fonds de Roulement) ===
            # Actif circulant (stocks + créances clients)
            stocks = bilan_data[
                bilan_data['account_code'].str.startswith('3') & 
                (bilan_data['nature'] == 'actif')
            ]['amount'].sum()
            
            clients = bilan_data[
                (bilan_data['account_code'] == '411') & 
                (bilan_data['nature'] == 'actif')
            ]['amount'].sum()
            
            actif_circulant = stocks + clients
            
            # Passif circulant (dettes fournisseurs + dettes fiscales + dettes sociales)
            fournisseurs = bilan_data[
                (bilan_data['account_code'] == '401') & 
                (bilan_data['nature'] == 'passif')
            ]['amount'].sum()
            
            dettes_fiscales = bilan_data[
                (bilan_data['account_code'] == '441') & 
                (bilan_data['nature'] == 'passif')
            ]['amount'].sum()
            
            dettes_sociales = bilan_data[
                (bilan_data['account_code'] == '431') & 
                (bilan_data['nature'] == 'passif')
            ]['amount'].sum()
            
            passif_circulant = fournisseurs + dettes_fiscales + dettes_sociales
            
            bfr = actif_circulant - passif_circulant
            
            # === Calcul du FR (Fonds de Roulement) ===
            # Capitaux permanents (capitaux propres + dettes long terme)
            capitaux_propres = bilan_data[
                bilan_data['account_code'].isin(['101', '106', '109']) & 
                (bilan_data['nature'] == 'passif')
            ]['amount'].sum()
            
            dettes_long_terme = bilan_data[
                (~bilan_data['account_code'].isin(['101', '106', '109', '401', '421', '431', '441'])) & 
                (bilan_data['nature'] == 'passif')
            ]['amount'].sum()
            
            capitaux_permanents = capitaux_propres + dettes_long_terme
            
            # Actif immobilisé
            actif_immobilise = bilan_data[
                (bilan_data['account_code'].str.startswith('2')) & 
                (bilan_data['nature'] == 'actif')
            ]['amount'].sum()
            
            fr = capitaux_permanents - actif_immobilise
            
            # === Calcul de la TN (Trésorerie Nette) ===
            tn = fr - bfr
            
            # Vérification alternative : Trésorerie active - Trésorerie passive
            tresorerie_active = bilan_data[
                (bilan_data['account_code'].isin(['511', '512'])) & 
                (bilan_data['nature'] == 'actif')
            ]['amount'].sum()
            
            tresorerie_passive = bilan_data[
                (bilan_data['account_code'].str.startswith('16')) &  # Concours bancaires
                (bilan_data['nature'] == 'passif')
            ]['amount'].sum()
            
            tn_alternative = tresorerie_active - tresorerie_passive
            
            working_capital_results[year] = {
                'caf': caf,
                'bfr': bfr,
                'fr': fr,
                'tn': tn,
                'tn_alternative': tn_alternative,
                'actif_circulant': actif_circulant,
                'passif_circulant': passif_circulant,
                'capitaux_permanents': capitaux_permanents,
                'actif_immobilise': actif_immobilise
            }
        
        return working_capital_results
    
    def analyze_working_capital_health(self, working_capital_results):
        """Analyse la santé du fonds de roulement"""
        health_analysis = {}
        
        for year, data in working_capital_results.items():
            # Analyse FRNG
            if data['fr'] > 0:
                fr_health = "Positif - Structure saine"
                fr_color = "green"
            else:
                fr_health = "Négatif - Risque structurel"
                fr_color = "red"
            
            # Analyse BFR
            if data['bfr'] > 0:
                bfr_health = "Positif - Besoin de financement"
                bfr_color = "orange"
            else:
                bfr_health = "Négatif - Ressource de financement"
                bfr_color = "blue"
            
            # Analyse TN
            if data['tn'] > 0:
                tn_health = "Excédent de trésorerie"
                tn_color = "green"
            else:
                tn_health = "Déficit de trésorerie"
                tn_color = "red"
            
            # Ratio CAF/BFR
            if data['bfr'] != 0:
                caf_bfr_ratio = data['caf'] / abs(data['bfr'])
                if caf_bfr_ratio > 1:
                    caf_health = "Bonne couverture"
                else:
                    caf_health = "Couverture insuffisante"
            else:
                caf_bfr_ratio = float('inf')
                caf_health = "BFR nul"
            
            health_analysis[year] = {
                'fr_health': fr_health,
                'fr_color': fr_color,
                'bfr_health': bfr_health,
                'bfr_color': bfr_color,
                'tn_health': tn_health,
                'tn_color': tn_color,
                'caf_health': caf_health,
                'caf_bfr_ratio': caf_bfr_ratio
            }
        
        return health_analysis