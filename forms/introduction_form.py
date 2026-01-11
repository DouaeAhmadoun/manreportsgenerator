# =============================================================================
# forms/introduction_form.py - Formulaire de l'introduction
# =============================================================================

import streamlit as st
from typing import Dict, Any
from .base_form import BaseForm, FormValidator


class IntroductionForm(BaseForm):
    """
    Formulaire pour la saisie de l'introduction du rapport.
    
    Gère :
    - Éléments à inclure dans l'introduction (guidelines)
    - Objectifs de l'étude
    - Validation des champs requis
    """
    
    def __init__(self):
        super().__init__("introduction")
        self.required_fields = ["guidelines", "objectifs"]
        self.min_length = 50  # Longueur minimale pour éviter des textes trop courts
    
    def render(self) -> Dict[str, Any]:
        """Rend le formulaire de l'introduction."""
        try:
            self.render_section_header(
                "✍️ Introduction", 
                divider=True,
                help_text="💡 Définissez le contexte et les objectifs de l'étude de manœuvrabilité"
            )
            
            # Récupérer les valeurs par défaut
            defaults = self.get_defaults()
            
            # Champs de l'introduction
            guidelines = self._render_guidelines_field(defaults)
            objectifs = self._render_objectifs_field(defaults)
            
            # Données du formulaire
            introduction_data = {
                "guidelines": guidelines,
                "objectifs": objectifs
            }
            
            # Validation
            if self.validate_data(introduction_data):
                self.display_validation_messages()
            
            return introduction_data
            
        except Exception as e:
            st.error(f"❌ Erreur dans le formulaire introduction : {str(e)}")
            return {"guidelines": "", "objectifs": ""}
    
    def _render_guidelines_field(self, defaults: Dict[str, Any]) -> str:
        """Rend le champ des éléments à inclure dans l'introduction."""
        guidelines = st.text_area(
            "Éléments à inclure dans l'introduction *",
            value=defaults["guidelines"],
            height=150,
            help="Contexte, enjeux, méthodologie générale...",
            placeholder="Ex: Contexte du projet, enjeux portuaires, méthodologie utilisée..."
        )
        
        # Compteur de caractères en temps réel
        if guidelines:
            char_count = len(guidelines.strip())
            if char_count < self.min_length:
                st.caption(f"📝 {char_count} caractères (minimum recommandé: {self.min_length})")
            else:
                st.caption(f"✅ {char_count} caractères")
        
        return guidelines
    
    def _render_objectifs_field(self, defaults: Dict[str, Any]) -> str:
        """Rend le champ des objectifs de l'étude."""
        objectifs = st.text_area(
            "Objectifs de l'étude * (un objectif par ligne)",
            value=defaults["objectifs"],
            height=150,
            help="Objectifs spécifiques de l'étude",
            placeholder="Ex: Évaluer la faisabilité des manœuvres, identifier les conditions critiques..."
        )

        # Convertir en liste
        objectifs_list = [c.strip() for c in objectifs.split("\n") if c.strip()]
        
        # Afficher le nombre d'objectifs
        if objectifs_list:
            char_count = len(objectifs_list)
            if char_count < 3:
                st.caption(f"⚠️ {char_count} objectifs(s) (minimum recommandé: 3)")
            else:
                st.caption(f"📝 {char_count} objectifs(s) identifié(s)")
        
        return objectifs
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Valide les données de l'introduction."""
        self.errors.clear()
        self.warnings.clear()
        
        # Validation des champs requis
        self.errors.extend(
            FormValidator.validate_required_fields(data, self.required_fields)
        )
        
        # Validation de la longueur minimale
        for field in ["guidelines", "objectifs"]:
            if field in data and data[field]:
                content = data[field].strip()
                if len(content) < self.min_length:
                    self.warnings.append(
                        f"Le champ '{field}' est très court (< {self.min_length} caractères)"
                    )
                
                # Vérifier qu'il ne s'agit pas juste d'un placeholder
                if content.lower().startswith("ex:") or content.lower().startswith("exemple"):
                    self.warnings.append(
                        f"Le champ '{field}' semble contenir du texte d'exemple"
                    )
        
        # Validation de cohérence
        guidelines_text = data.get("guidelines", "").lower()
        objectifs_text = data.get("objectifs", "").lower()
        
        # Vérifier si les objectifs sont cohérents avec les guidelines
        if guidelines_text and objectifs_text:
            # Mots-clés attendus dans une étude de manœuvrabilité
            expected_keywords = [
                "manoeuvre", "manœuvre", "navire", "port", "simulation", 
                "pilotage", "remorqueur", "accostage", "appareillage"
            ]
            
            found_in_guidelines = any(keyword in guidelines_text for keyword in expected_keywords)
            found_in_objectifs = any(keyword in objectifs_text for keyword in expected_keywords)
            
            if not found_in_guidelines and not found_in_objectifs:
                self.warnings.append(
                    "Le contenu ne semble pas spécifique à une étude de manœuvrabilité"
                )
        
        return len(self.errors) == 0
    
    def get_content_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse le contenu de l'introduction pour donner des suggestions.
        
        Args:
            data: Données de l'introduction
            
        Returns:
            Dict avec l'analyse du contenu
        """
        analysis = {
            "guidelines_length": len(data.get("guidelines", "").strip()),
            "objectifs_length": len(data.get("objectifs", "").strip()),
            "total_length": 0,
            "keywords_found": [],
            "suggestions": []
        }
        
        # Calcul de la longueur totale
        analysis["total_length"] = analysis["guidelines_length"] + analysis["objectifs_length"]
        
        # Recherche de mots-clés techniques
        text_combined = (data.get("guidelines", "") + " " + data.get("objectifs", "")).lower()
        
        technical_keywords = {
            "manœuvrabilité": ["manoeuvre", "manœuvre", "manoeuvrabilité"],
            "maritime": ["navire", "port", "maritime", "portuaire"],
            "simulation": ["simulation", "modélisation", "test"],
            "pilotage": ["pilote", "pilotage", "capitaine"],
            "assistance": ["remorqueur", "assistance", "aide"],
            "opérations": ["accostage", "appareillage", "évitage", "mouillage"]
        }
        
        for category, keywords in technical_keywords.items():
            if any(keyword in text_combined for keyword in keywords):
                analysis["keywords_found"].append(category)
        
        # Génération de suggestions
        if analysis["guidelines_length"] < 100:
            analysis["suggestions"].append(
                "Considérez développer davantage le contexte et la méthodologie"
            )
        
        if analysis["objectifs_length"] < 80:
            analysis["suggestions"].append(
                "Les objectifs pourraient être plus détaillés et spécifiques"
            )
        
        if len(analysis["keywords_found"]) < 3:
            analysis["suggestions"].append(
                "Intégrer plus de terminologie technique spécifique à la manœuvrabilité"
            )
        
        if "simulation" not in analysis["keywords_found"]:
            analysis["suggestions"].append(
                "Mentionner la méthodologie de simulation utilisée"
            )
        
        return analysis


# Fonction de compatibilité pour l'ancien code
def render() -> Dict[str, Any]:
    """Fonction de compatibilité avec l'ancien code."""
    form = IntroductionForm()
    return form.render()
