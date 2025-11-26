# app.py - Application Streamlit complète avec conformité COBAC/CEMAC - Version Exhaustive Corrigée

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
import traceback

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
    
    # Mode dégradé sans les modules COBAC
    class FinancialDataProcessor:
        def __init__(self, *args, **kwargs): 
            self.model = None
            self.scaler = None
        def load_excel_data(self, *args, **kwargs): 
            return pd.DataFrame()
        def prepare_prediction_features(self, *args, **kwargs):
            return None
        def predict_risk(self, *args, **kwargs):
            return None, None, None
    
    class FinancialAnalyzer:
        def calculate_soldes_intermediaires(self, *args, **kwargs): 
            return {}
        def calculate_financial_ratios(self, *args, **kwargs): 
            return {}
        def calculate_working_capital_indicators(self, *args, **kwargs): 
            return {}
    
    class ScoringSystemCOBAC:
        def calculer_score_global(self, *args, **kwargs): 
            return None
        def _create_default_score(self):
            return {
                'score_total': 0,
                'categorie': 'E',
                'libelle_categorie': 'Module COBAC non disponible',
                'couleur_categorie': 'gray',
                'scores_detailles': {},
                'conformite_cobac': {}
            }
        def calculer_provisionnement(self, *args, **kwargs):
            return {}
    
    REGLEMENTATION_COBAC = {}
    st.warning("⚠️ Mode dégradé - Fonctionnalités COBAC limitées")

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
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .risk-high {
        background-color: #ffebee;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 6px solid #f44336;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(244,67,54,0.1);
    }
    .risk-low {
        background-color: #e8f5e8;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 6px solid #4caf50;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(76,175,80,0.1);
    }
    .risk-moderate {
        background-color: #fff3e0;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 6px solid #ff9800;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(255,152,0,0.1);
    }
    .section-header {
        color: #1f77b4;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .cobac-alert {
        background-color: #fff3cd;
        border: 2px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(255,234,167,0.3);
    }
    .conforme {
        color: #28a745;
        font-weight: bold;
    }
    .non-conforme {
        color: #dc3545;
        font-weight: bold;
    }
    .score-A { 
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #155724;
    }
    .score-B { 
        background: linear-gradient(135deg, #cce7ff, #b3d9ff);
        color: #004085;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #004085;
    }
    .score-C { 
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        color: #856404;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #856404;
    }
    .score-D { 
        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
        color: #721c24;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #721c24;
    }
    .score-E { 
        background: linear-gradient(135deg, #f5c6cb, #f1b0b7);
        color: #721c24;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #721c24;
    }
    .dataframe {
        font-size: 0.9rem;
    }
    .stButton button {
        background-color: #1f77b4;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #1668a1;
    }
    .debug-info {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        font-family: monospace;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Fonction principale de l'application"""
    
    # Header principal avec logo COBAC
    st.markdown("""
    <div class="cobac-header">
        <h1 class="main-header">🏛️ Analyse du Risque de Crédit - COBAC/CEMAC</h1>
        <p style='font-size: 1.3rem; margin-bottom: 0.5rem; font-weight: bold;'>
            Application conforme à la réglementation bancaire de la CEMAC
        </p>
        <p style='font-size: 1rem; margin-bottom: 0; opacity: 0.9;'>
            Règlements R-2015/01 à R-2015/12 - Système de scoring réglementaire intégré
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar - Upload des fichiers avec section COBAC
    with st.sidebar:
        st.markdown("### 📁 Import des États Financiers")
        st.markdown("---")
        
        # Informations entreprise
        st.markdown("#### 🏢 Informations Entreprise")
        entreprise_nom = st.text_input("**Nom de l'entreprise**", "Entreprise ABC")
        entreprise_secteur = st.selectbox(
            "**Secteur d'activité**",
            ["Commerce", "Industrie", "Services", "BTP", "Agriculture", "Autre"]
        )
        entreprise_taille = st.selectbox(
            "**Taille de l'entreprise**",
            ["TPE", "PME", "ETI", "GE"]
        )
        
        st.markdown("#### 📊 Fichiers financiers requis")
        
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
        st.markdown("#### ⚙️ Paramètres COBAC")
        
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
        
        # Option de debug
        debug_mode = st.checkbox("🔧 Mode Debug", value=False, help="Afficher les informations de débogage")
        
        st.markdown("---")
        
        # Informations réglementaires COBAC
        with st.expander("📋 Références COBAC"):
            st.markdown("""
            **Règlementation applicable:**
            - **R-2015/03** : Ratio de solvabilité
            - **R-2015/04** : Risque de crédit et provisionnement  
            - **R-2015/06** : Gestion des risques
            - **R-2015/08** : Liquidité
            
            **Seuils réglementaires:**
            - Rentabilité nette ≥ 3%
            - Ratio d'endettement ≤ 200%
            - Ratio de liquidité ≥ 100%
            - Autonomie financière ≥ 20%
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
                # Chargement avec gestion d'erreur
                try:
                    df_consolide = processor.load_excel_data(bilan_file, cpc_file, flux_file)
                except Exception as load_error:
                    st.error(f"❌ Erreur lors du chargement des fichiers: {str(load_error)}")
                    if debug_mode:
                        st.code(traceback.format_exc())
                    st.info("Vérifiez le format de vos fichiers Excel et réessayez.")
                    return
                
                # Vérification des données chargées
                if df_consolide.empty:
                    st.error("""
                    ❌ Aucune donnée valide n'a pu être chargée depuis les fichiers.
                    
                    **Vérifiez :**
                    - Le format des fichiers Excel
                    - La présence des colonnes 'compte' et 'libellé'
                    - Les années doivent être en en-têtes de colonnes numériques
                    - Les montants doivent être numériques
                    """)
                    return
                
                # Affichage des données chargées pour debug
                if debug_mode:
                    with st.expander("🔍 Debug - Données chargées", expanded=False):
                        st.write(f"**Nombre total de lignes:** {len(df_consolide)}")
                        st.write(f"**Période couverte:** {df_consolide['year'].min()} - {df_consolide['year'].max()}")
                        st.write(f"**Répartition par source:** {df_consolide['source'].value_counts().to_dict()}")
                        st.write("**Aperçu des données:**")
                        st.dataframe(df_consolide.head(15), use_container_width=True)
                        st.write("**Statistiques des montants:**")
                        st.dataframe(df_consolide['amount'].describe(), use_container_width=True)
                
                # Calcul des indicateurs COBAC avec gestion d'erreur
                try:
                    sig_results = analyzer.calculate_soldes_intermediaires(df_consolide)
                    ratios_results = analyzer.calculate_financial_ratios(df_consolide)
                    working_capital_results = analyzer.calculate_working_capital_indicators(df_consolide)
                    
                    # Debug des résultats intermédiaires
                    if debug_mode:
                        with st.expander("🔍 Debug - Résultats calculs", expanded=False):
                            st.write("**SIG Results:**", sig_results)
                            st.write("**Ratios Results:**", ratios_results)
                            st.write("**Working Capital Results:**", working_capital_results)
                    
                    # Vérification que les calculs ont produit des résultats
                    validation_errors = []
                    
                    if not sig_results:
                        validation_errors.append("Aucun résultat pour les soldes intermédiaires")
                        sig_results = _create_default_sig_results(df_consolide)
                    
                    if not ratios_results:
                        validation_errors.append("Aucun résultat pour les ratios financiers")
                        ratios_results = _create_default_ratios_results(df_consolide)
                    
                    if not working_capital_results:
                        validation_errors.append("Aucun résultat pour l'analyse du fonds de roulement")
                        working_capital_results = _create_default_wc_results(df_consolide)
                    
                    if validation_errors and debug_mode:
                        st.warning("⚠️ " + " | ".join(validation_errors))
                    
                    # Scoring COBAC seulement si on a des données
                    try:
                        score_cobac = scoring_system.calculer_score_global(
                            sig_results, ratios_results, working_capital_results
                        )
                    except Exception as scoring_error:
                        st.warning(f"⚠️ Erreur lors du scoring COBAC: {scoring_error}")
                        if debug_mode:
                            st.code(traceback.format_exc())
                        score_cobac = scoring_system._create_default_score() if hasattr(scoring_system, '_create_default_score') else None
                    
                    # Préparation pour la prédiction IA
                    prediction_features = None
                    try:
                        if sig_results and ratios_results and working_capital_results:
                            prediction_features = processor.prepare_prediction_features(
                                df_consolide, sig_results, ratios_results, working_capital_results
                            )
                    except Exception as feature_error:
                        if debug_mode:
                            st.warning(f"⚠️ Erreur lors de la préparation des features: {feature_error}")
                        prediction_features = None
                    
                except Exception as calc_error:
                    st.error(f"❌ Erreur lors des calculs financiers: {str(calc_error)}")
                    if debug_mode:
                        st.code(traceback.format_exc())
                    # Initialisation de valeurs par défaut pour éviter les crashs
                    sig_results = _create_default_sig_results(df_consolide)
                    ratios_results = _create_default_ratios_results(df_consolide)
                    working_capital_results = _create_default_wc_results(df_consolide)
                    score_cobac = scoring_system._create_default_score() if hasattr(scoring_system, '_create_default_score') else None
                    prediction_features = None

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
            if debug_mode:
                st.markdown("#### 🔧 Stack Trace Complète")
                st.code(traceback.format_exc())
            st.info("""
            **Vérifiez :**
            - Le format des fichiers Excel
            - La conformité au plan comptable COBAC
            - La présence des comptes requis
            - Les types de données dans les colonnes
            """)
    
    else:
        display_welcome_message_cobac()

def _create_default_sig_results(df_consolide):
    """Crée des résultats SIG par défaut"""
    try:
        years = sorted(df_consolide['year'].unique())
        default_results = {}
        for year in years:
            default_results[year] = {
                'chiffre_affaires': 0,
                'marge_commerciale': 0,
                'valeur_ajoutee': 0,
                'ebe': 0,
                'resultat_net': 0,
                'charges_personnel': 0
            }
        return default_results
    except:
        return {2023: {'chiffre_affaires': 0, 'marge_commerciale': 0, 'valeur_ajoutee': 0, 'ebe': 0, 'resultat_net': 0, 'charges_personnel': 0}}

def _create_default_ratios_results(df_consolide):
    """Crée des résultats de ratios par défaut"""
    try:
        years = sorted(df_consolide['year'].unique())
        default_results = {}
        for year in years:
            default_results[year] = {
                'rentabilite_nette': '0%',
                'ratio_endettement': '0.00',
                'ratio_liquidite': '0.00',
                'ratio_autonomie': '0%',
                'capacite_remboursement': '0.00',
                'ebe': 0,
                'dettes_financieres': 0
            }
        return default_results
    except:
        return {2023: {'rentabilite_nette': '0%', 'ratio_endettement': '0.00', 'ratio_liquidite': '0.00', 'ratio_autonomie': '0%', 'capacite_remboursement': '0.00', 'ebe': 0, 'dettes_financieres': 0}}

def _create_default_wc_results(df_consolide):
    """Crée des résultats de fonds de roulement par défaut"""
    try:
        years = sorted(df_consolide['year'].unique())
        default_results = {}
        for year in years:
            default_results[year] = {
                'caf': 0,
                'bfr': 0,
                'fr': 0,
                'tn': 0,
                'actif_circulant': 0,
                'passif_circulant': 0,
                'capitaux_permanents': 0,
                'actif_immobilise': 0
            }
        return default_results
    except:
        return {2023: {'caf': 0, 'bfr': 0, 'fr': 0, 'tn': 0, 'actif_circulant': 0, 'passif_circulant': 0, 'capitaux_permanents': 0, 'actif_immobilise': 0}}

def display_quick_metrics_cobac(sig_results, ratios_results, working_capital_results, score_cobac):
    """Affiche les métriques rapides COBAC en haut de page"""
    if not sig_results:
        return
    
    try:
        last_year = max(sig_results.keys()) if sig_results else None
        if not last_year:
            return
            
        current_data = working_capital_results.get(last_year, {})
        
        st.markdown("---")
        st.markdown("### 📊 Indicateurs Clés COBAC")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            # Score COBAC
            if score_cobac and 'categorie' in score_cobac:
                categorie = score_cobac['categorie']
                couleur_classe = f"score-{categorie}"
                st.markdown(f"<div class='{couleur_classe}'>", unsafe_allow_html=True)
                st.metric("Score COBAC", f"{score_cobac.get('score_total', 0)}/100")
                st.write(f"Catégorie {categorie}")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.metric("Score COBAC", "N/A")
        
        with col2:
            if last_year in sig_results:
                ca = sig_results[last_year].get('chiffre_affaires', 0)
                st.metric("Chiffre d'affaires", f"{ca:,.0f} €")
            else:
                st.metric("Chiffre d'affaires", "N/A")
        
        with col3:
            if last_year in sig_results:
                ebe = sig_results[last_year].get('ebe', 0)
                st.metric("EBE", f"{ebe:,.0f} €")
            else:
                st.metric("EBE", "N/A")
        
        with col4:
            if last_year in ratios_results:
                rentabilite = ratios_results[last_year].get('rentabilite_nette', '0%')
                st.metric("Rentabilité nette", rentabilite)
            else:
                st.metric("Rentabilité nette", "N/A")
        
        with col5:
            tn = current_data.get('tn', 0)
            statut_tn = "✅" if tn > 0 else "❌"
            st.metric("Trésorerie Nette", f"{tn:,.0f} €")
            st.write(f"{statut_tn} {'Positive' if tn > 0 else 'Négative'}")
        
        st.markdown("---")
    except Exception as e:
        st.warning(f"⚠️ Erreur dans l'affichage des métriques rapides: {e}")

def display_dashboard_overview(df_consolide, sig_results, ratios_results, working_capital_results, score_cobac, entreprise_nom):
    """Onglet Tableau de Bord COBAC"""
    st.markdown("### 🏠 Tableau de Bord")
    
    if not sig_results:
        st.info("📊 Aucune donnée disponible pour le tableau de bord")
        return
    
    try:
        # Alertes COBAC immédiates
        display_cobac_alerts(score_cobac, ratios_results, working_capital_results)
        
        # Graphiques principaux
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 Évolution du Chiffre d'Affaires et EBE")
            fig_ca_ebe = create_ca_ebe_chart(sig_results)
            if fig_ca_ebe:
                st.plotly_chart(fig_ca_ebe, use_container_width=True)
            else:
                st.info("Données insuffisantes pour le graphique CA/EBE")
        
        with col2:
            st.markdown("#### 🎯 Score COBAC et Rentabilité")
            fig_score_rentabilite = create_score_rentabilite_chart(score_cobac, ratios_results)
            if fig_score_rentabilite:
                st.plotly_chart(fig_score_rentabilite, use_container_width=True)
            else:
                st.info("Données insuffisantes pour le graphique score/rentabilité")
        
        # Indicateurs de conformité
        st.markdown("#### ✅ Conformité Réglementaire COBAC")
        display_conformite_table(score_cobac, ratios_results)
        
    except Exception as e:
        st.error(f"❌ Erreur dans l'affichage du tableau de bord: {e}")

def display_cobac_alerts(score_cobac, ratios_results, working_capital_results):
    """Affiche les alertes COBAC"""
    if not ratios_results:
        return
        
    try:
        dernier_annee = max(ratios_results.keys()) if ratios_results else None
        if not dernier_annee:
            return
        
        alertes = []
        
        # Alerte score COBAC
        if score_cobac and score_cobac.get('categorie') in ['D', 'E']:
            alertes.append(("🔴", "Score COBAC critique", f"Catégorie {score_cobac['categorie']} - Surveillance renforcée requise"))
        
        # Alertes ratios
        if score_cobac:
            conformite = score_cobac.get('conformite_cobac', {})
            if not conformite.get('rentabilite', True):
                alertes.append(("🟡", "Rentabilité faible", "En dessous du seuil COBAC de 3%"))
            
            if not conformite.get('liquidite', True):
                alertes.append(("🟡", "Liquidité insuffisante", "Ratio de liquidité inférieur à 1"))
            
            if not conformite.get('endettement', True):
                alertes.append(("🟡", "Endettement élevé", "Ratio d'endettement supérieur à 200%"))
        
        # Alerte trésorerie
        if dernier_annee in working_capital_results:
            if working_capital_results[dernier_annee].get('tn', 0) < 0:
                alertes.append(("🔴", "Trésorerie négative", "Risque de liquidité à court terme"))
        
        if alertes:
            st.markdown("#### 🚨 Alertes COBAC")
            for icone, titre, description in alertes:
                st.markdown(f"""
                <div class="cobac-alert">
                    <strong>{icone} {titre}</strong><br>
                    {description}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ Aucune alerte COBAC détectée - Situation conforme")
            
    except Exception as e:
        st.warning(f"⚠️ Erreur dans l'affichage des alertes: {e}")

def display_conformite_table(score_cobac, ratios_results):
    """Affiche le tableau de conformité COBAC"""
    if not ratios_results:
        st.info("Aucune donnée de ratios disponible")
        return
        
    try:
        dernier_annee = max(ratios_results.keys()) if ratios_results else None
        if not dernier_annee:
            return
        
        conformite = score_cobac.get('conformite_cobac', {}) if score_cobac else {}
        ratios = ratios_results[dernier_annee]
        
        data = {
            'Critère': ['Rentabilité nette', 'Ratio d\'endettement', 'Ratio de liquidité', 'Ratio d\'autonomie', 'Conformité globale'],
            'Valeur': [
                ratios.get('rentabilite_nette', 'N/A'),
                ratios.get('ratio_endettement', 'N/A'),
                ratios.get('ratio_liquidite', 'N/A'), 
                ratios.get('ratio_autonomie', 'N/A'),
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
        
    except Exception as e:
        st.error(f"❌ Erreur dans l'affichage de la conformité: {e}")

def display_soldes_intermediaires(sig_results):
    """Onglet Soldes Intermédiaires de Gestion"""
    st.markdown("### 💰 Soldes Intermédiaires de Gestion COBAC")
    
    if not sig_results:
        st.info("📊 Aucune donnée disponible pour les soldes intermédiaires")
        return
    
    try:
        # Tableau des SIG
        sig_df = pd.DataFrame(sig_results).T
        sig_df_formatted = sig_df.applymap(lambda x: f"{x:,.0f} €" if isinstance(x, (int, float)) else x)
        
        st.dataframe(sig_df_formatted, use_container_width=True)
        
        # Graphique en cascade
        st.markdown("#### 📊 Construction du résultat")
        if len(sig_results) > 0:
            last_year = max(sig_results.keys())
            fig_waterfall = create_waterfall_chart(sig_results[last_year], last_year)
            if fig_waterfall:
                st.plotly_chart(fig_waterfall, use_container_width=True)
        
        # Évolution des SIG
        st.markdown("#### 📈 Évolution des principaux soldes")
        fig_evolution = create_sig_evolution_chart(sig_results)
        if fig_evolution:
            st.plotly_chart(fig_evolution, use_container_width=True)
            
    except Exception as e:
        st.error(f"❌ Erreur dans l'affichage des soldes intermédiaires: {e}")

def display_ratios_financiers_cobac(ratios_results):
    """Onglet Ratios Financiers COBAC"""
    st.markdown("### 📊 Analyse des Ratios Financiers COBAC")
    
    if not ratios_results:
        st.info("📈 Aucune donnée disponible pour les ratios financiers")
        return
    
    try:
        # Tableau des ratios
        ratios_df = pd.DataFrame(ratios_results).T
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 Ratios de Rentabilité et Structure")
            rentability_data = {
                'Année': list(ratios_results.keys()),
                'Rentabilité Nette': [r.get('rentabilite_nette', 'N/A') for r in ratios_results.values()],
                'Capacité Remboursement': [r.get('capacite_remboursement', 'N/A') for r in ratios_results.values()],
                'EBE (k€)': [f"{r.get('ebe', 0)/1000:,.0f}" for r in ratios_results.values()]
            }
            st.dataframe(pd.DataFrame(rentability_data), use_container_width=True)
            
            # Graphique de rentabilité
            st.markdown("#### 📊 Évolution de la rentabilité")
            fig_rent = create_rentability_detail_chart(ratios_results)
            if fig_rent:
                st.plotly_chart(fig_rent, use_container_width=True)
        
        with col2:
            st.markdown("#### 🏗️ Ratios de Structure COBAC")
            structure_data = {
                'Année': list(ratios_results.keys()),
                'Endettement': [r.get('ratio_endettement', 'N/A') for r in ratios_results.values()],
                'Autonomie': [r.get('ratio_autonomie', 'N/A') for r in ratios_results.values()],
                'Liquidité': [r.get('ratio_liquidite', 'N/A') for r in ratios_results.values()]
            }
            st.dataframe(pd.DataFrame(structure_data), use_container_width=True)
            
            # Radar chart des ratios
            st.markdown("#### 🎯 Profil des ratios")
            if len(ratios_results) > 0:
                last_year = max(ratios_results.keys())
                fig_radar = create_radar_chart(ratios_results[last_year], last_year)
                if fig_radar:
                    st.plotly_chart(fig_radar, use_container_width=True)
                    
    except Exception as e:
        st.error(f"❌ Erreur dans l'affichage des ratios financiers: {e}")

def display_working_capital_analysis(working_capital_results, score_cobac):
    """Onglet Analyse BFR/FR/TN"""
    st.markdown("### 🔄 Analyse du Fonds de Roulement COBAC")
    
    if not working_capital_results:
        st.info("💸 Données insuffisantes pour calculer le fonds de roulement")
        return
    
    try:
        # Métriques principales
        last_year = max(working_capital_results.keys())
        current_data = working_capital_results[last_year]
        
        st.markdown("#### 💰 Indicateurs de Trésorerie")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            caf = current_data.get('caf', 0)
            statut_caf = "✅" if caf > 0 else "❌"
            st.metric("CAF", f"{caf:,.0f} €")
            st.write(f"{statut_caf} {'Positive' if caf > 0 else 'Négative'}")
        
        with col2:
            bfr = current_data.get('bfr', 0)
            st.metric("BFR", f"{bfr:,.0f} €")
        
        with col3:
            fr = current_data.get('fr', 0)
            statut_fr = "✅" if fr > 0 else "❌"
            st.metric("FR", f"{fr:,.0f} €")
            st.write(f"{statut_fr} {'Positif' if fr > 0 else 'Négatif'}")
        
        with col4:
            tn = current_data.get('tn', 0)
            statut_tn = "✅" if tn > 0 else "❌"
            st.metric("TN", f"{tn:,.0f} €")
            st.write(f"{statut_tn} {'Positive' if tn > 0 else 'Négative'}")
        
        # Équilibre financier
        st.markdown("#### ⚖️ Équilibre Financier")
        col1, col2 = st.columns(2)
        
        with col1:
            fr_val = current_data.get('fr', 0)
            bfr_val = current_data.get('bfr', 0)
            tn_val = current_data.get('tn', 0)
            st.info(f"**FR - BFR = TN**\n\n{fr_val:,.0f} - {bfr_val:,.0f} = {tn_val:,.0f} €")
            if fr_val > 0 and tn_val > 0:
                st.success("✅ Structure financière équilibrée")
            elif fr_val > 0 and tn_val < 0:
                st.warning("⚠️ BFR trop élevé par rapport au FR")
            else:
                st.error("❌ Déséquilibre structurel")
        
        with col2:
            # Graphique des composants
            st.markdown("#### 📊 Composition du FR")
            fig_composants = create_working_capital_components_chart(current_data)
            if fig_composants:
                st.plotly_chart(fig_composants, use_container_width=True)
        
        # Tableau d'évolution
        st.markdown("#### 📈 Évolution des indicateurs")
        evolution_data = []
        for year in sorted(working_capital_results.keys()):
            data = working_capital_results[year]
            evolution_data.append({
                'Année': year,
                'CAF (k€)': f"{data.get('caf', 0)/1000:.0f}",
                'BFR (k€)': f"{data.get('bfr', 0)/1000:.0f}",
                'FR (k€)': f"{data.get('fr', 0)/1000:.0f}",
                'TN (k€)': f"{data.get('tn', 0)/1000:.0f}"
            })
        
        evolution_df = pd.DataFrame(evolution_data)
        st.dataframe(evolution_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Erreur dans l'affichage de l'analyse du fonds de roulement: {e}")

def display_scoring_cobac(score_cobac, scoring_system, montant_pret, sig_results, ratios_results, working_capital_results):
    """Onglet Scoring COBAC"""
    st.markdown("### 🏛️ Scoring COBAC - Analyse Réglementaire")
    
    if not score_cobac:
        st.info("🎯 Score COBAC non disponible - Données insuffisantes")
        return
    
    try:
        # Affichage du score principal
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            categorie = score_cobac.get('categorie', 'E')
            couleur = score_cobac.get('couleur_categorie', 'gray')
            libelle = score_cobac.get('libelle_categorie', 'Non disponible')
            st.markdown(f"<h2 style='color: {couleur};'>Catégorie {categorie}</h2>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='color: {couleur};'>{libelle}</h3>", unsafe_allow_html=True)
        
        with col2:
            st.metric("Score Global", f"{score_cobac.get('score_total', 0)}/100")
        
        with col3:
            # Jauge COBAC
            fig_gauge = create_cobac_gauge(score_cobac.get('score_total', 0))
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Détail des scores
        st.markdown("#### 📋 Détail du Scoring COBAC")
        scores_details = score_cobac.get('scores_detailles', {})
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Rentabilité", f"{scores_details.get('rentabilite', 0)}/25")
        col2.metric("Structure", f"{scores_details.get('structure', 0)}/25")
        col3.metric("Liquidité", f"{scores_details.get('liquidite', 0)}/20")
        col4.metric("Trésorerie", f"{scores_details.get('tresorerie', 0)}/15")
        col5.metric("Croissance", f"{scores_details.get('croissance', 0)}/15")
        
        # Graphique détaillé
        st.markdown("#### 📊 Analyse détaillée des scores")
        fig_details = create_scoring_details_chart(scores_details)
        if fig_details:
            st.plotly_chart(fig_details, use_container_width=True)
        
        # Provisionnement COBAC
        st.markdown("#### 💰 Provisionnement COBAC")
        try:
            provisionnement = scoring_system.calculer_provisionnement(montant_pret, categorie)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Montant prêt", f"{provisionnement.get('montant_pret', 0):,.0f} €")
            col2.metric("Catégorie", categorie)
            col3.metric("Taux provision", f"{provisionnement.get('taux_provision', 0):.0%}")
            col4.metric("Provision requise", f"{provisionnement.get('provision_requise', 0):,.0f} €")
        except Exception as e:
            st.warning(f"⚠️ Impossible de calculer le provisionnement: {e}")
        
        # Recommandations COBAC
        st.markdown("#### 💡 Recommandations COBAC")
        display_cobac_recommendations(score_cobac, provisionnement if 'provisionnement' in locals() else {})
        
    except Exception as e:
        st.error(f"❌ Erreur dans l'affichage du scoring COBAC: {e}")

def display_cobac_recommendations(score_cobac, provisionnement):
    """Affiche les recommandations COBAC"""
    if not score_cobac:
        return
        
    try:
        categorie = score_cobac.get('categorie', 'E')
        recommandations = []
        
        if categorie in ['A', 'B']:
            recommandations.append("✅ **Dossier de bonne qualité** - Procédure standard applicable")
            recommandations.append("📊 **Surveillance normale** - Revue annuelle suffisante")
            recommandations.append("💳 **Conditions favorables** - Taux préférentiels possibles")
            recommandations.append("📈 **Perspectives positives** - Croissance soutenable")
        
        elif categorie == 'C':
            recommandations.append("⚠️ **Surveillance renforcée** - Revue semestrielle recommandée")
            recommandations.append("📝 **Analyse approfondie** - Vérifier la pérennité du business model")
            recommandations.append("🔍 **Garanties complémentaires** - Exiger des garanties additionnelles")
            recommandations.append("💰 **Taux majoré** - Appliquer une prime de risque")
        
        elif categorie in ['D', 'E']:
            recommandations.append("🔴 **Dossier à risque** - Comité de crédit obligatoire")
            recommandations.append("🚨 **Surveillance étroite** - Revue trimestrielle requise")
            recommandations.append("💸 **Provisionnement élevé** - Considérer le rejet de la demande")
            recommandations.append("📉 **Restructuration** - Envisager une restructuration de dette")
            recommandations.append("🛡️ **Garanties maximales** - Exiger des garanties solides")
        
        for reco in recommandations:
            st.markdown(f"- {reco}")
        
        # Information provisionnement
        if provisionnement:
            st.info(f"""
            **Information provisionnement COBAC (R-2015/04):**
            - Catégorie {categorie} : Taux de {provisionnement.get('taux_provision', 0):.0%}
            - Provision requise : {provisionnement.get('provision_requise', 0):,.0f} €
            - Montant net après provision : {provisionnement.get('montant_net', 0):,.0f} €
            """)
            
    except Exception as e:
        st.warning(f"⚠️ Erreur dans l'affichage des recommandations: {e}")

def display_risk_prediction_cobac(processor, prediction_features, confidence_threshold, entreprise_nom, score_cobac, montant_pret):
    """Onglet Prédiction du Risque COBAC"""
    st.markdown("### 🎯 Prédiction du Risque de Crédit - IA COBAC")
    
    try:
        # Integration du scoring COBAC avec la prédiction IA
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏛️ Scoring COBAC")
            if score_cobac and 'categorie' in score_cobac:
                categorie = score_cobac['categorie']
                st.metric("Catégorie COBAC", f"{categorie}")
                st.metric("Appréciation", score_cobac.get('libelle_categorie', 'N/A'))
                st.metric("Score COBAC", f"{score_cobac.get('score_total', 0)}/100")
            else:
                st.info("Score COBAC non disponible")
        
        with col2:
            st.markdown("#### 🤖 Prédiction IA")
            if processor.model is not None and prediction_features is not None:
                try:
                    prediction, probability, feature_importance = processor.predict_risk(prediction_features)
                    
                    if prediction is not None:
                        # Jauge risque IA
                        fig_ia_gauge = create_risk_gauge(probability)
                        st.plotly_chart(fig_ia_gauge, use_container_width=True)
                        
                        st.metric("Probabilité défaut", f"{probability:.1%}")
                        
                        # Affichage du risque
                        if probability < 0.3:
                            st.success("✅ Risque faible")
                        elif probability < 0.7:
                            st.warning("⚠️ Risque modéré")
                        else:
                            st.error("🔴 Risque élevé")
                    else:
                        st.warning("Prédiction IA non disponible")
                except Exception as e:
                    st.warning(f"Prédiction IA temporairement indisponible: {e}")
            else:
                # Message d'information si le modèle n'est pas disponible
                st.info("""
                **Modèle IA non disponible**
                
                Pour activer la prédiction IA :
                1. Entraînez un modèle sur des données historiques
                2. Sauvegardez-le sous 'modele_risque_credit.pkl'
                3. Placez-le dans le dossier de l'application
                
                **Alternative :** L'analyse COBAC reste pleinement fonctionnelle
                """)
        
        # Analyse consolidée - seulement si le modèle IA est disponible
        if processor.model is not None and prediction_features is not None and score_cobac:
            st.markdown("#### 🔍 Analyse Consolidée Risque")
            
            try:
                prediction, probability, _ = processor.predict_risk(prediction_features)
                
                if prediction is not None:
                    # Décision consolidée
                    if score_cobac.get('categorie') in ['A', 'B'] and probability < 0.3:
                        st.success("""
                        ## ✅ RECOMMANDATION : ACCORD
                        
                        **Justification :**
                        - Score COBAC favorable (Catégorie A/B)
                        - Probabilité de défaut faible (< 30%)
                        - Conformité réglementaire respectée
                        - Structure financière saine
                        """)
                    elif score_cobac.get('categorie') in ['C'] or (probability >= 0.3 and probability < 0.7):
                        st.warning("""
                        ## ⚠️ RECOMMANDATION : MIXTE
                        
                        **Conditions :**
                        - Surveillance renforcée requise
                        - Garanties supplémentaires nécessaires
                        - Taux d'intérêt majoré
                        - Durée réduite recommandée
                        - Comité de crédit conseillé
                        """)
                    else:
                        st.error("""
                        ## 🔴 RECOMMANDATION : REFUS
                        
                        **Motifs :**
                        - Score COBAC défavorable (Catégorie D/E)
                        - Probabilité de défaut élevée (> 70%)
                        - Non-conformité réglementaire probable
                        - Risque de crédit trop important
                        """)
                else:
                    st.info("Prédiction IA non disponible pour l'analyse consolidée")
                    
            except Exception as e:
                st.warning(f"Analyse consolidée temporairement indisponible: {e}")
        else:
            # Afficher uniquement l'analyse COBAC si l'IA n'est pas disponible
            if score_cobac and 'categorie' in score_cobac:
                st.markdown("#### 🔍 Analyse COBAC Exclusive")
                display_cobac_exclusive_analysis(score_cobac)
                
    except Exception as e:
        st.error(f"❌ Erreur dans l'affichage de la prédiction du risque: {e}")

def display_cobac_exclusive_analysis(score_cobac):
    """Affiche l'analyse basée uniquement sur le scoring COBAC"""
    try:
        categorie = score_cobac.get('categorie', 'E')
        
        if categorie in ['A', 'B']:
            st.success("""
            ## ✅ RECOMMANDATION COBAC : ACCORD
            
            **Justification :**
            - Score COBAC favorable (Catégorie A/B)
            - Conformité réglementaire respectée
            - Structure financière saine
            - Faible risque détecté
            """)
        elif categorie == 'C':
            st.warning("""
            ## ⚠️ RECOMMANDATION COBAC : MIXTE
            
            **Conditions :**
            - Surveillance renforcée requise
            - Garanties supplémentaires nécessaires
            - Taux d'intérêt majoré recommandé
            - Comité de crédit conseillé
            """)
        else:
            st.error("""
            ## 🔴 RECOMMANDATION COBAC : REFUS
            
            **Motifs :**
            - Score COBAC défavorable (Catégorie D/E)
            - Risque de crédit élevé
            - Non-conformité réglementaire probable
            - Structure financière fragile
            """)
    except Exception as e:
        st.warning(f"⚠️ Erreur dans l'analyse COBAC exclusive: {e}")

def display_raw_data_cobac(df_consolide, sig_results, ratios_results, working_capital_results, score_cobac):
    """Onglet Données Brutes COBAC"""
    st.markdown("### 📋 Données Brutes et Export COBAC")
    
    st.markdown("#### 📊 Données consolidées")
    if not df_consolide.empty:
        st.dataframe(df_consolide, use_container_width=True)
    else:
        st.info("Aucune donnée consolidée disponible")
    
    # Export des données COBAC
    st.markdown("#### 💾 Export des résultats COBAC")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not df_consolide.empty:
            csv = df_consolide.to_csv(index=False, encoding='utf-8')
            st.download_button(
                label="📥 Données consolidées CSV",
                data=csv,
                file_name="donnees_consolidees_cobac.csv",
                mime="text/csv"
            )
    
    with col2:
        if sig_results:
            sig_df = pd.DataFrame(sig_results).T
            csv_sig = sig_df.to_csv()
            st.download_button(
                label="📥 Soldes intermédiaires CSV",
                data=csv_sig,
                file_name="soldes_intermediaires_cobac.csv",
                mime="text/csv"
            )
    
    with col3:
        if score_cobac:
            # Créer un rapport COBAC
            rapport_cobac = generate_rapport_cobac(score_cobac, sig_results, ratios_results)
            st.download_button(
                label="📄 Rapport COBAC complet",
                data=rapport_cobac,
                file_name=f"rapport_cobac_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
    
    # Statistiques descriptives
    st.markdown("#### 📈 Statistiques descriptives")
    if not df_consolide.empty:
        st.dataframe(df_consolide['amount'].describe(), use_container_width=True)

def display_welcome_message_cobac():
    """Message d'accueil COBAC"""
    st.markdown("""
    <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 15px;'>
        <h2 style='color: #1f77b4; margin-bottom: 1.5rem;'>🏛️ Bienvenue dans l'analyseur de risque de crédit COBAC</h2>
        <p style='font-size: 1.3rem; margin-bottom: 2rem; color: #495057;'>
            Application conforme à la réglementation bancaire de la CEMAC
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; background-color: #f8f9fa; border-radius: 10px; border: 2px solid #1f77b4;'>
            <h3 style='color: #1f77b4;'>📊 Bilan COBAC</h3>
            <p>Actif et passif selon plan comptable CEMAC</p>
            <small>Comptes normalisés COBAC</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; background-color: #f8f9fa; border-radius: 10px; border: 2px solid #1f77b4;'>
            <h3 style='color: #1f77b4;'>💰 Compte de résultat</h3>
            <p>Produits et charges normalisés</p>
            <small>Analyse SIG automatique</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; background-color: #f8f9fa; border-radius: 10px; border: 2px solid #1f77b4;'>
            <h3 style='color: #1f77b4;'>🏛️ Scoring COBAC</h3>
            <p>Analyse réglementaire intégrée</p>
            <small>Catégories A-E automatiques</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.info("""
    **📋 Format des fichiers attendu (COBAC) :**
    
    **Structure des fichiers Excel :**
    ```
    | compte | libellé              | 2023     | 2022     | 2021     |
    |--------|---------------------|----------|----------|----------|
    | 701    | Ventes de produits  | 1500000  | 1400000  | 1300000  |
    | 601    | Achats marchandises | 800000   | 750000   | 700000   |
    | 641    | Personnel           | 300000   | 280000   | 260000   |
    ```
    
    **Colonnes obligatoires :**
    - `compte` : Code comptable (ex: 701, 601, 641...)
    - `libellé` : Libellé du compte
    - Colonnes d'années : 2021, 2022, 2023...
    
    **Formats acceptés :**
    - Fichiers Excel (.xlsx, .xls)
    - Encodage UTF-8 recommandé
    - Séparateur décimal : point (.)
    - Montants en euros
    """)

# =============================================================================
# FONCTIONS DE CRÉATION DE GRAPHIQUES (inchangées)
# =============================================================================

def create_ca_ebe_chart(sig_results):
    """Crée un graphique CA et EBE"""
    if not sig_results:
        return None
        
    years = sorted(sig_results.keys())
    ca_values = [sig_results[y].get('chiffre_affaires', 0) for y in years]
    ebe_values = [sig_results[y].get('ebe', 0) for y in years]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Chiffre d\'affaires', x=years, y=ca_values, marker_color='#1f77b4'))
    fig.add_trace(go.Bar(name='EBE', x=years, y=ebe_values, marker_color='#2ca02c'))
    
    fig.update_layout(
        title="Évolution du CA et de l'EBE",
        barmode='group',
        height=400,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def create_score_rentabilite_chart(score_cobac, ratios_results):
    """Crée un graphique combiné score et rentabilité"""
    if not score_cobac or not ratios_results:
        return None
    
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
        marker_color=['#28a745' if x >= 3 else '#dc3545' for x in rentability_values]
    ))
    
    # Ligne de seuil COBAC
    fig.add_hline(y=3, line_dash="dash", line_color="red", annotation_text="Seuil COBAC 3%")
    
    fig.update_layout(
        title="Score COBAC vs Rentabilité nette",
        barmode='overlay',
        height=400,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)'
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
        increasing={"marker": {"color": "#28a745"}},
        decreasing={"marker": {"color": "#dc3545"}},
    ))
    
    fig.update_layout(
        title=f"Construction du résultat {year}",
        showlegend=False,
        height=400,
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_sig_evolution_chart(sig_results):
    """Crée un graphique d'évolution des SIG"""
    if not sig_results:
        return None
        
    years = sorted(sig_results.keys())
    
    fig = go.Figure()
    
    sig_to_plot = ['chiffre_affaires', 'marge_commerciale', 'valeur_ajoutee', 'ebe', 'resultat_net']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for sig, color in zip(sig_to_plot, colors):
        values = [sig_results[y].get(sig, 0) for y in years]
        fig.add_trace(go.Scatter(
            x=years, y=values, 
            name=sig.replace('_', ' ').title(),
            line=dict(color=color, width=3)
        ))
    
    fig.update_layout(
        title="Évolution des soldes intermédiaires",
        height=400,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def create_rentability_detail_chart(ratios_results):
    """Crée un graphique détaillé de rentabilité"""
    if not ratios_results:
        return None
        
    years = sorted(ratios_results.keys())
    rentability_values = [float(r['rentabilite_nette'].replace('%', '')) for r in ratios_results.values()]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, 
        y=rentability_values,
        marker_color=['#28a745' if x >= 3 else '#dc3545' for x in rentability_values]
    ))
    
    # Ligne de seuil COBAC
    fig.add_hline(y=3, line_dash="dash", line_color="red", annotation_text="Seuil COBAC 3%")
    
    fig.update_layout(
        title="Rentabilité nette vs Seuil COBAC",
        yaxis_title="Rentabilité nette (%)",
        height=300,
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def create_radar_chart(ratio_data, year):
    """Crée un radar chart pour les ratios"""
    categories = ['Rentabilité', 'Endettement', 'Liquidité', 'Autonomie']
    
    try:
        # Normalisation des valeurs avec gestion des erreurs
        rentability = min(float(ratio_data['rentabilite_nette'].replace('%', '')) / 20, 1) if ratio_data['rentabilite_nette'] != 'N/A' else 0
        endettement = 1 - min(float(ratio_data['ratio_endettement']) / 3, 1) if ratio_data['ratio_endettement'] != 'N/A' else 0
        liquidite = min(float(ratio_data['ratio_liquidite']) / 2, 1) if ratio_data['ratio_liquidite'] != 'N/A' else 0
        autonomie = float(ratio_data['ratio_autonomie'].replace('%', '')) / 100 if ratio_data['ratio_autonomie'] != 'N/A' else 0
        
        values = [rentability, endettement, liquidite, autonomie]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]],  # Fermer le cercle
            theta=categories + [categories[0]],
            fill='toself',
            name=f"Ratios {year}",
            line=dict(color='#1f77b4', width=2)
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
    except Exception:
        return None

def create_working_capital_components_chart(current_data):
    """Crée un graphique des composants du fonds de roulement"""
    labels = ['Capitaux Permanents', 'Actif Immobilisé', 'FR', 'BFR', 'TN']
    values = [
        current_data.get('capitaux_permanents', 0),
        current_data.get('actif_immobilise', 0),
        current_data.get('fr', 0),
        current_data.get('bfr', 0),
        current_data.get('tn', 0)
    ]
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    fig = go.Figure(data=[go.Bar(
        x=labels, y=values,
        marker_color=colors
    )])
    
    fig.update_layout(
        title="Composition du fonds de roulement",
        height=300,
        plot_bgcolor='rgba(0,0,0,0)'
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
                {'range': [0, 30], 'color': "#dc3545"},
                {'range': [30, 40], 'color': "#fd7e14"},
                {'range': [40, 50], 'color': "#ffc107"},
                {'range': [50, 60], 'color': "#a0d468"},
                {'range': [60, 100], 'color': "#28a745"}
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
        marker_color='#1f77b4'
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
        height=400,
        plot_bgcolor='rgba(0,0,0,0)'
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
                {'range': [0, 20], 'color': "#28a745"},
                {'range': [20, 50], 'color': "#ffc107"},
                {'range': [50, 100], 'color': "#dc3545"}
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
    try:
        dernier_annee = max(sig_results.keys()) if sig_results else "N/A"
        
        rapport = f"""
    RAPPORT D'ANALYSE COBAC - SYSTEME DE SCORING REGLEMENTAIRE
    ===========================================================
    Date de génération: {datetime.now().strftime('%d/%m/%Y à %H:%M')}
    Référence: R-2015/01 à R-2015/12 - Commission Bancaire de l'Afrique Centrale
    
    SYNTHESE DU SCORING COBAC
    -------------------------
    Score Global: {score_cobac.get('score_total', 0)}/100
    Catégorie: {score_cobac.get('categorie', 'N/A')}
    Appréciation: {score_cobac.get('libelle_categorie', 'N/A')}
    
    DETAIL DU SCORING PAR CRITERE
    -----------------------------
    """
        
        scores_details = score_cobac.get('scores_detailles', {})
        for critere, score in scores_details.items():
            rapport += f"- {critere.capitalize()}: {score} points\n"
        
        rapport += f"""
    ANALYSE DE CONFORMITE REGLEMENTAIRE
    -----------------------------------
    """
        
        conformite = score_cobac.get('conformite_cobac', {})
        for critere, statut in conformite.items():
            if critere != 'global':
                statut_text = "CONFORME" if statut else "NON CONFORME"
                rapport += f"- {critere.capitalize()}: {statut_text}\n"
        
        rapport += f"""
    INDICATEURS FINANCIERS CLES - EXERCICE {dernier_annee}
    -----------------------------------------------------
    """
        
        if dernier_annee in sig_results:
            sig = sig_results[dernier_annee]
            rapport += f"- Chiffre d'affaires: {sig.get('chiffre_affaires', 0):,.0f} €\n"
            rapport += f"- Marge commerciale: {sig.get('marge_commerciale', 0):,.0f} €\n"
            rapport += f"- Valeur ajoutée: {sig.get('valeur_ajoutee', 0):,.0f} €\n"
            rapport += f"- EBE: {sig.get('ebe', 0):,.0f} €\n"
            rapport += f"- Résultat net: {sig.get('resultat_net', 0):,.0f} €\n"
        
        if dernier_annee in ratios_results:
            ratios = ratios_results[dernier_annee]
            rapport += f"- Rentabilité nette: {ratios.get('rentabilite_nette', 'N/A')}\n"
            rapport += f"- Ratio d'endettement: {ratios.get('ratio_endettement', 'N/A')}\n"
            rapport += f"- Ratio de liquidité: {ratios.get('ratio_liquidite', 'N/A')}\n"
            rapport += f"- Ratio d'autonomie: {ratios.get('ratio_autonomie', 'N/A')}\n"
            rapport += f"- Capacité de remboursement: {ratios.get('capacite_remboursement', 'N/A')}\n"
        
        rapport += """
    RECOMMANDATIONS ET MESURES DE SURVEILLANCE
    ------------------------------------------
    """
        
        categorie = score_cobac.get('categorie', 'E')
        if categorie in ['A', 'B']:
            rapport += "- ✅ DOSSIER DE BONNE QUALITE\n"
            rapport += "- Procédure d'octroi standard applicable\n"
            rapport += "- Surveillance normale - Revue annuelle suffisante\n"
            rapport += "- Conditions de financement favorables envisageables\n"
        elif categorie == 'C':
            rapport += "- ⚠️ DOSSIER REQUERANT UNE ATTENTION PARTICULIERE\n"
            rapport += "- Surveillance renforcée requise - Revue semestrielle\n"
            rapport += "- Garanties complémentaires à exiger\n"
            rapport += "- Prime de risque à appliquer sur le taux d'intérêt\n"
            rapport += "- Comité de crédit recommandé pour décision\n"
        else:
            rapport += "- 🔴 DOSSIER A RISQUE ELEVE\n"
            rapport += "- Comité de crédit obligatoire pour décision\n"
            rapport += "- Surveillance étroite - Revue trimestrielle requise\n"
            rapport += "- Garanties maximales à exiger\n"
            rapport += "- Envisager le rejet ou la restructuration de la dette\n"
        
        rapport += f"""
    CONCLUSION
    ----------
    Le présent rapport a été généré automatiquement selon la méthodologie 
    de scoring COBAC. La catégorie {categorie} attribuée reflète l'analyse 
    réglementaire des risques conformément aux dispositions de la COBAC.
    
    ***
    Rapport généré par le Système d'Analyse du Risque de Crédit COBAC
    """
        
        return rapport
    except Exception as e:
        return f"Erreur lors de la génération du rapport: {str(e)}"

if __name__ == "__main__":
    main()