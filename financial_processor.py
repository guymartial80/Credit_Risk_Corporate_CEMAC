import pandas as pd
import numpy as np
import streamlit as st
import joblib
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

class FinancialDataProcessor:
    def __init__(self, model_path='modele_risque_credit.pkl', scaler_path='scaler.pkl'):
        self.model = joblib.load(model_path) if os.path.exists(model_path) else None
        self.scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None
        
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
        
        # Chargement Flux de Trésorerie
        df_flux = pd.read_excel(flux_file)
        df_flux = self._reshape_financial_data(df_flux, 'FLUX_TRESORERIE')
        data_frames.append(df_flux)
        
        # Consolidation
        consolidated_df = pd.concat(data_frames, ignore_index=True)
        return consolidated_df
    
    def _reshape_financial_data(self, df, source):
        """Transforme les données Excel au format long"""
        # Suppression des lignes vides
        df = df.dropna(subset=['compte'])
        
        # Transformation au format long
        df_melted = df.melt(
            id_vars=['compte', 'libellé'],
            var_name='year',
            value_name='amount'
        )
        
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
        if source == 'CPC':
            if str(account_code).startswith(('7', '706', '708')):
                return 'produit'
            else:
                return 'charge'
        
        elif source == 'BILAN':
            if str(account_code).startswith(('2', '3', '4', '5')):
                return 'actif'
            else:
                return 'passif'
        
        elif source == 'FLUX_TRESORERIE':
            if str(account_code).endswith('1'):
                if 'encaissement' in str(account_code).lower():
                    return 'encaissement'
                elif 'investissement' in str(account_code).lower():
                    return 'investissement'
                elif 'financement' in str(account_code).lower():
                    return 'financement'
                else:
                    return 'decaissement_exploitation'
        
        return 'autre'