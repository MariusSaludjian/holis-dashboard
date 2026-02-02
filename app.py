"""
Dashboard Holis - Visualisation Base Impacts
=============================================
Application Streamlit pour explorer les données d'impacts environnementaux

Auteur: Test Technique Holis
Date: 2026-01-29
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Holis - Base Impacts",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E7D32;
    }
    .stMetric {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Charge les données (avec mise en cache)"""
    try:
        merged = pd.read_csv('merged_data.csv')
        metadata = pd.read_csv('metadata_clean.csv')
        impacts = pd.read_csv('impacts_long.csv')
        indicators = pd.read_csv('indicators_clean.csv')
        
        return merged, metadata, impacts, indicators
    except FileNotFoundError:
        st.error("❌ Fichiers de données non trouvés. Assurez-vous que les fichiers CSV sont dans le même dossier que app.py")
        st.stop()


def normalize_column(series):
    """Normalise une série entre 0 et 1"""
    min_val = series.min()
    max_val = series.max()
    if max_val - min_val == 0:
        return series * 0
    return (series - min_val) / (max_val - min_val)


def create_bar_chart(data, title):
    """Crée un graphique en barres des impacts"""
    fig = px.bar(
        data,
        x='impact_name_fr',
        y='impact_value',
        title=title,
        labels={'impact_name_fr': 'Indicateur d\'impact', 'impact_value': 'Valeur'},
        color='impact_value',
        color_continuous_scale='RdYlGn_r',
        hover_data=['unit']
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        showlegend=False,
        title_font_size=18,
        title_x=0.5
    )
    
    return fig


def create_radar_chart(data):
    """Crée un graphique radar normalisé"""
    # Normaliser les valeurs
    data_copy = data.copy()
    data_copy['impact_value_norm'] = normalize_column(data_copy['impact_value'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=data_copy['impact_value_norm'],
        theta=data_copy['impact_name_fr'],
        fill='toself',
        name='Impact normalisé',
        line_color='#2E7D32',
        fillcolor='rgba(46, 125, 50, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickformat='.0%'
            )
        ),
        showlegend=False,
        title="Profil Environnemental (valeurs normalisées)",
        title_x=0.5,
        height=500
    )
    
    return fig


def create_ranking_chart(data, indicator_name, top_n=10):
    """Crée un classement des procédés pour un indicateur"""
    filtered = data[data['impact_name_fr'] == indicator_name].copy()
    
    if len(filtered) == 0:
        return None
    
    # Trier et prendre le top N
    top_data = filtered.nlargest(top_n, 'impact_value')
    
    # Tronquer les noms de procédés trop longs
    top_data['process_short'] = top_data['process_uuid'].str[:50] + '...'
    
    fig = px.bar(
        top_data,
        y='process_short',
        x='impact_value',
        orientation='h',
        title=f'Top {top_n} des procédés - {indicator_name}',
        labels={'process_short': 'Procédé', 'impact_value': 'Valeur d\'impact'},
        color='impact_value',
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(
        height=500,
        showlegend=False,
        title_x=0.5,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig


def create_comparison_heatmap(data, process_list):
    """Crée une heatmap de comparaison de plusieurs procédés"""
    # Filtrer sur les procédés sélectionnés
    comparison_data = data[data['process_uuid'].isin(process_list)]
    
    # Pivoter
    pivot = comparison_data.pivot_table(
        values='impact_value',
        index='process_uuid',
        columns='impact_name_fr',
        aggfunc='sum'
    ).fillna(0)
    
    # Normaliser par colonne
    pivot_norm = pivot.apply(normalize_column, axis=0)
    
    # Tronquer les noms
    pivot_norm.index = [str(idx)[:40] + '...' for idx in pivot_norm.index]
    
    fig = px.imshow(
        pivot_norm,
        labels=dict(x="Indicateur", y="Procédé", color="Impact normalisé"),
        color_continuous_scale='RdYlGn_r',
        aspect='auto'
    )
    
    fig.update_layout(
        title="Comparaison des Profils Environnementaux",
        title_x=0.5,
        height=400
    )
    
    return fig


def main():
    """Fonction principale de l'application"""
    
    # Header
    st.markdown('<h1 class="main-header">🌱 Dashboard Holis - Base Impacts</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Chargement des données
    with st.spinner('Chargement des données...'):
        merged, metadata, impacts, indicators = load_data()
    
    # Sidebar - Configuration
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/2E7D32/FFFFFF?text=HOLIS", use_container_width=True)
        st.markdown("## 🎛️ Configuration")
        
        # Sélection du mode
        mode = st.radio(
            "Mode d'exploration",
            ["🔍 Explorer un procédé", "📊 Comparer des procédés", "🏆 Classements"],
            index=0
        )
        
        st.markdown("---")
        st.markdown("### 📈 Statistiques Globales")
        st.metric("Nombre de procédés", f"{merged['process_uuid'].nunique():,}")
        st.metric("Nombre d'indicateurs", f"{merged['impact_category_uuid'].nunique()}")
        st.metric("Combinaisons analysées", f"{len(merged):,}")
    
    # Contenu principal selon le mode
    if mode == "🔍 Explorer un procédé":
        show_process_explorer(merged, metadata)
    
    elif mode == "📊 Comparer des procédés":
        show_process_comparison(merged)
    
    elif mode == "🏆 Classements":
        show_rankings(merged)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        Dashboard créé pour le test technique Holis | Base Impacts v2.02 | 
        Données issues de l'ADEME
        </div>
        """,
        unsafe_allow_html=True
    )


def show_process_explorer(merged, metadata):
    """Affiche l'explorateur de procédé individuel"""
    
    st.header("🔍 Explorateur de Procédé")
    
    # Sélection du procédé
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Liste des procédés uniques
        process_list = sorted(merged['process_uuid'].unique())
        selected_process = st.selectbox(
            "Sélectionnez un procédé:",
            process_list,
            index=0
        )
    
    with col2:
        # Option de recherche
        search_term = st.text_input("🔎 Rechercher", placeholder="Tapez pour filtrer...")
        if search_term:
            filtered_processes = [p for p in process_list if search_term.lower() in p.lower()]
            if filtered_processes:
                selected_process = st.selectbox(
                    "Résultats de recherche:",
                    filtered_processes,
                    key="search_select"
                )
    
    # Filtrer les données pour ce procédé
    process_data = merged[merged['process_uuid'] == selected_process].copy()
    
    if len(process_data) == 0:
        st.warning("Aucune donnée disponible pour ce procédé.")
        return
    
    st.markdown("---")
    
    # Section Métadonnées
    st.subheader("📋 Métadonnées du Procédé")
    
    # Afficher les métadonnées principales
    meta_cols = st.columns(3)
    
    with meta_cols[0]:
        st.markdown("**UUID:**")
        st.code(selected_process, language=None)
    
    with meta_cols[1]:
        if 'Nom du flux' in process_data.columns and not process_data['Nom du flux'].isna().all():
            st.markdown("**Nom du flux:**")
            st.write(process_data['Nom du flux'].iloc[0])
    
    with meta_cols[2]:
        if 'Version' in process_data.columns and not process_data['Version'].isna().all():
            st.markdown("**Version:**")
            st.write(process_data['Version'].iloc[0])
    
    # Tableau détaillé des métadonnées
    with st.expander("📄 Voir toutes les métadonnées"):
        # Sélectionner les colonnes intéressantes
        meta_cols_to_show = [
            col for col in process_data.columns 
            if not col.startswith('impact_') and col != 'process_uuid'
        ]
        
        if meta_cols_to_show:
            meta_display = process_data[meta_cols_to_show].iloc[0].to_frame(name='Valeur')
            meta_display.index.name = 'Attribut'
            st.dataframe(meta_display, use_container_width=True)
    
    st.markdown("---")
    
    # Section Impacts Environnementaux
    st.subheader("🌍 Impacts Environnementaux")
    
    # Tabs pour différentes visualisations
    tab1, tab2, tab3 = st.tabs(["📊 Graphique en Barres", "🎯 Graphique Radar", "📋 Tableau de Données"])
    
    with tab1:
        # Graphique en barres
        fig_bar = create_bar_chart(
            process_data,
            f"Impacts Environnementaux - {selected_process[:50]}..."
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Insights
        max_impact = process_data.loc[process_data['impact_value'].idxmax()]
        st.info(f"💡 **Impact le plus élevé:** {max_impact['impact_name_fr']} ({max_impact['impact_value']:.2e} {max_impact['unit']})")
    
    with tab2:
        # Graphique radar
        fig_radar = create_radar_chart(process_data)
        st.plotly_chart(fig_radar, use_container_width=True)
        st.caption("Les valeurs sont normalisées entre 0 et 100% pour permettre la comparaison visuelle.")
    
    with tab3:
        # Tableau de données
        display_data = process_data[['impact_name_fr', 'impact_value', 'unit']].copy()
        display_data.columns = ['Indicateur', 'Valeur', 'Unité']
        display_data = display_data.sort_values('Valeur', ascending=False)
        
        st.dataframe(
            display_data.style.format({'Valeur': '{:.2e}'}),
            use_container_width=True,
            hide_index=True
        )
        
        # Bouton de téléchargement
        csv = display_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger les données (CSV)",
            data=csv,
            file_name=f"impacts_{selected_process[:30]}.csv",
            mime="text/csv"
        )


def show_process_comparison(merged):
    """Affiche la comparaison de plusieurs procédés"""
    
    st.header("📊 Comparaison de Procédés")
    
    # Sélection des procédés à comparer
    st.markdown("Sélectionnez 2 à 5 procédés à comparer:")
    
    process_list = sorted(merged['process_uuid'].unique())
    
    # Méthode de sélection
    selection_method = st.radio(
        "Méthode de sélection:",
        ["Manuel", "Aléatoire"],
        horizontal=True
    )
    
    if selection_method == "Manuel":
        selected_processes = st.multiselect(
            "Procédés:",
            process_list,
            max_selections=5,
            default=process_list[:2] if len(process_list) >= 2 else process_list
        )
    else:
        n_random = st.slider("Nombre de procédés aléatoires:", 2, 5, 3)
        if st.button("🎲 Générer une sélection aléatoire"):
            selected_processes = list(np.random.choice(process_list, n_random, replace=False))
            st.session_state['random_selection'] = selected_processes
        
        selected_processes = st.session_state.get('random_selection', process_list[:3])
        st.write("**Procédés sélectionnés:**")
        for p in selected_processes:
            st.text(f"• {p[:60]}...")
    
    if len(selected_processes) < 2:
        st.warning("⚠️ Veuillez sélectionner au moins 2 procédés pour effectuer une comparaison.")
        return
    
    st.markdown("---")
    
    # Filtrer les données
    comparison_data = merged[merged['process_uuid'].isin(selected_processes)]
    
    # Tabs de visualisation
    tab1, tab2, tab3 = st.tabs(["📊 Comparaison par Indicateur", "🔥 Heatmap", "📈 Graphiques Radar"])
    
    with tab1:
        # Sélection d'un indicateur
        indicator_list = sorted(comparison_data['impact_name_fr'].unique())
        selected_indicator = st.selectbox("Choisissez un indicateur:", indicator_list)
        
        # Filtrer sur l'indicateur
        indicator_data = comparison_data[comparison_data['impact_name_fr'] == selected_indicator]
        
        # Graphique en barres groupées
        fig = px.bar(
            indicator_data,
            x='process_uuid',
            y='impact_value',
            title=f"Comparaison - {selected_indicator}",
            labels={'process_uuid': 'Procédé', 'impact_value': 'Valeur'},
            color='impact_value',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Heatmap de comparaison
        if len(selected_processes) > 0:
            fig_heatmap = create_comparison_heatmap(comparison_data, selected_processes)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            st.caption("🎨 Les couleurs représentent les valeurs normalisées pour chaque indicateur.")
    
    with tab3:
        # Plusieurs radars superposés
        fig = go.Figure()
        
        colors = ['#2E7D32', '#1976D2', '#D32F2F', '#F57C00', '#7B1FA2']
        
        for idx, process in enumerate(selected_processes):
            process_data = comparison_data[comparison_data['process_uuid'] == process]
            process_data_sorted = process_data.sort_values('impact_name_fr')
            
            # Normaliser
            process_data_sorted['impact_norm'] = normalize_column(process_data_sorted['impact_value'])
            
            fig.add_trace(go.Scatterpolar(
                r=process_data_sorted['impact_norm'],
                theta=process_data_sorted['impact_name_fr'],
                fill='toself',
                name=f"Procédé {idx + 1}",
                line_color=colors[idx % len(colors)]
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=True,
            title="Comparaison des Profils (normalisés)",
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)


def show_rankings(merged):
    """Affiche les classements par indicateur"""
    
    st.header("🏆 Classements par Indicateur")
    
    # Sélection de l'indicateur
    col1, col2 = st.columns([2, 1])
    
    with col1:
        indicator_list = sorted(merged['impact_name_fr'].unique())
        selected_indicator = st.selectbox(
            "Choisissez un indicateur d'impact:",
            indicator_list,
            index=0
        )
    
    with col2:
        top_n = st.slider("Nombre de procédés à afficher:", 5, 50, 10)
    
    st.markdown("---")
    
    # Créer le graphique de classement
    fig = create_ranking_chart(merged, selected_indicator, top_n)
    
    if fig:
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistiques
        indicator_data = merged[merged['impact_name_fr'] == selected_indicator]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Maximum", f"{indicator_data['impact_value'].max():.2e}")
        
        with col2:
            st.metric("Moyenne", f"{indicator_data['impact_value'].mean():.2e}")
        
        with col3:
            st.metric("Médiane", f"{indicator_data['impact_value'].median():.2e}")
        
        with col4:
            st.metric("Minimum", f"{indicator_data['impact_value'].min():.2e}")
        
        # Tableau des top procédés
        st.subheader(f"📋 Top {top_n} - {selected_indicator}")
        
        top_data = indicator_data.nlargest(top_n, 'impact_value')[
            ['process_uuid', 'impact_value', 'unit']
        ].copy()
        
        top_data.columns = ['Procédé', 'Valeur', 'Unité']
        top_data.insert(0, 'Rang', range(1, len(top_data) + 1))
        
        st.dataframe(
            top_data.style.format({'Valeur': '{:.2e}'}),
            use_container_width=True,
            hide_index=True
        )
        
        # Download
        csv = top_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Télécharger le Top {top_n} (CSV)",
            data=csv,
            file_name=f"top_{top_n}_{selected_indicator.replace(' ', '_')}.csv",
            mime="text/csv"
        )
    else:
        st.error("Aucune donnée disponible pour cet indicateur.")


if __name__ == "__main__":
    main()
