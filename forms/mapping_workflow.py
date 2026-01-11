# =============================================================================
# forms/mapping_workflow.py - Interface de workflow pour le mapping des colonnes
# FICHIER COMPLET SANS COUPURE
# =============================================================================

import streamlit as st
import pandas as pd
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from utils.excel_common import (
    detect_standard_columns, calculate_detection_confidence,
    validate_mapping_basic, get_clean_value, detect_simulation_result,
    detect_emergency_scenarios, get_custom_fields, suggest_custom_name,
    validate_custom_name, suggest_field_for_column
)

@dataclass
class MappingWorkflowState:
    """État du workflow de mapping"""
    phase: str = "analysis"  # analysis, mapping, validation, preview, complete
    excel_file = None
    selected_sheet: str = ""
    current_df: pd.DataFrame = None
    mapping: Dict[str, str] = None
    validation_results: Dict = None
    processing_options: Dict = None
    
    def reset(self):
        """Remet à zéro l'état"""
        self.phase = "analysis"
        self.excel_file = None
        self.selected_sheet = ""
        self.current_df = None
        self.mapping = {}
        self.validation_results = None
        self.processing_options = None


class MappingWorkflowManager:
    """Gestionnaire du workflow de mapping avec validation et révision"""
    FIELD_DESCRIPTIONS = {
            "numero_essai": "Identifiant unique de chaque simulation/essai",
            "navire": "Nom ou type du navire utilisé",
            "etat_chargement": "État de charge du navire (lège, chargé, ballast)",
            "manoeuvre": "Type de manœuvre effectuée (accostage, appareillage, etc.)",
            "vent": "Conditions de vent (vitesse, direction)",
            "houle": "Conditions de houle/vagues (hauteur, période)",
            "courant": "Conditions de courant (vitesse, direction)",
            "maree": "Niveau de marée ou coefficient",
            "condition": "Condition générale ou spéciale de la simulation",
            "remorqueurs": "Assistance remorquage (nombre, type)",
            "poste": "Poste d'accostage ou zone portuaire",
            "bord": "Côté d'accostage (bâbord/tribord)",
            "entree": "Point d'entrée au port",
            "pilote": "Pilote ou instructeur responsable",
            "commentaire": "Observations et commentaires détaillés",
            "resultat": "Résultat de la simulation (réussite/échec)"
        }
    def __init__(self):
        if "mapping_workflow" not in st.session_state:
            st.session_state.mapping_workflow = MappingWorkflowState()
    
    def _handle_phase_transition(self, workflow: MappingWorkflowState, next_phase: str):
        """Gère la transition entre les phases sans st.rerun()"""
        if workflow.phase != next_phase:
            workflow.phase = next_phase
            st.session_state.mapping_workflow = workflow
            st.rerun()
    
    def render_workflow(self, excel_file) -> Optional[Dict[str, Any]]:
        """Rend le workflow complet de mapping"""
        workflow = st.session_state.mapping_workflow

        # Réinitialiser le flag de changement de phase
        if st.session_state.get("phase_changed"):
            del st.session_state.phase_changed
            return None

        # AJOUT: Mettre à jour excel_file dans le workflow
        workflow.excel_file = excel_file  # Ajoutez cette ligne !

        # Si le résultat est déjà disponible, le retourner directement
        if hasattr(workflow, 'final_result'):
            result = workflow.final_result
            # Nettoyer l'état
            delattr(workflow, 'final_result')
            if "mapping_workflow" in st.session_state:
                del st.session_state["mapping_workflow"]
            return result
        
        # Affichage du progress bar
        self._render_progress_bar(workflow.phase)
        
        # Router vers la phase appropriée
        if workflow.phase == "analysis":
            self._render_analysis_phase(workflow)
        elif workflow.phase == "mapping":
            self._render_mapping_phase(workflow)
        elif workflow.phase == "validation":
            self._render_validation_phase(workflow)
        elif workflow.phase == "preview":
            self._render_preview_phase(workflow)
        elif workflow.phase == "complete":
            result = self._render_complete_phase(workflow)
            if result and result.get("success"):
                # Stocker le résultat final
                workflow.final_result = result
                return result
        
        return None
    
    def _render_progress_bar(self, current_phase: str):
        """Affiche la barre de progression du workflow"""
        
        phases = [
            ("analysis", "🔍 Analyse"),
            ("mapping", "🔗 Mapping"),
            ("validation", "✅ Validation"),
            ("preview", "👁️ Aperçu"),
            ("complete", "🎉 Terminé")
        ]
        
        current_index = next((i for i, (phase, _) in enumerate(phases) if phase == current_phase), 0)
        progress = (current_index + 1) / len(phases)
        
        st.progress(progress, text=f"Étape {current_index + 1}/{len(phases)}: {phases[current_index][1]}")
        
        # Navigation rapide
        cols = st.columns(len(phases))
        for i, (phase, label) in enumerate(phases):
            with cols[i]:
                if i < current_index:
                    st.success(f"✅ {label}")
                elif i == current_index:
                    st.info(f"▶️ {label}")
                else:
                    st.write(f"⭕ {label}")
    
    def _display_automatic_column_detection(self, df: pd.DataFrame):
        """Affiche la détection automatique des colonnes"""
        
        st.write("**🕵🏻 Détection automatique des colonnes:**")
        
        # Simpler detection logic
        detected_columns = detect_standard_columns(df.columns.tolist())
        
        if detected_columns:
            st.success(f"✅ {len(detected_columns)} colonne(s) reconnue(s) automatiquement")
            with st.expander("🔍 Colonnes détectées", expanded=True):
                for field, excel_col in detected_columns.items():
                    confidence = calculate_detection_confidence(field, excel_col)
                    confidence_icon = "🟢" if confidence >= 80 else "🟡" if confidence >= 60 else "🔴"
                    
                    st.write(f"{confidence_icon} **{field}** ← `{excel_col}` ({confidence}% confiance)")
        else:
            st.warning("⚠️ Aucune colonne reconnue automatiquement. Mapping manuel requis.")
        
        # Colonnes non reconnues
        used_columns = set(detected_columns.values()) if detected_columns else set()
        unmapped_columns = []
        for col in df.columns:
            if col not in used_columns:
                # Vérifier si la colonne a du contenu utile
                if self._is_column_useful(df[col], col):
                    unmapped_columns.append(col)
        
        if unmapped_columns:
            st.info(f"💡 {len(unmapped_columns)} colonne(s) non reconnue(s) avec du contenu pourront être mappées manuellement")
            
            # 🆕 Afficher les premières colonnes pour debug
            if len(unmapped_columns) > 10:
                preview_cols = unmapped_columns[:10]
                with st.expander(f"👁️ Aperçu des colonnes non mappées ({len(preview_cols)}/{len(unmapped_columns)})", expanded=False):
                    for col in preview_cols:
                        sample = df[col].dropna().head(2).tolist()
                        sample_text = ", ".join(str(v)[:20] for v in sample) if sample else "Vide"
                        st.write(f"• `{col}`: {sample_text}")
    
    def _is_column_useful(self, series: pd.Series, col_name: str) -> bool:
        """Détermine si une colonne mérite d'être proposée pour mapping"""
        
        # Ignorer les colonnes complètement vides
        if series.dropna().empty:
            return False
        
        # Ignorer les colonnes avec que des "Unnamed"
        if "unnamed" in col_name.lower():
            return False
        
        # Ignorer les colonnes avec très peu de données (< 5% du total)
        if series.notna().sum() < len(series) * 0.05:
            return False
        
        # Ignorer les colonnes avec que des espaces ou caractères vides
        string_values = series.dropna().astype(str)
        if string_values.str.strip().eq('').all():
            return False
        
        return True
    
    def _render_analysis_phase(self, workflow: MappingWorkflowState) -> None:
        """Phase 1: Analyse du fichier Excel"""
        if st.session_state.get("phase_changed"):
            return None
        st.subheader("🔍 Phase 1: Analyse du fichier Excel", divider=True)
        
        try:
            # Analyser le fichier
            sheets_data = pd.read_excel(workflow.excel_file, sheet_name=None)
            sheet_names = list(sheets_data.keys())
            
            # Sélection de feuille
            if len(sheet_names) > 1:
                st.info(f"📋 Fichier multi-feuilles détecté ({len(sheet_names)} feuilles)")
                selected_sheet = st.selectbox(
                    "Sélectionnez la feuille à traiter:",
                    sheet_names,
                    key="workflow_sheet_selection"
                )
            else:
                selected_sheet = sheet_names[0]
            
            # Analyser la feuille sélectionnée
            df = sheets_data[selected_sheet]
            workflow.current_df = df
            workflow.selected_sheet = selected_sheet

            # AJOUT: Détection automatique ET sauvegarde
            detected_mapping = detect_standard_columns(df.columns.tolist())
            
            # CORRECTION: Sauvegarder dans workflow.mapping
            if workflow.mapping is None:
                workflow.mapping = detected_mapping
            
            # Aperçu des données
            with st.expander("👁️ Aperçu des données", expanded=False):
                st.dataframe(df.head(), width='stretch')
            
            # Détection automatique des colonnes pertinentes
            detected_mapping = detect_standard_columns(df.columns.tolist())
            if workflow.mapping is None:
                workflow.mapping = detected_mapping  # SAUVEGARDER ICI
            self._display_automatic_column_detection(df)

            # Boutons de navigation
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Recharger fichier"):
                    workflow.reset()
                    self._handle_phase_transition(workflow, "analysis")
            with col2:
                if st.button("➡️ Configurer mapping", type="primary"):
                    workflow.phase = "mapping"
                    self._handle_phase_transition(workflow, "mapping")
                    
        except Exception as e:
            st.error(f"❌ Erreur d'analyse: {str(e)}")
            if st.button("🔄 Réessayer"):
                workflow.reset()
                st.rerun()
    
    def _render_mapping_phase(self, workflow: MappingWorkflowState) -> None:
        """Phase 2: Configuration du mapping"""
        if st.session_state.get("phase_changed"):
            return None
        st.subheader("🔗 Phase 2: Configuration du mapping", divider=True)
        
        if workflow.current_df is None:
            st.error("❌ Données perdues. Retour à l'analyse.")
            workflow.phase = "analysis"
            st.rerun()
            return
        
        df = workflow.current_df
        excel_columns = df.columns.tolist()
        
        # Pré-remplir avec la détection automatique
        if workflow.mapping is None:
            workflow.mapping = detect_standard_columns(excel_columns)
        
        st.info("🔗 Configurez le mapping des colonnes Excel vers les champs de l'application")
        
        # Interface de mapping avec sections
        mapping_result = self._render_mapping_interface(excel_columns, workflow.mapping, workflow)
        workflow.mapping = mapping_result
        
        # Validation en temps réel
        validation_errors = validate_mapping_basic(workflow.mapping, df)
        
        if validation_errors:
            st.error("❌ **Erreurs de mapping détectées:**")
            for error in validation_errors:
                st.error(f"• {error}")
        
        # Boutons de navigation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Retour analyse"):
                workflow.phase = "analysis"
                self._handle_phase_transition(workflow, "analysis")
        
        with col2:
            if st.button("🔄 Réinitialiser mapping"):
                workflow.mapping = {}
                self._handle_phase_transition(workflow, "mapping")
        
        with col3:
            can_continue = len(validation_errors) == 0 and "numero_essai" in workflow.mapping
            if st.button("➡️ Valider mapping", type="primary", disabled=not can_continue):
                workflow.phase = "validation"
                self._handle_phase_transition(workflow, "validation")
    
    def _render_validation_phase(self, workflow: MappingWorkflowState) -> None:
        """Phase 3: Validation détaillée et aperçu"""
        if st.session_state.get("phase_changed"):
            return None
        st.subheader("✅ Phase 3: Validation détaillée", divider=True)
        
        if not workflow.mapping:
            st.error("❌ Mapping perdu. Retour au mapping.")
            workflow.phase = "mapping"
            st.rerun()
            return
        
        # Validation détaillée
        from utils.excel_common import perform_detailed_validation
        validation_results = perform_detailed_validation(workflow.current_df, workflow.mapping)
        workflow.validation_results = validation_results
        
        if validation_results["is_valid"]:
            st.subheader("👁️ Aperçu des données mappées")
            self._display_data_preview_with_mapping(workflow.current_df, workflow.mapping)
            
            # Boutons de navigation
            col1, _, col3 = st.columns(3)
            
            with col1:
                if st.button("⬅️ Réviser mapping"):
                    workflow.phase = "mapping"
                    self._handle_phase_transition(workflow, "mapping")
            
            with col3:
                if st.button("➡️ Configurer traitement", type="primary"):
                    workflow.phase = "preview"
                    self._handle_phase_transition(workflow, "preview")
        else:
            st.error("❌ Veuillez corriger les erreurs avant de continuer")
            if st.button("⬅️ Retour au mapping", type="primary"):
                workflow.phase = "mapping"
                st.rerun()
        
    def _render_mapping_interface(self, excel_columns: List[str], current_mapping: Dict[str, str], workflow) -> Dict[str, str]:
        """Interface de mapping INVERSÉE : Colonne Excel → Champ Application"""
                
        # Préparer les options pour les champs application
        standard_fields = [
            ("", "🚫 [Ignorer cette colonne]"),
            ("numero_essai", "🔢 N° d'essai *"),
            ("navire", "🚢 Navire"),
            ("etat_chargement", "⚖️ État de charge"),
            ("manoeuvre", "⚓ Manœuvre"),
            ("vent", "🌪️ Vent"),
            ("houle", "🌊 Houle"),
            ("courant", "🌀 Courant"),
            ("maree", "🌙 Marée"),
            ("condition", "🆕 Condition"),
            ("remorqueurs", "🚛 Remorqueurs"),
            ("poste", "🏗️ Poste"),
            ("bord", "↔️ Bord"),
            ("entree", "🚪 Entrée"),
            ("pilote", "👨‍✈️ Pilote"),
            ("commentaire", "💬 Commentaires"),
            ("resultat", "✅ Résultat"),
            ("nouveau_champ", "➕ Créer nouveau champ...")
        ]
        
        field_options = [label for _, label in standard_fields]
        field_values = [value for value, _ in standard_fields]
        
        final_mapping = {}
        nouveaux_champs = {}
        champs_utilises = set()  # Pour éviter les doublons
        
        st.write("### 📊 Configuration du mapping")
        st.write("**Instructions :** Associez chaque colonne Excel à un champ de l'application")
        
        # Créer l'interface pour chaque colonne Excel
        for i, excel_col in enumerate(excel_columns):
            
            with st.container():
                if i > 0:  # Séparateur sauf pour la première
                    st.write("---")
                
                col1, col2, col3 = st.columns([3, 3, 3])
                
                with col1:
                    st.write(f"**📋 `{excel_col}`**")
                    
                    # Aperçu du contenu de la colonne
                    if workflow.current_df is not None and excel_col in workflow.current_df.columns:
                        sample = workflow.current_df[excel_col].dropna().head(3).tolist()
                        if sample:
                            sample_text = ", ".join(str(v)[:25] + ("..." if len(str(v)) > 25 else "") for v in sample)
                            st.caption(f"📄 Aperçu: {sample_text}")
                        else:
                            st.caption("📄 Colonne vide")
                        
                        # Statistiques rapides
                        total = len(workflow.current_df[excel_col])
                        non_null = workflow.current_df[excel_col].notna().sum()
                        st.caption(f"📊 {non_null}/{total} ({(non_null/total*100):.0f}%) de valeurs non vides")
                
                with col2:
                    # Déterminer la valeur par défaut depuis current_mapping
                    default_field = ""
                    for field, mapped_col in current_mapping.items():
                        if mapped_col == excel_col:
                            default_field = field
                            break
                    
                    # Si pas de mapping existant, essayer une suggestion automatique
                    if not default_field:
                        suggestion = suggest_field_for_column(excel_col, workflow.current_df[excel_col] if excel_col in workflow.current_df.columns else None)
                        if suggestion:
                            default_field = suggestion
                    
                    # Trouver l'index dans les options
                    try:
                        if default_field:
                            default_index = field_values.index(default_field)
                        else:
                            default_index = 0  # "[Ignorer cette colonne]"
                    except ValueError:
                        default_index = 0
                    
                    # Sélecteur de champ
                    selected_field_label = st.selectbox(
                        f"Champ pour '{excel_col}'",
                        field_options,
                        index=default_index,
                        key=f"mapping_excel_{i}",
                        label_visibility="collapsed",
                        help=f"Sélectionnez le champ de destination pour '{excel_col}'"
                    )
                    
                    # Récupérer la valeur correspondante
                    selected_field = field_values[field_options.index(selected_field_label)]
                    
                    # Gestion des différents cas
                    if selected_field == "nouveau_champ":
                        # Interface pour créer un nouveau champ
                        nouveau_nom = st.text_input(
                            "Nom du nouveau champ:",
                            value=suggest_custom_name(excel_col),
                            key=f"nouveau_champ_{i}",
                            placeholder="nom_du_champ",
                            help="Utilisez des lettres minuscules et des underscores"
                        )
                        
                        if nouveau_nom:
                            if validate_custom_name(nouveau_nom):
                                if nouveau_nom not in champs_utilises:
                                    nouveaux_champs[nouveau_nom] = excel_col
                                    final_mapping[nouveau_nom] = excel_col
                                    champs_utilises.add(nouveau_nom)
                                    st.success(f"✅ Nouveau champ: {nouveau_nom}")
                                else:
                                    st.error(f"❌ Le champ '{nouveau_nom}' existe déjà")
                            else:
                                st.error("❌ Nom invalide (lettres minuscules et _ uniquement)")
                    
                    elif selected_field and selected_field != "":
                        # Champ standard sélectionné
                        if selected_field in champs_utilises:
                            st.error(f"❌ '{selected_field}' déjà utilisé par une autre colonne")
                        else:
                            final_mapping[selected_field] = excel_col
                            champs_utilises.add(selected_field)
                            
                            # Indicateur visuel pour champ obligatoire
                            if selected_field == "numero_essai":
                                st.success("✅ Champ obligatoire mappé")
                    
                    # Affichage d'aide contextuelle
                    if selected_field and selected_field != "" and selected_field != "nouveau_champ":
                        field_info = self.FIELD_DESCRIPTIONS.get(selected_field, "")
                        if field_info:
                            st.caption(f"ℹ️ {field_info}")
                
                with col3:
                    show_preview = st.toggle("🔍", key=f"preview_toggle_{i}", help="Voir/masquer l'analyse")
    
                    # Afficher si activé
                    if show_preview:
                        self._show_column_preview_detailed(excel_col, workflow.current_df)
        
        # Section de résumé du mapping
        st.write("---")
        st.write("### 📋 Résumé du mapping")
        
        if final_mapping:
            # Métriques rapides
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Colonnes mappées", len(final_mapping))
            with col2:
                st.metric("🎯 Champs standards", len([f for f in final_mapping.keys() if f not in nouveaux_champs]))
            with col3:
                st.metric("➕ Nouveaux champs", len(nouveaux_champs))
            with col4:
                colonnes_ignorees = len(excel_columns) - len(final_mapping)
                st.metric("🚫 Colonnes ignorées", colonnes_ignorees)
            
            
            # Avertissements et validation
            issues = []
            
            # Vérifier les champs obligatoires
            if "numero_essai" not in final_mapping:
                issues.append("❌ Le champ 'N° d'essai' est obligatoire")
            
            # Colonnes ignorées (informatif)
            colonnes_ignorees_liste = [col for col in excel_columns if col not in final_mapping.values()]
            if colonnes_ignorees_liste:
                if len(colonnes_ignorees_liste) <= 3:
                    ignored_text = ", ".join(f"`{col}`" for col in colonnes_ignorees_liste)
                else:
                    ignored_text = f"{len(colonnes_ignorees_liste)} colonnes"
                issues.append(f"ℹ️ Colonnes ignorées: {ignored_text}")
            
            # Afficher les issues
            for issue in issues:
                if issue.startswith("❌"):
                    st.error(issue)
                elif issue.startswith("⚠️"):
                    st.warning(issue)
                else:
                    st.info(issue)
            
        else:
            st.warning("⚠️ Aucune colonne mappée. Configurez au moins le champ 'N° d'essai'")
        
        return final_mapping

    def _show_column_preview_detailed(self, column_name: str, df: pd.DataFrame):
        """Aperçu détaillé d'une colonne avec analyse"""
        
        if df is None or column_name not in df.columns:
            st.error(f"Colonne '{column_name}' introuvable")
            return
        
        with st.expander(f"🔍 Analyse détaillée : {column_name}", expanded=True):
            series = df[column_name]
            
            # Statistiques de base
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", len(series))
            with col2:
                st.metric("Non nulles", series.notna().sum())
            with col3:
                st.metric("Uniques", series.nunique())
            with col4:
                completeness = (series.notna().sum() / len(series)) * 100 if len(series) > 0 else 0
                st.metric("Complétude", f"{completeness:.0f}%")
            
            # Échantillon de données
            st.write("**📄 Échantillon de données:**")
            sample_data = series.dropna().head(9).tolist()
            
            if sample_data:
                # Afficher en colonnes pour un meilleur rendu
                cols = st.columns(3)
                for i, value in enumerate(sample_data):
                    col_idx = i % 3
                    with cols[col_idx]:
                        value_str = str(value)[:40]
                        if len(str(value)) > 40:
                            value_str += "..."
                        st.write(f"{value_str}")
                    
                if len(sample_data) < series.notna().sum():
                    st.caption(f"... et {series.notna().sum() - len(sample_data)} autres valeurs")
            else:
                st.info("Aucune donnée non nulle trouvée")
            
            # Suggestion automatique
            suggested_field = suggest_field_for_column(column_name, series)
            if suggested_field:
                field_label = suggested_field.replace('_', ' ').title()
                st.info(f"💡 **Suggestion automatique:** {field_label}")
            
            # Analyse du type de données
            if not series.empty:
                st.write("**🔬 Analyse du contenu:**")
                sample_str = series.dropna().astype(str).head(20)
                
                # Détecter les patterns
                patterns = []
                if sample_str.str.contains(r'\d+', na=False).any():
                    patterns.append("Contient des nombres")
                if sample_str.str.len().mean() > 50:
                    patterns.append("Texte long (probablement descriptif)")
                if sample_str.str.contains(r'[A-Za-z]{3,}', na=False).any():
                    patterns.append("Contient du texte")
                
                for pattern in patterns:
                    st.caption(f"• {pattern}")
    
    def _display_data_preview_with_mapping(self, df: pd.DataFrame, mapping: Dict[str, str]):
        """Affiche l'aperçu des données avec le mapping appliqué"""
        
        # Créer un DataFrame d'aperçu
        preview_rows = []
        
        for i, (_, row) in enumerate(df.head(8).iterrows()):
            preview_row = {}
            for field, excel_col in mapping.items():
                if excel_col in df.columns:
                    value = row[excel_col]
                    if pd.isna(value):
                        display_value = ""
                    else:
                        str_val = str(value)
                        display_value = str_val[:35] + "..." if len(str_val) > 35 else str_val
                    
                    preview_row[field] = display_value
            
            preview_rows.append(preview_row)
        
        if preview_rows:
            preview_df = pd.DataFrame(preview_rows)
            st.dataframe(preview_df, width='stretch')
            
            if len(df) > 8:
                st.caption(f"Aperçu des 8 premières lignes sur {len(df)} total")
    
    def _render_preview_phase(self, workflow: MappingWorkflowState) -> None:
        """Phase 4: Configuration du traitement et aperçu final"""
        if st.session_state.get("phase_changed"):
            return None
        st.subheader("👁️ Phase 4: Configuration du traitement", divider=True)
        
        # Options de traitement
        st.write("**⚙️ Options de traitement:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_clean = st.checkbox(
                "🧹 Nettoyage automatique", 
                value=True,
                help="Nettoie les espaces et formate les données"
            )
            detect_emergency = st.checkbox(
                "🔴 Détecter scénarios d'urgence", 
                value=True,
                help="Détecte automatiquement les lignes d'urgence"
            )
        
        with col2:
            auto_detect_results = st.checkbox(
                "🎯 Détection automatique résultats", 
                value=True,
                help="Analyse les commentaires pour détecter succès/échec"
            )
            preserve_original = st.checkbox(
                "💾 Conserver données originales", 
                value=True,
                help="Garde une copie des valeurs Excel originales"
            )
        
        # Sauvegarder les options
        workflow.processing_options = {
            "auto_clean": auto_clean,
            "detect_emergency": detect_emergency,
            "auto_detect_results": auto_detect_results,
            "preserve_original": preserve_original
        }
        
        # Mode d'import
        st.write("**📥 Mode d'import:**")
        
        import_mode = st.radio(
            "Comment intégrer les données:",
            ["🔄 Remplacer toutes les simulations existantes", "➕ Ajouter aux simulations existantes"],
            help="Choisissez comment traiter les simulations existantes"
        )
        
        workflow.processing_options["import_mode"] = import_mode
        
        # Boutons de navigation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Retour validation"):
                workflow.phase = "validation"
                self._handle_phase_transition(workflow, "validation")
        
        with col2:
            if st.button("🔄 Recommencer"):
                workflow.reset()
                self._handle_phase_transition(workflow, "analysis")
        
        with col3:
            if st.button("🚀 Lancer le traitement", type="primary"):
                workflow.phase = "complete"
                self._handle_phase_transition(workflow, "complete")
    
    def _render_complete_phase(self, workflow: MappingWorkflowState) -> Dict[str, Any]:
        """Phase 5: Version SANS RERUN pour éviter la boucle infinie"""
        if st.session_state.get("phase_changed"):
            return None
    
        # Si déjà traité, retourner le résultat
        if hasattr(workflow, 'processed_result'):
            return workflow.processed_result
        
        # Traitement une seule fois
        try:
            result = self._process_final_data(workflow)
            if result["success"]:
                # Sauvegarder le résultat
                workflow.processed_result = result
                return result
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")
        
        return None

    def _process_final_data(self, workflow: MappingWorkflowState) -> Dict[str, Any]:
        """Traite les données finales"""
        
        try:
            df = workflow.current_df
            mapping = workflow.mapping
            options = workflow.processing_options
            
            # Debug
            st.write(f"🔍 Processing {len(df)} lignes avec {len(mapping)} mappings")
            
            simulations = []
            
            # Détecter les scénarios d'urgence si demandé
            emergency_rows = set()
            if options.get("detect_emergency", False):
                emergency_rows = detect_emergency_scenarios(df)
            
            # Traiter chaque ligne du DataFrame
            for index, row in df.iterrows():
                # Vérifier que la ligne a un numéro d'essai valide
                if "numero_essai" not in mapping:
                    continue
                        
                numero_essai = row.get(mapping["numero_essai"], None)
                if pd.isna(numero_essai) or str(numero_essai).strip() == "":
                    continue
                        
                # Créer la simulation de base
                simulation = {
                    "id": len(simulations) + 1,
                    "numero_essai_original": get_clean_value(numero_essai, options.get("auto_clean", True)),
                    "is_emergency_scenario": index in emergency_rows,
                    "images": []
                }
                        
                # Mapper tous les champs standard
                standard_fields = {
                    "navire": "",
                    "etat_chargement": "",
                    "manoeuvre": "",
                    "remorqueurs": "",
                    "poste": "",
                    "pilote": "",
                    "bord": "",
                    "entree": "",
                    "commentaire_pilote": "",
                    "resultat": "Non défini",
                    "condition": ""  # ✨ NOUVEAU CHAMP CONDITION
                }
                        
                for field in standard_fields:
                    if field == "commentaire_pilote":
                        # Mapping spécial pour commentaire
                        source_field = "commentaire"
                    else:
                        source_field = field
                            
                    if source_field in mapping:
                        value = get_clean_value(row[mapping[source_field]], options.get("auto_clean", True)) if source_field in mapping else ""
                        simulation[field] = value
                    else:
                        simulation[field] = standard_fields[field]
                    
                # Conditions environnementales
                conditions_env = {}
                for condition_type in ["vent", "houle", "courant", "maree"]:
                    if condition_type in mapping:
                        value = get_clean_value(row[mapping[condition_type]], options.get("auto_clean", True))
                        conditions_env[condition_type] = value
                    else:
                        conditions_env[condition_type] = ""
                        
                simulation["conditions_env"] = conditions_env
                        
                # ✨ NOUVEAUTÉ: Champs personnalisés
                custom_fields = get_custom_fields(mapping)
                if custom_fields:
                    simulation["champs_personnalises"] = {}
                    for custom_field in custom_fields:
                        if custom_field in mapping:
                            value = get_clean_value(row, mapping[custom_field], options.get("auto_clean", True))
                            simulation["champs_personnalises"][custom_field] = value
                        
                # Détection automatique du résultat
                if options.get("auto_detect_results", True):
                    detected_result = detect_simulation_result(simulation, mapping, row)
                    simulation["resultat"] = detected_result
                        
                # Conserver les données originales si demandé
                if options.get("preserve_original", True):
                    simulation["donnees_originales"] = {}
                    for field, excel_col in mapping.items():
                        if excel_col in df.columns:
                            simulation["donnees_originales"][excel_col] = str(row[excel_col])
                        
                # Métadonnées de traitement
                simulation["metadata_import"] = {
                    "date_import": pd.Timestamp.now().isoformat(),
                    "ligne_excel": index + 2,  # +2 car Excel commence à 1 et il y a l'en-tête
                    "mapping_utilise": dict(mapping),
                    "options_traitement": dict(options)
                }
                
                simulations.append(simulation)
            
            # Calculer les statistiques
            stats = {
                "total": len(simulations),
                "reussites": sum(1 for s in simulations if s.get("resultat") == "Réussite"),
                "echecs": sum(1 for s in simulations if s.get("resultat") == "Échec"),
                "non_definis": sum(1 for s in simulations if s.get("resultat") == "Non défini"),
                "urgences": len(emergency_rows),
                "conditions_renseignees": sum(1 for s in simulations if s.get("condition", "").strip())
            }
            
            # Identifier les champs personnalisés pour le résultat
            custom_fields_detected = custom_fields if custom_fields else []
            
            return {
                "success": True,
                "simulations": simulations,
                "stats": stats,
                "custom_fields_detected": custom_fields_detected,
                "count": len(simulations),
                "mapping": workflow.mapping
            }
            
        except Exception as e:
            import traceback
            st.error(f"Erreur détaillée: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e)
            }

# =============================================================================
# POINTS D'ENTRÉE ET INTÉGRATION FINALE
# =============================================================================

def render_enhanced_mapping_workflow(excel_file) -> Optional[Dict[str, Any]]:
    """Point d'entrée principal pour le workflow de mapping amélioré"""
    # Réinitialiser l'état si nouveau fichier
    if "current_excel_file" not in st.session_state or st.session_state.current_excel_file != excel_file:
        st.session_state.current_excel_file = excel_file
        if "mapping_workflow" in st.session_state:
            del st.session_state["mapping_workflow"]
    
    # Exécuter le workflow
    workflow_manager = MappingWorkflowManager()
    result = workflow_manager.render_workflow(excel_file)
    
    # Retourner le résultat final si la phase est complete
    if result and result.get("success"):
        return result
    
    return None
