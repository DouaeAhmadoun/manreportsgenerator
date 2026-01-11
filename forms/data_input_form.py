# =============================================================================
# forms/data_input_form.py - Formulaire des données d'entrée
# =============================================================================

import streamlit as st
from typing import Dict, Any, List
from .base_form import BaseForm, FormValidator
from .form_utils import initialize_session_key


class DataInputForm(BaseForm):
    """
    Formulaire pour les données d'entrée de l'étude.
    """
    
    def __init__(self):
        super().__init__("data_input")
        self.required_fields = ["source", "date", "notes_profondeur"]  # Pour bathymétrie
    
    def render(self) -> Dict[str, Any]:
        """Rend le formulaire des données d'entrée."""
        try:
            self.render_section_header("📊 Données d'entrée", divider=True)
            
            # Organisation en onglets
            tabs = st.tabs([
                "📍 Plan de masse",
                "🚩 Plan de balisage",
                "🗺️ Bathymétrie",
                "🌬️ Conditions environnementales"
            ])

            with tabs[0]:
                plan_masse = self._render_plan_masse()
            
            with tabs[1]:
                balisage = self._render_balisage()
            
            with tabs[2]:
                bathymetrie = self._render_bathymetry()
            
            with tabs[3]:
                conditions = self._render_conditions()
            
            # Données complètes
            data_input = {
                "plan_de_masse": plan_masse,
                "balisage": balisage,
                "bathymetrie": bathymetrie,
                "conditions_environnementales": conditions
            }
            
            # Validation
            if self.validate_data(data_input):
                self.display_validation_messages()

            return data_input
            
        except Exception as e:
            st.error(f"Erreur dans le formulaire données d'entrée : {str(e)}")
            return self._get_default_data_input()
    
    def _render_plan_masse(self) -> Dict[str, Any]:
        """Rend la section du plan de masse."""
        self.render_section_header(
            "📍 Plan de masse", 
            divider=False,
            help_text="Définissez les différentes phases du plan de masse"
        )
        
        # Initialiser les phases depuis rapport_data
        initialize_session_key(
            "phases", 
            [], 
            "donnees_entree.plan_de_masse.phases"
        )
        
        # Interface de gestion des phases
        phases = self.create_dynamic_list_widget(
            "Phases du plan de masse",
            "phases",
            [],
            self._render_single_phase
        )
        
        # Commentaire global
        defaults = self.get_defaults()
        commentaire = self._render_optional_comment(
            "Ajouter un commentaire sur le plan de masse",
            "Commentaire plan de masse",
            defaults["plan_commentaire"]
        )
        
        return {
            "phases": phases,
            "commentaire": commentaire
        }
    
    def _render_single_phase(self, index: int, existing_phase: Dict[str, Any]) -> Dict[str, Any]:
        """Rend le formulaire pour une phase individuelle."""
        nom = st.text_input(
            f"Nom de la phase {index+1} *", 
            value=existing_phase.get("nom", ""), 
            key=f"phase_nom_{index}",
            placeholder="Ex: Phase 1 - Configuration actuelle"
        )
        
        description = st.text_area(
            "Description de la phase", 
            value=existing_phase.get("description", ""), 
            key=f"phase_desc_{index}", 
            height=100,
            placeholder="Description détaillée de cette phase d'aménagement..."
        )
        
        # Upload des figures
        figures = self.handle_file_upload_with_legend(
            "Figures de la phase", 
            ["png", "jpg", "jpeg"], 
            f"phase_fig_{index}"
        )
        
        return {
            "nom": nom,
            "description": description,
            "figures": figures
        }
    
    def _render_balisage(self) -> Dict[str, Any]:
        """Rend la section du plan de balisage."""
        self.render_section_header(
            "🚩 Plan de balisage", 
            divider=False,
            help_text="Ajoutez les planches de balisage"
        )
        
        # Upload des planches de balisage
        figures = self.handle_file_upload_with_legend(
            "Planches de balisage", 
            ["png", "jpg", "jpeg"], 
            "balisage_fig"
        )
        
        # Commentaire
        defaults = self.get_defaults()
        commentaire = self._render_optional_comment(
            "Ajouter un commentaire sur les plans de balisage",
            "Commentaire sur les planches de balisage",
            defaults["balisage_commentaire"]
        )

        return {
            "actif": len(figures) > 0,
            "figures": figures,
            "commentaire": commentaire
        }
    
    def _render_bathymetry(self) -> Dict[str, Any]:
        """Rend la section de bathymétrie."""
        self.render_section_header(
            "🗺️ Bathymétrie", 
            divider=False,
            help_text="Informations bathymétriques"
        )
        
        # Récupérer les valeurs par défaut
        defaults = self.get_defaults()
        
        # Champs obligatoires
        col1, col2 = st.columns(2)
        
        with col1:
            source = st.text_input(
                "Source bathymétrie *", 
                value=defaults["source_bathy"], 
                help="Source des données bathymétriques",
                placeholder="Ex: SHOM, Service Hydrographique..."
            )
            
            date = st.text_input(
                "Date *", 
                value=defaults["date_bathy"], 
                help="Date des relevés bathymétriques",
                placeholder="Ex: Octobre 2023"
            )
        
        with col2:
            notes = st.text_area(
                "Notes profondeur *", 
                value=defaults["notes_profondeur"], 
                help="Notes sur les profondeurs", 
                height=100,
                placeholder="Ex: Profondeurs suffisantes dans le chenal principal..."
            )
        
        # Upload des figures bathymétriques
        figures = self.handle_file_upload_with_legend(
            "Figures bathymétrie", 
            ["png", "jpg", "jpeg"], 
            "bathy_fig"
        )

        # Commentaire optionnel
        commentaire = self._render_optional_comment(
            "Ajouter un commentaire sur la bathymétrie",
            "Commentaire bathymétrie",
            defaults["bathy_commentaire"]
        )
        
        return {
            "source": source,
            "date": date,
            "notes_profondeur": notes,
            "figures": figures,
            "commentaire": commentaire
        }
    
    def _render_conditions(self) -> Dict[str, Any]:
        """Rend la section des conditions environnementales."""
        self.render_section_header(
            "🌬️ Conditions environnementales", 
            divider=False,
            help_text="💡 Définissez les données concernant les conditions environnementales pour l'étude. N'ouliez pas de précisez les valeurs retenues pour chaque condition."
        )
        
        # Onglets pour chaque type de condition
        condition_tabs = st.tabs(["🌊 Houle", "⚡ Agitation", "💨 Vent", "🌀 Courant", "🌊 Marée"])
        
        conditions_data = {}
        
        # Configuration des conditions
        condition_configs = [
            ("houle", "🌊 Houle"),
            ("agitation", "⚡ Agitation"),
            ("vent", "💨 Vent"),
            ("courant", "🌀 Courant"),
            ("maree", "🌊 Marée")
        ]
        
        for i, (condition_key, condition_title) in enumerate(condition_configs):
            with condition_tabs[i]:
                conditions_data[condition_key] = self._render_single_condition(
                    condition_key, condition_title
                )
        
        return conditions_data
    
    def _render_single_condition(self, condition_key: str, title: str,) -> Dict[str, Any]:
        """Rend une condition environnementale spécifique avec la nouvelle structure améliorée."""
        # Récupérer les valeurs par défaut
        defaults = self.get_defaults()
        
        source = st.text_input(
            "📍 Source et référence des données",
            value=st.session_state.get(f"{condition_key}_source", ""),
            placeholder=self._get_source_placeholder(condition_key),
            help="Origine et référence des données utilisées pour cette condition",
            key=f"{condition_key}_source"
        )
                
        col1, col2 = st.columns(2)
        
        with col1:
            figures = self.handle_file_upload_with_legend(
                f"📊 Figures {condition_key}", 
                ["png", "jpg", "jpeg", "pdf"], 
                f"{condition_key}_fig"
            )
            
        
        with col2:
            tableaux = self.handle_file_upload_with_legend(
                f"📋 Tableaux {condition_key}", 
                ["xlsx", "csv", "pdf"], 
                f"{condition_key}_tab"
            )
            
        # Affichage du statut des fichiers
        total_files = len(figures) + len(tableaux)
        if total_files > 0:
            st.success(f"{total_files} fichier(s) ajouté(s)")
        
        st.write("---")  # Séparateur visuel
        
        st.write("**📈 Analyse des données**")
        analyse = st.text_area(
            "Interprétation et analyse des figures/tableaux",
            value=st.session_state.get(f"{condition_key}_analyse", ""),
            placeholder=self._get_analysis_placeholder(condition_key),
            help="Analysez et interprétez les données présentées dans les figures et tableaux",
            key=f"{condition_key}_analyse",
            height=100
        )
        
        retenues_key = f"{condition_key}_retenues"
        valeurs_retenues = st.text_area(
            f"Valeurs {condition_key} critiques retenues",
            value=defaults.get(retenues_key, ""),
            key=f"{condition_key}_retenues_input",
            placeholder=self._get_conditions_placeholder(condition_key),
            help="Définissez les seuils et conditions critiques retenus pour les simulations",
            height=80
        )
        
        comment_key = f"{condition_key}_commentaire"
        commentaire = self._render_optional_comment(
            f"Ajouter un commentaire général sur {condition_key}",
            f"Commentaire {condition_key}",
            defaults.get(comment_key, ""),
            key=f"{condition_key}_comment_check"
        )
        
        return {
            "source": source,
            "figures": figures,
            "tableaux": tableaux,
            "analyse": analyse,
            "valeurs_retenues": valeurs_retenues,
            "commentaire": commentaire
        }
    
    def _get_source_placeholder(self, condition_key: str) -> str:
        """Retourne le placeholder approprié pour la source selon le type de condition."""
        placeholders = {
            "houle": "Ex: Données houlographe SHOM station X, Modèle WAVEWATCH III, Mesures in-situ 2020-2024",
            "vent": "Ex: Station météorologique Tanger Med, Données Météo-France, Rose des vents 10 ans",
            "courant": "Ex: Mesures ADCP campagne 2023, Modèle hydrodynamique TELEMAC, Observations terrain",
            "maree": "Ex: SHOM - Annuaire des marées, Données marégraphiques Port Tanger Med, Prédictions harmoniques",
            "agitation": "Ex: Modélisation numérique MIKE21, Mesures agitomètre bassin, Campagne de mesures 2023"
        }
        return placeholders.get(condition_key, "Ex: Source des données...")
    
    def _get_analysis_placeholder(self, condition_key: str) -> str:
        """Retourne le placeholder approprié pour l'analyse selon le type de condition."""
        placeholders = {
            "houle": "Ex: Analyse de la houle dominante du NW, périodes caractéristiques 8-12s, hauteurs significatives 1-3m selon les saisons...",
            "vent": "Ex: Rose des vents montrant une dominante Est (Chergui) en été, vents d'Ouest en hiver, vitesses moyennes et extrêmes...",
            "courant": "Ex: Courants de marée faibles < 1 kt, courants de dérive liés au vent, variations saisonnières et influence de la bathymétrie...",
            "maree": "Ex: Marnage semi-diurne 1.8m en VE à 0.4m en ME, hauteurs d'eau exploitables, coefficients critiques...",
            "agitation": "Ex: Agitation résiduelle faible dans le bassin protégé, critères d'exploitation < 0.5m, zones sensibles identifiées..."
        }
        return placeholders.get(condition_key, "Analysez les données présentées...")
    
    def _get_conditions_placeholder(self, condition_key: str) -> str:
        """Retourne le placeholder approprié pour les conditions retenues selon le type."""
        placeholders = {
            "houle": "Ex: Houle critique Hs=3m, Tp=10s, direction NW\nHoule opérationnelle Hs=1.5m, Tp=8s",
            "vent": "Ex: Vent critique 30 kts secteur Ouest avec rafales 40 kts\nVent limite d'exploitation 25 kts",
            "courant": "Ex: Courant maximal 1.2 kt direction variable selon marée\nCourant critique pour manœuvres > 1 kt",
            "maree": "Ex: Conditions extrêmes PM +2.4m, BM -0.7m (coeff 95-120)\nConditions moyennes PM +1.8m, BM +0.2m",
            "agitation": "Ex: Agitation maximale admissible 0.5m au poste d'amarrage\nCritère d'interruption des opérations > 0.8m"
        }
        return placeholders.get(condition_key, f"Définissez les seuils critiques pour {condition_key}...")
    
    def _adapt_data_to_columns(self, example_data: List[List[str]], 
                              original_columns: List[str], 
                              current_columns: List[str]) -> List[List[str]]:
        """Adapte les données d'exemple à la structure actuelle des colonnes."""
        if not example_data:
            return []
        
        adapted_data = []
        
        for row in example_data:
            new_row = []
            
            # Pour chaque colonne actuelle, essayer de trouver la correspondance
            for current_col in current_columns:
                value = ""
                
                # Chercher une correspondance exacte
                if current_col in original_columns:
                    orig_index = original_columns.index(current_col)
                    if orig_index < len(row):
                        value = row[orig_index]
                
                # Chercher une correspondance partielle (mots-clés)
                elif not value:
                    for i, orig_col in enumerate(original_columns):
                        if (any(word.lower() in current_col.lower() for word in orig_col.split()) or
                            any(word.lower() in orig_col.lower() for word in current_col.split())):
                            if i < len(row):
                                value = row[i]
                                break
                
                new_row.append(value)
            
            adapted_data.append(new_row)
        
        return adapted_data
        
    def _render_optional_comment(self, checkbox_label: str, textarea_label: str, 
                                default_value: str, key: str = None) -> str:
        """Rend un commentaire optionnel avec checkbox."""
        comment_exists = bool(default_value)
        
        checkbox_key = key if key else f"comment_check_{id(textarea_label)}"
        
        if st.checkbox(f"➕ {checkbox_label}", value=comment_exists, key=checkbox_key):
            return st.text_area(textarea_label, value=default_value)
        
        return ""
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Valide les données d'entrée."""
        self.errors.clear()
        self.warnings.clear()
        
        # Validation de la bathymétrie (champs requis)
        bathymetrie = data.get("bathymetrie", {})
        self.errors.extend(
            FormValidator.validate_required_fields(bathymetrie, self.required_fields)
        )
        
        # Validation des phases du plan de masse
        phases = data.get("plan_de_masse", {}).get("phases", [])
        if not phases:
            self.warnings.append("Aucune phase de plan de masse définie")
        else:
            for i, phase in enumerate(phases):
                if not phase.get("nom"):
                    self.warnings.append(f"Phase {i+1}: nom manquant")
        
        # Validation des conditions environnementales
        conditions_env = data.get("conditions_environnementales", {})
        for condition_type in ["houle", "vent", "courant", "maree", "agitation"]:
            condition_data = conditions_env.get(condition_type, {})
            
            # Vérifier qu'il y a au moins des valeurs retenues ou des conditions
            has_conditions = bool(condition_data.get("conditions"))
            has_retenues = bool(condition_data.get("valeurs_retenues", "").strip())
            
            if not has_conditions and not has_retenues:
                self.warnings.append(f"Aucune donnée pour {condition_type}")
        
        # Validation de cohérence
        self._validate_environmental_coherence(conditions_env)
        
        return len(self.errors) == 0
    
    def _validate_environmental_coherence(self, conditions_env: Dict[str, Any]):
        """Valide la cohérence des conditions environnementales."""
        # Vérifier que les conditions sont cohérentes entre elles
        houle_data = conditions_env.get("houle", {})
        vent_data = conditions_env.get("vent", {})
        
        # Exemple de validation: si houle forte, vérifier qu'il y a du vent
        houle_retenues = houle_data.get("valeurs_retenues", "").lower()
        vent_retenues = vent_data.get("valeurs_retenues", "").lower()
        
        if any(word in houle_retenues for word in ["3m", "4m", "forte"]):
            if not any(word in vent_retenues for word in ["25", "30", "35", "fort"]):
                self.warnings.append(
                    "Houle forte sans vent correspondant (vérifier la cohérence)"
                )
        
        # Vérifier la marée
        maree_data = conditions_env.get("maree", {})
        maree_retenues = maree_data.get("valeurs_retenues", "")
        
        if maree_retenues and "+" not in maree_retenues and "-" not in maree_retenues:
            self.warnings.append(
                "Valeurs de marée sans indication de hauteur (+/-)"
            )
    
    def _get_default_data_input(self) -> Dict[str, Any]:
        """Retourne des données par défaut en cas d'erreur."""
        return {
            "plan_de_masse": {"phases": [], "commentaire": ""},
            "balisage": {"actif": False, "figures": [], "commentaire": ""},
            "bathymetrie": {"source": "", "date": "", "notes_profondeur": "", "figures": [], "commentaire": ""},
            "conditions_environnementales": {
                "houle": {"conditions": [], "valeurs_retenues": "", "figures": [], "tableaux": [], "commentaire": ""},
                "vent": {"conditions": [], "valeurs_retenues": "", "figures": [], "tableaux": [], "commentaire": ""},
                "courant": {"conditions": [], "valeurs_retenues": "", "figures": [], "tableaux": [], "commentaire": ""},
                "maree": {"conditions": [], "valeurs_retenues": "", "figures": [], "tableaux": [], "commentaire": ""},
                "agitation": {"conditions": [], "valeurs_retenues": "", "figures": [], "tableaux": [], "commentaire": ""}
            }
        }


# Fonction de compatibilité pour l'ancien code
def render() -> Dict[str, Any]:
    """Fonction de compatibilité avec l'ancien code."""
    form = DataInputForm()
    return form.render()
