"""
Script de traitement des données Base Impacts pour Holis
Auteur: Assistant IA
Date: 2026-01-29
"""

import pandas as pd
import numpy as np

def load_and_clean_metadata(filepath):
    """
    Charge et nettoie les métadonnées des procédés
    
    Structure du fichier:
    - Ligne 0: Headers génériques (attributs)
    - Colonnes: Chaque colonne = un procédé
    - ATTENTION: Ligne 1 contient le mot "UUID" pas les valeurs!
    """
    # Charger le fichier
    df = pd.read_excel(filepath)
    
    # Transposer pour avoir les procédés en lignes
    df_transposed = df.T
    
    # La première ligne contient les noms des attributs
    df_transposed.columns = df_transposed.iloc[0]
    
    # Retirer la première ligne (headers) ET la deuxième (qui contient "UUID", "Nom du flux", etc.)
    df_transposed = df_transposed[2:].reset_index(drop=True)
    
    # Nettoyer les noms de colonnes (espaces)
    df_transposed.columns = df_transposed.columns.str.strip()
    
    # CRUCIAL : Nettoyer les espaces dans les UUID !
    if 'UUID' in df_transposed.columns:
        df_transposed['UUID'] = df_transposed['UUID'].str.strip()
    
    # Nettoyer aussi tous les autres champs texte
    string_columns = df_transposed.select_dtypes(include=['object']).columns
    for col in string_columns:
        df_transposed[col] = df_transposed[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    
    return df_transposed


def load_and_clean_impacts(filepath):
    """
    Charge et nettoie les données d'impacts
    
    Structure:
    - Colonne 0: UUID catégorie d'impact
    - Colonnes suivantes: UUID des procédés (valeurs d'impact)
    - Ligne 0: Headers
    - Lignes 1+: Valeurs d'impact
    """
    df = pd.read_csv(filepath, encoding='latin-1', sep=';')
    
    # La ligne 0 semble être un header descriptif
    # Enlever cette ligne et réinitialiser
    df = df.iloc[1:].reset_index(drop=True)
    
    # Renommer les premières colonnes pour clarté
    df = df.rename(columns={
        "UUID de la catégorie d'impacts": "impact_category_uuid",
        "Nom anglais": "impact_name_en",
        "Nom français": "impact_name_fr",
        "Unité": "unit"
    })
    
    return df


def load_and_clean_indicators(filepath):
    """
    Charge et nettoie les détails des catégories d'impact
    
    Structure similaire aux métadonnées:
    - Headers multi-niveaux
    - Transposition nécessaire
    - Sauter la ligne de header
    """
    df = pd.read_excel(filepath)
    
    # Transposer
    df_transposed = df.T
    
    # Utiliser la première ligne comme noms de colonnes
    df_transposed.columns = df_transposed.iloc[0]
    
    # Retirer les 2 premières lignes (header + ligne "UUID", "Nom français", etc.)
    df_transposed = df_transposed[2:].reset_index(drop=True)
    
    # Nettoyer les noms de colonnes
    df_transposed.columns = df_transposed.columns.str.strip()
    
    # Nettoyer les espaces dans les valeurs texte
    string_columns = df_transposed.select_dtypes(include=['object']).columns
    for col in string_columns:
        df_transposed[col] = df_transposed[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    
    return df_transposed


def reshape_impacts_to_long(impacts_df):
    """
    Transforme le DataFrame impacts de format wide à long
    
    Format wide: une colonne par procédé
    Format long: une ligne par (procédé, indicateur)
    """
    # Colonnes d'identification
    id_cols = ["impact_category_uuid", "impact_name_en", "impact_name_fr", "unit"]
    
    # Colonnes de valeurs (UUID des procédés)
    value_cols = [col for col in impacts_df.columns if col not in id_cols]
    
    # Melt pour passer en format long
    df_long = impacts_df.melt(
        id_vars=id_cols,
        value_vars=value_cols,
        var_name='process_uuid',
        value_name='impact_value'
    )
    
    # Convertir les valeurs en numérique
    df_long['impact_value'] = pd.to_numeric(df_long['impact_value'], errors='coerce')
    
    return df_long


def merge_all_data(metadata_df, impacts_long_df, indicators_df):
    """
    Fusionne les 3 DataFrames
    
    Returns:
        DataFrame avec toutes les données combinées
    """
    # Nettoyer les noms de colonnes (enlever les espaces)
    metadata_df.columns = metadata_df.columns.str.strip()
    indicators_df.columns = indicators_df.columns.str.strip()
    
    # Étape 1: Joindre impacts avec les indicateurs
    # On utilise UUID de la catégorie d'impact
    
    merged = impacts_long_df.merge(
        indicators_df,
        left_on='impact_category_uuid',
        right_on='UUID',
        how='left',
        suffixes=('', '_indicator')
    )
    
    # Étape 2: Joindre avec les métadonnées des procédés
    # On utilise l'UUID du procédé
    
    # Dans metadata_df, l'UUID est dans la colonne 'UUID'
    merged_final = merged.merge(
        metadata_df,
        left_on='process_uuid',
        right_on='UUID',
        how='left',
        suffixes=('', '_process')
    )
    
    return merged_final


def main():
    """Fonction principale pour tester le pipeline"""
    print("=" * 80)
    print("🚀 PIPELINE DE TRAITEMENT DES DONNÉES HOLIS")
    print("=" * 80)
    
    # Chemins des fichiers
    metadata_path = '/mnt/user-data/uploads/BI_2_02__02_Procedes_Details.xlsx'
    impacts_path = '/mnt/user-data/uploads/BI_2_02__03_Procedes_Impacts.csv'
    indicators_path = '/mnt/user-data/uploads/BI_2_02__06_CatImpacts_Details.xlsx'
    
    # Charger et nettoyer
    print("\n📂 Étape 1: Chargement des fichiers...")
    metadata = load_and_clean_metadata(metadata_path)
    impacts = load_and_clean_impacts(impacts_path)
    indicators = load_and_clean_indicators(indicators_path)
    
    print(f"✅ Métadonnées: {metadata.shape}")
    print(f"✅ Impacts: {impacts.shape}")
    print(f"✅ Indicateurs: {indicators.shape}")
    
    # Reshaper les impacts en format long
    print("\n🔄 Étape 2: Transformation des impacts en format long...")
    impacts_long = reshape_impacts_to_long(impacts)
    print(f"✅ Impacts (format long): {impacts_long.shape}")
    
    # Merger tout
    print("\n🔗 Étape 3: Fusion des données...")
    merged = merge_all_data(metadata, impacts_long, indicators)
    print(f"✅ Données fusionnées: {merged.shape}")
    
    # Afficher un aperçu
    print("\n" + "=" * 80)
    print("📊 APERÇU DES DONNÉES FUSIONNÉES")
    print("=" * 80)
    print(merged.head(10))
    
    print("\n" + "=" * 80)
    print("📈 STATISTIQUES")
    print("=" * 80)
    print(f"Nombre total de lignes: {len(merged):,}")
    print(f"Nombre de procédés uniques: {merged['process_uuid'].nunique()}")
    print(f"Nombre d'indicateurs uniques: {merged['impact_category_uuid'].nunique()}")
    print(f"Valeurs manquantes dans impact_value: {merged['impact_value'].isna().sum()}")
    
    # Sauvegarder
    print("\n💾 Sauvegarde des données...")
    metadata.to_csv('/home/claude/metadata_clean.csv', index=False)
    impacts_long.to_csv('/home/claude/impacts_long.csv', index=False)
    indicators.to_csv('/home/claude/indicators_clean.csv', index=False)
    merged.to_csv('/home/claude/merged_data.csv', index=False)
    print("✅ Fichiers sauvegardés dans /home/claude/")
    
    return metadata, impacts_long, indicators, merged


if __name__ == "__main__":
    metadata, impacts_long, indicators, merged = main()
