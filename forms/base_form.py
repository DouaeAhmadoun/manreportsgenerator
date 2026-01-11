import streamlit as st
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseForm(ABC):
    """
    Classe de base abstraite pour tous les formulaires.
    
    Fournit les fonctionnalités communes :
    - Gestion des valeurs par défaut
    - Validation de base
    - Gestion des erreurs
    - Interface standardisée
    """
    
    def __init__(self, form_key: str):
        """
        Initialise le formulaire.
        
        Args:
            form_key: Clé unique pour ce formulaire
        """
        self.form_key = form_key
        self.errors = []
        self.warnings = []
    
    @abstractmethod
    def render(self) -> Dict[str, Any]:
        """
        Rend le formulaire et retourne les données.
        
        Cette méthode doit être implémentée par chaque formulaire.
        
        Returns:
            Dict contenant les données du formulaire
        """
        pass
    
    def get_defaults(self) -> Dict[str, Any]:
        """
        Récupère les valeurs par défaut depuis rapport_data.
        
        Returns:
            Dict des valeurs par défaut pour ce formulaire
        """
        from .form_utils import get_form_defaults
        return get_form_defaults()
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Valide les données du formulaire.
        
        Args:
            data: Données à valider
            
        Returns:
            True si valide, False sinon
        """
        self.errors.clear()
        self.warnings.clear()
        
        # Validation de base - peut être surchargée
        if not data:
            self.errors.append("Aucune donnée fournie")
            return False
        
        return True
    
    def display_validation_messages(self):
        """Affiche les messages de validation."""
        for error in self.errors:
            st.error(f"{error}")
        
        for warning in self.warnings:
            st.warning(f"{warning}")
    
    def is_filled(self, value: Any) -> bool:
        """
        Vérifie si une valeur n'est pas vide.
        
        Args:
            value: Valeur à tester
            
        Returns:
            True si la valeur n'est pas vide
        """
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ""
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return bool(value)
    
    def save_uploaded_file(self, uploaded_file) -> str:
        """
        Sauvegarde un fichier uploadé.
        
        Args:
            uploaded_file: Fichier Streamlit uploadé
            
        Returns:
            Chemin du fichier sauvé ou chaîne vide si erreur
        """
        from utils.data import save_uploaded_file   
        return save_uploaded_file(uploaded_file)
    
    def handle_file_upload_with_legend(self, label: str, file_types: List[str], key: str) -> List[dict]:
        """
        Gère l'upload de fichiers avec légendes.
        
        Args:
            label: Label du widget d'upload
            file_types: Types de fichiers acceptés
            key: Clé unique pour le widget
            
        Returns:
            Liste des fichiers avec métadonnées
        """
        from .form_utils import handle_file_upload_with_legend
        return handle_file_upload_with_legend(label, file_types, key)
    
    def create_dynamic_list_widget(self, 
                                 label: str, 
                                 session_key: str, 
                                 default_items: List[Any] = None,
                                 item_renderer = None) -> List[Any]:
        """
        Crée un widget de liste dynamique avec boutons Ajouter/Supprimer.
        
        Args:
            label: Label de la section
            session_key: Clé de session pour stocker la liste
            default_items: Éléments par défaut
            item_renderer: Fonction pour rendre chaque élément
            
        Returns:
            Liste des éléments
        """
        if session_key not in st.session_state:
            st.session_state[session_key] = default_items or []
        
        items = []
        for i in range(len(st.session_state[session_key])):
            with st.expander(f"{label} {i+1}", expanded=True):
                existing_item = st.session_state[session_key][i]
                
                if item_renderer:
                    item = item_renderer(i, existing_item)
                else:
                    item = existing_item
                
                if st.button(f"🗑️ Supprimer {label} {i+1}", key=f"del_{session_key}_{i}"):
                    st.session_state[session_key].pop(i)
                    st.rerun()
                
                items.append(item)
        
        if st.button(f"➕ Ajouter {label}", key=f"add_{session_key}"):
            st.session_state[session_key].append({})
            st.rerun()
        
        return items
    
    def render_section_header(self, title: str, divider: bool = True, help_text: str = None):
        """
        Rend un en-tête de section standardisé.
        
        Args:
            title: Titre de la section
            divider: Afficher un diviseur
            help_text: Texte d'aide optionnel
        """
        st.subheader(title, divider=divider)
        if help_text:
            st.info(help_text)


class FormValidator:
    """Validateur spécialisé pour les formulaires."""
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        Valide les champs requis.
        
        Args:
            data: Données à valider
            required_fields: Liste des champs requis
            
        Returns:
            Liste des erreurs
        """
        errors = []
        for field in required_fields:
            if field not in data or not FormValidator._is_field_filled(data[field]):
                errors.append(f"Champ requis manquant : {field}")
        return errors
    
    @staticmethod
    def _is_field_filled(value: Any) -> bool:
        """Vérifie si un champ est rempli."""
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ""
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return bool(value)


class FormErrorHandler:
    """Gestionnaire d'erreurs pour les formulaires."""
    
    @staticmethod
    def handle_form_error(form_name: str, error: Exception, show_details: bool = False):
        """
        Gère une erreur de formulaire de manière standardisée.
        
        Args:
            form_name: Nom du formulaire
            error: Exception levée
            show_details: Afficher les détails techniques
        """
        st.error(f"Erreur dans le formulaire {form_name}: {str(error)}")
        
        if show_details:
            import traceback
            with st.expander("🔍 Détails techniques"):
                st.error(traceback.format_exc())
