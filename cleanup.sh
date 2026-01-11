#!/bin/bash
echo "Nettoyage des fichiers temporaires..."

# Compter avant suppression
echo "Fichiers à supprimer :"
find . -name ".DS_Store" | wc -l | xargs echo "- .DS_Store files:"
find . -name "__pycache__" -type d | wc -l | xargs echo "- __pycache__ directories:"
find . -name "*.backup" | wc -l | xargs echo "- .backup files:"

# Suppression
find . \( -name ".DS_Store" -o -name "__pycache__" -o -name "*.backup" \) -exec rm -rf {} +

# Supprimer tous les __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Supprimer les .pyc
find . -name "*.pyc" -delete

# Nettoyer les logs anciens (garder seulement les 5 derniers)
cd logs 2>/dev/null && ls -t *.log 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null

# Nettoyer le cache
rm -rf cache/* 2>/dev/null
# Nettoyer les exports temporaires
find exports/ -name "*.tmp" -delete 2>/dev/null

echo "Nettoyage terminé !"

# À ajouter à la fin de votre script
echo "📊 Espace libéré :"
du -sh cache/ logs/ exports/ 2>/dev/null | head -3
