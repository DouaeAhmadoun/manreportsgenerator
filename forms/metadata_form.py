# =============================================================================
# forms/metadata_form.py - Formulaire des métadonnées
# =============================================================================

import streamlit as st
import os
from typing import Dict, Any, List
from .base_form import BaseForm, FormValidator
from .form_utils import initialize_session_key


class MetadataForm(BaseForm):
    """
    Formulaire pour la saisie des métadonnées du rapport.
    
    Gère :
    - Informations de base du projet
    - Informations client
    - Informations du document
    - Historique des révisions
    - Upload des images (logo, image principale)
    """
    
    def __init__(self):
        super().__init__("metadata")
        self.required_fields = ["titre", "code_projet", "client", "type", "numero", "annee"]
    
    def render(self) -> Dict[str, Any]:
        """Rend le formulaire des métadonnées."""
        try:
            self.render_section_header("📁 Métadonnées du rapport", divider=True)
            
            # Récupérer les valeurs par défaut
            defaults = self.get_defaults()
            
            # Sections du formulaire
            basic_info = self._render_basic_info(defaults)
            client_info = self._render_client_info(defaults)
            document_info = self._render_document_info(defaults)
            revisions = self._render_revisions()
            
            # Combiner toutes les données
            metadata = {
                **basic_info,
                **client_info,
                **document_info,
                "historique_revisions": revisions
            }
            
            # Validation
            if self.validate_data(metadata):
                self.display_validation_messages()
            
            return metadata
            
        except Exception as e:
            st.error(f"❌ Erreur dans le formulaire métadonnées : {str(e)}")
            return {}
    
    def _render_basic_info(self, defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Rend la section des informations de base."""
        #st.subheader("Informations de base", divider=True)
        
        # Champs obligatoires
        titre = st.text_input(
            "Nom du projet *", 
            value=defaults["titre"], 
            help="Nom du projet étudié"
        )
        
        code_projet = st.text_input(
            "Code projet *", 
            value=defaults["code_projet"], 
            help="Code unique du projet"
        )
        
        # Type d'étude
        type_options = ["initiale", "complémentaire", "provisoire"]
        current_type = defaults["type_etude"]
        type_index = type_options.index(current_type) if current_type in type_options else 0
        
        type_etude = st.selectbox(
            "Type d'étude",
            type_options,
            index=None,
            help="Veuillez sélectionner le type d'étude de manœuvrabilité"
        )
        
        # Image principale
        main_image_path = self._render_image_upload(
            "Image principale", 
            "main_image_upload",
            defaults["main_image"],
            "Image principale du rapport (optionnel)"
        )
        
        return {
            "titre": titre,
            "code_projet": code_projet,
            "type_etude": type_etude,
            "main_image": main_image_path
        }
    
    def _render_client_info(self, defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Rend la section des informations client."""
        from datetime import datetime

        st.subheader("Informations du client", divider=True)
        
        client = st.text_input(
            "Client *", 
            value=defaults["client"], 
            help="Nom du client"
        )
        
        # Logo client
        logo_path = self._render_image_upload(
            "Logo du client",
            "client_logo_upload", 
            defaults["client_logo"],
            "Logo du client (optionnel)"
        )
        
        return {
            "client": client,
            "client_logo": logo_path
        }
    
    def _render_document_info(self, defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Rend la section des informations du document."""
        from datetime import datetime
        st.subheader("Informations du document", divider=True)
        
        type_doc = st.text_input(
            "Type de document *", 
            value=defaults["type"]
        )
        
        numero_doc = st.text_input(
            "Numéro de document *", 
            value=defaults["numero"], 
            help="Numéro unique du document"
        )
        
        annee_doc = st.number_input(
            "Année *",
            min_value=2000,
            max_value=2999,
            value=int(defaults["annee"]) if defaults["annee"] else datetime.now().year, 
            help="Année du document"
        )
        
        return {
            "type": type_doc,
            "numero": numero_doc,
            "annee": annee_doc
        }
    
    def _render_revisions(self) -> List[Dict[str, Any]]:
        """Rend la section de gestion des révisions."""
        st.subheader("Révisions", divider=True)
        
        # Initialiser les révisions depuis rapport_data
        initialize_session_key(
            "revisions",
            [], 
            "metadonnees.historique_revisions"
        )
        
        return self.create_dynamic_list_widget(
            "Révision",
            "revisions",
            [],
            self._render_single_revision
        )
    
    def _render_single_revision(self, index: int, existing_rev: Dict[str, Any]) -> Dict[str, Any]:
        """Rend un formulaire de révision individuelle."""
        col1, col2 = st.columns(2)
        
        with col1:
            version = st.text_input(
                "Version", 
                value=existing_rev.get("version", ""), 
                key=f"rev_version_{index}"
            )
            
            date = st.date_input(
                "Date", 
                value=existing_rev.get("date", ""), 
                format="DD/MM/YYYY", 
                key=f"rev_date_{index}"
            )
            
            description = st.text_input(
                "Description", 
                value=existing_rev.get("description", ""), 
                key=f"rev_description_{index}"
            )
        
        with col2:
            auteur = st.text_input(
                "Auteur", 
                value=existing_rev.get("auteur", ""), 
                key=f"rev_auteur_{index}"
            )
            
            verificateur = st.text_input(
                "Vérificateur", 
                value=existing_rev.get("verificateur", ""), 
                key=f"rev_verificateur_{index}"
            )
            
            approbateur = st.text_input(
                "Approbateur", 
                value=existing_rev.get("approbateur", ""), 
                key=f"rev_approbateur_{index}"
            )
        
        return {
            "version": version,
            "date": str(date) if date else existing_rev.get("date", ""),
            "description": description,
            "auteur": auteur,
            "verificateur": verificateur,
            "approbateur": approbateur
        }
    
    def _render_image_upload(self, label: str, key: str, current_path: str, help_text: str) -> str:
        """Rend un widget d'upload d'image avec aperçu."""
        uploaded_file = st.file_uploader(
            label,
            type=["png", "jpg", "jpeg"],
            help=help_text,
            key=key
        )
        
        # Utiliser le nouveau fichier ou garder l'existant
        image_path = self.save_uploaded_file(uploaded_file) if uploaded_file else current_path
        
        # Afficher l'aperçu si une image existe
        if image_path and os.path.exists(image_path):
            st.image(image_path, caption=label, width=200)
        
        return image_path
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Valide les données des métadonnées."""
        self.errors.clear()
        self.warnings.clear()
        
        # Validation des champs requis
        self.errors.extend(
            FormValidator.validate_required_fields(data, self.required_fields)
        )
        
        # Validation spécifique
        if data.get("annee"):
            try:
                annee = int(data["annee"])
                if annee < 2000 or annee > 2030:
                    self.warnings.append("Année inhabituelle détectée")
            except ValueError:
                self.errors.append("L'année doit être un nombre")
        
        # Validation des révisions
        revisions = data.get("historique_revisions", [])
        if not revisions:
            self.warnings.append("Aucune révision définie")
        else:
            for i, rev in enumerate(revisions):
                if not rev.get("version"):
                    self.warnings.append(f"Version manquante pour la révision {i+1}")
        
        return len(self.errors) == 0


# Fonction de compatibilité pour l'ancien code
def render() -> Dict[str, Any]:
    """Fonction de compatibilité avec l'ancien code."""
    form = MetadataForm()
    return form.render()
