
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os
import warnings
from datetime import datetime
import io
import sys
from pathlib import Path

# Configuration des warnings
warnings.filterwarnings('ignore')

# Ajout du chemin pour les imports locaux
sys.path.append(str(Path(__file__).parent))

# Import des modules personnalisés
try:
    from financial_processor import FinancialDataProcessor
    from financial_analyzer import FinancialAnalyzer
    from scoring_cobac import ScoringSystemCOBAC
    from regulations_cobac import (
        REGLEMENTATION_COBAC, 
        get_cobac_requirements, 
        get_provision_taux,
        check_seuils_conformite
    )
except ImportError as e:
    st.error(f"❌ Erreur d'importation des modules personnalisés: {e}")
    st.info("""
    Vérifiez que tous les fichiers suivants sont présents :
    - financial_processor.py
    - financial_analyzer.py  
    - scoring_cobac.py
    - regulations_cobac.py
    """)
    st.stop()

# Configuration de la page
st.set_page_config(
    page_title="Analyse Risque Crédit COBAC - IA",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour l'application COBAC
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .cobac-header {
        background: linear-gradient(135deg, #1f77b4, #ff7f0e);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .risk-high {
        background-color: #ffcccc;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 6px solid #ff0000;
        margin-bottom: 1rem;
    }
    .risk-low {
        background-color: #ccffcc;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 6px solid #00cc00;
        margin-bottom: 1rem;
    }
    .risk-moderate {
        background-color: #fff4cc;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 6px solid #ffcc00;
        margin-bottom: 1rem;
    }
    .section-header {
        color: #1f77b4;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .cobac-alert {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .conforme {
        color: #28a745;
        font-weight: bold;
    }
    .non-conforme {
        color: #dc3545;
        font-weight: bold;
    }
    .score-A { background-color: #d4edda; color: #155724; }
    .score-B { background-color: #cce7ff; color: #004085; }
    .score-C { background-color: #fff3cd; color: #856404; }
    .score-D { background-color: #f8d7da; color: #721c24; }
    .score-E { background-color: #f5c6cb; color: #721c24; }
</style>
""", unsafe_allow_html=True)

def main():
    """Fonction principale de l'application"""
    
    # Header principal avec logo COBAC
    st.markdown("""
    <div class="cobac-header">
        <h1 class="main-header">🏛️ Analyse du Risque de Crédit - COBAC/CEMAC</h1>
        <p style='font-size: 1.2rem; margin-bottom: 0;'>
            Application conforme à la réglementation bancaire de la CEMAC - R-2015/01 à R-2015/12
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar - Upload des fichiers avec section COBAC
    with st.sidebar:
        st.header("📁 Import des États Financiers")
        st.markdown("---")
        
        # Informations entreprise
        entreprise_nom = st.text_input("**Nom de l'entreprise**", "Entreprise ABC")
        entreprise_secteur = st.selectbox(
            "**Secteur d'activité**",
            ["Commerce", "Industrie", "Services", "BTP", "Agriculture", "Autre"]
        )
        entreprise_taille = st.selectbox(
            "**Taille de l'entreprise**",
            ["TPE", "PME", "ETI", "GE"]
        )
        
        st.subheader("📊 Fichiers financiers requis:")
        
        bilan_file = st.file_uploader(
            "**Bilan Comptable**", 
            type=['xlsx', 'xls'], 
            key='bilan',
            help="Fichier Excel contenant le bilan actif/passif selon plan comptable COBAC"
        )
        
        cpc_file = st.file_uploader(
            "**Compte de Résultat**", 
            type=['xlsx', 'xls'], 
            key='cpc',
            help="Fichier Excel contenant le compte de résultat produits/charges"
        )
        
        flux_file = st.file_uploader(
            "**Flux de Trésorerie** (Optionnel)", 
            type=['xlsx', 'xls'], 
            key='flux',
            help="Fichier Excel contenant le tableau des flux de trésorerie"
        )
        
        st.markdown("---")
        st.subheader("⚙️ Paramètres COBAC")
        
        n_years_analysis = st.slider(
            "**Nombre d'années d'analyse**", 
            min_value=1, 
            max_value=5, 
            value=3,
            help="Période d'analyse des états financiers"
        )
        
        confidence_threshold = st.slider(
            "**Seuil d'alerte risque**", 
            min_value=0.5, 
            max_value=0.95, 
            value=0.7,
            help="Seuil de probabilité pour déclencher les alertes COBAC"
        )
        
        montant_pret_reference = st.number_input(
            "**Montant prêt de référence (€)**",
            min_value=0,
            value=100000,
            help="Montant utilisé pour le calcul du provisionnement COBAC"
        )
        
        st.markdown("---")
        
        # Informations réglementaires COBAC
        with st.expander("📋 Références COBAC"):
            st.markdown("""
            **Règlementation applicable:**
            - R-2015/03 : Ratio de solvabilité
            - R-2015/04 : Risque de crédit et provisionnement  
            - R-2015/06 : Gestion des risques
            - R-2015/08 : Liquidité
            """)

    # Traitement principal
    if bilan_file and cpc_file:
        try:
            # Initialisation des modules COBAC
            with st.spinner('🔄 Initialisation des modules d\'analyse COBAC...'):
                processor = FinancialDataProcessor()
                analyzer = FinancialAnalyzer()
                scoring_system = ScoringSystemCOBAC()

            # Chargement et traitement des données
            with st.spinner('📊 Traitement des données financières selon normes COBAC...'):
                df_consolide = processor.load_excel_data(bilan_file, cpc_file, flux_file)
                
                # Vérification des données chargées
                if df_consolide.empty:
                    st.error("❌ Aucune donnée valide n'a pu être chargée depuis les fichiers.")
                    return
                
                # Calcul des indicateurs COBAC
                sig_results = analyzer.calculate_soldes_intermediaires(df_consolide)
                ratios_results = analyzer.calculate_financial_ratios(df_consolide)
                working_capital_results = analyzer.calculate_working_capital_indicators(df_consolide)
                
                # Scoring COBAC
                score_cobac = scoring_system.calculer_score_global(
                    sig_results, ratios_results, working_capital_results
                )
                
                # Préparation pour la prédiction IA
                prediction_features = processor.prepare_prediction_features(
                    df_consolide, sig_results, ratios_results, working_capital_results
                )

            st.success(f"✅ **Analyse COBAC terminée pour {entreprise_nom}**")
            
            # Métriques rapides COBAC
            display_quick_metrics_cobac(sig_results, ratios_results, working_capital_results, score_cobac)
            
            # Onglets principaux avec analyse COBAC
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "🏠 Tableau de Bord", 
                "💰 Soldes Intermédiaires", 
                "📊 Ratios Financiers",
                "🔄 Analyse BFR/FR/TN", 
                "🏛️ Scoring COBAC",
                "🎯 Prédiction Risque",
                "📋 Données Brutes"
            ])
            
            with tab1:
                display_dashboard_overview(
                    df_consolide, sig_results, ratios_results, 
                    working_capital_results, score_cobac, entreprise_nom
                )
            
            with tab2:
                display_soldes_intermediaires(sig_results)
            
            with tab3:
                display_ratios_financiers_cobac(ratios_results)
            
            with tab4:
                display_working_capital_analysis(working_capital_results, score_cobac)
            
            with tab5:
                display_scoring_cobac(
                    score_cobac, scoring_system, montant_pret_reference,
                    sig_results, ratios_results, working_capital_results
                )
            
            with tab6:
                display_risk_prediction_cobac(
                    processor, prediction_features, confidence_threshold, 
                    entreprise_nom, score_cobac, montant_pret_reference
                )
            
            with tab7:
                display_raw_data_cobac(
                    df_consolide, sig_results, ratios_results, 
                    working_capital_results, score_cobac
                )
                
        except Exception as e:
            st.error(f"❌ Erreur lors du traitement COBAC : {str(e)}")
            st.info("""
            **Vérifiez :**
            - Le format des fichiers Excel
            - La conformité au plan comptable COBAC
            - La présence des comptes requis
            """)
    
    else:
        display_welcome_message_cobac()

def display_quick_metrics_cobac(sig_results, ratios_results, working_capital_results, score_cobac):
    """Affiche les métriques rapides COBAC en haut de page"""
    if not sig_results or not score_cobac:
        return
    
    last_year = max(sig_results.keys())
    current_data = working_capital_results.get(last_year, {})
    
    st.markdown("---")
    st.subheader("📊 Indicateurs Clés COBAC")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        # Score COBAC
        categorie = score_cobac['categorie']
        couleur_classe = f"score-{categorie}"
        st.markdown(f"<div class='{couleur_classe}' style='padding: 1rem; border-radius: 10px; text-align: center;'>", unsafe_allow_html=True)
        st.metric("Score COBAC", f"{score_cobac['score_total']}/100")
        st.write(f"Catégorie {categorie}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        if last_year in sig_results:
            ca = sig_results[last_year].get('chiffre_affaires', 0)
            st.metric("Chiffre d'affaires", f"{ca:,.0f} €")
    
    with col3:
        if last_year in sig_results:
            ebe = sig_results[last_year].get('ebe', 0)
            st.metric("EBE", f"{ebe:,.0f} €")
    
    with col4:
        if last_year in ratios_results:
            rentabilite = ratios_results[last_year].get('rentabilite_nette', '0%')
            st.metric("Rentabilité nette", rentabilite)
    
    with col5:
        tn = current_data.get('tn', 0)
        statut_tn = "✅" if tn > 0 else "❌"
        st.metric("Trésorerie Nette", f"{tn:,.0f} €")
        st.write(f"{statut_tn} {'Positive' if tn > 0 else 'Négative'}")
    
    st.markdown("---")

def display_dashboard_overview(df_consolide, sig_results, ratios_results, working_capital_results, score_cobac, entreprise_nom):
    """Onglet Tableau de Bord COBAC"""
    st.header(f"🏠 Tableau de Bord - {entreprise_nom}")
    
    if not sig_results or not score_cobac:
        st.info("Aucune donnée disponible pour le tableau de bord")
        return
    
    # Alertes COBAC immédiates
    display_cobac_alerts(score_cobac, ratios_results, working_capital_results)
    
    # Graphiques principaux
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Évolution du Chiffre d'Affaires et EBE")
        fig_ca_ebe = create_ca_ebe_chart(sig_results)
        st.plotly_chart(fig_ca_ebe, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Score COBAC et Rentabilité")
        fig_score_rentabilite = create_score_rentabilite_chart(score_cobac, ratios_results)
        st.plotly_chart(fig_score_rentabilite, use_container_width=True)
    
    # Indicateurs de conformité
    st.subheader("✅ Conformité Réglementaire COBAC")
    display_conformite_table(score_cobac, ratios_results)

def display_cobac_alerts(score_cobac, ratios_results, working_capital_results):
    """Affiche les alertes COBAC"""
    dernier_annee = max(ratios_results.keys()) if ratios_results else None
    if not dernier_annee:
        return
    
    alertes = []
    
    # Alerte score COBAC
    if score_cobac['categorie'] in ['D', 'E']:
        alertes.append(("🔴", "Score COBAC critique", f"Catégorie {score_cobac['categorie']} - Surveillance renforcée requise"))
    
    # Alertes ratios
    conformite = score_cobac.get('conformite_cobac', {})
    if not conformite.get('rentabilite', True):
        alertes.append(("🟡", "Rentabilité faible", "En dessous du seuil COBAC de 3%"))
    
    if not conformite.get('liquidite', True):
        alertes.append(("🟡", "Liquidité insuffisante", "Ratio de liquidité inférieur à 1"))
    
    if not conformite.get('endettement', True):
        alertes.append(("🟡", "Endettement élevé", "Ratio d'endettement supérieur à 200%"))
    
    # Alerte trésorerie
    if dernier_annee in working_capital_results:
        if working_capital_results[dernier_annee]['tn'] < 0:
            alertes.append(("🔴", "Trésorerie négative", "Risque de liquidité à court terme"))
    
    if alertes:
        st.subheader("🚨 Alertes COBAC")
        for icone, titre, description in alertes:
            st.markdown(f"""
            <div class="cobac-alert">
                <strong>{icone} {titre}</strong><br>
                {description}
            </div>
            """, unsafe_allow_html=True)

def display_conformite_table(score_cobac, ratios_results):
    """Affiche le tableau de conformité COBAC"""
    dernier_annee = max(ratios_results.keys()) if ratios_results else None
    if not dernier_annee:
        return
    
    conformite = score_cobac.get('conformite_cobac', {})
    ratios = ratios_results[dernier_annee]
    
    data = {
        'Critère': ['Rentabilité nette', 'Ratio d\'endettement', 'Ratio de liquidité', 'Ratio d\'autonomie', 'Conformité globale'],
        'Valeur': [
            ratios['rentabilite_nette'],
            ratios['ratio_endettement'],
            ratios['ratio_liquidite'], 
            ratios['ratio_autonomie'],
            'CONFORME' if conformite.get('global', False) else 'NON CONFORME'
        ],
        'Seuil COBAC': ['≥ 3%', '≤ 200%', '≥ 100%', '≥ 20%', 'Tous critères'],
        'Statut': [
            '✅' if conformite.get('rentabilite', False) else '❌',
            '✅' if conformite.get('endettement', False) else '❌', 
            '✅' if conformite.get('liquidite', False) else '❌',
            '✅' if conformite.get('autonomie', False) else '❌',
            '✅' if conformite.get('global', False) else '❌'
        ]
    }
    
    df_conformite = pd.DataFrame(data)
    st.dataframe(df_conformite, use_container_width=True)

def display_soldes_intermediaires(sig_results):
    """Onglet Soldes Intermédiaires de Gestion"""
    st.header("💰 Soldes Intermédiaires de Gestion COBAC")
    
    if not sig_results:
        st.info("Aucune donnée disponible pour les soldes intermédiaires")
        return
    
    # Tableau des SIG
    sig_df = pd.DataFrame(sig_results).T
    sig_df_formatted = sig_df.applymap(lambda x: f"{x:,.0f} €" if isinstance(x, (int, float)) else x)
    
    st.dataframe(sig_df_formatted, use_container_width=True)
    
    # Graphique en cascade
    st.subheader("📊 Construction du résultat")
    if len(sig_results) > 0:
        last_year = max(sig_results.keys())
        fig_waterfall = create_waterfall_chart(sig_results[last_year], last_year)
        st.plotly_chart(fig_waterfall, use_container_width=True)
    
    # Évolution des SIG
    st.subheader("📈 Évolution des principaux soldes")
    fig_evolution = create_sig_evolution_chart(sig_results)
    st.plotly_chart(fig_evolution, use_container_width=True)

def display_ratios_financiers_cobac(ratios_results):
    """Onglet Ratios Financiers COBAC"""
    st.header("📊 Analyse des Ratios Financiers COBAC")
    
    if not ratios_results:
        st.info("Aucune donnée disponible pour les ratios financiers")
        return
    
    # Tableau des ratios
    ratios_df = pd.DataFrame(ratios_results).T
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Ratios de Rentabilité et Structure")
        rentability_data = {
            'Année': list(ratios_results.keys()),
            'Rentabilité Nette': [r['rentabilite_nette'] for r in ratios_results.values()],
            'Capacité Remboursement': [r['capacite_remboursement'] for r in ratios_results.values()],
            'EBE (k€)': [f"{r['ebe']/1000:,.0f}" for r in ratios_results.values()]
        }
        st.dataframe(pd.DataFrame(rentability_data), use_container_width=True)
        
        # Graphique de rentabilité
        fig_rent = create_rentability_detail_chart(ratios_results)
        st.plotly_chart(fig_rent, use_container_width=True)
    
    with col2:
        st.subheader("🏗️ Ratios de Structure COBAC")
        structure_data = {
            'Année': list(ratios_results.keys()),
            'Endettement': [r['ratio_endettement'] for r in ratios_results.values()],
            'Autonomie': [r['ratio_autonomie'] for r in ratios_results.values()],
            'Liquidité': [r['ratio_liquidite'] for r in ratios_results.values()]
        }
        st.dataframe(pd.DataFrame(structure_data), use_container_width=True)
        
        # Radar chart des ratios
        if len(ratios_results) > 0:
            last_year = max(ratios_results.keys())
            fig_radar = create_radar_chart(ratios_results[last_year], last_year)
            st.plotly_chart(fig_radar, use_container_width=True)

def display_working_capital_analysis(working_capital_results, score_cobac):
    """Onglet Analyse BFR/FR/TN"""
    st.header("🔄 Analyse du Fonds de Roulement COBAC")
    
    if not working_capital_results:
        st.info("Données insuffisantes pour calculer le fonds de roulement")
        return
    
    # Métriques principales
    last_year = max(working_capital_results.keys())
    current_data = working_capital_results[last_year]
    
    st.subheader("💰 Indicateurs de Trésorerie")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        caf = current_data['caf']
        statut_caf = "✅" if caf > 0 else "❌"
        st.metric("CAF", f"{caf:,.0f} €")
        st.write(f"{statut_caf} {'Positive' if caf > 0 else 'Négative'}")
    
    with col2:
        bfr = current_data['bfr']
        st.metric("BFR", f"{bfr:,.0f} €")
    
    with col3:
        fr = current_data['fr']
        statut_fr = "✅" if fr > 0 else "❌"
        st.metric("FR", f"{fr:,.0f} €")
        st.write(f"{statut_fr} {'Positif' if fr > 0 else 'Négatif'}")
    
    with col4:
        tn = current_data['tn']
        statut_tn = "✅" if tn > 0 else "❌"
        st.metric("TN", f"{tn:,.0f} €")
        st.write(f"{statut_tn} {'Positive' if tn > 0 else 'Négative'}")
    
    # Équilibre financier
    st.subheader("⚖️ Équilibre Financier")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**FR - BFR = TN**\n\n{fr:,.0f} - {bfr:,.0f} = {tn:,.0f} €")
        if fr > 0 and tn > 0:
            st.success("✅ Structure financière équilibrée")
        elif fr > 0 and tn < 0:
            st.warning("⚠️ BFR trop élevé par rapport au FR")
        else:
            st.error("❌ Déséquilibre structurel")
    
    with col2:
        # Graphique des composants
        fig_composants = create_working_capital_components_chart(current_data)
        st.plotly_chart(fig_composants, use_container_width=True)
    
    # Tableau d'évolution
    st.subheader("📈 Évolution des indicateurs")
    evolution_data = []
    for year in sorted(working_capital_results.keys()):
        data = working_capital_results[year]
        evolution_data.append({
            'Année': year,
            'CAF (k€)': f"{data['caf']/1000:.0f}",
            'BFR (k€)': f"{data['bfr']/1000:.0f}",
            'FR (k€)': f"{data['fr']/1000:.0f}",
            'TN (k€)': f"{data['tn']/1000:.0f}"
        })
    
    evolution_df = pd.DataFrame(evolution_data)
    st.dataframe(evolution_df, use_container_width=True)

def display_scoring_cobac(score_cobac, scoring_system, montant_pret, sig_results, ratios_results, working_capital_results):
    """Onglet Scoring COBAC"""
    st.header("🏛️ Scoring COBAC - Analyse Réglementaire")
    
    if not score_cobac:
        st.info("Score COBAC non disponible")
        return
    
    # Affichage du score principal
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        categorie = score_cobac['categorie']
        couleur = score_cobac['couleur_categorie']
        st.markdown(f"<h2 style='color: {couleur};'>Catégorie {categorie}</h2>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color: {couleur};'>{score_cobac['libelle_categorie']}</h3>", unsafe_allow_html=True)
    
    with col2:
        st.metric("Score Global", f"{score_cobac['score_total']}/100")
    
    with col3:
        # Jauge COBAC
        fig_gauge = create_cobac_gauge(score_cobac['score_total'])
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Détail des scores
    st.subheader("📋 Détail du Scoring COBAC")
    scores_details = score_cobac['scores_detailles']
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Rentabilité", f"{scores_details['rentabilite']}/25")
    col2.metric("Structure", f"{scores_details['structure']}/25")
    col3.metric("Liquidité", f"{scores_details['liquidite']}/20")
    col4.metric("Trésorerie", f"{scores_details['tresorerie']}/15")
    col5.metric("Croissance", f"{scores_details['croissance']}/15")
    
    # Graphique détaillé
    fig_details = create_scoring_details_chart(scores_details)
    st.plotly_chart(fig_details, use_container_width=True)
    
    # Provisionnement COBAC
    st.subheader("💰 Provisionnement COBAC")
    provisionnement = scoring_system.calculer_provisionnement(montant_pret, categorie)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Montant prêt", f"{provisionnement['montant_pret']:,.0f} €")
    col2.metric("Catégorie", categorie)
    col3.metric("Taux provision", f"{provisionnement['taux_provision']:.0%}")
    col4.metric("Provision requise", f"{provisionnement['provision_requise']:,.0f} €")
    
    # Recommandations COBAC
    st.subheader("💡 Recommandations COBAC")
    display_cobac_recommendations(score_cobac, provisionnement)

def display_cobac_recommendations(score_cobac, provisionnement):
    """Affiche les recommandations COBAC"""
    categorie = score_cobac['categorie']
    recommandations = []
    
    if categorie in ['A', 'B']:
        recommandations.append("✅ **Dossier de bonne qualité** - Procédure standard applicable")
        recommandations.append("📊 **Surveillance normale** - Revue annuelle suffisante")
        recommandations.append("💳 **Conditions favorables** - Taux préférentiels possibles")
    
    elif categorie == 'C':
        recommandations.append("⚠️ **Surveillance renforcée** - Revue semestrielle recommandée")
        recommandations.append("📝 **Analyse approfondie** - Vérifier la pérennité du business model")
        recommandations.append("🔍 **Garanties complémentaires** - Exiger des garanties additionnelles")
    
    elif categorie in ['D', 'E']:
        recommandations.append("🔴 **Dossier à risque** - Comité de crédit obligatoire")
        recommandations.append("🚨 **Surveillance étroite** - Revue trimestrielle requise")
        recommandations.append("💸 **Provisionnement élevé** - Considérer le rejet de la demande")
        recommandations.append("📉 **Restructuration** - Envisager une restructuration de dette")
    
    for reco in recommandations:
        st.markdown(f"- {reco}")
    
    # Information provisionnement
    st.info(f"""
    **Information provisionnement COBAC (R-2015/04):**
    - Catégorie {categorie} : Taux de {provisionnement['taux_provision']:.0%}
    - Provision requise : {provisionnement['provision_requise']:,.0f} €
    - Montant net après provision : {provisionnement['montant_net']:,.0f} €
    """)

def display_risk_prediction_cobac(processor, prediction_features, confidence_threshold, entreprise_nom, score_cobac, montant_pret):
    """Onglet Prédiction du Risque COBAC"""
    st.header("🎯 Prédiction du Risque de Crédit - IA COBAC")
    
    # Integration du scoring COBAC avec la prédiction IA
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏛️ Scoring COBAC")
        if score_cobac:
            categorie = score_cobac['categorie']
            st.metric("Catégorie COBAC", f"{categorie} - {score_cobac['libelle_categorie']}")
            st.metric("Score COBAC", f"{score_cobac['score_total']}/100")
    
    with col2:
        st.subheader("🤖 Prédiction IA")
        if processor.model is not None and prediction_features is not None:
            try:
                prediction, probability, feature_importance = processor.predict_risk(prediction_features)
                
                if prediction is not None:
                    # Jauge risque IA
                    fig_ia_gauge = create_risk_gauge(probability)
                    st.plotly_chart(fig_ia_gauge, use_container_width=True)
                    
                    st.metric("Probabilité défaut", f"{probability:.1%}")
                else:
                    st.warning("Prédiction IA non disponible")
            except Exception as e:
                st.warning(f"Prédiction IA temporairement indisponible: {e}")
        else:
            st.info("Modèle IA non chargé")
    
    # Analyse consolidée
    st.subheader("🔍 Analyse Consolidée Risque")
    
    if score_cobac and processor.model is not None and prediction_features is not None:
        try:
            prediction, probability, _ = processor.predict_risk(prediction_features)
            
            # Décision consolidée
            if score_cobac['categorie'] in ['A', 'B'] and probability < 0.3:
                st.success("""
                ## ✅ RECOMMANDATION : ACCORD
                
                **Justification :**
                - Score COBAC favorable (Catégorie A/B)
                - Probabilité de défaut faible
                - Conformité réglementaire respectée
                """)
            elif score_cobac['categorie'] in ['C'] or (probability >= 0.3 and probability < 0.7):
                st.warning("""
                ## ⚠️ RECOMMANDATION : MIXTE
                
                **Conditions :**
                - Surveillance renforcée
                - Garanties supplémentaires
                - Taux d'intérêt majoré
                - Durée réduite
                """)
            else:
                st.error("""
                ## 🔴 RECOMMANDATION : REFUS
                
                **Motifs :**
                - Score COBAC défavorable (Catégorie D/E)
                - Probabilité de défaut élevée
                - Non-conformité réglementaire
                """)
                
        except Exception as e:
            st.warning(f"Analyse consolidée temporairement indisponible: {e}")

def display_raw_data_cobac(df_consolide, sig_results, ratios_results, working_capital_results, score_cobac):
    """Onglet Données Brutes COBAC"""
    st.header("📋 Données Brutes et Export COBAC")
    
    st.subheader("📊 Données consolidées")
    st.dataframe(df_consolide, use_container_width=True)
    
    # Export des données COBAC
    st.subheader("💾 Export des résultats COBAC")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Exporter données consolidées"):
            csv = df_consolide.to_csv(index=False)
            st.download_button(
                label="Télécharger CSV",
                data=csv,
                file_name="donnees_consolidees_cobac.csv",
                mime="text/csv"
            )
    
    with col2:
        if sig_results:
            sig_df = pd.DataFrame(sig_results).T
            csv_sig = sig_df.to_csv()
            st.download_button(
                label="📥 Exporter SIG",
                data=csv_sig,
                file_name="soldes_intermediaires_cobac.csv",
                mime="text/csv"
            )
    
    with col3:
        if score_cobac:
            # Créer un rapport COBAC
            rapport_cobac = generate_rapport_cobac(score_cobac, sig_results, ratios_results)
            st.download_button(
                label="📄 Rapport COBAC",
                data=rapport_cobac,
                file_name=f"rapport_cobac_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    
    # Statistiques descriptives
    st.subheader("📈 Statistiques descriptives")
    if not df_consolide.empty:
        st.dataframe(df_consolide['amount'].describe(), use_container_width=True)

def display_welcome_message_cobac():
    """Message d'accueil COBAC"""
    st.markdown("""
    <div style='text-align: center; padding: 4rem;'>
        <h2>🏛️ Bienvenue dans l'analyseur de risque de crédit COBAC</h2>
        <p style='font-size: 1.2rem; margin-bottom: 2rem;'>
            Application conforme à la réglementation bancaire de la CEMAC
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h3>📊 Bilan COBAC</h3>
            <p>Actif et passif selon plan comptable CEMAC</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h3>💰 Compte de résultat</h3>
            <p>Produits et charges normalisés</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h3>🏛️ Scoring COBAC</h3>
            <p>Analyse réglementaire intégrée</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.info("""
    **📋 Format des fichiers attendu (COBAC) :**
    - Fichiers Excel (.xlsx ou .xls)
    - Colonnes : compte, libellé, 2021, 2022, 2023...
    - Plan comptable général CEMAC
    - Montants en euros
    - Comptes normalisés selon directives COBAC
    """)

# =============================================================================
# FONCTIONS DE CRÉATION DE GRAPHIQUES
# =============================================================================

def create_ca_ebe_chart(sig_results):
    """Crée un graphique CA et EBE"""
    years = sorted(sig_results.keys())
    ca_values = [sig_results[y].get('chiffre_affaires', 0) for y in years]
    ebe_values = [sig_results[y].get('ebe', 0) for y in years]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Chiffre d\'affaires', x=years, y=ca_values, marker_color='blue'))
    fig.add_trace(go.Bar(name='EBE', x=years, y=ebe_values, marker_color='green'))
    
    fig.update_layout(
        title="Évolution du CA et de l'EBE",
        barmode='group',
        height=400
    )
    return fig

def create_score_rentabilite_chart(score_cobac, ratios_results):
    """Crée un graphique combiné score et rentabilité"""
    if not ratios_results:
        return go.Figure()
    
    years = sorted(ratios_results.keys())
    rentability_values = [float(r['rentabilite_nette'].replace('%', '')) for r in ratios_results.values()]
    
    fig = go.Figure()
    
    # Score COBAC (ligne)
    fig.add_trace(go.Scatter(
        x=years, y=[score_cobac['score_total']] * len(years),
        mode='lines',
        name='Score COBAC',
        line=dict(color='purple', width=4, dash='dash')
    ))
    
    # Rentabilité (barres)
    fig.add_trace(go.Bar(
        x=years, y=rentability_values,
        name='Rentabilité nette (%)',
        marker_color=['green' if x >= 3 else 'red' for x in rentability_values]
    ))
    
    fig.update_layout(
        title="Score COBAC vs Rentabilité",
        barmode='overlay',
        height=400
    )
    
    return fig

def create_waterfall_chart(sig_data, year):
    """Crée un graphique en cascade pour les SIG"""
    labels = ['Chiffre d\'affaires', 'Marge commerciale', 'Valeur ajoutée', 'EBE', 'Résultat net']
    values = [
        sig_data.get('chiffre_affaires', 0),
        sig_data.get('marge_commerciale', 0),
        sig_data.get('valeur_ajoutee', 0),
        sig_data.get('ebe', 0),
        sig_data.get('resultat_net', 0)
    ]
    
    fig = go.Figure(go.Waterfall(
        name="SIG",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=labels,
        y=values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title=f"Construction du résultat {year}",
        showlegend=False,
        height=400
    )
    
    return fig

def create_sig_evolution_chart(sig_results):
    """Crée un graphique d'évolution des SIG"""
    years = sorted(sig_results.keys())
    
    fig = go.Figure()
    
    sig_to_plot = ['chiffre_affaires', 'marge_commerciale', 'valeur_ajoutee', 'ebe', 'resultat_net']
    colors = ['blue', 'green', 'orange', 'red', 'purple']
    
    for sig, color in zip(sig_to_plot, colors):
        values = [sig_results[y].get(sig, 0) for y in years]
        fig.add_trace(go.Scatter(
            x=years, y=values, 
            name=sig.replace('_', ' ').title(),
            line=dict(color=color)
        ))
    
    fig.update_layout(
        title="Évolution des soldes intermédiaires",
        height=400
    )
    return fig

def create_rentability_detail_chart(ratios_results):
    """Crée un graphique détaillé de rentabilité"""
    years = sorted(ratios_results.keys())
    rentability_values = [float(r['rentabilite_nette'].replace('%', '')) for r in ratios_results.values()]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, 
        y=rentability_values,
        marker_color=['green' if x >= 3 else 'red' for x in rentability_values]
    ))
    
    # Ligne de seuil COBAC
    fig.add_hline(y=3, line_dash="dash", line_color="red", annotation_text="Seuil COBAC 3%")
    
    fig.update_layout(
        title="Rentabilité nette vs Seuil COBAC",
        yaxis_title="Rentabilité nette (%)",
        height=300
    )
    return fig

def create_radar_chart(ratio_data, year):
    """Crée un radar chart pour les ratios"""
    categories = ['Rentabilité', 'Endettement', 'Liquidité', 'Autonomie']
    
    # Normalisation des valeurs
    rentability = min(float(ratio_data['rentabilite_nette'].replace('%', '')) / 20, 1)  # Max 20%
    endettement = 1 - min(float(ratio_data['ratio_endettement']) / 3, 1)  # Inverse, max 300%
    liquidite = min(float(ratio_data['ratio_liquidite']) / 2, 1)  # Max 200%
    autonomie = float(ratio_data['ratio_autonomie'].replace('%', '')) / 100  # Max 100%
    
    values = [rentability, endettement, liquidite, autonomie]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],  # Fermer le cercle
        theta=categories + [categories[0]],
        fill='toself',
        name=f"Ratios {year}"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=False,
        title=f"Profil des ratios {year}",
        height=300
    )
    
    return fig

def create_working_capital_components_chart(current_data):
    """Crée un graphique des composants du fonds de roulement"""
    labels = ['Capitaux Permanents', 'Actif Immobilisé', 'FR', 'BFR', 'TN']
    values = [
        current_data['capitaux_permanents'],
        current_data['actif_immobilise'],
        current_data['fr'],
        current_data['bfr'],
        current_data['tn']
    ]
    
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    fig = go.Figure(data=[go.Bar(
        x=labels, y=values,
        marker_color=colors
    )])
    
    fig.update_layout(
        title="Composition du fonds de roulement",
        height=300
    )
    
    return fig

def create_cobac_gauge(score):
    """Crée une jauge COBAC"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Score COBAC"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "red"},
                {'range': [30, 40], 'color': "orange"},
                {'range': [40, 50], 'color': "yellow"},
                {'range': [50, 60], 'color': "lightgreen"},
                {'range': [60, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    fig.update_layout(height=250)
    return fig

def create_scoring_details_chart(scores_details):
    """Crée un graphique détaillé du scoring"""
    categories = list(scores_details.keys())
    values = list(scores_details.values())
    max_scores = [25, 25, 20, 15, 15]  # Scores maximaux par catégorie
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Score obtenu',
        x=categories,
        y=values,
        marker_color='blue'
    ))
    
    fig.add_trace(go.Bar(
        name='Score maximal',
        x=categories,
        y=max_scores,
        marker_color='lightgray',
        opacity=0.3
    ))
    
    fig.update_layout(
        title="Détail du scoring COBAC",
        barmode='overlay',
        height=400
    )
    
    return fig

def create_risk_gauge(probability):
    """Crée une jauge de risque IA"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = probability * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Risque Défaut IA"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 20], 'color': "green"},
                {'range': [20, 50], 'color': "yellow"},
                {'range': [50, 100], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': probability * 100
            }
        }
    ))
    fig.update_layout(height=250)
    return fig

def generate_rapport_cobac(score_cobac, sig_results, ratios_results):
    """Génère un rapport COBAC textuel"""
    dernier_annee = max(sig_results.keys()) if sig_results else "N/A"
    
    rapport = f"""
    RAPPORT D'ANALYSE COBAC
    ======================
    Date: {datetime.now().strftime('%d/%m/%Y')}
    
    SCORING COBAC
    -------------
    Score Global: {score_cobac['score_total']}/100
    Catégorie: {score_cobac['categorie']}
    Appréciation: {score_cobac['libelle_categorie']}
    
    DÉTAIL DU SCORING
    -----------------
    """
    
    for critere, score in score_cobac['scores_detailles'].items():
        rapport += f"- {critere.capitalize()}: {score} points\n"
    
    rapport += f"""
    CONFORMITÉ RÉGLEMENTAIRE
    ------------------------
    """
    
    conformite = score_cobac.get('conformite_cobac', {})
    for critere, statut in conformite.items():
        if critere != 'global':
            statut_text = "CONFORME" if statut else "NON CONFORME"
            rapport += f"- {critere.capitalize()}: {statut_text}\n"
    
    rapport += f"""
    INDICATEURS CLÉS {dernier_annee}
    ----------------------------
    """
    
    if dernier_annee in sig_results:
        sig = sig_results[dernier_annee]
        rapport += f"- Chiffre d'affaires: {sig['chiffre_affaires']:,.0f} €\n"
        rapport += f"- EBE: {sig['ebe']:,.0f} €\n"
        rapport += f"- Résultat net: {sig['resultat_net']:,.0f} €\n"
    
    if dernier_annee in ratios_results:
        ratios = ratios_results[dernier_annee]
        rapport += f"- Rentabilité nette: {ratios['rentabilite_nette']}\n"
        rapport += f"- Ratio d'endettement: {ratios['ratio_endettement']}\n"
        rapport += f"- Ratio de liquidité: {ratios['ratio_liquidite']}\n"
    
    rapport += """
    RECOMMANDATIONS
    ---------------
    """
    
    categorie = score_cobac['categorie']
    if categorie in ['A', 'B']:
        rapport += "- Dossier de bonne qualité\n- Procédure standard applicable\n"
    elif categorie == 'C':
        rapport += "- Surveillance renforcée requise\n- Garanties complémentaires recommandées\n"
    else:
        rapport += "- Dossier à risque élevé\n- Comité de crédit obligatoire\n"
    
    return rapport

if __name__ == "__main__":
    main()