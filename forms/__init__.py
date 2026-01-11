import importlib
from typing import Type, Optional, Callable


# =============================================================================
# CONFIGURATION DES FORMULAIRES
# =============================================================================

FORM_MAPPING = {
    # (module_name, class_name, has_static_render)
    'MetadataForm': ('metadata_form', 'MetadataForm', True),
    'IntroductionForm': ('introduction_form', 'IntroductionForm', True),
    'DataInputForm': ('data_input_form', 'DataInputForm', True),
    'ShipsForm': ('ships_form', 'ShipsForm', True),
    'SimulationsForm': ('simulations_form', 'SimulationsForm', True),
    'AnalysisForm': ('analysis_form', 'AnalysisForm', False),  # Prend des paramètres
    'ConclusionForm': ('conclusion_form', 'ConclusionForm', True),
    'AnnexesForm': ('annexes_form', 'AnnexesForm', True),
}

UTILITY_FUNCTIONS = [
    'get_form_defaults', 'safe_get_value', 'get_existing_conditions',
    'sort_all_simulations', 'categorize_file_type', 'generate_auto_legend',
    'organize_zip_contents', 'process_zip_file', 'handle_file_upload_with_legend'
]


def safe_import_form(module_name: str, class_name: str) -> Optional[Type]:
    """Import sécurisé avec fallback automatique."""
    for base_module in [f".{module_name}", f"forms.{module_name}"]:
        try:
            module = importlib.import_module(base_module, __name__ if base_module.startswith('.') else None)
            return getattr(module, class_name)
        except (ImportError, AttributeError):
            continue
    return None

def safe_import_utilities():
    """Import sécurisé des fonctions utilitaires."""
    utilities = {}
    
    for func_name in UTILITY_FUNCTIONS:
        # Essayer d'importer depuis form_utils
        for base_module in [".form_utils", "forms.form_utils"]:
            try:
                module = importlib.import_module(base_module, __name__ if base_module.startswith('.') else None)
                utilities[func_name] = getattr(module, func_name)
                break
            except (ImportError, AttributeError):
                continue
        
        # Fonction stub si import échoue
        if func_name not in utilities:
            utilities[func_name] = create_stub_function(func_name)
    
    return utilities

def create_stub_function(func_name: str) -> Callable:
    """Crée une fonction stub pour les utilitaires manquants."""
    def stub(*args, **kwargs):
        if func_name == 'safe_get_value':
            d, k, default = args[0], args[1], args[2] if len(args) > 2 else None
            return d.get(k, default) if d else default
        elif func_name in ['get_existing_conditions', 'sort_all_simulations']:
            return args[0] if args else []
        elif func_name == 'get_form_defaults':
            return {}
        else:
            return {} if 'dict' in func_name.lower() else ""
    return stub


# =============================================================================
# REGISTRE DE FORMULAIRES
# =============================================================================

class FormRegistry:
    """Gestionnaire centralisé des formulaires avec lazy loading."""
    
    def __init__(self):
        self._forms = {}
        self._loaded = False
    
    def _load_forms(self):
        """Charge tous les formulaires de manière paresseuse."""
        if self._loaded:
            return
        
        for form_name, (module_name, class_name, _) in FORM_MAPPING.items():
            form_class = safe_import_form(module_name, class_name)
            self._forms[form_name] = form_class
        
        self._loaded = True
    
    def get_form_class(self, form_name: str) -> Optional[Type]:
        """Récupère une classe de formulaire."""
        self._load_forms()
        return self._forms.get(form_name)
    
    def is_available(self, form_name: str) -> bool:
        """Vérifie si un formulaire est disponible."""
        return self.get_form_class(form_name) is not None


# Instance globale du registre
_registry = FormRegistry()


# =============================================================================
# WRAPPERS DE COMPATIBILITÉ
# =============================================================================

class FormWrapper:
    """Wrapper générique pour maintenir la compatibilité."""
    
    def __init__(self, form_name: str):
        self.form_name = form_name
    
    def _get_form_instance(self):
        """Récupère une instance du formulaire."""
        form_class = _registry.get_form_class(self.form_name)
        if form_class is None:
            return None
        return form_class()
    
    @staticmethod
    def render(*args, **kwargs):
        """Méthode render statique générique."""
        raise NotImplementedError("Doit être implémentée par les sous-classes")


class MetadataForm(FormWrapper):
    def __init__(self):
        super().__init__('MetadataForm')
    
    @staticmethod
    def render():
        form_class = _registry.get_form_class('MetadataForm')
        if form_class is None:
            return {"error": "MetadataForm non disponible"}
        try:
            return form_class().render()
        except Exception as e:
            return {"error": f"Erreur MetadataForm: {str(e)}"}


class AnalysisForm(FormWrapper):
    def __init__(self):
        super().__init__('AnalysisForm')
    
    @staticmethod
    def render(simulations):
        form_class = _registry.get_form_class('AnalysisForm')
        if form_class is None:
            return {"error": "AnalysisForm non disponible"}
        try:
            return form_class().render(simulations)
        except Exception as e:
            return {"error": f"Erreur AnalysisForm: {str(e)}"}


class ConclusionForm(FormWrapper):
    def __init__(self):
        super().__init__('ConclusionForm')
    
    @staticmethod
    def render():
        form_class = _registry.get_form_class('ConclusionForm')
        if form_class is None:
            return {"error": "ConclusionForm non disponible"}
        try:
            form = form_class()
            result = form.render()
            # Extraire juste la string si c'est un dict avec 'conclusion'
            if isinstance(result, dict) and 'conclusion' in result:
                return result['conclusion']
            return result
        except Exception as e:
            return {"error": f"Erreur ConclusionForm: {str(e)}"}


# Générer automatiquement les autres wrappers
def _create_simple_wrapper(form_name: str):
    """Crée un wrapper simple pour les formulaires sans paramètres."""
    class SimpleWrapper(FormWrapper):
        @staticmethod
        def render():
            form_class = _registry.get_form_class(form_name)
            if form_class is None:
                return {"error": f"{form_name} non disponible"}
            try:
                return form_class().render()
            except Exception as e:
                return {"error": f"Erreur {form_name}: {str(e)}"}
    
    return SimpleWrapper

# Créer les wrappers automatiquement
IntroductionForm = _create_simple_wrapper('IntroductionForm')
DataInputForm = _create_simple_wrapper('DataInputForm')
ShipsForm = _create_simple_wrapper('ShipsForm')
SimulationsForm = _create_simple_wrapper('SimulationsForm')
AnnexesForm = _create_simple_wrapper('AnnexesForm')


# =============================================================================
# UTILITAIRES ET EXPORTS
# =============================================================================

# Charger les fonctions utilitaires
_utilities = safe_import_utilities()

# Exporter les fonctions utilitaires
for func_name, func in _utilities.items():
    globals()[func_name] = func

# Classes originales pour usage avancé
def get_original_form_classes():
    """Retourne les classes de formulaires originales."""
    _registry._load_forms()
    return {name: cls for name, cls in _registry._forms.items() if cls is not None}

# Export principal
__all__ = [
    # Wrappers de compatibilité
    'MetadataForm', 'IntroductionForm', 'DataInputForm',
    'ShipsForm', 'SimulationsForm', 'AnalysisForm',
    'ConclusionForm', 'AnnexesForm',
    
    # Registre pour usage avancé
    'FormRegistry', '_registry', 'get_original_form_classes',
    
    # Fonctions utilitaires
    *UTILITY_FUNCTIONS
]


# =============================================================================
# FONCTIONS DE DIAGNOSTIC
# =============================================================================

def diagnose_forms():
    """Diagnostique l'état des formulaires (pour debug)."""
    _registry._load_forms()
    
    available = []
    missing = []
    
    for form_name in FORM_MAPPING.keys():
        if _registry.is_available(form_name):
            available.append(form_name)
        else:
            missing.append(form_name)
    
    return {
        "available": available,
        "missing": missing,
        "total": len(FORM_MAPPING)
    }

def get_form_health():
    """Retourne l'état de santé du module forms."""
    diagnosis = diagnose_forms()
    health_score = len(diagnosis["available"]) / diagnosis["total"] * 100
    
    return {
        "health_score": health_score,
        "status": "healthy" if health_score > 80 else "degraded" if health_score > 50 else "critical",
        "diagnosis": diagnosis
    }
