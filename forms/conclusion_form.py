# =============================================================================
# forms/conclusion_form.py - Formulaire de conclusion simplifié (copier-coller)
# =============================================================================

import streamlit as st
from typing import Dict, Any
from .base_form import BaseForm


class ConclusionForm(BaseForm):
    """
    Formulaire simplifié pour la saisie de la conclusion du rapport.
    
    NOUVEAU: Interface de copier-coller simple pour conclusion convenue avec le client.
    
    Gère :
    - Zone de texte simple pour copier-coller
    - Métriques de base (caractères, mots, temps de lecture)
    - Conseils pour la rédaction
    - Indicateur de statut (Court/Moyen/Complet)
    """
    
    def __init__(self):
        super().__init__("conclusion")
        self.required_fields = []  # Plus de champs obligatoires
        self.min_length = 50  # Longueur minimale réduite
        self.recommended_length = 200  # Longueur recommandée réduite
    
    def render(self) -> str:
        """
        Rend le formulaire de conclusion simplifié.
        
        Returns:
            String de la conclusion
        """
        try:
            self.render_section_header(
                "📝 Conclusion", 
                divider=True,
                help_text="💡 Copiez-collez ici la conclusion convenue avec le client"
            )
            
            # Récupérer la conclusion existante
            defaults = self.get_defaults()
            current_conclusion = defaults.get("conclusion", "")
            
            # Champ de saisie principal
            conclusion = self._render_conclusion_field(current_conclusion)
            
            return conclusion
            
        except Exception as e:
            st.error(f"❌ Erreur dans le formulaire conclusion : {str(e)}")
            return ""
    
    def _render_conclusion_field(self, current_value: str) -> str:
        """Rend le champ de saisie de la conclusion."""
        conclusion = st.text_area(
            "Conclusion du rapport*",
            value=current_value,
            height=200,
            placeholder="Le texte de conclusion doit être collé depuis la conclusion convenue avec votre client",
            help="Saisissez ou collez la conclusion finale qui a été validée avec le client"
        )
        
        return conclusion
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validation simplifiée des données de conclusion."""
        self.errors.clear()
        self.warnings.clear()
        
        conclusion = data.get("conclusion", "").strip()
        
        if conclusion:
            # Validation de longueur minimale (optionnelle)
            if len(conclusion) < self.min_length:
                self.warnings.append(
                    f"Conclusion courte (< {self.min_length} caractères) - Vérifiez qu'elle est complète"
                )
            
            # Vérification du contenu placeholder
            if conclusion.lower().startswith(("copiez ici", "exemple", "lorem ipsum")):
                self.warnings.append("La conclusion semble contenir du texte d'exemple")
            
            # Vérification des éléments essentiels (optionnel)
            elements_cles = ["résultat", "faisab", "recommand", "condition"]
            elements_trouves = [elem for elem in elements_cles 
                              if elem in conclusion.lower()]
            
            if len(elements_trouves) < 2:
                self.warnings.append(
                    "La conclusion pourrait inclure plus d'éléments clés "
                    "(résultats, faisabilité, recommandations, conditions)"
                )
        
        return True  # Pas d'erreurs bloquantes, seulement des avertissements


# Fonction de compatibilité pour l'ancien code
def render() -> str:
    """Fonction de compatibilité avec l'ancien code."""
    form = ConclusionForm()
    return form.render()


# Fonction utilitaire pour sauvegarder les données
def save_conclusion_data(conclusion: str):
    """Sauvegarde la conclusion dans rapport_data."""
    if 'rapport_data' not in st.session_state:
        st.session_state.rapport_data = {}
    
    st.session_state.rapport_data['conclusion'] = conclusion


# Fonction utilitaire pour récupérer les données
def get_conclusion_data() -> str:
    """Récupère la conclusion depuis rapport_data."""
    rapport_data = st.session_state.get("rapport_data", {})
    return rapport_data.get("conclusion", "")
