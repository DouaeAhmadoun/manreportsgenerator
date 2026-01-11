from pathlib import Path

# Configuration
CACHE_DIR = Path("agents/training_cache")
REPORTS_DIR = Path("exemples_rapports")


def is_training_available() -> bool:
    """Vérifie si l'entraînement est disponible"""
    cache_file = CACHE_DIR / "training_data_granular.json"
    metadata_file = CACHE_DIR / "training_metadata_granular.json"
    
    if not (cache_file.exists() and metadata_file.exists()):
        return False
    
    try:
        import json
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata.get("training_type") == "granular_v2"
    except:
        return False


def get_training_status() -> dict:
    """Statut rapide de l'entraînement"""
    available = is_training_available()
    
    sections_count = 0
    if available:
        try:
            import json
            with open(CACHE_DIR / "training_data_granular.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            sections_count = len([s for s, examples in data.items() if examples])
        except:
            pass
    
    return {
        "ready": available,
        "training_type": "granular_v2" if available else "none",
        "sections_count": sections_count,
    }


# =============================================================================
# RE-EXPORTS depuis pretrained_agents
# =============================================================================

from .pretrained_agents import (
    PretrainedManager,
    create_pretrained_manager,
    generate_granular_sections_for_report,
    get_granular_system_status,
)

# =============================================================================
# RE-EXPORTS depuis training_manager
# =============================================================================

from .training_manager import (
    TrainingManager,
    force_granular_retrain,
    check_granular_prompts_integration,
)


# =============================================================================
# EXPORTS PUBLICS
# =============================================================================

__all__ = [
    # Configuration
    "CACHE_DIR",
    "REPORTS_DIR",
    
    # Statut
    "is_training_available",
    "get_training_status",
    
    # Génération (depuis pretrained_agents)
    "PretrainedManager",
    "create_pretrained_manager",
    "generate_granular_sections_for_report",
    "get_granular_system_status",
    
    # Entraînement (depuis training_manager)
    "TrainingManager",
    "force_granular_retrain",
    "check_granular_prompts_integration",
]


'''
from pathlib import Path
from typing import List


# Configuration globale granulaire
CACHE_DIR = Path("agents/training_cache")
REPORTS_DIR = Path("exemples_rapports")
GRANULAR_CACHE_FILES = [
    "training_data_granular.json",
    "training_metadata_granular.json", 
    "prompts_mapping_granular.json"
]


def is_granular_training_available() -> bool:
    """Vérifie rapidement si l'entraînement granulaire est disponible"""
    granular_cache = CACHE_DIR / "training_data_granular.json"
    metadata_cache = CACHE_DIR / "training_metadata_granular.json"
    
    if not (granular_cache.exists() and metadata_cache.exists()):
        return False
    
    # Vérifier que c'est bien granulaire
    try:
        import json
        with open(metadata_cache, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata.get("training_type") == "granular_v2"
    except:
        return False


def get_training_status() -> dict:
    """Statut rapide sans imports lourds"""
    
    granular_available = is_granular_training_available()
    reports_count = len(list(REPORTS_DIR.glob("*.docx"))) if REPORTS_DIR.exists() else 0
    
    # Compter les sections granulaires disponibles
    granular_sections = 0
    if granular_available:
        try:
            import json
            granular_cache = CACHE_DIR / "training_data_granular.json"
            with open(granular_cache, 'r', encoding='utf-8') as f:
                data = json.load(f)
            granular_sections = len([s for s, examples in data.items() if examples])
        except:
            pass
    
    return {
        "cache_exists": granular_available,
        "reports_dir_exists": REPORTS_DIR.exists(),
        "reports_count": reports_count,
        "ready": granular_available,
        "training_type": "granular_v2" if granular_available else "none",
        "granular_sections": granular_sections,
        "completeness": granular_sections / 25 if granular_sections > 0 else 0  # 25 sections granulaires prévues
    }


# ✨ INTERFACE PRINCIPALE - GRANULAIRE
def generate_ai_sections_for_report(rapport_data: dict, 
                                   model: str = "mistralai/mistral-nemo:free",
                                   granular: bool = True,
                                   sections_requested: List[str] = None) -> dict:
    """
    Génère automatiquement les sections avec agents pré-entraînés granulaires
    
    Args:
        rapport_data: Données complètes du rapport (format existant)
        model: Modèle IA à utiliser
        granular: True = génération granulaire, False = format classique
        sections_requested: Sections spécifiques à générer
        
    Returns:
        Dict {section_name: generated_content} - Compatible + Granulaire
    """
    
    try:
        if granular and is_granular_training_available():
            # Import paresseux du système granulaire
            from .pretrained_agents import generate_ai_sections_for_report as generate_granular
            
            print("🚀 Génération granulaire avec agents pré-entraînés ...")
            return generate_granular(rapport_data, model)
        
        else:
            # Fallback vers l'ancien système si disponible
            try:
                from .pretrained_agents import generate_with_pretrained_agents
                print("🔄 Fallback vers système classique...")
                return generate_with_pretrained_agents(rapport_data, model)
            except ImportError:
                print("⚠️ Système classique non disponible")
                return _generate_fallback_sections(rapport_data)
        
    except ImportError as e:
        print(f"⚠️ Agents granulaires non disponibles: {e}")
        return _generate_fallback_sections(rapport_data)
    
    except Exception as e:
        print(f"❌ Erreur génération IA: {e}")
        return _generate_fallback_sections(rapport_data)


def generate_granular_sections_for_report(rapport_data: dict,
                                         model: str = "mistralai/mistral-nemo:free",
                                         sections_requested: List[str] = None) -> dict:
    """
    Force l'utilisation du système granulaire
    """
    
    try:
        from .pretrained_agents import generate_granular_sections_for_report
        
        print("🚀 Génération granulaire explicite...")
        return generate_granular_sections_for_report(rapport_data, model, sections_requested)
        
    except ImportError as e:
        print(f"❌ Système granulaire non disponible: {e}")
        return {}
    
    except Exception as e:
        print(f"❌ Erreur génération granulaire: {e}")
        return {}


def _generate_fallback_sections(rapport_data: dict) -> dict:
    """Sections de fallback sans IA (mode dégradé)"""
    return {
        "introduction": "TO-DO: Rédigez ici votre introduction.",
        "donnees_entree": "TO-DO: Rédigez ici la section des données d'entrée.",
        "navires": "TO-DO: Rédigez ici la section sur les navires.",
        "remorqueurs": "TO-DO: Rédigez ici la section sur les remorqueurs.",
        "simulations": "TO-DO: Rédigez ici la description des simulations.",
        "analyse": "TO-DO: Rédigez ici votre analyse des simulations.",
        "conclusion": "TO-DO: Rédigez ici votre conclusion et recommandations."
    }


# ✨ UTILITAIRES D'ENTRAÎNEMENT GRANULAIRE
def train_granular_agents(force_retrain: bool = False) -> bool:
    """Lance l'entraînement granulaire des agents"""
    
    try:
        if force_retrain or not is_granular_training_available():
            from .training_manager import force_granular_retrain
            
            print("🎓 Lancement de l'entraînement granulaire...")
            return force_granular_retrain()
        else:
            print("✅ Agents granulaires déjà entraînés")
            return True
        
    except ImportError as e:
        print(f"❌ Module d'entraînement granulaire non disponible: {e}")
        return False
    
    except Exception as e:
        print(f"❌ Erreur entraînement granulaire: {e}")
        return False


def train_agents(force_retrain: bool = False) -> bool:
    """Lance l'entraînement (privilégie le granulaire)"""
    return train_granular_agents(force_retrain)


def add_training_report(report_path: str) -> bool:
    """Ajoute un rapport à l'entraînement granulaire"""
    
    try:
        from training_manager import TrainingManager
        
        manager = TrainingManager()
        
        # Copier le rapport
        import shutil
        REPORTS_DIR.mkdir(exist_ok=True)
        dst_path = REPORTS_DIR / Path(report_path).name
        shutil.copy2(report_path, dst_path)
        
        print(f"✅ Rapport ajouté: {dst_path.name}")
        
        # Relancer l'entraînement granulaire
        return train_granular_agents(force_retrain=True)
        
    except Exception as e:
        print(f"❌ Erreur ajout rapport: {e}")
        return False


def get_detailed_status() -> dict:
    """Statut détaillé avec performance du système granulaire"""
    
    try:
        from .pretrained_agents import get_granular_system_status
        
        status = get_granular_system_status()
        
        # Ajouter des infos sur l'entraînement
        training_status = get_training_status()
        status.update({
            "training_completeness": training_status["completeness"],
            "granular_sections_available": training_status["granular_sections"],
            "reports_count": training_status["reports_count"]
        })
        
        return status
        
    except Exception as e:
        return {
            "error": str(e),
            "overall_readiness": 0,
            "recommendation": "❌ Système granulaire non disponible - Vérifiez l'installation"
        }


def check_granular_prompts_integration() -> dict:
    """Vérifie l'intégration granulaire avec les prompts"""
    
    try:
        from .training_manager import check_granular_prompts_integration
        return check_granular_prompts_integration()
    
    except Exception as e:
        return {"error": str(e), "ready_for_training": False}


# ✨ INTERFACE CLI INTÉGRÉE GRANULAIRE
def run_granular_training_cli():
    """Lance l'interface CLI granulaire"""
    
    try:
        from .training_manager import cli_force_granular_retrain
        return cli_force_granular_retrain()
        
    except ImportError:
        print("❌ CLI granulaire non disponible")
        return 1


def run_training_cli():
    """Lance l'interface CLI (privilégie granulaire)"""
    return run_granular_training_cli()


# ✨ SETUP AUTOMATIQUE GRANULAIRE
def auto_setup_granular():
    """Setup automatique granulaire complet"""
    
    print("🚀 Setup automatique des agents IA granulaires")
    
    # 1. Créer les dossiers
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. Vérifier les rapports
    reports = list(REPORTS_DIR.glob("*.docx")) + list(REPORTS_DIR.glob("*.pdf"))
    
    if not reports:
        print(f"📁 Dossiers créés: {REPORTS_DIR}")
        print("💡 Ajoutez vos rapports .docx/.pdf puis relancez train_granular_agents()")
        return False
    
    # 3. Vérifier si entraînement granulaire existe
    if not is_granular_training_available():
        print(f"📚 {len(reports)} rapports trouvés - Lancement entraînement granulaire...")
        return train_granular_agents(force_retrain=True)
    else:
        print("✅ Agents granulaires déjà entraînés et prêts")
        
        # Afficher le statut détaillé
        status = get_training_status()
        print(f"🎯 Sections granulaires: {status['granular_sections']}")
        print(f"📊 Complétude: {status['completeness']:.1%}")
        
        return True


def auto_setup():
    """Setup automatique (privilégie granulaire)"""
    return auto_setup_granular()


# ✨ MIGRATION ET COMPATIBILITÉ
def migrate_to_granular() -> bool:
    """Migre l'ancien système vers le granulaire"""
    
    print("🔄 Migration vers le système granulaire")
    
    # Vérifier si l'ancien système existe
    old_cache = CACHE_DIR / "training_data.json"
    if old_cache.exists():
        print("📦 Ancien système détecté - Sauvegarde...")
        
        # Sauvegarder l'ancien cache
        backup_dir = CACHE_DIR / "backup_classic"
        backup_dir.mkdir(exist_ok=True)
        
        import shutil
        import json
        from datetime import datetime
        
        try:
            shutil.copy2(old_cache, backup_dir / f"training_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            print("✅ Sauvegarde effectuée")
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde: {e}")
    
    # Lancer l'entraînement granulaire
    print("🚀 Lancement de l'entraînement granulaire...")
    success = train_granular_agents(force_retrain=True)
    
    if success:
        print("✅ Migration vers granulaire réussie!")
        return True
    else:
        print("❌ Migration échouée")
        return False


# ✨ COMPATIBILITÉ AVEC L'EXISTANT (vos anciens imports)
def check_agents_availability() -> bool:
    """Compatibilité avec l'ancien code"""
    return is_granular_training_available()


def get_mock_ai_generator():
    """Compatibilité - Retourne l'interface principale granulaire"""
    class UnifiedAIGenerator:
        def generate_ai_sections_for_report(self, rapport_data: dict, **kwargs) -> dict:
            return generate_ai_sections_for_report(rapport_data, **kwargs)
        
        def generate_granular_sections_for_report(self, rapport_data: dict, **kwargs) -> dict:
            return generate_granular_sections_for_report(rapport_data, **kwargs)
    
    return UnifiedAIGenerator()


# ✨ UTILITAIRES AVANCÉS
def get_available_granular_sections() -> List[str]:
    """Retourne la liste des sections granulaires disponibles"""
    
    try:
        from .pretrained_agents import PretrainedManager
        manager = PretrainedManager()
        return list(manager.section_generators.keys())
    except:
        return []


def validate_granular_system() -> dict:
    """Validation complète du système granulaire"""
    
    validation = {
        "system_valid": False,
        "training_data": False,
        "prompts_available": False,
        "agents_functional": False,
        "recommendations": []
    }
    
    try:
        # 1. Vérifier les données d'entraînement
        if is_granular_training_available():
            validation["training_data"] = True
            print("✅ Données d'entraînement granulaires OK")
        else:
            validation["recommendations"].append("Lancer train_granular_agents()")
            print("❌ Données d'entraînement manquantes")
        
        # 2. Vérifier les prompts
        prompts_status = check_granular_prompts_integration()
        if not prompts_status.get("error") and prompts_status.get("prompts_found", 0) > 0:
            validation["prompts_available"] = True
            print(f"✅ Prompts granulaires OK ({prompts_status['prompts_found']} trouvés)")
        else:
            validation["recommendations"].append("Vérifier le dossier prompts/")
            print("❌ Prompts granulaires insuffisants")
        
        # 3. Test des agents
        try:
            test_data = {"metadonnees": {"titre": "Test", "client": "Test"}}
            result = generate_granular_sections_for_report(test_data, sections_requested=["introduction"])
            
            if result and "introduction" in result:
                validation["agents_functional"] = True
                print("✅ Agents granulaires fonctionnels")
            else:
                validation["recommendations"].append("Vérifier la configuration des agents")
                print("❌ Agents granulaires non fonctionnels")
        except Exception as e:
            validation["recommendations"].append(f"Erreur agents: {e}")
            print(f"❌ Test agents échoué: {e}")
        
        # 4. Validation globale
        validation["system_valid"] = all([
            validation["training_data"],
            validation["prompts_available"], 
            validation["agents_functional"]
        ])
        
        if validation["system_valid"]:
            print("🎉 Système granulaire entièrement validé!")
        else:
            print("⚠️ Système granulaire partiellement fonctionnel")
        
        return validation
        
    except Exception as e:
        validation["recommendations"].append(f"Erreur validation: {e}")
        return validation


# ✨ CONFIGURATION ET CONSTANTES
RECOMMENDED_MODELS = [
    "mistralai/mistral-nemo:free",
    "microsoft/phi-3-medium-128k-instruct:free", 
    "google/gemma-2-9b-it:free",
    "meta-llama/llama-3.1-8b-instruct:free"
]

GRANULAR_SECTIONS_CATEGORIES = {
    "principales": ["introduction", "analyse", "conclusion"],
    "donnees_entree": ["donnees_entree_intro", "donnees_entree_bathymetrie", "donnees_entree_houle", "donnees_entree_vent"],
    "navires": ["navires", "remorqueurs"],
    "simulations": ["simulations", "scenarios_urgence"],
    "analyse_detaillee": ["analyse_statistiques", "analyse_performance", "analyse_conditions_critiques"]
}


# ✨ EXPORTS FINAUX - Interface granulaire unifiée
__all__ = [
    # Interface principale (remplace tout l'ancien système)
    "generate_ai_sections_for_report",
    "generate_granular_sections_for_report",
    
    # Utilitaires d'entraînement granulaire
    "train_granular_agents",
    "train_agents",
    "add_training_report", 
    "auto_setup",
    "auto_setup_granulaire",
    
    # Migration et compatibilité
    "migrate_to_granular",
    
    # Statut et info granulaire
    "get_training_status",
    "get_detailed_status",
    "is_granular_training_available",
    "check_granular_prompts_integration",
    
    # Validation système
    "validate_granular_system",
    "get_available_granular_sections",
    
    # CLI intégrée
    "run_training_cli",
    "run_granular_training_cli",
    
    # Compatibilité avec l'existant
    "check_agents_availability",
    "get_mock_ai_generator",
    
    # Configuration
    "RECOMMENDED_MODELS",
    "GRANULAR_SECTIONS_CATEGORIES",
    "CACHE_DIR",
    "REPORTS_DIR"
]


# ✨ AUTO-SETUP AU PREMIER IMPORT (granulaire)
def _check_granular_first_run():
    """Vérifie si c'est la première exécution granulaire"""
    
    if not CACHE_DIR.exists() and not REPORTS_DIR.exists():
        print("\n🌊 Premier lancement détecté - Système Granulaire")
        print("💡 Lancez agents.auto_setup_granular() pour configurer le système")
        return True
    
    elif not is_granular_training_available():
        print("\n🔄 Migration granulaire recommandée")
        print("💡 Lancez agents.migrate_to_granular() pour migrer")
        return True
    
    return False


# Vérification discrète au premier import
_check_granular_first_run()
'''
