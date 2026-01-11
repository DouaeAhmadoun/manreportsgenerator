import sys
import argparse
from pathlib import Path
from typing import Optional

# Import local
try:
    from .training_manager import TrainingManager
    from .pretrained_agents import create_pretrained_manager
except ImportError:
    # Fallback pour exécution directe
    sys.path.append(str(Path(__file__).parent))
    from training_manager import TrainingManager
    from pretrained_agents import create_pretrained_manager


def cmd_train(args):
    """Commande: Entraînement des agents"""
    print("🎓 ENTRAÎNEMENT DES AGENTS")
    print("="*40)
    
    manager = TrainingManager(args.reports_dir)
    
    # Lancer l'entraînement
    result = manager.force_retrain_granular()
    #result = manager.train_offline(force_retrain=args.force)
    
    if result.get("status") == "failed":
        print(f"❌ Entraînement échoué: {result.get('reason', 'Erreur inconnue')}")
        return False
    
    print("\n✅ Entraînement terminé avec succès")
    return True


def cmd_status(args):
    """Commande: Statut du système"""
    print("📊 STATUT DU SYSTÈME")
    print("="*40)
    
    # Statut d'entraînement
    training_manager = TrainingManager(args.reports_dir)
    training_status = training_manager.get_training_status()
    
    print(f"🎓 Entraînement: {training_status['message']}")
    
    if training_status["ready"]:
        metadata = training_status["metadata"]
        print(f"📅 Date: {metadata.get('training_date', 'N/A')}")
        print(f"📚 Total exemples: {metadata.get('total_examples', 0)}")
        
        # Détail par section
        sections = metadata.get("sections", {})
        print(f"\n📋 Sections:")
        for section_name, stats in sections.items():
            count = stats["count"]
            quality = stats["avg_quality"]
            status_icon = "✅" if count > 0 else "❌"
            print(f"  {status_icon} {section_name:15}: {count} exemples (Q: {quality:.2f})")
    
    # Statut des agents
    try:
        agents_manager = create_pretrained_manager()
        agent_status = agents_manager.get_system_status()
        
        print(f"\n🤖 Agents:")
        print(f"Modèle: {agent_status['model']}")
        print(f"Performance: {agent_status['overall_readiness']:.1%}")
        print(f"Recommandation: {agent_status['recommendation']}")
        
    except Exception as e:
        print(f"\n⚠️ Agents: Erreur ({e})")
    
    return True


def cmd_add_report(args):
    """Commande: Ajouter un nouveau rapport"""
    print("📄 AJOUT D'UN NOUVEAU RAPPORT")
    print("="*40)
    
    report_path = Path(args.report_file)
    
    if not report_path.exists():
        print(f"❌ Fichier non trouvé: {report_path}")
        return False
    
    if not report_path.suffix.lower() == '.docx':
        print(f"❌ Le fichier doit être un .docx: {report_path}")
        return False
    
    manager = TrainingManager(args.reports_dir)
    success = manager.add_new_report(str(report_path))
    
    if success:
        print("✅ Rapport ajouté et entraînement mis à jour")
        return True
    else:
        print("❌ Échec de l'ajout du rapport")
        return False


def cmd_test(args):
    """Commande: Test du système"""
    print("🧪 TEST DU SYSTÈME")
    print("="*40)
    
    # Données de test
    test_data = {
        "metadonnees": {
            "titre": "Test - Terminal Conteneurs",
            "client": "Port de Test"
        },
        "introduction": {
            "objectifs": "Évaluer la faisabilité des manœuvres pour les porte-conteneurs"
        },
        "simulations": {
            "simulations": [
                {"id": 1, "navire": "Porte-conteneurs A", "resultat": "Réussite"},
                {"id": 2, "navire": "Porte-conteneurs B", "resultat": "Échec"},
                {"id": 3, "navire": "Porte-conteneurs C", "resultat": "Réussite"}
            ]
        },
        "donnees_navires": {
            "navires": {
                "navires": [
                    {"nom": "Porte-conteneurs A", "type": "Conteneur"},
                    {"nom": "Porte-conteneurs B", "type": "Conteneur"}
                ]
            }
        }
    }
    
    try:
        # Test avec les agents pré-entraînés
        from pretrained_agents import generate_with_pretrained_agents
        
        print("🤖 Test génération avec agents pré-entraînés...")
        results = generate_with_pretrained_agents(test_data, args.model)
        
        if results:
            print(f"\n✅ {len(results)} sections générées:")
            for section_name, content in results.items():
                print(f"  📋 {section_name}: {len(content)} caractères")
                if args.verbose:
                    print(f"     Aperçu: {content[:100]}...")
        else:
            print("⚠️ Aucune section générée")
        
        return bool(results)
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False


def cmd_clean(args):
    """Commande: Nettoyer le cache"""
    print("🧹 NETTOYAGE DU CACHE")
    print("="*40)
    
    cache_dir = Path("agents/training_cache")
    
    if not cache_dir.exists():
        print("ℹ️ Aucun cache à nettoyer")
        return True
    
    try:
        # Supprimer les fichiers de cache
        cache_files = list(cache_dir.glob("*.json"))
        
        if not cache_files:
            print("ℹ️ Cache déjà vide")
            return True
        
        if not args.force:
            response = input(f"❓ Supprimer {len(cache_files)} fichiers de cache? (y/N): ")
            if response.lower() != 'y':
                print("⚠️ Nettoyage annulé")
                return False
        
        for cache_file in cache_files:
            cache_file.unlink()
            print(f"🗑️ Supprimé: {cache_file.name}")
        
        print("✅ Cache nettoyé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur nettoyage: {e}")
        return False


def cmd_info(args):
    """Commande: Informations détaillées"""
    print("ℹ️ INFORMATIONS SYSTÈME")
    print("="*40)
    
    # Configuration
    reports_dir = Path(args.reports_dir)
    cache_dir = Path("agents/training_cache")
    
    print(f"📁 Dossier rapports: {reports_dir}")
    print(f"   Existe: {'✅' if reports_dir.exists() else '❌'}")
    
    if reports_dir.exists():
        docx_files = list(reports_dir.glob("*.docx"))
        pdf_files = list(reports_dir.glob("*.pdf"))
        print(f"   Rapports .docx: {len(docx_files)}")
        print(f"   Rapports .pdf: {len(pdf_files)}")
        total_files = len(docx_files) + len(pdf_files)
        print(f"   Total rapports: {total_files}") 
    
    print(f"\n💾 Dossier cache: {cache_dir}")
    print(f"   Existe: {'✅' if cache_dir.exists() else '❌'}")
    
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*.json"))
        print(f"   Fichiers cache: {len(cache_files)}")
        
        for cache_file in cache_files:
            size_kb = cache_file.stat().st_size / 1024
            print(f"     💾 {cache_file.name} ({size_kb:.1f} KB)")
    
    # Dépendances
    print(f"\n🔧 Dépendances:")
    
    dependencies = [
        ("docx", "Lecture des rapports Word"),
        ("openai", "Client API OpenRouter"),
        ("jinja2", "Templates de prompts"),
        ("requests", "Requêtes HTTP")
    ]
    
    for dep_name, description in dependencies:
        try:
            __import__(dep_name)
            print(f"   ✅ {dep_name}: {description}")
        except ImportError:
            print(f"   ❌ {dep_name}: {description} (MANQUANT)")
    
    # Variables d'environnement
    print(f"\n🔑 Configuration:")
    
    import os
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"   ✅ OPENROUTER_API_KEY: {masked_key}")
    else:
        print(f"   ⚠️ OPENROUTER_API_KEY: Non définie")
    
    return True


def create_parser():
    """Crée le parser d'arguments CLI"""
    
    parser = argparse.ArgumentParser(
        description="🌊 Gestionnaire d'entraînement pour agents IA de manœuvrabilité",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'usage:
  %(prog)s train                    # Entraîner les agents
  %(prog)s train --force           # Forcer le ré-entraînement  
  %(prog)s status                  # Voir le statut
  %(prog)s add rapport.docx        # Ajouter un rapport
  %(prog)s test --verbose          # Tester avec détails
  %(prog)s clean --force           # Nettoyer le cache
        """
    )
    
    # Arguments globaux
    parser.add_argument(
        "--reports-dir", 
        default="examples",
        help="Dossier contenant les rapports d'entraînement (défaut: examples)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Affichage détaillé"
    )
    
    # Sous-commandes
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")
    
    # Commande: train
    parser_train = subparsers.add_parser("train", help="Entraîner les agents")
    parser_train.add_argument(
        "--force", "-f",
        action="store_true", 
        help="Forcer le ré-entraînement même si le cache existe"
    )
    parser_train.set_defaults(func=cmd_train)
    
    # Commande: status
    parser_status = subparsers.add_parser("status", help="Afficher le statut")
    parser_status.set_defaults(func=cmd_status)
    
    # Commande: add
    parser_add = subparsers.add_parser("add", help="Ajouter un nouveau rapport")
    parser_add.add_argument("report_file", help="Chemin vers le fichier .docx à ajouter")
    parser_add.set_defaults(func=cmd_add_report)
    
    # Commande: test  
    parser_test = subparsers.add_parser("test", help="Tester le système")
    parser_test.add_argument(
        "--model", 
        default="mistralai/mistral-nemo:free",
        help="Modèle IA à utiliser pour le test"
    )
    parser_test.set_defaults(func=cmd_test)
    
    # Commande: clean
    parser_clean = subparsers.add_parser("clean", help="Nettoyer le cache")
    parser_clean.add_argument(
        "--force", "-f",
        action="store_true",
        help="Nettoyer sans confirmation"
    )
    parser_clean.set_defaults(func=cmd_clean)
    
    # Commande: info
    parser_info = subparsers.add_parser("info", help="Informations détaillées")
    parser_info.set_defaults(func=cmd_info)
    
    return parser


def setup_directories():
    """Crée les dossiers nécessaires s'ils n'existent pas"""
    
    directories = [
        "examples",
        "agents", 
        "agents/training_cache"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def main():
    """Point d'entrée principal"""
    
    # Créer les dossiers nécessaires
    setup_directories()
    
    # Parser les arguments
    parser = create_parser()
    args = parser.parse_args()
    
    # Si aucune commande, afficher l'aide
    if not args.command:
        parser.print_help()
        return 0
    
    # Exécuter la commande
    try:
        success = args.func(args)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrompu par l'utilisateur")
        return 1
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def quick_setup():
    """Setup rapide interactif"""
    
    print("🚀 SETUP RAPIDE DES AGENTS IA")
    print("="*40)
    
    # Vérifier les dossiers
    reports_dir = Path("examples")
    
    if not reports_dir.exists():
        print("📁 Création du dossier examples/")
        reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Vérifier les rapports
    docx_files = list(reports_dir.glob("*.docx"))
    
    if not docx_files:
        print(f"📄 Aucun rapport trouvé dans {reports_dir}/")
        print("💡 Ajoutez vos rapports .docx dans ce dossier puis relancez")
        
        choice = input("❓ Continuer quand même? (y/N): ")
        if choice.lower() != 'y':
            print("⚠️ Setup annulé")
            return False
    else:
        print(f"✅ {len(docx_files)} rapports trouvés")
    
    # Lancer l'entraînement
    print("\n🎓 Lancement de l'entraînement...")
    
    try:
        manager = TrainingManager()
        result = manager.force_retrain_granular()
        #result = manager.train_offline()
        
        if result.get("status") != "failed":
            print("\n✅ Setup terminé avec succès!")
            print("💡 Utilisez 'python -m agents.training_cli status' pour voir le résultat")
            return True
        else:
            print(f"\n❌ Setup échoué: {result.get('reason', 'Erreur')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur setup: {e}")
        return False


if __name__ == "__main__":
    # Si exécuté directement, proposer le setup rapide
    if len(sys.argv) == 1:
        print("🌊 Générateur de Rapports de Manœuvrabilité")
        print("CLI d'entraînement des agents IA")
        print()
        
        choice = input("❓ Lancer le setup rapide? (Y/n): ")
        if choice.lower() in ['', 'y', 'yes']:
            success = quick_setup()
            sys.exit(0 if success else 1)
        else:
            print("💡 Utilisez --help pour voir les commandes disponibles")
            sys.exit(0)
    
    # Sinon, traitement normal des arguments
    sys.exit(main())
