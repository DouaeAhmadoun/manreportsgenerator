import streamlit as st
from datetime import datetime
from typing import Dict, Any, List

from utils.validation import validate_report
from utils.data import (clean_data_for_export, create_json_download)
from word_export import export_word_ui
from sample_data_generator import add_sample_data_ui
from config import Config, STREAMLIT_CONFIG

st.set_page_config(**STREAMLIT_CONFIG)

# =============================================================================
# CONFIGURATION DES ONGLETS
# =============================================================================

TABS_CONFIG = [
    ("📁", "Métadonnées", "MetadataForm"),
    ("✍️", "Introduction", "IntroductionForm"), 
    ("📊", "Données d'entrée", "DataInputForm"),
    ("🚢", "Navires", "ShipsForm"),
    ("🌀", "Simulations", "SimulationsForm"),
    ("📈", "Analyse", "AnalysisForm"),
    ("📝", "Conclusion", "ConclusionForm"),
    ("📎", "Annexes", "AnnexesForm"),
    ("🧾", "Export", None)
]


# =============================================================================
# CLASSE PRINCIPALE SIMPLIFIÉE
# =============================================================================

class ReportApp:
    """Application principale simplifiée et optimisée"""
    
    def __init__(self):
        self.config = Config()
        self.rapport_data = self._initialize_session_state()
        self.form_classes = self._load_form_classes()
    
    def _load_form_classes(self) -> Dict[str, Any]:
        """Charge les classes de formulaires une seule fois."""
        from forms import (MetadataForm, IntroductionForm, DataInputForm,
                           ShipsForm, SimulationsForm, AnalysisForm,
                           ConclusionForm, AnnexesForm)
        
        return {
            "MetadataForm": MetadataForm,
            "IntroductionForm": IntroductionForm,
            "DataInputForm": DataInputForm,
            "ShipsForm": ShipsForm,
            "SimulationsForm": SimulationsForm,
            "AnalysisForm": AnalysisForm,
            "ConclusionForm": ConclusionForm,
            "AnnexesForm": AnnexesForm
        }
    
    def _initialize_session_state(self) -> Dict[str, Any]:
        """Initialise les données de session de manière centralisée"""
        if "rapport_data" not in st.session_state:
            st.session_state.rapport_data = {}
        return st.session_state.rapport_data
    
    def run(self):
        """Point d'entrée principal"""
        self._render_header()
        self._render_tabs()
        self._save_session_state()
    
    def _render_header(self):
        """En-tête optimisé"""
        st.title("📄 Générateur de Rapport de Manœuvrabilité - TME")
        
        # Interface données de test
        with st.container():
            add_sample_data_ui()
    
    def _render_tabs(self):
        """Rendu des onglets optimisé"""
        # Créer les onglets
        tab_labels = [f"{icon} {label}" for icon, label, _ in TABS_CONFIG]
        tabs = st.tabs(tab_labels)
        
        # Rendre chaque onglet avec gestion d'erreur
        for i, (icon, label, form_class) in enumerate(TABS_CONFIG):
            with tabs[i]:
                try:
                    if form_class:
                        self._render_form_tab(label, form_class)
                    else:
                        self._render_export_tab()
                except Exception as e:
                    st.error(f"❌ Erreur onglet {label}: {str(e)}")
    
    def _render_form_tab(self, label: str, form_class_name: str):
        """Rendu optimisé des onglets de formulaire"""
        section_key = self._get_section_key(label)
        
        # Import dynamique optimisé
        form_result = self._import_and_render_form(form_class_name)
        
        if form_result is not None:
            self.rapport_data[section_key] = form_result
    
    def _import_and_render_form(self, form_class_name: str):
        """Import et rendu de formulaire avec cache et gestion d'erreur"""
        try:
            form_class = self.form_classes.get(form_class_name)
                        
            if form_class:
                # Gestion spéciale pour AnalysisForm
                if form_class_name == "AnalysisForm":
                    simulations_data = self._get_simulations_data()
                    return form_class.render(simulations_data)
                else:
                    return form_class.render()
            else:
                st.error(f"❌ Formulaire {form_class_name} non trouvé")
                return None
                
        except Exception as e:
            st.error(f"❌ Erreur formulaire {form_class_name}: {str(e)}")
            return None
    
    def _get_section_key(self, label: str) -> str:
        """Mapping optimisé des labels vers les clés de section"""
        mapping = {
            "Métadonnées": "metadonnees",
            "Données d'entrée": "donnees_entree", 
            "Navires": "donnees_navires"
        }
        return mapping.get(label, label.lower().replace(" ", "_").replace("'", ""))
    
    def _get_simulations_data(self) -> List:
        """Récupère les données de simulation de manière sûre"""
        simulations = self.rapport_data.get("simulations", {})
        if isinstance(simulations, dict):
            return simulations.get("simulations", [])
        return []
    
    def _render_export_tab(self):
        """Onglet d'export optimisé"""
        ExportManager(self.rapport_data).render()
    
    def _save_session_state(self):
        """Sauvegarde optimisée de l'état"""
        st.session_state.rapport_data = self.rapport_data


# =============================================================================
# GESTIONNAIRE D'EXPORT OPTIMISÉ
# =============================================================================

class ExportManager:
    """Gestionnaire d'export simplifié et optimisé"""
    
    def __init__(self, rapport_data: Dict[str, Any]):
        self.rapport_data = rapport_data
        self.is_valid = validate_report(rapport_data)
    
    def render(self):
        """Interface d'export principale"""
        self._render_word_export()
        self._render_reset_section()
    
    def _render_download_buttons(self):
        """Boutons de téléchargement optimisés"""
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON Download
            clean_data = clean_data_for_export(self.rapport_data)
            json_buffer = create_json_download(clean_data)
            
            st.download_button(
                "📥 Télécharger JSON",
                json_buffer,
                file_name=f"rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # Aperçu JSON
            if st.button("👁️ Aperçu JSON"):
                with st.expander("🔍 Données JSON", expanded=True):
                    st.json(clean_data)
    
    def _render_word_export(self):
        """Section export Word"""
        export_word_ui(self.rapport_data)
    
    def _render_reset_section(self):
        """Section de réinitialisation simplifiée"""
        if st.button("🗑️ Réinitialiser", type="secondary"):
            if st.session_state.get("_confirm_reset"):
                st.session_state.rapport_data = {}
                st.session_state._confirm_reset = False
                st.success("✅ Données réinitialisées")
                st.rerun()
            else:
                st.session_state._confirm_reset = True
                st.warning("⚠️ Cliquez à nouveau pour confirmer")


# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================

def main():
    """Point d'entrée principal optimisé"""
    try:
        # Lancer l'application
        app = ReportApp()
        app.run()
        
    except Exception as e:
        st.error(f"❌ Erreur critique: {str(e)}")
        
        # Debug info en expandeur
        with st.expander("🔍 Détails techniques"):
            import traceback
            st.code(traceback.format_exc())
        
        st.info("💡 Essayez de recharger la page")


if __name__ == "__main__":
    main()
