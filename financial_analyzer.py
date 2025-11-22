# financial_analyzer.py - Version COBAC
import pandas as pd
import numpy as np
from regulations_cobac import REGLEMENTATION_COBAC

class FinancialAnalyzer:
    def __init__(self):
        self.seuils_cobac = REGLEMENTATION_COBAC['seuils_alertes']
    
    def calculate_soldes_intermediaires(self, df, company_id="001"):
        """Calcule les soldes intermédiaires de gestion version COBAC"""
        sig_results = {}
        
        for year in df['year'].unique():
            year_data = df[df['year'] == year]
            cpc_data = year_data[year_data['source'] == 'CPC']
            bilan_data = year_data[year_data['source'] == 'BILAN']
            
            # Calcul des SIG selon normes COBAC
            ventes = cpc_data[cpc_data['nature'] == 'produit']['amount'].sum()
            
            # Marge commerciale (normes COBAC)
            achats_marchandises = cpc_data[
                (cpc_data['account_code'] == '601') | 
                (cpc_data['account_label'].str.contains('achat', case=False))
            ]['amount'].sum()
            marge_commerciale = ventes - abs(achats_marchandises)
            
            # Production (normes COBAC)
            production = cpc_data[
                (cpc_data['account_code'].str.startswith('70')) &
                (cpc_data['nature'] == 'produit')
            ]['amount'].sum()
            
            # Valeur ajoutée
            consommations = cpc_data[
                (cpc_data['account_code'].str.startswith('60')) &
                (cpc_data['nature'] == 'charge')
            ]['amount'].sum()
            valeur_ajoutee = marge_commerciale + production - abs(consommations)
            
            # EBE selon normes COBAC
            charges_personnel = cpc_data[
                cpc_data['account_code'].isin(['641', '645'])
            ]['amount'].sum()
            autres_charges_gestion = cpc_data[
                (cpc_data['account_code'].str.startswith('62')) |
                (cpc_data['account_code'].str.startswith('63'))
            ]['amount'].sum()
            
            ebe = valeur_ajoutee - abs(charges_personnel) - abs(autres_charges_gestion)
            
            # Résultat net
            charges_total = cpc_data[cpc_data['nature'] == 'charge']['amount'].sum()
            resultat_net = ventes - abs(charges_total)
            
            sig_results[year] = {
                'chiffre_affaires': ventes,
                'marge_commerciale': marge_commerciale,
                'valeur_ajoutee': valeur_ajoutee,
                'ebe': ebe,
                'resultat_net': resultat_net,
                'charges_personnel': abs(charges_personnel)
            }
        
        return sig_results
    
    def calculate_financial_ratios(self, df, company_id="001"):
        """Calcule les ratios financiers selon normes COBAC"""
        ratios_results = {}
        
        for year in df['year'].unique():
            year_data = df[df['year'] == year]
            
            # Données CPC
            cpc_data = year_data[year_data['source'] == 'CPC']
            ventes = cpc_data[cpc_data['nature'] == 'produit']['amount'].sum()
            resultat_net = ventes - cpc_data[cpc_data['nature'] == 'charge']['amount'].sum()
            
            # Données Bilan selon plan comptable COBAC
            bilan_data = year_data[year_data['source'] == 'BILAN']
            
            # Actif total
            actif_total = bilan_data[bilan_data['nature'] == 'actif']['amount'].sum()
            
            # Passif total
            passif_total = bilan_data[bilan_data['nature'] == 'passif']['amount'].sum()
            
            # Capitaux propres (normes COBAC)
            capitaux_propres = bilan_data[
                bilan_data['account_code'].isin(['101', '106', '107', '109', '11'])
            ]['amount'].sum()
            
            # Dettes financières (normes COBAC)
            dettes_financieres = bilan_data[
                bilan_data['account_code'].str.startswith(('16', '17')) & 
                (bilan_data['nature'] == 'passif')
            ]['amount'].sum()
            
            # Actif circulant (normes COBAC)
            actif_circulant = bilan_data[
                bilan_data['account_code'].str.startswith(('3', '4', '5')) & 
                (bilan_data['nature'] == 'actif')
            ]['amount'].sum()
            
            # Passif circulant (normes COBAC)
            passif_circulant = bilan_data[
                bilan_data['account_code'].str.startswith(('40', '41', '42', '43', '44', '45')) & 
                (bilan_data['nature'] == 'passif')
            ]['amount'].sum()
            
            # === RATIOS COBAC ===
            
            # Rentabilité nette
            rentabilite_nette = (resultat_net / ventes * 100) if ventes > 0 else 0
            
            # Ratio d'endettement
            ratio_endettement = (dettes_financieres / capitaux_propres) if capitaux_propres > 0 else float('inf')
            
            # Ratio de liquidité générale
            ratio_liquidite = (actif_circulant / passif_circulant) if passif_circulant > 0 else 0
            
            # Ratio d'autonomie financière
            ratio_autonomie = (capitaux_propres / passif_total * 100) if passif_total > 0 else 0
            
            # Capacité de remboursement
            ebe = self.calculate_ebe(year_data)
            capacite_remboursement = (ebe / dettes_financieres) if dettes_financieres > 0 else float('inf')
            
            ratios_results[year] = {
                'rentabilite_nette': f"{rentabilite_nette:.1f}%",
                'ratio_endettement': f"{ratio_endettement:.2f}",
                'ratio_liquidite': f"{ratio_liquidite:.2f}",
                'ratio_autonomie': f"{ratio_autonomie:.1f}%",
                'capacite_remboursement': f"{capacite_remboursement:.2f}",
                'ebe': ebe,
                'dettes_financieres': dettes_financieres
            }
        
        return ratios_results
    
    def calculate_working_capital_indicators(self, df, company_id="001"):
        """Calcule la CAF, BFR, TN et FR selon normes COBAC"""
        working_capital_results = {}
        
        for year in df['year'].unique():
            year_data = df[df['year'] == year]
            cpc_data = year_data[year_data['source'] == 'CPC']
            bilan_data = year_data[year_data['source'] == 'BILAN']
            
            # === CAF (Capacité d'Autofinancement) - Méthode additive ===
            resultat_net = cpc_data[cpc_data['nature'] == 'produit']['amount'].sum() - \
                          cpc_data[cpc_data['nature'] == 'charge']['amount'].sum()
            
            # Dotations aux amortissements selon COBAC
            dotations_amortissement = cpc_data[
                (cpc_data['account_code'] == '681') | 
                (cpc_data['account_label'].str.contains('amortissement', case=False))
            ]['amount'].sum()
            
            # Dotations aux provisions
            dotations_provisions = cpc_data[
                (cpc_data['account_code'] == '691') |
                (cpc_data['account_label'].str.contains('provision', case=False))
            ]['amount'].sum()
            
            caf = resultat_net + abs(dotations_amortissement) + abs(dotations_provisions)
            
            # === Calcul du BFR (Besoin en Fonds de Roulement) COBAC ===
            # Actif circulant d'exploitation
            stocks = bilan_data[
                bilan_data['account_code'].str.startswith('3') & 
                (bilan_data['nature'] == 'actif')
            ]['amount'].sum()
            
            clients = bilan_data[
                (bilan_data['account_code'].str.startswith('41')) & 
                (bilan_data['nature'] == 'actif')
            ]['amount'].sum()
            
            actif_circulant_exploitation = stocks + clients
            
            # Passif circulant d'exploitation
            fournisseurs = bilan_data[
                (bilan_data['account_code'].str.startswith('40')) & 
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
            
            passif_circulant_exploitation = fournisseurs + dettes_fiscales + dettes_sociales
            
            bfr = actif_circulant_exploitation - passif_circulant_exploitation
            
            # === Calcul du FR (Fonds de Roulement) COBAC ===
            # Capitaux permanents
            capitaux_propres = bilan_data[
                bilan_data['account_code'].isin(['101', '106', '109']) & 
                (bilan_data['nature'] == 'passif')
            ]['amount'].sum()
            
            dettes_long_terme = bilan_data[
                (bilan_data['account_code'].str.startswith(('16', '17'))) & 
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
            
            working_capital_results[year] = {
                'caf': caf,
                'bfr': bfr,
                'fr': fr,
                'tn': tn,
                'actif_circulant': actif_circulant_exploitation,
                'passif_circulant': passif_circulant_exploitation,
                'capitaux_permanents': capitaux_permanents,
                'actif_immobilise': actif_immobilise
            }
        
        return working_capital_results
    
    def calculate_ebe(self, year_data):
        """Calcule l'EBE selon normes COBAC"""
        cpc_data = year_data[year_data['source'] == 'CPC']
        
        ventes = cpc_data[cpc_data['nature'] == 'produit']['amount'].sum()
        achats_consommes = cpc_data[
            cpc_data['account_code'].str.startswith('60') & 
            (cpc_data['nature'] == 'charge')
        ]['amount'].sum()
        charges_personnel = cpc_data[
            cpc_data['account_code'].isin(['641', '645']) & 
            (cpc_data['nature'] == 'charge')
        ]['amount'].sum()
        
        ebe = ventes - abs(achats_consommes) - abs(charges_personnel)
        return ebe