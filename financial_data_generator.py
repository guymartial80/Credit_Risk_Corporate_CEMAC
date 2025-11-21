import pandas as pd
import numpy as np
import random
from datetime import datetime

# Configuration pour la reproductibilité
np.random.seed(42)
random.seed(42)

# Définition des comptes détaillés
comptes_cpc = {
    '701': 'Ventes de produits finis',
    '706': 'Prestations de services',
    '707': 'Ventes de marchandises',
    '601': 'Achats de marchandises',
    '602': 'Achats de matières premières',
    '603': 'Autres achats et charges externes',
    '604': 'Transports',
    '605': 'Services bancaires',
    '606': 'Assurances',
    '607': 'Publicité',
    '608': 'Frais de déplacement',
    '609': 'Frais postaux et télécommunications',
    '641': 'Rémunérations du personnel',
    '645': 'Charges sociales',
    '651': 'Impôts et taxes',
    '661': 'Charges financières',
    '681': 'Dotations aux amortissements'
}

comptes_bilan = {
    '101': 'Capital social',
    '106': 'Réserves',
    '109': 'Report à nouveau',
    '211': 'Terrains',
    '213': 'Constructions',
    '215': 'Installations techniques',
    '218': 'Matériel de transport',
    '223': 'Matériel informatique',
    '231': 'Immobilisations en cours',
    '281': 'Amortissements cumulés',
    '311': 'Stocks de matières premières',
    '312': 'Stocks de produits finis',
    '401': 'Fournisseurs',
    '411': 'Clients',
    '421': 'Personnel',
    '431': 'Sécurité sociale',
    '441': 'État',
    '456': 'Associés',
    '511': 'Banque',
    '512': 'Caisse'
}

comptes_flux_tresorerie = {
    '7011': 'Encaissements clients',
    '6011': 'Décaissements fournisseurs',
    '6411': 'Décaissements personnel',
    '6511': 'Décaissements impôts',
    '6611': 'Décaissements charges financières',
    '2111': 'Acquisitions immobilisations',
    '1011': 'Apports en capital',
    '4561': 'Dividendes versés',
    '5111': 'Variation trésorerie'
}

def calculer_ratios_avances(donnees_entreprise, annee):
    """Calcule les ratios financiers avancés incluant les flux de trésorerie"""
    # Extraire les données par source
    data_cpc = [d for d in donnees_entreprise if d[1] == annee and d[5] == 'CPC']
    data_bilan = [d for d in donnees_entreprise if d[1] == annee and d[5] == 'BILAN']
    data_flux = [d for d in donnees_entreprise if d[1] == annee and d[5] == 'FLUX_TRESORERIE']
    
    # Calculs CPC
    ventes = sum([d[4] for d in data_cpc if d[6] == 'produit'])
    charges = sum([d[4] for d in data_cpc if d[6] == 'charge'])
    resultat_net = ventes - charges
    
    # Calculs Bilan
    actif = sum([d[4] for d in data_bilan if d[6] == 'actif'])
    passif = sum([d[4] for d in data_bilan if d[6] == 'passif'])
    
    # Calculs Flux de Trésorerie
    flux_exploitation = sum([d[4] for d in data_flux if d[6] in ['encaissement', 'decaissement_exploitation']])
    flux_investissement = sum([d[4] for d in data_flux if d[6] in ['investissement', 'desinvestissement']])
    flux_financement = sum([d[4] for d in data_flux if d[6] in ['financement', 'remboursement']])
    
    # Ratios classiques
    marge_nette = resultat_net / ventes if ventes > 0 else -1
    endettement = passif / actif if actif > 0 else 1
    couverture_charges = ventes / charges if charges > 0 else 0
    
    # Nouveaux ratios basés sur les flux de trésorerie
    flux_tresorerie_net = flux_exploitation + flux_investissement + flux_financement
    capacite_autofinancement = flux_exploitation / ventes if ventes > 0 else 0
    couverture_flux = flux_exploitation / charges if charges > 0 else 0
    
    # Score de défaut amélioré
    score_defaut = (
        (1 - marge_nette) * 0.25 +           # Rentabilité
        endettement * 0.25 +                 # Structure financière
        (1 - min(1, couverture_flux)) * 0.3 + # Capacité à générer des flux
        (1 - min(1, capacite_autofinancement)) * 0.2 # Autofinancement
    )
    
    return score_defaut, marge_nette, endettement, capacite_autofinancement, flux_tresorerie_net

def generer_flux_tresorerie(company_id, annee, ventes, charges, actif, passif, resultat_net):
    """Génère les flux de trésorerie réalistes"""
    flux_data = []
    
    # Flux d'exploitation
    encaissements_clients = ventes * random.uniform(0.85, 1.05)  # Délais clients
    decaissements_fournisseurs = charges * 0.6 * random.uniform(0.8, 1.1)  # Délais fournisseurs
    decaissements_personnel = charges * 0.25 * random.uniform(0.9, 1.0)   # Charges de personnel
    decaissements_impots = max(0, resultat_net * 0.25 * random.uniform(0.8, 1.2))  # Impôts
    
    flux_exploitation = encaissements_clients - decaissements_fournisseurs - decaissements_personnel - decaissements_impots
    
    flux_data.append([company_id, annee, '7011', 'Encaissements clients', 
                     int(encaissements_clients), 'FLUX_TRESORERIE', 'encaissement'])
    flux_data.append([company_id, annee, '6011', 'Décaissements fournisseurs', 
                     int(decaissements_fournisseurs), 'FLUX_TRESORERIE', 'decaissement_exploitation'])
    flux_data.append([company_id, annee, '6411', 'Décaissements personnel', 
                     int(decaissements_personnel), 'FLUX_TRESORERIE', 'decaissement_exploitation'])
    flux_data.append([company_id, annee, '6511', 'Décaissements impôts', 
                     int(decaissements_impots), 'FLUX_TRESORERIE', 'decaissement_exploitation'])
    
    # Flux d'investissement
    if random.random() < 0.6:  # 60% de chance d'investir
        acquisitions_immobilisations = actif * 0.1 * random.uniform(0.5, 1.5)
        flux_data.append([company_id, annee, '2111', 'Acquisitions immobilisations', 
                         int(acquisitions_immobilisations), 'FLUX_TRESORERIE', 'investissement'])
    else:
        acquisitions_immobilisations = 0
    
    # Flux de financement
    if flux_exploitation < 0 or random.random() < 0.3:  # Besoin de financement
        apports_capital = max(0, -flux_exploitation * random.uniform(0.5, 1.2))
        flux_data.append([company_id, annee, '1011', 'Apports en capital', 
                         int(apports_capital), 'FLUX_TRESORERIE', 'financement'])
    else:
        apports_capital = 0
    
    # Dividendes (seulement si résultat positif)
    if resultat_net > 0 and random.random() < 0.4:
        dividendes = resultat_net * 0.2 * random.uniform(0.5, 1.0)
        flux_data.append([company_id, annee, '4561', 'Dividendes versés', 
                         int(dividendes), 'FLUX_TRESORERIE', 'remboursement'])
    
    return flux_data

def generer_donnees_completes_avec_flux():
    data = []
    company_id = 1
    
    for _ in range(120):  # 120 entreprises
        secteur = random.choice(['industrie', 'services', 'commerce', 'technologie', 'construction'])
        taille = random.choice(['TPE', 'PME', 'ETI'])
        sante_base = np.random.normal(0, 1)
        
        # Données historiques pour calculer les variations
        historique = {}
        
        for annee in range(2021, 2024):
            donnees_entreprise = []
            
            # Génération des données CPC
            if secteur == 'industrie':
                ventes = np.random.lognormal(13.5, 0.7) * (1 + sante_base * 0.1)
                taux_marge = random.uniform(0.15, 0.35)
            elif secteur == 'services':
                ventes = np.random.lognormal(13, 0.6) * (1 + sante_base * 0.1)
                taux_marge = random.uniform(0.25, 0.45)
            elif secteur == 'commerce':
                ventes = np.random.lognormal(14, 0.8) * (1 + sante_base * 0.1)
                taux_marge = random.uniform(0.08, 0.25)
            elif secteur == 'technologie':
                ventes = np.random.lognormal(12.5, 0.9) * (1 + sante_base * 0.1)
                taux_marge = random.uniform(0.3, 0.6)
            else:  # construction
                ventes = np.random.lognormal(13.2, 0.75) * (1 + sante_base * 0.1)
                taux_marge = random.uniform(0.1, 0.3)
            
            ventes = max(50000, ventes)
            marge_brute = ventes * taux_marge
            charges_total = ventes - marge_brute
            resultat_net = marge_brute - charges_total * 0.4  # Charges fixes
            
            # Comptes de produits CPC
            donnees_entreprise.append([company_id, annee, '701', 'Ventes de produits finis', 
                                     int(ventes * 0.7), 'CPC', 'produit'])
            donnees_entreprise.append([company_id, annee, '706', 'Prestations de services', 
                                     int(ventes * 0.3), 'CPC', 'produit'])
            
            # Comptes de charges CPC
            donnees_entreprise.append([company_id, annee, '601', 'Achats de marchandises', 
                                     int(charges_total * 0.4), 'CPC', 'charge'])
            donnees_entreprise.append([company_id, annee, '602', 'Achats de matières premières', 
                                     int(charges_total * 0.2), 'CPC', 'charge'])
            donnees_entreprise.append([company_id, annee, '641', 'Rémunérations du personnel', 
                                     int(charges_total * 0.25), 'CPC', 'charge'])
            donnees_entreprise.append([company_id, annee, '645', 'Charges sociales', 
                                     int(charges_total * 0.15), 'CPC', 'charge'])
            
            # Génération des données Bilan
            actif_total = ventes * random.uniform(0.7, 1.3)
            passif_total = actif_total * random.uniform(0.4, 0.9)
            
            # Actifs
            donnees_entreprise.append([company_id, annee, '213', 'Constructions', 
                                     int(actif_total * 0.4), 'BILAN', 'actif'])
            donnees_entreprise.append([company_id, annee, '223', 'Matériel informatique', 
                                     int(actif_total * 0.1), 'BILAN', 'actif'])
            donnees_entreprise.append([company_id, annee, '411', 'Clients', 
                                     int(ventes * 0.18), 'BILAN', 'actif'])
            donnees_entreprise.append([company_id, annee, '511', 'Banque', 
                                     int(actif_total * 0.05), 'BILAN', 'actif'])
            
            # Passifs
            donnees_entreprise.append([company_id, annee, '101', 'Capital social', 
                                     int(actif_total * 0.3), 'BILAN', 'passif'])
            donnees_entreprise.append([company_id, annee, '401', 'Fournisseurs', 
                                     int(charges_total * 0.3), 'BILAN', 'passif'])
            donnees_entreprise.append([company_id, annee, '421', 'Personnel', 
                                     int(charges_total * 0.1), 'BILAN', 'passif'])
            
            # Génération des Flux de Trésorerie
            flux_tresorerie = generer_flux_tresorerie(company_id, annee, ventes, charges_total, 
                                                     actif_total, passif_total, resultat_net)
            donnees_entreprise.extend(flux_tresorerie)
            
            # Calcul du défaut avec ratios avancés incluant les flux
            score_defaut, marge_nette, endettement, capacite_autofinancement, flux_tresorerie_net = \
                calculer_ratios_avances(donnees_entreprise, annee)
            
            # Détermination réaliste du défaut
            if (marge_nette < -0.1 or 
                endettement > 0.9 or 
                capacite_autofinancement < 0 or 
                flux_tresorerie_net < -ventes * 0.1):
                prob_defaut = min(0.95, score_defaut)
            else:
                prob_defaut = max(0.02, score_defaut * 0.3)
            
            # Facteur temporel (défaut plus probable dans les années récentes)
            if annee == 2023:
                prob_defaut *= 1.3
            
            defaut = 'oui' if random.random() < prob_defaut else 'non'
            
            # Ajout de la variable défaut à toutes les lignes
            for ligne in donnees_entreprise:
                ligne.append(defaut)
                data.append(ligne)
            
            historique[annee] = {
                'ventes': ventes,
                'resultat_net': resultat_net,
                'actif_total': actif_total
            }
            
        company_id += 1
    
    return data

# Génération des données complètes
print("Génération des données avec flux de trésorerie...")
donnees_completes = generer_donnees_completes_avec_flux()

# Création du DataFrame
colonnes = ['company_id', 'year', 'account_code', 'account_label', 'amount', 'source', 'nature', 'defaut']
df = pd.DataFrame(donnees_completes, columns=colonnes)

# Statistiques détaillées
print(f"Nombre total d'observations : {len(df)}")
print(f"Répartition par source :")
print(df['source'].value_counts())
print(f"\nRépartition des défauts :")
print(df['defaut'].value_counts())
print(f"Taux de défaut global : {(df['defaut'] == 'oui').sum() / len(df) * 100:.2f}%")

# Taux de défaut par source
print(f"\nTaux de défaut par type de données :")
for source in df['source'].unique():
    subset = df[df['source'] == source]
    taux_defaut = (subset['defaut'] == 'oui').sum() / len(subset) * 100
    print(f"- {source}: {taux_defaut:.2f}%")

# Affichage d'un échantillon avec les trois types de données
print("\nÉchantillon des données générées (CPC, Bilan, Flux Trésorerie) :")
echantillon_cpc = df[df['source'] == 'CPC'].head(3)
echantillon_bilan = df[df['source'] == 'BILAN'].head(3)
echantillon_flux = df[df['source'] == 'FLUX_TRESORERIE'].head(3)

echantillon_complet = pd.concat([echantillon_cpc, echantillon_bilan, echantillon_flux])
print(echantillon_complet.to_string(index=False))

# Sauvegarde en CSV
nom_fichier = "donnees_financieres_completes_flux.csv"
df.to_csv(nom_fichier, index=False, encoding='utf-8')
print(f"\n✅ Fichier sauvegardé : {nom_fichier}")

# Vérification finale
print(f"\n📊 SYNTHÈSE FINALE :")
print(f"Entreprises : {df['company_id'].nunique()}")
print(f"Période : {df['year'].min()} - {df['year'].max()}")
print(f"Observations CPC : {len(df[df['source'] == 'CPC'])}")
print(f"Observations Bilan : {len(df[df['source'] == 'BILAN'])}")
print(f"Observations Flux Trésorerie : {len(df[df['source'] == 'FLUX_TRESORERIE'])}")