# =============================================================================
# word_export/__init__.py - Point d'entrée du package d'export Word
# =============================================================================

"""
Package d'export Word pour rapports de manœuvrabilité
Version finale et optimisée
"""

from .export_manager import export_word_ui, WordExportManager
from .context_builder import ContextBuilder
from .image_processor import ImageProcessor
from .word_utils import WordUtils
from agents.ai_generator import AIGenerator

# Exports principaux
__all__ = [
    "export_word_ui",           # Fonction principale pour main.py
    "WordExportManager",        # Gestionnaire principal
    "ContextBuilder",          # Construction du contexte
    "ImageProcessor",          # Traitement des images
    "WordUtils",               # Utilitaires Word
    "AIGenerator"              # Génération IA
]
