# Version complète avec prepare_prediction_features

import pandas as pd
import numpy as np
import joblib
import os
from sklearn.preprocessing import StandardScaler

class FinancialDataProcessor:
    def __init__(self, model_path='modele_risque_credit.pkl', scaler_path='scaler.pkl'):
        try:
            self.model = joblib.load(model_path) if model_path and os.path.exists(model_path) else None
            self.scaler = joblib.load(scaler_path) if scaler_path and os.path.exists(scaler_path) else None
        except:
            self.model = None
            self.scaler = None
    
    def load_excel_data(self, bilan_file, cpc_file, flux_file):
        """Charge les données Excel et les transforme au format standard"""
        data_frames = []
        
        # Chargement Bilan
        df_bilan = pd.read_excel(bilan_file)
        df_bilan = self._reshape_financial_data(df_bilan, 'BILAN')
        data_frames.append(df_bilan)
        
        # Chargement CPC
        df_cpc = pd.read_excel(cpc_file)
        df_cpc = self._reshape_financial_data(df_cpc, 'CPC')
        data_frames.append(df_cpc)
        
        # Chargement Flux de Trésorerie si fourni
        if flux_file is not None:
            try:
                df_flux = pd.read_excel(flux_file)
                df_flux = self._reshape_financial_data(df_flux, 'FLUX_TRESORERIE')
                data_frames.append(df_flux)
            except Exception as e:
                print(f"Attention: Impossible de charger le fichier flux: {e}")
        
        # Consolidation
        if data_frames:
            consolidated_df = pd.concat(data_frames, ignore_index=True)
            
            # Nettoyage et conversion des types
            consolidated_df = self._clean_dataframe(consolidated_df)
            
            return consolidated_df
        else:
            return pd.DataFrame()
    
    def _clean_dataframe(self, df):
        """Nettoie et convertit les types de données"""
        df = df.copy()
        
        # Conversion des codes comptables en string
        if 'account_code' in df.columns:
            df['account_code'] = df['account_code'].astype(str)
        
        # Conversion des libellés en string
        if 'account_label' in df.columns:
            df['account_label'] = df['account_label'].astype(str)
        
        # Conversion des années en int
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(0).astype(int)
        
        # Conversion des montants en float
        if 'amount' in df.columns:
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
        
        return df
    
    def _reshape_financial_data(self, df, source):
        """Transforme les données Excel au format long"""
        # Suppression des lignes vides
        df = df.dropna(subset=[df.columns[0]])  # Première colonne (compte)
        
        # Vérification des colonnes
        required_columns = ['compte', 'libellé']
        if not all(col in df.columns for col in required_columns):
            print(f"Colonnes manquantes dans le fichier {source}. Attendu: {required_columns}")
            return pd.DataFrame()
        
        # Identification des colonnes d'années (celles qui sont numériques)
        year_columns = []
        for col in df.columns:
            if col not in ['compte', 'libellé']:
                try:
                    # Essaye de convertir en numérique
                    pd.to_numeric(col)
                    year_columns.append(col)
                except:
                    # Si ce n'est pas numérique, on ignore
                    pass
        
        if not year_columns:
            print(f"Aucune colonne d'année trouvée dans le fichier {source}")
            return pd.DataFrame()
        
        # Transformation au format long
        df_melted = df.melt(
            id_vars=['compte', 'libellé'],
            value_vars=year_columns,
            var_name='year',
            value_name='amount'
        )
        
        # Conversion des types
        df_melted['compte'] = df_melted['compte'].astype(str)
        df_melted['libellé'] = df_melted['libellé'].astype(str)
        df_melted['year'] = pd.to_numeric(df_melted['year'], errors='coerce').fillna(0).astype(int)
        df_melted['amount'] = pd.to_numeric(df_melted['amount'], errors='coerce').fillna(0)
        
        # Détermination de la nature du compte
        df_melted['source'] = source
        df_melted['nature'] = df_melted['compte'].apply(
            lambda x: self._determine_nature(x, source)
        )
        
        # Renommage des colonnes
        df_melted = df_melted.rename(columns={
            'compte': 'account_code',
            'libellé': 'account_label'
        })
        
        return df_melted[['account_code', 'account_label', 'year', 'amount', 'source', 'nature']]
    
    def _determine_nature(self, account_code, source):
        """Détermine la nature du compte"""
        account_code = str(account_code)
        
        if source == 'CPC':
            if account_code.startswith(('7', '706', '708')):
                return 'produit'
            else:
                return 'charge'
        
        elif source == 'BILAN':
            if account_code.startswith(('2', '3', '4', '5')):
                return 'actif'
            else:
                return 'passif'
        
        elif source == 'FLUX_TRESORERIE':
            if account_code.endswith('1'):
                if 'encaissement' in account_code.lower():
                    return 'encaissement'
                elif 'investissement' in account_code.lower():
                    return 'investissement'
                elif 'financement' in account_code.lower():
                    return 'financement'
                else:
                    return 'decaissement_exploitation'
        
        return 'autre'
    
    def prepare_prediction_features(self, df, sig_results, ratios_results, working_capital_results):
        """
        Prépare les features pour la prédiction en utilisant tous les indicateurs calculés
        """
        try:
            features_list = []
            
            if not sig_results or not ratios_results or not working_capital_results:
                return None
            
            for year in sorted(sig_results.keys()):
                if year in ratios_results and year in working_capital_results:
                    features = {}
                    
                    # === FEATURES DES SIG ===
                    sig = sig_results[year]
                    features['chiffre_affaires'] = sig.get('chiffre_affaires', 0)
                    features['marge_commerciale'] = sig.get('marge_commerciale', 0)
                    features['valeur_ajoutee'] = sig.get('valeur_ajoutee', 0)
                    features['ebe'] = sig.get('ebe', 0)
                    features['resultat_net'] = sig.get('resultat_net', 0)
                    
                    # Ratios de marge
                    features['marge_commerciale_pct'] = (sig.get('marge_commerciale', 0) / sig.get('chiffre_affaires', 1)) * 100 if sig.get('chiffre_affaires', 0) > 0 else 0
                    features['marge_ebe_pct'] = (sig.get('ebe', 0) / sig.get('chiffre_affaires', 1)) * 100 if sig.get('chiffre_affaires', 0) > 0 else 0
                    features['marge_nette_pct'] = (sig.get('resultat_net', 0) / sig.get('chiffre_affaires', 1)) * 100 if sig.get('chiffre_affaires', 0) > 0 else 0
                    
                    # === FEATURES DES RATIOS ===
                    ratios = ratios_results[year]
                    features['rentabilite_nette'] = float(ratios.get('rentabilite_nette', '0%').replace('%', '')) if ratios.get('rentabilite_nette') != 'N/A' else 0
                    features['ratio_endettement'] = float(ratios.get('ratio_endettement', 0)) if ratios.get('ratio_endettement') != 'N/A' else 0
                    features['ratio_liquidite'] = float(ratios.get('ratio_liquidite', 0)) if ratios.get('ratio_liquidite') != 'N/A' else 0
                    features['ratio_autonomie'] = float(ratios.get('ratio_autonomie', '0%').replace('%', '')) if ratios.get('ratio_autonomie') != 'N/A' else 0
                    
                    # === FEATURES TRÉSORERIE (BFR/FR/TN/CAF) ===
                    wc = working_capital_results[year]
                    features['caf'] = wc.get('caf', 0)
                    features['bfr'] = wc.get('bfr', 0)
                    features['fr'] = wc.get('fr', 0)
                    features['tn'] = wc.get('tn', 0)
                    
                    # Ratios de trésorerie
                    features['caf_sur_ca'] = (wc.get('caf', 0) / sig.get('chiffre_affaires', 1)) * 100 if sig.get('chiffre_affaires', 0) > 0 else 0
                    features['bfr_sur_ca'] = (wc.get('bfr', 0) / sig.get('chiffre_affaires', 1)) * 100 if sig.get('chiffre_affaires', 0) > 0 else 0
                    features['fr_sur_ca'] = (wc.get('fr', 0) / sig.get('chiffre_affaires', 1)) * 100 if sig.get('chiffre_affaires', 0) > 0 else 0
                    
                    # Ratios de couverture
                    features['caf_couv_bfr'] = wc.get('caf', 0) / abs(wc.get('bfr', 1)) if wc.get('bfr', 0) != 0 else 0
                    features['fr_couv_bfr'] = wc.get('fr', 0) / abs(wc.get('bfr', 1)) if wc.get('bfr', 0) != 0 else 0
                    
                    # === FEATURES DE CROISSANCE ===
                    # Croissance du CA
                    if year > min(sig_results.keys()):
                        prev_year = year - 1
                        if prev_year in sig_results:
                            ca_croissance = ((sig.get('chiffre_affaires', 0) - sig_results[prev_year].get('chiffre_affaires', 0)) 
                                           / sig_results[prev_year].get('chiffre_affaires', 1)) * 100
                            features['croissance_ca'] = ca_croissance
                        else:
                            features['croissance_ca'] = 0
                    else:
                        features['croissance_ca'] = 0
                    
                    # Croissance de l'EBE
                    if year > min(sig_results.keys()):
                        prev_year = year - 1
                        if prev_year in sig_results:
                            ebe_croissance = ((sig.get('ebe', 0) - sig_results[prev_year].get('ebe', 0)) 
                                            / abs(sig_results[prev_year].get('ebe', 1))) * 100 if sig_results[prev_year].get('ebe', 0) != 0 else 0
                            features['croissance_ebe'] = ebe_croissance
                        else:
                            features['croissance_ebe'] = 0
                    else:
                        features['croissance_ebe'] = 0
                    
                    features['year'] = year
                    features_list.append(features)
            
            if not features_list:
                return None
            
            features_df = pd.DataFrame(features_list)
            
            # Prendre la dernière année pour la prédiction
            latest_features = features_df[features_df['year'] == max(features_df['year'])].drop('year', axis=1)
            
            if latest_features.empty:
                return None
            
            return latest_features
            
        except Exception as e:
            print(f"Erreur dans prepare_prediction_features: {e}")
            return None
    
    def predict_risk(self, features_df):
        """Effectue la prédiction du risque"""
        if self.model is None or features_df is None:
            return None, None, None
        
        try:
            # Standardisation des features si le scaler est disponible
            if self.scaler is not None:
                features_scaled = self.scaler.transform(features_df)
            else:
                features_scaled = features_df.values
            
            # Prédiction
            prediction = self.model.predict(features_scaled)[0]
            probability = self.model.predict_proba(features_scaled)[0][1]
            
            # Importance des features si disponible
            feature_importance = None
            if hasattr(self.model, 'feature_importances_'):
                feature_importance = dict(zip(features_df.columns, self.model.feature_importances_))
            
            return prediction, probability, feature_importance
            
        except Exception as e:
            print(f"Erreur lors de la prédiction: {e}")
            return None, None, None