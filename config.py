import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

# Modèle IA par défaut
DEFAULT_MODEL = "openai/gpt-oss-20b:free"


def _load_json(config_file: str) -> Dict[str, Any]:
    """Charge un JSON de config; retourne {} en cas d'erreur."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(config_file: str, data: Dict[str, Any]) -> None:
    """Écrit le JSON de config de façon sûre."""
    Path(config_file).parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =============================================================================
# ENUMS ESSENTIELS
# =============================================================================

class FileType(Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"


# =============================================================================
# PARAMÈTRES APPLICATION AND API CONFIG
# =============================================================================

@dataclass
class AppSettings:
    """Paramètres essentiels de l'application"""
    max_file_size_mb: int = 50
    default_image_quality: int = 90
    log_level: str = "INFO"
    
    @classmethod
    def from_file(cls, config_file: str) -> 'AppSettings':
        data = _load_json(config_file)
        try:
            return cls(**data.get('app_settings', {}))
        except Exception:
            return cls()
    
    def save_to_file(self, config_file: str) -> None:
        try:
            config = _load_json(config_file)
            config['app_settings'] = {
                'max_file_size_mb': self.max_file_size_mb,
                'default_image_quality': self.default_image_quality,
                'log_level': self.log_level
            }
            _write_json(config_file, config)
        except Exception as e:
            logging.warning(f"Erreur sauvegarde AppSettings: {e}")

@dataclass
class APIConfig:
    """Configuration des APIs externes pour génération IA"""
    
    # OpenRouter API
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    
    # Modèles recommandés par priorité
    primary_model: str = DEFAULT_MODEL
    fallback_models: List[str] = field(default_factory=lambda: [
        "mistralai/mistral-nemo:free",
        "microsoft/phi-3-medium-128k-instruct:free",
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.1-8b-instruct:free"
    ])
    
    # Paramètres de requête
    max_tokens: int = 1500
    temperature: float = 0.7
    request_timeout: int = 30
    max_retries: int = 2
    
    # Activation/désactivation
    enable_ai_generation: bool = True
    fallback_on_error: bool = True
    
    @classmethod
    def from_file(cls, config_file: str) -> 'APIConfig':
        """Charge la config API depuis un fichier"""
        data = _load_json(config_file)
        api_data = data.get('api_config', {})
        try:
            return cls(**api_data)
        except Exception:
            return cls()
    
    def save_to_file(self, config_file: str) -> None:
        """Sauvegarde la config API dans un fichier"""
        try:
            config = _load_json(config_file)
            config['api_config'] = {
                'openrouter_api_key': self.openrouter_api_key,
                'openrouter_base_url': self.openrouter_base_url,
                'primary_model': self.primary_model,
                'fallback_models': self.fallback_models,
                'max_tokens': self.max_tokens,
                'temperature': self.temperature,
                'request_timeout': self.request_timeout,
                'max_retries': self.max_retries,
                'enable_ai_generation': self.enable_ai_generation,
                'fallback_on_error': self.fallback_on_error
            }
            _write_json(config_file, config)
        except Exception as e:
            logging.warning(f"Erreur sauvegarde config API: {e}")
    
    def is_configured(self) -> bool:
        """Vérifie si l'API est correctement configurée"""
        key = os.getenv("OPENROUTER_API_KEY", "").strip() or self.openrouter_api_key
        return bool(key)
    
    def get_active_model(self) -> str:
        """Retourne le modèle actif (primary ou fallback AI_CONFIG)"""
        if self.enable_ai_generation and self.is_configured():
            return self.primary_model
        return AI_CONFIG.get("default_model", DEFAULT_MODEL)

# =============================================================================
# CONFIGURATION PRINCIPALE
# =============================================================================

class Config:
    """Configuration essentielle"""
    
    # Dossiers (réorganisés pour plus de cohérence)
    UPLOAD_DIR = "uploads"
    OUTPUT_DIR = "exports"
    TEMPLATE_DIR = "static/templates"
    STATIC_DIR = "static"
    PROMPTS_DIR = "prompts"
    CACHE_DIR = "cache"
    
    # Fichiers
    DEFAULT_TEMPLATE = "report_template.docx"
    CONFIG_FILE = "config.json"
    
    # Validation
    REQUIRED_FIELDS = ["titre", "code_projet", "client", "type", "numero", "annee"]
    
    # Formats supportés (simplifié)
    SUPPORTED_FORMATS = {
        FileType.IMAGE: {
            "extensions": ["png", "jpg", "jpeg", "gif", "webp"],
            "max_size_mb": 20
        },
        FileType.DOCUMENT: {
            "extensions": ["pdf", "docx", "doc"],
            "max_size_mb": 50
        },
        FileType.SPREADSHEET: {
            "extensions": ["xlsx", "xls", "csv"],
            "max_size_mb": 30
        }
    }
    
    # Instance des paramètres
    _app_settings: Optional[AppSettings] = None
    _api_config: Optional[APIConfig] = None  # AJOUTEZ CETTE LIGNE
    
    @classmethod
    def get_api_config(cls) -> APIConfig:
        """Récupère la config API (singleton)"""
        if cls._api_config is None:
            cls._api_config = APIConfig.from_file(cls.CONFIG_FILE)
        return cls._api_config
    
    # AJOUTEZ CETTE MÉTHODE
    @classmethod
    def set_api_key(cls, api_key: str) -> bool:
        """Configure la clé API et sauvegarde"""
        try:
            api_config = cls.get_api_config()
            api_config.openrouter_api_key = api_key
            api_config.save_to_file(cls.CONFIG_FILE)
            cls._api_config = None  # Force reload
            return True
        except Exception as e:
            print(f"Erreur configuration API: {e}")
            return False
    
    @classmethod
    def get_app_settings(cls) -> AppSettings:
        """Récupère les paramètres (singleton)"""
        if cls._app_settings is None:
            cls._app_settings = AppSettings.from_file(cls.CONFIG_FILE)
        return cls._app_settings
    
    @classmethod
    def setup_directories(cls) -> None:
        """Crée les dossiers nécessaires"""
        directories = [cls.UPLOAD_DIR, cls.OUTPUT_DIR, cls.TEMPLATE_DIR,
                      cls.STATIC_DIR, cls.PROMPTS_DIR, cls.CACHE_DIR]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True, parents=True)
    
    @classmethod
    def validate_file_format(cls, filename: str, file_type: FileType) -> bool:
        """Valide le format d'un fichier"""
        ext = Path(filename).suffix.lower().replace('.', '')
        extensions = cls.SUPPORTED_FORMATS.get(file_type, {}).get("extensions", [])
        return ext in extensions
    
    @classmethod
    def setup_logging(cls) -> None:
        """Configure le logging"""
        settings = cls.get_app_settings()
        level = getattr(logging, settings.log_level.upper(), logging.INFO)
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')


# =============================================================================
# CONFIGURATIONS EXPORT
# =============================================================================

STREAMLIT_CONFIG = {
    "page_title": "Manœuvrabilité: Générateur de Rapports",
    "layout": "wide",
    "page_icon": "📑",
    "initial_sidebar_state": "collapsed"
}

AI_CONFIG = {
    "default_model": DEFAULT_MODEL,
    "max_tokens": 2000,
    "temperature": 0.7,
    "timeout_seconds": 30
}

def get_api_config() -> APIConfig:
    """Récupère la configuration API"""
    return Config.get_api_config()

def is_ai_configured() -> bool:
    """Vérifie si l'IA est configurée"""
    return get_api_config().is_configured()

def get_active_ai_model() -> str:
    """Récupère le modèle IA actif"""
    return get_api_config().get_active_model()

def get_openrouter_key() -> str:
    """Récupère la clé OpenRouter"""
    return os.getenv("OPENROUTER_API_KEY", "").strip() or get_api_config().openrouter_api_key

# Function to get AI model
def get_default_ai_model() -> str:
    """Retourne le modèle IA par défaut depuis la configuration"""
    return AI_CONFIG["default_model"]


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def get_app_settings() -> AppSettings:
    return Config.get_app_settings()

def validate_image_format(filename: str) -> bool:
    return Config.validate_file_format(filename, FileType.IMAGE)

def validate_document_format(filename: str) -> bool:
    return Config.validate_file_format(filename, FileType.DOCUMENT)

def validate_excel_format(filename: str) -> bool:
    return Config.validate_file_format(filename, FileType.SPREADSHEET)

def validate_file_size(file_size: int) -> bool:
    """Valide la taille d'un fichier selon les paramètres de l'application"""
    settings = get_app_settings()
    max_size = settings.max_file_size_mb * 1024 * 1024
    return file_size <= max_size

def get_upload_path(filename: str) -> Path:
    return Path(Config.UPLOAD_DIR) / filename

def get_template_path(template_name: str = None) -> Path:
    template_name = template_name or Config.DEFAULT_TEMPLATE
    return Path(Config.TEMPLATE_DIR) / template_name

def get_sample_data_path() -> Path:
    """Données d'exemple (auto-détection)"""
    new_path = Path("static/samples/sample_data_complete.json")
    return new_path if new_path.exists() else Path("static/sample_data_complete.json")

def get_static_asset_path(asset_path: str) -> Path:
    """Asset dans static/"""
    return Path("static") / asset_path


def initialize_config():
    """Initialise l'application"""
    try:
        # Créer dossiers
        Config.setup_directories()
        
        # Créer structure static/ complète
        for folder in ["static/templates", "static/samples", "static/assets"]:
            Path(folder).mkdir(parents=True, exist_ok=True)
        
        # Migrer sample_data si nécessaire
        old_path = Path("static/sample_data_complete.json")
        new_path = Path("static/samples/sample_data_complete.json")
        if old_path.exists() and not new_path.exists():
            old_path.rename(new_path)
        
        # Logging
        Config.setup_logging()
        logging.info(f"Application initialisée")
        
        return True
    except Exception as e:
        print(f"Erreur initialisation: {e}")
        return False



# Auto-initialisation
if __name__ != "__main__":
    initialize_config()
