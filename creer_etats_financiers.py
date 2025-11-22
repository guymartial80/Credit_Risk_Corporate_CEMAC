import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

def creer_bilan():
    """Crée le fichier Excel pour le bilan"""
    data = {
        'compte': ['211', '213', '214', '215', '218', '261', '267', '271', '275', '281', '31', '33', '34', '35', '37', '39', 
                  '41', '44', '481', '486', '491', '16', '17', '40', '42', '43', '44', '45', '46', '47', '48', '49', '10', '11', '12', '13', '15', '16', '18'],
        'libellé': ['Terrains', 'Constructions', 'Installations techniques', 'Autres immobilisations', 'Avances et acomptes',
                   'Dépôts et cautionnements', 'Prêts', 'Stocks', 'En-cours', 'Créances clients', 'Capital social', 'Réserves',
                   'Report à nouveau', 'Résultat de l\'exercice', 'Provisions réglementées', 'Dettes financières',
                   'Fournisseurs', 'Personnel', 'Clients - avances et acomptes', 'État', 'Débiteurs divers',
                   'Emprunts et dettes assimilées', 'Dettes fournisseurs et comptes rattachés',
                   'Dettes fiscales et sociales', 'Dettes sur immobilisations', 'Dettes financières',
                   'Comptes de liaison', 'Charges constatées d\'avance', 'Produits constatés d\'avance',
                   'Capital souscrit - non appelé', 'Écarts de conversion actif', 'Écarts de conversion passif',
                   'Frais d\'établissement', 'Frais de recherche et développement', 'Concessions et droits similaires',
                   'Brevets, marques et droits similaires', 'Fonds commercial', 'Autres immobilisations incorporelles'],
        '2021': [150000, 300000, 80000, 50000, 20000, 15000, 25000, 120000, 45000, 180000, 
                200000, 80000, 15000, 35000, 10000, 150000, 90000, 65000, 25000, 40000, 15000,
                120000, 85000, 35000, 20000, 130000, 5000, 8000, 6000, 10000, 5000, 3000, 15000, 25000, 30000, 20000, 35000, 18000],
        '2022': [145000, 320000, 85000, 52000, 22000, 16000, 27000, 125000, 48000, 190000,
                200000, 85000, 18000, 42000, 12000, 160000, 95000, 68000, 27000, 42000, 16000,
                125000, 88000, 38000, 22000, 135000, 5500, 8500, 6500, 11000, 5500, 3200, 16000, 26000, 32000, 21000, 36000, 19000],
        '2023': [140000, 350000, 90000, 55000, 25000, 18000, 30000, 130000, 50000, 200000,
                200000, 90000, 20000, 48000, 15000, 170000, 100000, 70000, 30000, 45000, 18000,
                130000, 90000, 40000, 25000, 140000, 6000, 9000, 7000, 12000, 6000, 3500, 17000, 27000, 35000, 22000, 38000, 20000]
    }
    
    df = pd.DataFrame(data)
    return df

def creer_compte_resultat():
    """Crée le fichier Excel pour le compte de résultat"""
    data = {
        'compte': ['701', '702', '703', '704', '705', '706', '707', '708', '709',
                  '601', '602', '603', '604', '605', '606', '607', '608', '609',
                  '611', '612', '613', '614', '615', '616', '617', '618', '619',
                  '621', '622', '623', '624', '625', '626', '627', '628', '629',
                  '631', '632', '633', '634', '635', '636', '637', '638', '639',
                  '641', '642', '643', '644', '645', '646', '647', '648', '649',
                  '651', '652', '653', '654', '655', '656', '657', '658', '659',
                  '661', '662', '663', '664', '665', '666', '667', '668', '669',
                  '671', '672', '673', '674', '675', '676', '677', '678', '679',
                  '681', '682', '683', '684', '685', '686', '687', '688', '689',
                  '691', '692', '693', '694', '695', '696', '697', '698', '699'],
        'libellé': ['Ventes de produits finis', 'Ventes de produits intermédiaires', 'Ventes de produits résiduels',
                   'Travaux', 'Études', 'Prestations de services', 'Chiffre d\'affaires nets', 'Produits des activités annexes',
                   'Rabais, remises et ristournes accordés',
                   'Achats de matières premières', 'Achats de fournitures', 'Achats de marchandises',
                   'Achats d\'emballages', 'Achats stockés de matières et fournitures',
                   'Autres achats et charges externes', 'Transports', 'Déplacements, missions et réceptions',
                   'Services bancaires et assimilés',
                   'Rémunérations du personnel', 'Charges sociales', 'Autres charges de personnel',
                   'Impôts, taxes et versements assimilés', 'Redevances pour concessions, brevets, etc.',
                   'Entretien et réparations', 'Assurances', 'Études et recherches',
                   'Documentation générale', 'Publicité, relations publiques',
                   'Honoraires', 'Locations', 'Charges locatives et de copropriété',
                   'Frais postaux et de télécommunications', 'Frais de déplacement',
                   'Frais de mission', 'Frais de réception', 'Frais de transport',
                   'Cotisations et versements', 'Achats de matériel, équipements et travaux',
                   'Fournitures administratives', 'Services extérieurs',
                   'Autres services extérieurs', 'Commissions et courtages',
                   'Frais financiers', 'Intérêts des emprunts et dettes',
                   'Escomptes accordés', 'Pertes de change', 'Charges nettes sur cessions de valeurs mobilières de placement',
                   'Dotations aux amortissements', 'Dotations aux provisions',
                   'Dotations pour dépréciation', 'Autres dotations',
                   'Impôts sur les bénéfices', 'Taxes sur le chiffre d\'affaires',
                   'Participations des salariés', 'Subventions d\'exploitation',
                   'Produits financiers', 'Produits des participations',
                   'Produits des autres immobilisations financières',
                   'Produits des autres créances', 'Produits des valeurs mobilières de placement',
                   'Escomptes obtenus', 'Gains de change', 'Produits nets sur cessions de valeurs mobilières de placement',
                   'Reprises sur amortissements et provisions', 'Transferts de charges',
                   'Produits exceptionnels', 'Charges exceptionnelles',
                   'Participation des salariés aux résultats', 'Impôts différés',
                   'Produits des cessions d\'éléments d\'actif', 'Valeur comptable des éléments d\'actif cédés',
                   'Subventions d\'équipement', 'Reprises sur subventions d\'investissement',
                   'Résultat de l\'exercice'],
        '2021': [500000, 120000, 25000, 80000, 45000, 60000, 30000, 15000, 20000,
                180000, 45000, 35000, 12000, 8000, 55000, 15000, 12000, 8000,
                120000, 45000, 15000, 25000, 8000, 12000, 6000, 15000, 8000, 12000,
                18000, 15000, 8000, 12000, 10000, 8000, 12000, 6000,
                8000, 15000, 12000, 18000, 10000, 15000, 12000, 8000, 6000, 4000,
                25000, 15000, 8000, 12000, 35000, 45000, 15000, 12000,
                18000, 8000, 6000, 4000, 3000, 2000, 1500, 12000, 8000,
                15000, 12000, 18000, 15000, 35000, 25000, 15000, 12000, 35000],
        '2022': [550000, 130000, 28000, 85000, 48000, 65000, 32000, 16000, 22000,
                190000, 48000, 38000, 13000, 8500, 58000, 16000, 13000, 8500,
                125000, 48000, 16000, 27000, 8500, 13000, 6500, 16000, 8500, 13000,
                19000, 16000, 8500, 13000, 11000, 8500, 13000, 6500,
                8500, 16000, 13000, 19000, 11000, 16000, 13000, 8500, 6500, 4500,
                27000, 16000, 8500, 13000, 42000, 48000, 16000, 13000,
                19000, 8500, 6500, 4500, 3500, 2500, 1800, 13000, 8500,
                16000, 13000, 19000, 16000, 42000, 27000, 16000, 13000, 42000],
        '2023': [600000, 140000, 30000, 90000, 50000, 70000, 35000, 18000, 25000,
                200000, 50000, 40000, 15000, 9000, 60000, 18000, 15000, 9000,
                130000, 50000, 18000, 30000, 9000, 15000, 7000, 18000, 9000, 15000,
                20000, 18000, 9000, 15000, 12000, 9000, 15000, 7000,
                9000, 18000, 15000, 20000, 12000, 18000, 15000, 9000, 7000, 5000,
                30000, 18000, 9000, 15000, 48000, 50000, 18000, 15000,
                20000, 9000, 7000, 5000, 4000, 3000, 2000, 15000, 9000,
                18000, 15000, 20000, 18000, 48000, 30000, 18000, 15000, 48000]
    }
    
    df = pd.DataFrame(data)
    return df

def creer_flux_tresorerie():
    """Crée le fichier Excel pour le tableau de flux de trésorerie"""
    data = {
        'compte': ['7011', '7012', '7013', '7014', '7015', '7016', '7017', '7018', '7019',
                  '6011', '6012', '6013', '6014', '6015', '6016', '6017', '6018', '6019',
                  '6111', '6112', '6113', '6114', '6115', '6116', '6117', '6118', '6119',
                  '6211', '6212', '6213', '6214', '6215', '6216', '6217', '6218', '6219',
                  '6311', '6312', '6313', '6314', '6315', '6316', '6317', '6318', '6319',
                  '6411', '6412', '6413', '6414', '6415', '6416', '6417', '6418', '6419',
                  '6511', '6512', '6513', '6514', '6515', '6516', '6517', '6518', '6519',
                  '6611', '6612', '6613', '6614', '6615', '6616', '6617', '6618', '6619',
                  '6711', '6712', '6713', '6714', '6715', '6716', '6717', '6718', '6719',
                  '6811', '6812', '6813', '6814', '6815', '6816', '6817', '6818', '6819'],
        'libellé': ['Encaissements clients', 'Encaissements autres produits', 'Encaissements produits financiers',
                   'Encaissements produits exceptionnels', 'Subventions d\'investissement reçues',
                   'Encaissements cessions d\'immobilisations', 'Encaissements augmentations de capital',
                   'Encaissements emprunts', 'Autres encaissements',
                   'Décaissements fournisseurs', 'Décaissements charges externes',
                   'Décaissements personnel', 'Décaissements impôts et taxes',
                   'Décaissements charges financières', 'Décaissements charges exceptionnelles',
                   'Décaissements acquisitions immobilisations', 'Décaissements remboursements emprunts',
                   'Autres décaissements',
                   'Flux de trésorerie liés à l\'activité', 'Flux de trésorerie liés aux investissements',
                   'Flux de trésorerie liés au financement', 'Variation de trésorerie',
                   'Trésorerie début de période', 'Trésorerie fin de période',
                   'Solde net de trésorerie', 'Capacité d\'autofinancement',
                   'Variation du besoin en fonds de roulement', 'Flux de trésorerie disponible',
                   'Dividendes versés', 'Intérêts versés', 'Impôts versés',
                   'Acquisitions d\'immobilisations', 'Cessions d\'immobilisations',
                   'Augmentations de capital', 'Dividendes reçus', 'Intérêts reçus',
                   'Variation des concours bancaires', 'Variation des placements',
                   'Variation des autres éléments de trésorerie'],
        '2021': [480000, 115000, 22000, 75000, 40000, 55000, 28000, 14000, 18000,
                170000, 42000, 32000, 11000, 7000, 52000, 14000, 11000, 7000,
                115000, 42000, 14000, 22000, 7000, 11000, 5500, 14000, 7000, 11000,
                17000, 14000, 7000, 11000, 9000, 7000, 11000, 5500,
                7000, 14000, 11000, 17000, 9000, 14000, 11000, 7000, 5500, 3500,
                22000, 14000, 7000, 11000, 32000, 42000, 14000, 11000,
                17000, 7000, 5500, 3500, 2500, 1500, 1000, 11000, 7000,
                14000, 11000, 17000, 14000, 32000, 22000, 14000, 11000, 32000],
        '2022': [530000, 125000, 25000, 80000, 45000, 60000, 30000, 15000, 20000,
                180000, 45000, 35000, 12000, 8000, 55000, 15000, 12000, 8000,
                120000, 45000, 15000, 25000, 8000, 12000, 6000, 15000, 8000, 12000,
                18000, 15000, 8000, 12000, 10000, 8000, 12000, 6000,
                8000, 15000, 12000, 18000, 10000, 15000, 12000, 8000, 6000, 4000,
                25000, 15000, 8000, 12000, 35000, 45000, 15000, 12000,
                18000, 8000, 6000, 4000, 3000, 2000, 1500, 12000, 8000,
                15000, 12000, 18000, 15000, 35000, 25000, 15000, 12000, 35000],
        '2023': [580000, 135000, 28000, 85000, 48000, 65000, 32000, 16000, 22000,
                190000, 48000, 38000, 13000, 8500, 58000, 16000, 13000, 8500,
                125000, 48000, 16000, 27000, 8500, 13000, 6500, 16000, 8500, 13000,
                19000, 16000, 8500, 13000, 11000, 8500, 13000, 6500,
                8500, 16000, 13000, 19000, 11000, 16000, 13000, 8500, 6500, 4500,
                27000, 16000, 8500, 13000, 42000, 48000, 16000, 13000,
                19000, 8500, 6500, 4500, 3500, 2500, 1800, 13000, 8500,
                16000, 13000, 19000, 16000, 42000, 27000, 16000, 13000, 42000]
    }
    
    df = pd.DataFrame(data)
    return df

def formater_fichier_excel(nom_fichier, df, titre):
    """Formate le fichier Excel avec mise en page professionnelle"""
    with pd.ExcelWriter(nom_fichier, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=titre, index=False)
        
        # Accéder au workbook et worksheet
        workbook = writer.book
        worksheet = writer.sheets[titre]
        
        # Définir les styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        center_alignment = Alignment(horizontal='center', vertical='center')
        
        # Formater l'en-tête
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
        
        # Ajuster la largeur des colonnes
        column_widths = {
            'A': 10,  # compte
            'B': 40,  # libellé
            'C': 15,  # 2021
            'D': 15,  # 2022
            'E': 15   # 2023
        }
        
        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width
        
        # Formater les nombres avec séparateurs de milliers
        for row in range(2, worksheet.max_row + 1):
            for col in ['C', 'D', 'E']:
                cell = worksheet[f'{col}{row}']
                try:
                    value = float(cell.value)
                    cell.number_format = '#,##0'
                except (ValueError, TypeError):
                    pass

def generer_fichiers_excel():
    """Génère les trois fichiers Excel demandés"""
    try:
        # Créer les dataframes
        bilan_df = creer_bilan()
        compte_resultat_df = creer_compte_resultat()
        flux_tresorerie_df = creer_flux_tresorerie()
        
        # Générer les fichiers Excel
        formater_fichier_excel('bilan_entreprise_2021_2023.xlsx', bilan_df, 'Bilan')
        formater_fichier_excel('compte_resultat_entreprise_2021_2023.xlsx', compte_resultat_df, 'Compte de Resultat')
        formater_fichier_excel('flux_tresorerie_entreprise_2021_2023.xlsx', flux_tresorerie_df, 'Flux de Tresorerie')
        
        print("✅ Les trois fichiers Excel ont été générés avec succès:")
        print("   - bilan_entreprise_2021_2023.xlsx")
        print("   - compte_resultat_entreprise_2021_2023.xlsx")
        print("   - flux_tresorerie_entreprise_2021_2023.xlsx")
        
        # Afficher un aperçu des données
        print("\n📊 Aperçu du bilan:")
        print(bilan_df.head())
        print("\n📊 Aperçu du compte de résultat:")
        print(compte_resultat_df.head())
        print("\n📊 Aperçu du tableau de flux de trésorerie:")
        print(flux_tresorerie_df.head())
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération des fichiers: {e}")

# Exécuter le programme
if __name__ == "__main__":
    generer_fichiers_excel()