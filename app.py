# app.py - Application Streamlit complète d'analyse du risque de crédit

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

warnings.filterwarnings('ignore')

# Import des modules personnalisés
try:
    from financial_processor import FinancialDataProcessor
    from financial_analyzer import FinancialAnalyzer
except ImportError:
    st.error("Les modules financial_processor et financial_analyzer sont requis")
    st.stop()

# Configuration de la page
st.set_page_config(
    page_title="Analyse Risque Crédit - IA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .risk-high {
        background-color: #ffcccc;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff0000;
    }
    .risk-low {
        background-color: #ccffcc;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #00cc00;
    }
    .section-header {
        color: #1f77b4;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header principal
    st.markdown('<h1 class="main-header">📊 Analyse du Risque de Crédit - Intelligence Artificielle</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        Chargez les états financiers d'une entreprise pour analyser sa santé financière 
        et prédire son risque de défaut à l'aide de l'intelligence artificielle.
    </div>
    """, unsafe_allow_html=True)

    # Sidebar - Upload des fichiers
    with st.sidebar:
        st.header("📁 Import des États Financiers")
        st.markdown("---")
        
        entreprise_nom = st.text_input("Nom de l'entreprise", "Entreprise ABC")
        
        st.subheader("Fichiers requis:")
        
        bilan_file = st.file_uploader(
            "**Bilan** (Actif/Passif)", 
            type=['xlsx', 'xls'], 
            key='bilan',
            help="Fichier Excel contenant le bilan comptable"
        )
        
        cpc_file = st.file_uploader(
            "**Compte de Résultat**", 
            type=['xlsx', 'xls'], 
            key='cpc',
            help="Fichier Excel contenant le compte de résultat"
        )
        
        flux_file = st.file_uploader(
            "**Flux de Trésorerie**", 
            type=['xlsx', 'xls'], 
            key='flux',
            help="Fichier Excel contenant le tableau des flux de trésorerie"
        )
        
        st.markdown("---")
        st.subheader("Options d'analyse")
        
        n_years_analysis = st.slider(
            "Nombre d'années à analyser", 
            min_value=1, 
            max_value=5, 
            value=3
        )
        
        confidence_threshold = st.slider(
            "Seuil de confiance pour la prédiction", 
            min_value=0.5, 
            max_value=0.95, 
            value=0.7,
            help="Probabilité minimale pour considérer une prédiction comme fiable"
        )
        
        st.markdown("---")
        st.info("""
        **Format des fichiers attendu:**
        - Colonnes: compte, libellé, 2021, 2022, 2023...
        - Comptes selon le plan comptable général
        - Montants en euros
        """)

    # Traitement principal
    if bilan_file and cpc_file and flux_file:
        try:
            # Initialisation des processeurs
            with st.spinner('Initialisation des modules d\'analyse...'):
                processor = FinancialDataProcessor()
                analyzer = FinancialAnalyzer()

            # Chargement et traitement des données
            with st.spinner('Traitement des données financières...'):
                df_consolide = processor.load_excel_data(bilan_file, cpc_file, flux_file)
                
                # Vérification des données chargées
                if df_consolide.empty:
                    st.error("Aucune donnée valide n'a pu être chargée depuis les fichiers.")
                    return
                
                # Calcul des indicateurs
                sig_results = analyzer.calculate_soldes_intermediaires(df_consolide)
                ratios_results = analyzer.calculate_financial_ratios(df_consolide)
                working_capital_results = analyzer.calculate_working_capital_indicators(df_consolide)
                health_analysis = analyzer.analyze_working_capital_health(working_capital_results)
                
                # Préparation pour la prédiction
                prediction_features = processor.prepare_prediction_features(df_consolide)

            st.success(f"✅ Données financières de **{entreprise_nom}** traitées avec succès!")
            
            # Métriques rapides en haut
            display_quick_metrics(sig_results, ratios_results, working_capital_results, health_analysis)
            
            # Onglets principaux
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "📈 Vue d'ensemble", 
                "💰 Soldes Intermédiaires", 
                "📊 Ratios Financiers",
                "🔄 Analyse BFR/FR/TN", 
                "🎯 Prédiction Risque",
                "📋 Données Brutes"
            ])
            
            with tab1:
                display_overview(df_consolide, sig_results, ratios_results, working_capital_results)
            
            with tab2:
                display_soldes_intermediaires(sig_results)
            
            with tab3:
                display_ratios_financiers(ratios_results)
            
            with tab4:
                display_working_capital_analysis(working_capital_results, health_analysis)
            
            with tab5:
                display_risk_prediction(processor, prediction_features, confidence_threshold, entreprise_nom)
            
            with tab6:
                display_raw_data(df_consolide, sig_results, ratios_results, working_capital_results)
                
        except Exception as e:
            st.error(f"❌ Erreur lors du traitement : {str(e)}")
            st.info("Vérifiez le format de vos fichiers Excel et réessayez.")
    
    else:
        display_welcome_message()

def display_quick_metrics(sig_results, ratios_results, working_capital_results, health_analysis):
    """Affiche les métriques rapides en haut de page"""
    if not sig_results or not working_capital_results:
        return
    
    last_year = max(sig_results.keys())
    current_data = working_capital_results.get(last_year, {})
    current_health = health_analysis.get(last_year, {})
    
    st.markdown("---")
    st.subheader("📊 Indicateurs Clés")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if last_year in sig_results:
            ca = sig_results[last_year].get('chiffre_affaires', 0)
            st.metric("Chiffre d'affaires", f"{ca:,.0f} €")
    
    with col2:
        if last_year in sig_results:
            ebe = sig_results[last_year].get('ebe', 0)
            st.metric("EBE", f"{ebe:,.0f} €")
    
    with col3:
        if last_year in ratios_results:
            rentabilite = ratios_results[last_year].get('rentabilite_net', '0%')
            st.metric("Rentabilité nette", rentabilite)
    
    with col4:
        bfr = current_data.get('bfr', 0)
        bfr_color = current_health.get('bfr_color', 'gray')
        st.metric("BFR", f"{bfr:,.0f} €")
    
    with col5:
        tn = current_data.get('tn', 0)
        tn_health = current_health.get('tn_health', '')
        st.metric("Trésorerie Nette", f"{tn:,.0f} €")
    
    st.markdown("---")

def display_overview(df, sig_results, ratios_results, working_capital_results):
    """Onglet Vue d'ensemble"""
    st.header("📈 Vue d'ensemble financière")
    
    if not sig_results:
        st.info("Aucune donnée disponible pour l'analyse")
        return
    
    # Graphiques principaux
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Évolution du Chiffre d'Affaires et EBE")
        fig_ca_ebe = create_ca_ebe_chart(sig_results)
        st.plotly_chart(fig_ca_ebe, use_container_width=True)
    
    with col2:
        st.subheader("Évolution de la Rentabilité")
        fig_rentability = create_rentability_chart(ratios_results)
        st.plotly_chart(fig_rentability, use_container_width=True)
    
    # Graphique des indicateurs de trésorerie
    st.subheader("Synthèse de la Trésorerie")
    fig_tresorerie = create_tresorerie_synthesis_chart(working_capital_results)
    st.plotly_chart(fig_tresorerie, use_container_width=True)
    
    # Alertes automatiques
    display_automatic_alerts(sig_results, ratios_results, working_capital_results)

def display_soldes_intermediaires(sig_results):
    """Onglet Soldes Intermédiaires de Gestion"""
    st.header("💰 Soldes Intermédiaires de Gestion")
    
    if not sig_results:
        st.info("Aucune donnée disponible pour les soldes intermédiaires")
        return
    
    # Tableau des SIG
    sig_df = pd.DataFrame(sig_results).T
    sig_df_formatted = sig_df.applymap(lambda x: f"{x:,.0f} €" if isinstance(x, (int, float)) else x)
    
    st.dataframe(sig_df_formatted, use_container_width=True)
    
    # Graphique en cascade
    st.subheader("Construction du résultat")
    if len(sig_results) > 0:
        last_year = max(sig_results.keys())
        fig_waterfall = create_waterfall_chart(sig_results[last_year], last_year)
        st.plotly_chart(fig_waterfall, use_container_width=True)
    
    # Évolution des SIG
    st.subheader("Évolution des principaux soldes")
    fig_evolution = create_sig_evolution_chart(sig_results)
    st.plotly_chart(fig_evolution, use_container_width=True)

def display_ratios_financiers(ratios_results):
    """Onglet Ratios Financiers"""
    st.header("📊 Analyse des Ratios Financiers")
    
    if not ratios_results:
        st.info("Aucune donnée disponible pour les ratios financiers")
        return
    
    # Tableau des ratios
    ratios_df = pd.DataFrame(ratios_results).T
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ratios de Rentabilité")
        rentability_data = {
            'Année': list(ratios_results.keys()),
            'Rentabilité Nette': [r['rentabilite_net'] for r in ratios_results.values()],
            'Résultat Net (k€)': [f"{r['resultat_net']/1000:,.0f}" for r in ratios_results.values()]
        }
        st.dataframe(pd.DataFrame(rentability_data), use_container_width=True)
        
        # Graphique de rentabilité
        fig_rent = create_rentability_detail_chart(ratios_results)
        st.plotly_chart(fig_rent, use_container_width=True)
    
    with col2:
        st.subheader("Ratios de Structure")
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

def display_working_capital_analysis(working_capital_results, health_analysis):
    """Onglet Analyse BFR/FR/TN"""
    st.header("🔄 Analyse du Fonds de Roulement")
    
    if not working_capital_results:
        st.info("Données insuffisantes pour calculer le fonds de roulement")
        return
    
    # Métriques principales
    last_year = max(working_capital_results.keys())
    current_data = working_capital_results[last_year]
    current_health = health_analysis[last_year]
    
    st.subheader("Indicateurs de Trésorerie - Dernière Exercice")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "CAF", 
            f"{current_data['caf']:,.0f} €",
            help="Capacité d'Autofinancement"
        )
        st.markdown(f"<div style='color: black;'>{current_health['caf_health']}</div>", 
                   unsafe_allow_html=True)
    
    with col2:
        st.metric(
            "BFR", 
            f"{current_data['bfr']:,.0f} €",
            help="Besoin en Fonds de Roulement"
        )
        st.markdown(f"<div style='color: {current_health['bfr_color']};'>{current_health['bfr_health']}</div>", 
                   unsafe_allow_html=True)
    
    with col3:
        st.metric(
            "FR", 
            f"{current_data['fr']:,.0f} €",
            help="Fonds de Roulement"
        )
        st.markdown(f"<div style='color: {current_health['fr_color']};'>{current_health['fr_health']}</div>", 
                   unsafe_allow_html=True)
    
    with col4:
        st.metric(
            "TN", 
            f"{current_data['tn']:,.0f} €",
            help="Trésorerie Nette"
        )
        st.markdown(f"<div style='color: {current_health['tn_color']};'>{current_health['tn_health']}</div>", 
                   unsafe_allow_html=True)
    
    # Tableau d'évolution
    st.subheader("Évolution des indicateurs de trésorerie")
    evolution_data = []
    for year in sorted(working_capital_results.keys()):
        data = working_capital_results[year]
        health = health_analysis[year]
        evolution_data.append({
            'Année': year,
            'CAF (k€)': f"{data['caf']/1000:.0f}",
            'BFR (k€)': f"{data['bfr']/1000:.0f}",
            'FR (k€)': f"{data['fr']/1000:.0f}",
            'TN (k€)': f"{data['tn']/1000:.0f}",
            'Santé FR': health['fr_health'],
            'Santé BFR': health['bfr_health']
        })
    
    evolution_df = pd.DataFrame(evolution_data)
    st.dataframe(evolution_df, use_container_width=True)
    
    # Graphique d'évolution
    fig = create_working_capital_chart(working_capital_results)
    st.plotly_chart(fig, use_container_width=True)
    
    # Analyse détaillée
    st.subheader("📋 Analyse détaillée du fonds de roulement")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Composition du BFR**")
        bfr_data = {
            'Composant': ['Actif Circulant', 'Passif Circulant', 'BFR Net'],
            f'Valeur {last_year} (k€)': [
                f"{current_data['actif_circulant']/1000:.0f}",
                f"{current_data['passif_circulant']/1000:.0f}",
                f"{current_data['bfr']/1000:.0f}"
            ]
        }
        st.dataframe(pd.DataFrame(bfr_data), use_container_width=True)
    
    with col2:
        st.markdown("**Composition du FR**")
        fr_data = {
            'Composant': ['Capitaux Permanents', 'Actif Immobilisé', 'FR Net'],
            f'Valeur {last_year} (k€)': [
                f"{current_data['capitaux_permanents']/1000:.0f}",
                f"{current_data['actif_immobilise']/1000:.0f}",
                f"{current_data['fr']/1000:.0f}"
            ]
        }
        st.dataframe(pd.DataFrame(fr_data), use_container_width=True)
    
    # Diagnostic de santé
    st.subheader("🏥 Diagnostic de santé financière")
    
    diagnostic_messages = []
    
    if current_health['fr_color'] == 'red':
        diagnostic_messages.append("❌ **Problème structurel** : Le Fonds de Roulement est négatif, indiquant un déséquilibre financier structurel.")
    
    if current_health['tn_color'] == 'red':
        diagnostic_messages.append("⚠️ **Problème de trésorerie** : La trésorerie nette est négative, risque de liquidité à court terme.")
    
    if current_health['caf_bfr_ratio'] < 1 and current_data['bfr'] > 0:
        diagnostic_messages.append("📉 **Couverture insuffisante** : La CAF ne couvre pas suffisamment le BFR.")
    
    if current_data['caf'] < 0:
        diagnostic_messages.append("💸 **CAF négative** : L'entreprise ne génère pas suffisamment de ressources internes.")
    
    if not diagnostic_messages:
        diagnostic_messages.append("✅ **Situation saine** : Tous les indicateurs de trésorerie sont positifs.")
    
    for message in diagnostic_messages:
        st.markdown(message)

def display_risk_prediction(processor, prediction_features, confidence_threshold, entreprise_nom):
    """Onglet Prédiction du Risque"""
    st.header("🎯 Prédiction du Risque de Crédit")
    
    if processor.model is None:
        st.warning("""
        ⚠️ **Modèle de prédiction non disponible** 
        
        Pour activer les prédictions IA :
        1. Entraînez d'abord un modèle sur des données historiques
        2. Sauvegardez-le sous 'modele_risque_credit.pkl'
        3. Placez-le dans le même dossier que cette application
        """)
        return
    
    if prediction_features is None:
        st.error("Impossible de préparer les features pour la prédiction.")
        return
    
    try:
        # Prédiction
        prediction = processor.model.predict(prediction_features)[0]
        probability = processor.model.predict_proba(prediction_features)[0][1]
        confidence = max(probability, 1 - probability)
        
        # Affichage des résultats
        st.subheader(f"Résultat pour {entreprise_nom}")
        
        if confidence < confidence_threshold:
            st.warning(f"⚠️ **Prédiction peu fiable** (confiance: {confidence:.1%})")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Jauge de risque
            fig_gauge = create_risk_gauge(probability)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col2:
            if prediction == 1:
                st.markdown(f"""
                <div class="risk-high">
                    <h3>🚨 RISQUE ÉLEVÉ DE DÉFAUT</h3>
                    <p>Probabilité estimée : <strong>{probability:.1%}</strong></p>
                    <p>L'entreprise présente des signaux financiers préoccupants nécessitant une attention particulière.</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.info("""
                **Recommandations :**
                - Analyser en détail la structure financière
                - Vérifier la capacité de remboursement
                - Mettre en place un suivi renforcé
                - Considérer des garanties supplémentaires
                """)
            else:
                st.markdown(f"""
                <div class="risk-low">
                    <h3>✅ RISQUE FAIBLE DE DÉFAUT</h3>
                    <p>Probabilité estimée : <strong>{probability:.1%}</strong></p>
                    <p>L'entreprise présente une situation financière saine avec un faible risque de défaut.</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.success("""
                **Perspectives favorables :**
                - Structure financière équilibrée
                - Capacité de remboursement satisfaisante
                - Risque de crédit limité
                """)
        
        # Facteurs d'influence
        st.subheader("🔍 Facteurs d'influence")
        if hasattr(processor.model, 'feature_importances_'):
            display_feature_importance(processor.model, prediction_features)
        else:
            st.info("L'analyse détaillée des facteurs d'influence n'est pas disponible pour ce modèle.")
    
    except Exception as e:
        st.error(f"Erreur lors de la prédiction : {str(e)}")

def display_raw_data(df_consolide, sig_results, ratios_results, working_capital_results):
    """Onglet Données Brutes"""
    st.header("📋 Données Brutes et Export")
    
    st.subheader("Données consolidées")
    st.dataframe(df_consolide, use_container_width=True)
    
    # Export des données
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Exporter données consolidées CSV"):
            csv = df_consolide.to_csv(index=False)
            st.download_button(
                label="Télécharger CSV",
                data=csv,
                file_name="donnees_consolidees.csv",
                mime="text/csv"
            )
    
    with col2:
        if sig_results:
            sig_df = pd.DataFrame(sig_results).T
            csv_sig = sig_df.to_csv()
            st.download_button(
                label="📥 Exporter SIG CSV",
                data=csv_sig,
                file_name="soldes_intermediaires.csv",
                mime="text/csv"
            )
    
    with col3:
        if ratios_results:
            ratios_df = pd.DataFrame(ratios_results).T
            csv_ratios = ratios_df.to_csv()
            st.download_button(
                label="📥 Exporter ratios CSV",
                data=csv_ratios,
                file_name="ratios_financiers.csv",
                mime="text/csv"
            )
    
    # Statistiques descriptives
    st.subheader("Statistiques descriptives")
    if not df_consolide.empty:
        st.dataframe(df_consolide['amount'].describe(), use_container_width=True)

def display_welcome_message():
    """Message d'accueil"""
    st.markdown("""
    <div style='text-align: center; padding: 4rem;'>
        <h2>🚀 Bienvenue dans l'analyseur de risque de crédit</h2>
        <p style='font-size: 1.2rem; margin-bottom: 2rem;'>
            Commencez par charger les états financiers dans la sidebar 👈
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h3>📊 Bilan</h3>
            <p>Actif et passif de l'entreprise</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h3>💰 Compte de résultat</h3>
            <p>Produits et charges</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h3>🔄 Flux de trésorerie</h3>
            <p>Mouvements de cash</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.info("""
    **Format des fichiers attendu :**
    - Fichiers Excel (.xlsx ou .xls)
    - Colonnes : compte, libellé, 2021, 2022, 2023...
    - Plan comptable général français
    - Montants en euros
    """)

# Fonctions de création de graphiques
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

def create_rentability_chart(ratios_results):
    """Crée un graphique de rentabilité"""
    years = sorted(ratios_results.keys())
    rentability_values = [float(r['rentabilite_net'].replace('%', '')) for r in ratios_results.values()]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=rentability_values, 
        mode='lines+markers', 
        name='Rentabilité nette (%)',
        line=dict(color='purple', width=3)
    ))
    
    fig.update_layout(
        title="Évolution de la rentabilité nette",
        yaxis_title="Rentabilité nette (%)",
        height=400
    )
    return fig

def create_tresorerie_synthesis_chart(working_capital_results):
    """Crée un graphique de synthèse de la trésorerie"""
    if not working_capital_results:
        return go.Figure()
    
    years = sorted(working_capital_results.keys())
    caf_values = [wc['caf'] for wc in working_capital_results.values()]
    bfr_values = [wc['bfr'] for wc in working_capital_results.values()]
    fr_values = [wc['fr'] for wc in working_capital_results.values()]
    tn_values = [wc['tn'] for wc in working_capital_results.values()]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=caf_values, name='CAF', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=years, y=bfr_values, name='BFR', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=years, y=fr_values, name='FR', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=years, y=tn_values, name='TN', line=dict(color='purple', dash='dash')))
    
    fig.update_layout(
        title="Synthèse des indicateurs de trésorerie",
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
    rentability_values = [float(r['rentabilite_net'].replace('%', '')) for r in ratios_results.values()]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, 
        y=rentability_values,
        marker_color=['green' if x >= 0 else 'red' for x in rentability_values]
    ))
    
    fig.update_layout(
        title="Rentabilité nette par année",
        yaxis_title="Rentabilité nette (%)",
        height=300
    )
    return fig

def create_radar_chart(ratio_data, year):
    """Crée un radar chart pour les ratios"""
    categories = ['Rentabilité', 'Autonomie', 'Liquidité']
    
    # Normalisation des valeurs pour le radar chart
    rentability = float(ratio_data['rentabilite_net'].replace('%', '')) / 20  # Normalisation
    autonomie = float(ratio_data['ratio_autonomie'].replace('%', '')) / 100   # Normalisation
    liquidite = min(float(ratio_data['ratio_liquidite']) / 2, 1)              # Normalisation
    
    values = [rentability, autonomie, liquidite]
    
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

def create_working_capital_chart(working_capital_results):
    """Crée un graphique d'évolution du fonds de roulement"""
    years = sorted(working_capital_results.keys())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=years, 
        y=[working_capital_results[y]['caf']/1000 for y in years],
        name='CAF (k€)',
        line=dict(color='green', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=years, 
        y=[working_capital_results[y]['bfr']/1000 for y in years],
        name='BFR (k€)',
        line=dict(color='orange', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=years, 
        y=[working_capital_results[y]['fr']/1000 for y in years],
        name='FR (k€)',
        line=dict(color='blue', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=years, 
        y=[working_capital_results[y]['tn']/1000 for y in years],
        name='TN (k€)',
        line=dict(color='purple', width=3, dash='dash')
    ))
    
    fig.update_layout(
        title="Évolution des indicateurs de trésorerie",
        xaxis_title="Année",
        yaxis_title="Montant (k€)",
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_risk_gauge(probability):
    """Crée une jauge de risque"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = probability * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Probabilité de Défaut"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 20], 'color': "lightgreen"},
                {'range': [20, 50], 'color': "yellow"},
                {'range': [50, 100], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=300)
    return fig

def display_feature_importance(model, features):
    """Affiche l'importance des features"""
    if hasattr(model, 'feature_importances_'):
        feature_importance = pd.DataFrame({
            'feature': [f'Feature {i}' for i in range(len(model.feature_importances_))],
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=True)
        
        fig = px.bar(
            feature_importance.tail(10), 
            x='importance', 
            y='feature', 
            orientation='h',
            title="Top 10 des facteurs d'influence"
        )
        st.plotly_chart(fig, use_container_width=True)

def display_automatic_alerts(sig_results, ratios_results, working_capital_results):
    """Affiche les alertes automatiques"""
    if not sig_results or not working_capital_results:
        return
    
    last_year = max(sig_results.keys())
    current_sig = sig_results[last_year]
    current_ratios = ratios_results.get(last_year, {})
    current_wc = working_capital_results.get(last_year, {})
    
    alerts = []
    
    # Alertes sur la rentabilité
    if last_year in ratios_results:
        rentability = float(current_ratios['rentabilite_net'].replace('%', ''))
        if rentability < 0:
            alerts.append("**Rentabilité négative**")
        elif rentability < 2:
            alerts.append("**Rentabilité faible** (< 2%)")
    
    # Alertes sur la trésorerie
    if current_wc.get('tn', 0) < 0:
        alerts.append("**Trésorerie nette négative**")
    
    if current_wc.get('fr', 0) < 0:
        alerts.append("**Fonds de roulement négatif**")
    
    if current_wc.get('caf', 0) < 0:
        alerts.append("**CAF négative**")
    
    # Alertes sur l'endettement
    if last_year in ratios_results:
        endettement = float(current_ratios['ratio_endettement'])
        if endettement > 2:
            alerts.append("**Endettement élevé** (> 200%)")
    
    if alerts:
        st.subheader("Alertes automatiques")
        for alert in alerts:
            st.markdown(f"- {alert}")

if __name__ == "__main__":
    main()