# =============================================================================
# forms/simulations_form.py - Formulaire des simulations AMÉLIORÉ
# =============================================================================

import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from .base_form import BaseForm
from .form_utils import initialize_session_key, sort_all_simulations
from utils.excel_common import (
    process_excel_file_with_mapping,
    validate_mapping_basic, get_clean_value,
    detect_simulation_result, detect_emergency_scenarios,
    get_custom_fields, suggest_custom_name, validate_custom_name
)

class SimulationsForm(BaseForm):
    """ Formulaire pour la gestion des simulations de manœuvrabilité."""
    

    ICONS = {
        "numero_essai": "🏷️",
        "condition": "🍃",
        "resultat": "🎯",
        "navire": "🚢",
        "manoeuvre": "⚓",
        "vent": "🌪️",
        "houle": "🌊",
        "courant": "🌀",
        "maree": "🌙",
        "commentaire": "💬",
        "remorqueurs": "🚛",
        "poste": "🏗️",
        "pilote": "👨‍✈️",
        "etat_chargement": "⚖️"
    }

    def __init__(self):
        super().__init__("simulations")
    
    def render(self) -> Dict[str, Any]:
        """Rend le formulaire des simulations avec mapping amélioré."""
        try:
            self.render_section_header("🌀 Simulations de manœuvrabilité", divider=True)
            
            # Initialiser les données de session
            initialize_session_key("simulations_data", [], "simulations.simulations")
            
            # Interface principale
            self._render_data_input_section()
            self._render_simulations_table()
            
            # Retourner les données
            return {"simulations": st.session_state.simulations_data}
            
        except Exception as e:
            st.error(f"❌ Erreur dans le formulaire simulations : {str(e)}")
            return {"simulations": []}
    
    def _render_data_input_section(self):
        """Rend la section d'entrée des données Excel avec mapping amélioré."""
        # Vérifier si un mapping précédent existe
        previous_mapping = st.session_state.get("last_successful_mapping")
        
        if previous_mapping:
            with st.expander("ℹ️ Structure des données actuelle", expanded=False):
                st.success("✅ **Configuration de mapping active**")
                
                st.write("**🔍 Colonnes actuellement mappées:**")
                
                # Afficher en deux colonnes pour un meilleur rendu
                col1, col2 = st.columns(2)
                mapping_items = list(previous_mapping.items())
                mid_point = len(mapping_items) // 2
                
                with col1:
                    for field, excel_col in mapping_items[:mid_point]:
                        st.write(f"• **{field}** ← `{excel_col}`")
                
                with col2:
                    for field, excel_col in mapping_items[mid_point:]:
                        st.write(f"• **{field}** ← `{excel_col}`")
                
                st.info("💡 Pour ajouter de nouvelles données, utilisez un fichier Excel avec ces mêmes noms de colonnes")
                
                # Bouton pour réinitialiser le mapping
                if st.button("🔄 Réinitialiser le mapping (nouveau format de fichier)"):
                    del st.session_state["last_successful_mapping"]
                    st.success("✅ Mapping réinitialisé. Vous pouvez maintenant importer un fichier avec une structure différente.")
                    st.rerun()

        # Section d'import
        with st.expander("📤 Importer le tableau des simulations", expanded=not previous_mapping):
            excel_file = st.file_uploader(
                "Sélectionnez votre fichier Excel",
                type=["xlsx", "xls"],
                help="Le système va automatiquement détecter et mapper les colonnes"
            )
            # Traitement du fichier Excel
            if excel_file is not None:
                try:
                    from .mapping_workflow import render_enhanced_mapping_workflow
                    result = render_enhanced_mapping_workflow(excel_file)
                        
                    if result and result.get("success"):
                        # Sauvegarder le mapping pour utilisation future
                        if result.get("mapping"):
                            st.session_state.last_successful_mapping = result["mapping"]
                        
                        # Intégrer les données
                        simulations = result.get("simulations", [])
                        if simulations:
                            # Mode d'intégration
                            if result.get("import_mode") and "🔄 Remplacer" in result["import_mode"]:
                                st.session_state.simulations_data = simulations
                            else:
                                st.session_state.simulations_data.extend(simulations)
                            
                            st.success(f"✅ {len(simulations)} simulations importées avec succès !")
                            
                            # Informations sur le nouveau mapping
                            if result.get("mapping"):
                                st.info(f"📋 Mapping sauvegardé pour {len(result['mapping'])} colonnes")
                            
                            # Nettoyer l'état du workflow
                            for key in ["mapping_workflow", "mapping_workflow_complete"]:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            st.rerun()

                except Exception as e:
                    st.error(f"❌ Erreur lors de l'import: {str(e)}")
                    with st.expander("🔍 Détails de l'erreur"):
                        import traceback
                        st.code(traceback.format_exc())
    
    # =============================================================================
    # MÉTHODES EXISTANTES ADAPTÉES
    # =============================================================================
    
    def _render_simulations_table(self):
        """Version modifiée avec configuration globale AVANT les onglets"""
        
        st.subheader("📋 Tableau des simulations", divider=True)
        
        all_simulations = st.session_state.simulations_data
        
        if not all_simulations:
            st.info("📝 Aucune simulation. Importez un fichier Excel.")
            return
        
        # ✨ CONFIGURATION GLOBALE EN PREMIER
        self._render_column_order_config()
                
        # Vérifier s'il y a des champs personnalisés
        has_custom_fields = any("champs_personnalises" in sim for sim in all_simulations)
        
        if has_custom_fields:
            st.info("🆕 **Champs personnalisés détectés** - Ordre appliqué à toutes les vues")
        
        # Séparer pour l'affichage en onglets
        normal_simulations = [s for s in all_simulations if not s.get("is_emergency_scenario", False)]
        emergency_simulations = [s for s in all_simulations if s.get("is_emergency_scenario", False)]
        
        # Onglets si il y a des scénarios d'urgence
        if emergency_simulations:
            tab1, tab2 = st.tabs([
                f"🌀 Simulations normales ({len(normal_simulations)})", 
                f"⚠️ Scénarios d'urgence ({len(emergency_simulations)})"
            ])
            
            with tab1:
                self._render_simple_editable_table(normal_simulations, "normal")
            
            with tab2:
                self._render_simple_editable_table(emergency_simulations, "emergency")
        else:
            self._render_simple_editable_table(normal_simulations, "normal")

    def _render_simple_editable_table(self, simulations: List[Dict], table_type: str):
        """Version simplifiée sans interface de contrôle dans les onglets"""
        
        if not simulations:
            st.info(f"Aucune simulation de type {table_type}")
            return
        
        # Mode d'affichage (seule option restante dans les onglets)
        has_custom_fields = any("champs_personnalises" in sim for sim in simulations)
        
        if has_custom_fields:
            display_mode = st.radio(
                "Mode d'affichage:",
                ["📋 Standard", "🔧 Avec champs personnalisés"],
                key=f"simple_display_mode_{table_type}",
                help="Standard: colonnes classiques | Avec champs personnalisés: toutes les colonnes"
            )
        else:
            display_mode = "📋 Standard"
        
        # Préparer les données avec l'ordre GLOBAL
        extended = display_mode == "🔧 Avec champs personnalisés"
        table_data = self._prepare_table_data(simulations, extended)
        column_config = self._get_table_column_config(simulations, extended)
        
        # Afficher le tableau (avec clé simple)
        df = pd.DataFrame(table_data)
        
        edited_df = st.data_editor(
            df,
            width='stretch',
            num_rows="dynamic",
            column_config=column_config,
            key=f"simple_table_{table_type}_{display_mode.replace(' ', '_')}",
            hide_index=True
        )
        
        # Bouton d'ajout simple
        if st.button(f"➕ Ajouter simulation {table_type}", key=f"simple_add_{table_type}"):
            new_sim = self._create_empty_simulation(len(st.session_state.simulations_data) + 1)
            if table_type == "emergency":
                new_sim["is_emergency_scenario"] = True
            st.session_state.simulations_data.append(new_sim)
            st.rerun()
        
        # Traitement des modifications (logique existante)
        if not edited_df.equals(df):
            self._handle_table_modifications_extended(edited_df, simulations, table_type, display_mode)
        
        # Statistiques
        self._render_table_statistics(simulations)
        
        # Champs personnalisés si applicable
        if has_custom_fields:
            self._render_custom_fields_summary(simulations)

    def _create_empty_simulation(self, sim_id: int) -> Dict[str, Any]:
        """Crée une simulation vide pour la saisie manuelle."""
        return {
            "id": sim_id,
            "numero_essai_original": str(sim_id),
            "navire": "",
            "etat_chargement": "",
            "manoeuvre": "",
            "conditions_env": {
                "vent": "",
                "houle": "",
                "courant": "",
                "maree": ""
            },
            "resultat": "Non défini",
            "commentaire_pilote": "",
            "remorqueurs": "",
            "poste": "",
            "pilote": "",
            "bord": "",
            "entree": "",
            "condition": "",  # ✨ NOUVEAU CHAMP CONDITION
            "images": [],
            "is_emergency_scenario": False
        }
    
    def _prepare_table_data(self, simulations: List[Dict], extended: bool = False) -> List[Dict]:
        """Prépare les données pour affichage avec ordre intelligent"""
        table_data = []
        previous_mapping = st.session_state.get("last_successful_mapping", {})
        
        if not previous_mapping:
            # Mode fallback simple
            for i, sim in enumerate(simulations):
                row = {
                    "Sélection": False,
                    "N°": sim.get("numero_essai_original", str(i+1)),
                    "Navire": sim.get("navire", ""),
                    "Résultat": sim.get("resultat", "Non défini"),
                    "Commentaire": sim.get("commentaire_pilote", "")
                }
                table_data.append(row)
            return table_data
        
        # Mode mapping
        for i, sim in enumerate(simulations):
            row = {"Sélection": False}
            
            # Champs standards
            for field, excel_col in previous_mapping.items():
                value = self._get_field_value(sim, field, i)
                header = excel_col if "unnamed" not in excel_col.lower() else field.replace('_', ' ').title()
                row[header] = str(value) if value is not None else ""
            
            # Champs personnalisés si demandé
            if extended and "champs_personnalises" in sim:
                for custom_field, custom_value in sim["champs_personnalises"].items():
                    row[f"🆕 {custom_field.replace('_', ' ').title()}"] = str(custom_value)
            
            table_data.append(row)
        
        return self._order_table_columns_combined(table_data)
    
    def _get_table_column_config(self, simulations: List[Dict], extended: bool = False) -> Dict[str, Any]:
        """Configuration unifiée des colonnes"""
        config = {"Sélection": st.column_config.CheckboxColumn("☑️", width="small")}
        
        previous_mapping = st.session_state.get("last_successful_mapping", {})
        
        if not previous_mapping:
            # Configuration de base
            config.update({
                "N°": st.column_config.TextColumn("N°", width="small"),
                "Navire": st.column_config.TextColumn("Navire", width="medium"),
                "Résultat": st.column_config.SelectboxColumn("Résultat", options=["Réussite", "Échec", "Non défini"], width="small"),
                "Commentaire": st.column_config.TextColumn("Commentaire", width="large")
            })
            return config
        
        # Configuration basée sur le mapping
        for field, excel_col in previous_mapping.items():
            header = excel_col if "unnamed" not in excel_col.lower() else field.replace('_', ' ').title()
            
            if field == "resultat":
                config[header] = st.column_config.SelectboxColumn(header, options=["Réussite", "Échec", "Non défini"], width="small")
            elif field == "etat_chargement":
                config[header] = st.column_config.SelectboxColumn(header, options=["Lège", "Chargé", "Ballast", ""], width="small")
            elif field in ["commentaire", "commentaire_pilote"]:
                config[header] = st.column_config.TextColumn(header, width="large")
            elif field == "numero_essai":
                config[header] = st.column_config.TextColumn(header, width="small")
            elif field in ["vent", "houle", "courant", "maree"]:
                config[header] = st.column_config.TextColumn(header, width="small")
            else:
                config[header] = st.column_config.TextColumn(header, width="small")
        
        # Champs personnalisés si demandé
        if extended:
            all_custom_fields = set()
            for sim in simulations:
                if "champs_personnalises" in sim:
                    all_custom_fields.update(sim["champs_personnalises"].keys())
            
            for custom_field in sorted(all_custom_fields):
                field_label = f"🆕 {custom_field.replace('_', ' ').title()}"
                config[field_label] = st.column_config.TextColumn(field_label, width="medium", help=f"Champ personnalisé: {custom_field}")
        
        return config

    def _get_field_value(self, sim: Dict, field: str, index: int):
        """Extrait la valeur d'un champ depuis une simulation"""
        if field == "numero_essai":
            return sim.get("numero_essai_original", str(index+1))
        elif field in ["vent", "houle", "courant", "maree"]:
            return sim.get("conditions_env", {}).get(field, "")
        elif field == "commentaire":
            return sim.get("commentaire_pilote", "")
        elif field in sim:
            return sim.get(field, "")
        elif "champs_personnalises" in sim and field in sim["champs_personnalises"]:
            return sim["champs_personnalises"][field]
        return ""

    def _get_standard_table_column_config(self) -> Dict[str, Any]:
        """Configuration des colonnes basée sur le mapping."""
        config = {
            "Sélection": st.column_config.CheckboxColumn("☑️", width="small")
        }
        
        # Récupérer le mapping précédent
        previous_mapping = st.session_state.get("last_successful_mapping", {})
        
        if not previous_mapping:
            # Configuration de base si pas de mapping
            config.update({
                "N°": st.column_config.TextColumn("N°", width="small"),
                "Navire": st.column_config.TextColumn("Navire", width="medium"),
                "Résultat": st.column_config.SelectboxColumn(
                    "Résultat",
                    options=["Réussite", "Échec", "Non défini"],
                    width="small"
                ),
                "Commentaire": st.column_config.TextColumn("Commentaire", width="large")
            })
            return config
        
        # Configuration dynamique basée sur le mapping
        for field, excel_col in previous_mapping.items():
            
            # Utiliser le nom de colonne Excel (nettoyé si besoin)
            if "unnamed" in excel_col.lower():
                header = field.replace('_', ' ').title()
            else:
                header = excel_col
            
            # Configuration selon le type de champ
            if field == "resultat":
                config[header] = st.column_config.SelectboxColumn(
                    header,
                    options=["Réussite", "Échec", "Non défini"],
                    width="small"
                )
            elif field == "etat_chargement":
                config[header] = st.column_config.SelectboxColumn(
                    header,
                    options=["Lège", "Chargé", "Ballast", ""],
                    width="small"
                )
            elif field in ["commentaire", "commentaire_pilote"]:
                config[header] = st.column_config.TextColumn(header, width="large")
            elif field == "numero_essai":
                config[header] = st.column_config.TextColumn(header, width="small")
            elif field in ["vent", "houle", "courant", "maree"]:
                config[header] = st.column_config.TextColumn(header, width="small")
            else:
                # Champs personnalisés ou autres
                config[header] = st.column_config.TextColumn(header, width="small")
        
        return config

    def _render_column_order_config(self):
        """Interface simplifiée pour l'ordre des colonnes"""
        previous_mapping = st.session_state.get("last_successful_mapping", {})
        if not previous_mapping or len(previous_mapping) <= 3:
            return
        
        is_custom = "custom_column_order" in st.session_state
        
        with st.expander("⏭️ Ordre des colonnes"):
            # Déterminer l'ordre actuel
            is_custom = "custom_column_order" in st.session_state
            
            if not is_custom:
                current_mode = "🧠 Intelligent (recommandé)"
                st.session_state.show_custom_interface = False
            else:
                current_order = st.session_state.custom_column_order
                excel_order = list(previous_mapping.keys())
                current_mode = "📊 Excel" if current_order == excel_order else "⚙️ Personnalisé"
            
            st.write(f"**Ordre actuel :** {current_mode}")
            
            # 3 boutons simples
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🧠 Intelligent", key="btn_smart_order"):
                    if "custom_column_order" in st.session_state:
                        del st.session_state.custom_column_order
                    st.session_state.show_custom_interface = False
                    st.success("✅ Ordre intelligent appliqué")
                    st.rerun()
            
            with col2:
                if st.button("📊 Excel", key="btn_excel_order"):
                    st.session_state.custom_column_order = list(previous_mapping.keys())
                    st.session_state.show_custom_interface = False
                    st.success("✅ Ordre Excel appliqué")
                    st.rerun()
            
            with col3:
                if st.button("⚙️ Personnalisé", key="btn_custom"):
                    st.session_state.show_custom_interface = True
                    if "custom_column_order" not in st.session_state:
                        st.session_state.custom_column_order = self._get_intelligent_column_order()
                    st.info("👇 Utilisez l'interface ci-dessous pour personnaliser l'ordre")
            
            if st.session_state.show_custom_interface:
                self._render_simple_column_reorder_interface(previous_mapping)
                
            # Aperçu simple
            st.write("**👀 Aperçu :**")
            current = self._get_current_column_order()
            preview = " | ".join([f"{self.ICONS.get(f, '📋')} {f}" for f in current])
            st.write(preview)

    def _render_simple_column_reorder_interface(self, previous_mapping: Dict):
            """Interface simple de réorganisation par drag & drop simulé"""
            
            st.write("---")
            st.write("**🔧 Personnalisation de l'ordre :**")
            
            # Obtenir l'ordre actuel
            current_order = self._get_current_column_order()
            
            # S'assurer que tous les champs sont présents
            available_fields = set(previous_mapping.keys())
            for field in previous_mapping.keys():
                if field not in current_order:
                    current_order.append(field)
            current_order = [f for f in current_order if f in available_fields]
            
            # Afficher l'ordre avec des boutons simples
            for i, field in enumerate(current_order):
                excel_col = previous_mapping.get(field, field)
                display_name = excel_col if "unnamed" not in excel_col.lower() else field.replace('_', ' ').title()
                    
                # Ligne pour chaque colonne
                subcol1, subcol2, subcol3, subcol4 = st.columns([3, 1, 1, 1])
                    
                with subcol1:
                    icon = self.ICONS.get(field, "📋")
                    st.write(f"**{i+1}. {icon} {display_name}**")
                    
                with subcol2:
                    # Monter
                    if i > 0:
                        if st.button("⬆️", key=f"global_up_{field}_{i}", help="Monter"):
                            new_order = current_order.copy()
                            new_order[i], new_order[i-1] = new_order[i-1], new_order[i]
                            st.session_state.custom_column_order = new_order
                            st.rerun()
                    
                with subcol3:
                    # Descendre
                    if i < len(current_order) - 1:
                        if st.button("⬇️", key=f"global_down_{field}_{i}", help="Descendre"):
                            new_order = current_order.copy()
                            new_order[i], new_order[i+1] = new_order[i+1], new_order[i]
                            st.session_state.custom_column_order = new_order
                            st.rerun()
                    
                with subcol4:
                    # Priorité
                    if i > 0:
                        if st.button("🥇", key=f"global_first_{field}_{i}", help="Première position"):
                            new_order = current_order.copy()
                            field_to_move = new_order.pop(i)
                            new_order.insert(0, field_to_move)
                            st.session_state.custom_column_order = new_order
                            st.rerun()

        
    def _get_extended_table_column_config(self, simulations: List[Dict]) -> Dict[str, Any]:
        """Retourne la configuration pour le tableau étendu avec champs personnalisés."""
        
        # Configuration de base
        config = self._get_standard_table_column_config()
        
        # Identifier les champs personnalisés
        all_custom_fields = set()
        for sim in simulations:
            custom_fields = sim.get("champs_personnalises", {})
            all_custom_fields.update(custom_fields.keys())
        
        # Ajouter la configuration pour les champs personnalisés
        for custom_field in sorted(all_custom_fields):
            field_label = f"🆕 {custom_field.replace('_', ' ').title()}"
            config[field_label] = st.column_config.TextColumn(
                field_label, 
                width="medium",
                help=f"Champ personnalisé: {custom_field}"
            )
        
        return config
    
    def _handle_table_modifications_extended(self, edited_df, simulations: List[Dict], table_type: str, display_mode: str):
        """Gère les modifications du tableau avec support des champs personnalisés."""
        selected_indices = []
        previous_mapping = st.session_state.get("last_successful_mapping", {})
        
        # Créer un mapping inversé : nom_colonne -> champ
        reverse_mapping = {}
        for field, excel_col in previous_mapping.items():
            if "unnamed" in excel_col.lower():
                header = field.replace('_', ' ').title()
            else:
                header = excel_col
            reverse_mapping[header] = field
        
        for i, row in edited_df.iterrows():
            if row["Sélection"]:
                # Trouver l'index dans la liste principale
                sim_to_find = simulations[i]
                main_index = next((idx for idx, s in enumerate(st.session_state.simulations_data) 
                                if s is sim_to_find), None)
                if main_index is not None:
                    selected_indices.append(main_index)
            
            # Mettre à jour la simulation
            if i < len(simulations):
                sim_to_update = simulations[i]
                main_index = next((idx for idx, s in enumerate(st.session_state.simulations_data) 
                                if s is sim_to_update), None)
                
                if main_index is not None:
                    # Mettre à jour selon le mapping dynamique
                    for header, value in row.items():
                        if header == "Sélection":
                            continue
                        
                        # Trouver le champ correspondant
                        field = reverse_mapping.get(header)
                        if not field:
                            continue
                        
                        # Mettre à jour selon le type de champ
                        if field == "numero_essai":
                            st.session_state.simulations_data[main_index]["numero_essai_original"] = str(value)
                        elif field in ["vent", "houle", "courant", "maree"]:
                            if "conditions_env" not in st.session_state.simulations_data[main_index]:
                                st.session_state.simulations_data[main_index]["conditions_env"] = {}
                            st.session_state.simulations_data[main_index]["conditions_env"][field] = str(value)
                        elif field == "commentaire":
                            st.session_state.simulations_data[main_index]["commentaire_pilote"] = str(value)
                        elif field in ["navire", "etat_chargement", "manoeuvre", "condition", "resultat", 
                                    "remorqueurs", "poste", "pilote", "bord", "entree"]:
                            # Champs standard directs
                            st.session_state.simulations_data[main_index][field] = str(value)
                        else:
                            # Champ personnalisé
                            if "champs_personnalises" not in st.session_state.simulations_data[main_index]:
                                st.session_state.simulations_data[main_index]["champs_personnalises"] = {}
                            st.session_state.simulations_data[main_index]["champs_personnalises"][field] = str(value)
        
        # Gestion des suppressions
        if selected_indices and st.button(f"🗑️ Supprimer {len(selected_indices)} ligne(s) sélectionnée(s)", key=f"confirm_del_{table_type}_{display_mode}"):
            # Supprimer en ordre inverse
            for idx in sorted(selected_indices, reverse=True):
                st.session_state.simulations_data.pop(idx)
            
            st.success(f"✅ {len(selected_indices)} éléments supprimés")
            st.rerun()
    
    def _render_custom_fields_summary(self, simulations: List[Dict]):
        """Affiche un résumé des champs personnalisés détectés."""
        
        # Collecter tous les champs personnalisés
        all_custom_fields = {}
        for sim in simulations:
            custom_fields = sim.get("champs_personnalises", {})
            for field, value in custom_fields.items():
                if field not in all_custom_fields:
                    all_custom_fields[field] = {"count": 0, "sample_values": set()}
                
                all_custom_fields[field]["count"] += 1
                if value and len(str(value).strip()) > 0:
                    all_custom_fields[field]["sample_values"].add(str(value)[:30])
        
        if all_custom_fields:
            with st.expander(f"🆕 Champs personnalisés détectés ({len(all_custom_fields)})", expanded=False):
                for field, info in all_custom_fields.items():
                    field_label = field.replace('_', ' ').title()
                    sample_text = ", ".join(list(info["sample_values"])[:3])
                    if len(info["sample_values"]) > 3:
                        sample_text += "..."
                    
                    st.write(f"**{field_label}** ({info['count']} valeurs)")
                    if sample_text:
                        st.caption(f"Exemples: {sample_text}")
                    st.write("---")
    
    def _render_table_statistics(self, simulations: List[Dict]):
        """Affiche les statistiques des simulations avec support des champs personnalisés."""
        total = len(simulations)
        reussites = sum(1 for s in simulations if s.get("resultat") == "Réussite")
        echecs = sum(1 for s in simulations if s.get("resultat") == "Échec")
        nondefinis = sum(1 for s in simulations if s.get("resultat") == "Non défini")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", total)
        with col2:
            st.metric("✅ Réussites", reussites)
        with col3:
            st.metric("❌ Échecs", echecs)
        with col4:
            st.metric("❓ Non définis", nondefinis)
        
        # Avertissement pour résultats non définis
        if nondefinis > 0:
            st.warning(f"⚠️ {nondefinis} simulations sans résultat défini. Modifiez-les dans le tableau si nécessaire.")
        
    # =============================================================================
    # ORDRE DES COLONNES
    # =============================================================================
    
    def _get_intelligent_column_order(self):
        """Ordre intelligent par défaut (Option 1)"""
        return [
            # 🎯 Informations essentielles (toujours visibles en premier)
            "numero_essai",      # ID unique
            "condition",         # Condition spéciale/générale
            "resultat",          # Résultat de l'opération
            
            # 🌪️ Conditions environnementales (groupe logique)
            "vent", 
            "houle",
            "courant", 
            "maree",
            
            # ⚓ Détails techniques et logistiques
            "manoeuvre",         # Action effectuée
            "navire",            # Acteur principal
            "etat_chargement",
            "remorqueurs",
            "poste",
            "bord",
            "entree",
            "pilote",
            
            # 💬 Informations descriptives (souvent longues, donc à la fin)
            "commentaire"
        ]

    def _get_current_column_order(self):
        """Retourne l'ordre actuel des colonnes (intelligent ou personnalisé)"""
        if "custom_column_order" in st.session_state:
            return st.session_state.custom_column_order
        return self._get_intelligent_column_order()

    def _order_table_columns_combined(self, table_data: List[Dict]) -> List[Dict]:
        """Ordonne selon l'ordre intelligent OU personnalisé"""
        
        if not table_data:
            return table_data
        
        previous_mapping = st.session_state.get("last_successful_mapping", {})
        if not previous_mapping:
            return table_data
        
        # Obtenir l'ordre à utiliser (intelligent par défaut, personnalisé si défini)
        column_order = self._get_current_column_order()
        
        # Créer le mapping champ -> nom de colonne
        field_to_header = {}
        for field, excel_col in previous_mapping.items():
            if "unnamed" in excel_col.lower():
                header = field.replace('_', ' ').title()
            else:
                header = excel_col
            field_to_header[field] = header
        
        # Construire l'ordre final des headers
        ordered_headers = ["Sélection"]  # Toujours en premier
        
        # Ajouter selon l'ordre choisi
        for field in column_order:
            if field in field_to_header:
                ordered_headers.append(field_to_header[field])
        
        # Ajouter les champs personnalisés restants (non dans le mapping standard)
        all_headers = set(table_data[0].keys()) if table_data else set()
        remaining_headers = all_headers - set(ordered_headers)
        remaining_headers = sorted(remaining_headers)  # Alphabétique pour les champs custom
        ordered_headers.extend(remaining_headers)
        
        # Réorganiser les données
        ordered_data = []
        for row in table_data:
            ordered_row = {}
            for header in ordered_headers:
                if header in row:
                    ordered_row[header] = row[header]
            ordered_data.append(ordered_row)
        
        return ordered_data



def render() -> Dict[str, Any]:
    """Fonction de compatibilité avec l'ancien code."""
    form = SimulationsForm()
    return form.render()
