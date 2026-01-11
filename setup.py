#!/usr/bin/env python3
"""
Script de configuration pour l'application de génération de rapports de manœuvrabilité
"""

import os
import sys
import subprocess
from pathlib import Path

def create_directory_structure():
    """Crée la structure de dossiers nécessaire avec la nouvelle organisation"""
    directories = [
        "uploads",
        "exports", 
        "static",
        "static/templates", 
        "static/samples",
        "logs",
        "prompts"
    ]
    
    print("📁 Création de la structure de dossiers...")
    for directory in directories:
        Path(directory).mkdir(exist_ok=True, parents=True)
        print(f"  ✅ {directory}/")
    
    print()

def migrate_existing_files():
    """Migre les fichiers existants vers la nouvelle structure"""
    print("🔄 Migration des fichiers existants...")
    
    migrations = [
        ("templates/report_template.docx", "static/templates/report_template.docx"),
        ("static/sample_data_complete.json", "static/samples/sample_data_complete.json"),
    ]
    
    migrated_count = 0
    for old_path, new_path in migrations:
        if os.path.exists(old_path):
            # Créer le dossier de destination si nécessaire
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            # Déplacer le fichier
            os.rename(old_path, new_path)
            print(f"  📦 {old_path} → {new_path}")
            migrated_count += 1
    
    # Supprimer l'ancien dossier templates s'il est vide
    if os.path.exists("templates") and not os.listdir("templates"):
        os.rmdir("templates")
        print(f"  🗑️ Ancien dossier templates/ supprimé")
    
    if migrated_count > 0:
        print(f"  ✅ {migrated_count} fichier(s) migré(s)")
    else:
        print("  ℹ️ Aucun fichier à migrer")
    
    print()

def install_requirements():
    """Installe les dépendances"""
    print("📦 Installation des dépendances...")
    
    if not os.path.exists("requirements.txt"):
        print("❌ Fichier requirements.txt non trouvé")
        return False
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("  ✅ Dépendances installées avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Erreur lors de l'installation: {e}")
        return False

def check_template():
    """Vérifie la présence du template Word dans la nouvelle structure"""
    template_path = "static/templates/report_template.docx"
    old_template_path = "templates/report_template.docx"
    
    print("📄 Vérification du template...")
    if os.path.exists(template_path):
        print(f"  ✅ Template trouvé: {template_path}")
        return True
    elif os.path.exists(old_template_path):
        print(f"  🔄 Template trouvé dans l'ancien emplacement: {old_template_path}")
        print("  💡 Exécutez la migration pour le déplacer automatiquement")
        return True
    else:
        print(f"  ⚠️  Template non trouvé: {template_path}")
        print("  💡 Vous devez créer ce fichier pour utiliser l'export Word")
        print("  📍 Nouveau chemin: static/templates/report_template.docx")
        return False

def create_sample_data():
    """Crée des données d'exemple dans la nouvelle structure"""
    print("📋 Création des données d'exemple...")
    
    sample_data = {
        "metadonnees": {
            "titre": "Étude de manœuvrabilité - Port de Tanger",
            "code_projet": "TMD-2024-001",
            "client": "Agence Nationale des Ports",
            "type": "Rapport de manœuvrabilité",
            "numero": "RM-001",
            "annee": "2024"
        },
        "introduction": {
            "guidelines": "Cette étude vise à évaluer la faisabilité des manœuvres portuaires dans le port de Tanger Med.",
            "objectifs": "Déterminer les conditions limites d'exploitation et identifier les mesures d'optimisation."
        }
    }
    
    import json
    # ✅ NOUVEAU CHEMIN
    sample_path = "static/samples/sample_data_complete.json"
    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Données d'exemple créées: {sample_path}")

def check_python_version():
    """Vérifie la version de Python"""
    print("🐍 Vérification de la version Python...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro} (compatible)")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (Python 3.8+ requis)")
        return False

def create_run_script():
    """Crée un script de lancement"""
    print("🚀 Création du script de lancement...")
    
    # Script pour Windows
    bat_content = '''@echo off
echo 🚀 Démarrage de l'application de génération de rapports
echo.
python -m streamlit run main.py --server.port 8501 --server.address 0.0.0.0
pause
'''
    
    with open("run_app.bat", "w") as f:
        f.write(bat_content)
    
    # Script pour Unix/Linux/Mac
    sh_content = '''#!/bin/bash
echo "🚀 Démarrage de l'application de génération de rapports"
echo ""
python -m streamlit run main.py --server.port 8501 --server.address 0.0.0.0
'''
    
    with open("run_app.sh", "w") as f:
        f.write(sh_content)
    
    # Rendre le script exécutable sur Unix
    try:
        os.chmod("run_app.sh", 0o755)
    except:
        pass
    
    print("  ✅ Scripts créés: run_app.bat, run_app.sh")

def create_config_file():
    """Crée un fichier de configuration par défaut avec nouvelle structure"""
    print("⚙️  Création du fichier de configuration...")
    
    config_content = '''# Configuration pour l'application de génération de rapports
# Modifiez ces paramètres selon vos besoins

[DEFAULT]
# Répertoires (nouvelle structure unifiée)
upload_dir = uploads
export_dir = exports
template_dir = static/templates
static_dir = static

# Taille maximale des fichiers (en MB)
max_file_size = 50

# Formats d'images supportés
image_formats = png,jpg,jpeg,gif,bmp,webp

# Formats de documents supportés
document_formats = pdf,docx,doc,xlsx,csv

# Port par défaut pour Streamlit
port = 8501

# Langue par défaut
language = fr

# Thème
theme = light

[EXPORT]
# Qualité des images dans le rapport Word (1-100)
image_quality = 90

# Taille maximale des images en largeur (pixels)
max_image_width = 1200

# Compression des images
compress_images = true

[TEMPLATE]
# Nom du template par défaut
default_template = report_template.docx

# Vérification automatique du template
check_template = true

[STATIC]
# Structure des assets
logos_dir = static/assets/logos
samples_dir = static/samples
word_templates_dir = static/templates

[LOGGING]
# Niveau de logging (DEBUG, INFO, WARNING, ERROR)
log_level = INFO

# Fichier de log
log_file = logs/app.log
'''
    
    with open("config.ini", "w") as f:
        f.write(config_content)
    
    print("  ✅ Configuration créée: config.ini")

def run_initial_test():
    """Exécute un test initial de l'application"""
    print("🧪 Test initial de l'application...")
    
    try:
        # Tester l'import des modules principaux
        from config import Config, get_template_path, get_sample_data_path
        from utils.validation import validate_report
        from forms import MetadataForm
        
        # Tester la configuration
        Config.setup_directories()
        
        # Tester les nouveaux chemins
        template_path = get_template_path()
        sample_path = get_sample_data_path()
        
        print("  ✅ Imports réussis")
        print("  ✅ Configuration OK")
        print(f"  📄 Chemin template: {template_path}")
        print(f"  📊 Chemin données: {sample_path}")
        return True
    except Exception as e:
        print(f"  ❌ Erreur de test: {e}")
        import traceback
        traceback.print_exc()
        return False

def display_next_steps():
    """Affiche les étapes suivantes avec nouvelle structure"""
    print("\n" + "="*60)
    print("🎉 CONFIGURATION TERMINÉE")
    print("="*60)
    print()
    print("📋 Étapes suivantes :")
    print()
    print("1. 📄 Créer le template Word :")
    print("   - Placer 'report_template.docx' dans static/templates/")
    print("   - Templates additionnels dans static/templates")
    print()
    print("2. 🖼️ Ajouter les assets :")
    print("   - Logos dans static/assets/logos/")
    print("   - Ex: static/assets/logos/logo_tme.png")
    print()
    print("3. 🚀 Lancer l'application :")
    print("   - Windows: double-cliquer sur run_app.bat")
    print("   - Unix/Linux/Mac: ./run_app.sh")
    print("   - Ou manuellement: streamlit run main.py")
    print()
    print("4. 🌐 Accéder à l'application :")
    print("   - Ouvrir http://localhost:8501 dans votre navigateur")
    print()
    print("5. 📚 Structure des fichiers :")
    print("   static/")
    print("   ├── templates/        ← Templates Word")
    print("   └── samples/          ← Données d'exemple")
    print()
    print("💡 Conseil : La nouvelle structure unifie tous les assets dans static/")
    print()

def main():
    """Fonction principale de configuration"""
    print("🔧 CONFIGURATION DE L'APPLICATION")
    print("🌊 Générateur de Rapports de Manœuvrabilité")
    print("📁 Structure optimisée et centralisée")
    print("="*60)
    print()
    
    # Vérifications préalables
    if not check_python_version():
        print("\n❌ Version Python incompatible. Veuillez installer Python 3.8+")
        return False
    
    # Configuration avec nouvelle structure
    create_directory_structure()
    migrate_existing_files()  # ✅ NOUVEAU: Migration automatique
    
    if not install_requirements():
        print("\n❌ Échec de l'installation des dépendances")
        return False
    
    create_config_file()
    create_run_script()
    create_sample_data()
    check_template()
    
    # Test initial
    if not run_initial_test():
        print("\n⚠️  Des erreurs ont été détectées lors du test initial")
        print("L'application peut ne pas fonctionner correctement")
    
    display_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuration interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
