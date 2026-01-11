import streamlit as st
import json
import os
import re
from io import BytesIO
from typing import Any, List
from datetime import datetime
from pathlib import Path
from config import Config


class FileManager:
    """Gestionnaire de fichiers pour l'application"""
    
    @staticmethod
    def save_uploaded_file(uploaded_file) -> str:
        """Sauvegarde un fichier uploadé et retourne le chemin"""
        if uploaded_file is None:
            return ""
        
        from config import get_upload_path
        Config.setup_directories()
        file_path = get_upload_path(uploaded_file.name)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return str(file_path)
    
    @staticmethod
    def create_safe_filename(filename: str) -> str:
        """Crée un nom de fichier sûr en supprimant les caractères dangereux"""
        # Supprimer les caractères dangereux
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limiter la longueur
        if len(safe_filename) > 100:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:100-len(ext)] + ext
        
        return safe_filename
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Formate la taille d'un fichier en bytes vers un format lisible"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    @staticmethod
    def validate_file_type(file_path: str, allowed_types: List[str]) -> bool:
        """Valide le type d'un fichier selon son extension"""
        if not file_path or not os.path.exists(file_path):
            return False
        
        file_ext = Path(file_path).suffix.lower()
        normalized_types = [f".{ext}" if not ext.startswith('.') else ext for ext in allowed_types]
        
        return file_ext in normalized_types


class DataCleaner:
    """Nettoyeur de données pour l'export et la validation"""
    
    @staticmethod
    def clean_data_for_export(data: dict) -> dict:
        """Nettoie les données pour l'export en supprimant les éléments non sérialisables"""
        def clean_recursive(obj):
            if isinstance(obj, dict):
                cleaned = {}
                for k, v in obj.items():
                    # Ignorer les objets InlineImage et autres non-sérialisables
                    if k.endswith('_inline') or k.endswith('_exists'):
                        continue
                    cleaned[k] = clean_recursive(v)
                return cleaned
            elif isinstance(obj, list):
                return [clean_recursive(item) for item in obj]
            else:
                # Vérifier si l'objet est sérialisable
                try:
                    json.dumps(obj)
                    return obj
                except (TypeError, ValueError):
                    return str(obj) if obj is not None else None
        
        return clean_recursive(data)
    
    @staticmethod
    def prepare_report_for_export(data: dict) -> dict:
        """Prépare les données du rapport avec des métadonnées pour la génération"""
        # Ajouter les métadonnées de génération
        data["_metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "version": "2.0",
            "format": "manoeuvrability_report"
        }
        
        # Ajouter l'ordre des sections pour la génération du rapport
        data["_structure"] = {
            "sections": [
                "metadonnees",
                "introduction", 
                "donnees_entree",
                "donnees_navires",
                "simulations",
                "analyse_synthese",
                "conclusion",
                "annexes"
            ]
        }
        
        # Assurer une structure de données cohérente
        if "simulations" in data and isinstance(data["simulations"], dict):
            if "simulations" not in data["simulations"]:
                data["simulations"]["simulations"] = []
        
        return data


class ReportSummaryGenerator:
    """Générateur de résumés de rapports"""
    
    @staticmethod
    def get_report_summary(data: dict) -> dict:
        """Extrait les métriques clés des données du rapport"""
        summary = {}
        
        # Informations de base
        metadata = data.get("metadonnees", {})
        summary["titre"] = metadata.get("titre", "")
        summary["client"] = metadata.get("client", "")
        summary["code_projet"] = metadata.get("code_projet", "")
        
        # Comptages
        navires_data = data.get("donnees_navires", {})
        navires = navires_data.get("navires", {}).get("navires", [])
        summary["nb_navires"] = len(navires)
        
        remorqueurs = navires_data.get("remorqueurs", {}).get("remorqueurs", [])
        summary["nb_remorqueurs"] = len(remorqueurs)
        
        simulations_data = data.get("simulations", {})
        simulations = simulations_data.get("simulations", [])
        summary["nb_simulations"] = len(simulations)
        
        # Taux de réussite
        if simulations:
            reussites = sum(1 for sim in simulations if sim.get("resultat") == "Réussite")
            summary["taux_reussite"] = reussites / len(simulations)
        else:
            summary["taux_reussite"] = 0
        
        return summary
    
    @staticmethod
    def get_annexes_summary(annexes_data: Any) -> str:
        """Retourne un résumé des annexes pour l'affichage"""
        if not annexes_data:
            return "Aucune annexe"
        
        if isinstance(annexes_data, list):
            return f"Liste: {len(annexes_data)} éléments"
        
        if isinstance(annexes_data, dict):
            annexes_type = annexes_data.get("type", "manual")
            
            if annexes_type == "automatic":
                annexes_content = annexes_data.get("annexes", {})
                if isinstance(annexes_content, dict):
                    tableau = annexes_content.get("tableau_complet", {})
                    essais = annexes_content.get("essais_detailles", [])
                    nb_simulations = len(tableau.get("simulations", []))
                    nb_essais = len(essais)
                    return f"Automatique: {nb_simulations} simulations, {nb_essais} essais détaillés"
                return "Automatique: structure invalide"
            
            elif annexes_type == "manual":
                organized = annexes_data.get("organized_files", {})
                nb_figures = len(organized.get("figures", []))
                nb_tableaux = len(organized.get("tableaux", []))
                return f"Manuel: {nb_figures} figures, {nb_tableaux} tableaux"
            
            elif annexes_type == "zip":
                total_files = annexes_data.get("total_files", 0)
                return f"ZIP: {total_files} fichiers"
        
        return "Type d'annexe non reconnu"
    
    @staticmethod
    def prepare_annexes_for_export(annexes_data: Any) -> dict:
        """Prépare les annexes pour l'export Word"""
        if not annexes_data:
            return {"type": "none"}
        
        if isinstance(annexes_data, list):
            return {
                "type": "list",
                "elements": annexes_data
            }
        
        if isinstance(annexes_data, dict):
            annexes_type = annexes_data.get("type", "manual")
            
            if annexes_type == "automatic":
                annexes_content = annexes_data.get("annexes", {})
                return {
                    "type": "automatic",
                    "tableau_complet": annexes_content.get("tableau_complet", {}),
                    "essais_detailles": annexes_content.get("essais_detailles", []),
                    "stats": annexes_data.get("stats", {})
                }
            
            elif annexes_type == "zip":
                organized = annexes_data.get("organized_files", {})
                return {
                    "type": "zip",
                    "source_zip": annexes_data.get("zip_file", ""),
                    "total_files": annexes_data.get("total_files", 0),
                    "commentaire": annexes_data.get("commentaire", ""),
                    "figures": organized.get("figures", []),
                    "tableaux": organized.get("tableaux", []),
                    "documents": organized.get("documents", []),
                    "autres": organized.get("autres", [])
                }
            
            else:
                # Pour le manuel, garder la structure existante
                return annexes_data
        
        return {"type": "unknown", "data": annexes_data}


class DownloadManager:
    """Gestionnaire de téléchargements"""
    
    @staticmethod
    def create_json_download(data: dict) -> BytesIO:
        """Crée un téléchargement JSON"""
        buffer = BytesIO()
        json_string = json.dumps(data, indent=2, ensure_ascii=False)
        buffer.write(json_string.encode('utf-8'))
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_filename(base_name: str, extension: str = "", timestamp: bool = True) -> str:
        """Génère un nom de fichier sécurisé"""
        # Nettoyer le nom de base
        safe_base = FileManager.create_safe_filename(base_name)
        
        # Ajouter le timestamp si demandé
        if timestamp:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_base = f"{safe_base}_{ts}"
        
        # Ajouter l'extension
        if extension and not extension.startswith('.'):
            extension = f".{extension}"
        
        return f"{safe_base}{extension}"


class FileUploadHandler:
    """Gestionnaire d'upload de fichiers avec légendes"""
    
    @staticmethod
    def handle_file_upload_with_legend(label: str, file_types: List[str], key: str) -> List[dict]:
        """Gère l'upload de fichiers avec légendes"""
        uploaded_files = st.file_uploader(
            label, 
            type=file_types, 
            accept_multiple_files=True, 
            key=key
        )
        
        figures = []
        for i, file in enumerate(uploaded_files or []):
            path = FileManager.save_uploaded_file(file)
            legend = st.text_input(
                f"Légende pour {file.name}", 
                key=f"{key}_legend_{i}"
            )
            
            # Afficher l'aperçu si c'est une image
            if path and os.path.exists(path) and FileManager.validate_file_type(path, ['png', 'jpg', 'jpeg', 'gif']):
                st.image(path, caption=legend, width=200)
            
            figures.append({
                "chemin": path,
                "legende": legend,
                "nom_fichier": file.name,
                "taille": len(file.getvalue())
            })
        
        return figures


class SimulationSorter:
    """Trieur de simulations"""
    
    @staticmethod
    def sort_all_simulations(simulations: List[dict]) -> List[dict]:
        """Trie toutes les simulations par numéro d'essai"""
        if not simulations:
            return []
        
        def extract_sort_key(numero_essai):
            """Extrait une clé de tri depuis le numéro d'essai"""
            if not numero_essai:
                return (9999, 0)
            
            # Extraire le numéro principal
            match = re.match(r'^(\d+)', str(numero_essai))
            if match:
                num = int(match.group(1))
                
                # Gérer bis, ter, etc.
                numero_str = str(numero_essai).lower()
                if 'bis' in numero_str:
                    suffixe = 1
                elif 'ter' in numero_str:
                    suffixe = 2
                elif 'quater' in numero_str:
                    suffixe = 3
                else:
                    suffixe = 0
                
                return (num, suffixe)
            else:
                try:
                    return (int(float(str(numero_essai))), 0)
                except:
                    return (9999, 0)
        
        # Trier et retourner
        sorted_sims = sorted(
            simulations, 
            key=lambda s: extract_sort_key(s.get("numero_essai_original", ""))
        )
        
        return sorted_sims


class DateFormatter:
    """Formateur de dates"""
    
    @staticmethod
    def format_date(date_str) -> str:
        """Formate une date pour l'affichage"""
        if not date_str:
            return ""
        
        try:
            # Si c'est déjà une string de date formatée
            if isinstance(date_str, str) and len(date_str) == 10:
                return date_str
            
            # Sinon essayer de parser et reformater
            if isinstance(date_str, str):
                dt = datetime.fromisoformat(date_str)
            else:
                dt = datetime(date_str) if hasattr(date_str, 'year') else datetime.now()
            
            return dt.strftime("%d/%m/%Y")
        except:
            return str(date_str)


# Classes pour la compatibilité avec l'ancien code
class LegacyUtils:
    """Fonctions de compatibilité avec l'ancien utils.py"""
    
    @staticmethod
    def is_filled(value: Any) -> bool:
        """Vérifie si une valeur n'est pas vide"""
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ""
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return bool(value)


# Fonctions utilitaires pour la compatibilité
def save_uploaded_file(uploaded_file) -> str:
    """Fonction de compatibilité"""
    return FileManager.save_uploaded_file(uploaded_file)


def clean_data_for_export(data: dict) -> dict:
    """Fonction de compatibilité"""
    return DataCleaner.clean_data_for_export(data)


def prepare_report_for_export(data: dict) -> dict:
    """Fonction de compatibilité"""
    return DataCleaner.prepare_report_for_export(data)


def get_report_summary(data: dict) -> dict:
    """Fonction de compatibilité"""
    return ReportSummaryGenerator.get_report_summary(data)


def get_annexes_summary(annexes_data: Any) -> str:
    """Fonction de compatibilité"""
    return ReportSummaryGenerator.get_annexes_summary(annexes_data)


def prepare_annexes_for_export(annexes_data: Any) -> dict:
    """Fonction de compatibilité"""
    return ReportSummaryGenerator.prepare_annexes_for_export(annexes_data)


def create_json_download(data: dict) -> BytesIO:
    """Fonction de compatibilité"""
    return DownloadManager.create_json_download(data)


def handle_file_upload_with_legend(label: str, file_types: List[str], key: str) -> List[dict]:
    """Fonction de compatibilité"""
    return FileUploadHandler.handle_file_upload_with_legend(label, file_types, key)


def sort_all_simulations(simulations: List[dict]) -> List[dict]:
    """Fonction de compatibilité"""
    return SimulationSorter.sort_all_simulations(simulations)


def format_date(date_str) -> str:
    """Fonction de compatibilité"""
    return DateFormatter.format_date(date_str)


def format_file_size(size_bytes: int) -> str:
    """Fonction de compatibilité"""
    return FileManager.format_file_size(size_bytes)


def validate_file_type(file_path: str, allowed_types: List[str]) -> bool:
    """Fonction de compatibilité"""
    return FileManager.validate_file_type(file_path, allowed_types)


def create_safe_filename(filename: str) -> str:
    """Fonction de compatibilité"""
    return FileManager.create_safe_filename(filename)


def is_filled(value: Any) -> bool:
    """Fonction de compatibilité"""
    return LegacyUtils.is_filled(value)
