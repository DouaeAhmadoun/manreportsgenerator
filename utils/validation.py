# =============================================================================
# validation.py - Utilitaires de validation ENRICHIS
# Ajout des validateurs Excel extraits de excel.py
# =============================================================================

import streamlit as st
import os
import re
import pandas as pd
from typing import Any, Dict, List, Union
from config import (
    Config, 
    validate_image_format, 
    validate_file_size
)


class ExcelContentValidators:
    """Validateurs de contenu pour colonnes Excel"""
    
    @staticmethod
    def validate_numero_essai(series) -> bool:
        """Valide que la série contient des numéros d'essai"""
        sample = series.dropna().astype(str).head(10)
        if len(sample) == 0:
            return False
        
        valid_count = 0
        for value in sample:
            value_clean = str(value).strip()
            # Patterns pour numéros d'essai
            if re.match(r'^\d+[a-z]*$|^[a-z]\d+$|^\d+[-_\.]\d*$', value_clean.lower()):
                valid_count += 1
        
        return valid_count >= len(sample) * 0.7  # 70% doivent être valides
    
    @staticmethod
    def validate_vent(series) -> bool:
        """Valide que la série contient des données de vent"""
        sample = series.dropna().astype(str).head(10)
        if len(sample) == 0:
            return False
        
        valid_count = 0
        for value in sample:
            value_str = str(value).lower()
            # Chercher des indicateurs de vent
            if any(pattern in value_str for pattern in ['kt', 'nds', 'wind', 'calme', 'nul', 'mph']) or \
               re.search(r'\d+\s*[nsew]', value_str) or \
               re.search(r'[nsew]{1,3}\s*\d+', value_str):
                valid_count += 1
        
        return valid_count >= len(sample) * 0.4
    
    @staticmethod
    def validate_houle(series) -> bool:
        """Valide que la série contient des données de houle"""
        sample = series.dropna().astype(str).head(10)
        if len(sample) == 0:
            return False
        
        valid_count = 0
        for value in sample:
            value_str = str(value).lower()
            # Chercher des indicateurs de houle
            if 'm' in value_str or 's' in value_str or 'wave' in value_str or \
               re.search(r'\d+[.,]\d*', value_str) or \
               any(word in value_str for word in ['houle', 'swell', 'period']):
                valid_count += 1
        
        return valid_count >= len(sample) * 0.4
    
    @staticmethod
    def validate_courant(series) -> bool:
        """Valide que la série contient des données de courant"""
        sample = series.dropna().astype(str).head(10)
        if len(sample) == 0:
            return False
        
        valid_count = 0
        for value in sample:
            value_str = str(value).lower()
            # Chercher des indicateurs de courant
            if any(pattern in value_str for pattern in ['kt', 'current', 'nul', 'flow', 'drift']) or \
               re.search(r'\d+[.,]?\d*\s*(kt|nds)', value_str) or \
               re.search(r'[nsew]{1,3}\s*\d+', value_str):
                valid_count += 1
        
        return valid_count >= len(sample) * 0.4
    
    @staticmethod
    def validate_maree(series) -> bool:
        """Valide que la série contient des données de marée"""
        sample = series.dropna().astype(str).head(10)
        if len(sample) == 0:
            return False
        
        valid_count = 0
        for value in sample:
            value_str = str(value).lower()
            # Chercher des indicateurs de marée
            if any(pattern in value_str for pattern in ['m', '+', '-', 'pm', 'bm', 'tide', 'level']) or \
               re.search(r'[+\-]?\d+[.,]\d*', value_str):
                valid_count += 1
        
        return valid_count >= len(sample) * 0.4
    
    @staticmethod
    def validate_commentaire(series) -> bool:
        """Valide que la série contient vraiment des commentaires"""
        sample = series.dropna().astype(str).head(10)
        if len(sample) == 0:
            return False
        
        # Les commentaires sont généralement longs
        long_text_count = sum(1 for text in sample if len(str(text)) > 15)
        
        # Les commentaires contiennent du vocabulaire du domaine
        domain_keywords = ["manœuvre", "manoeuvre", "simulation", "pilote", "remorqueur", 
                          "navire", "accostage", "réussi", "échec", "difficulté"]
        
        domain_matches = 0
        for text in sample:
            text_lower = str(text).lower()
            if any(keyword in text_lower for keyword in domain_keywords):
                domain_matches += 1
        
        # Au moins 60% de textes longs OU 20% avec vocabulaire du domaine
        return (long_text_count >= len(sample) * 0.6) or (domain_matches >= len(sample) * 0.2)
    
    @staticmethod
    def validate_navire(series) -> bool:
        """Valide que la série contient vraiment des noms de navires"""
        sample = series.dropna().astype(str).head(10)
        if len(sample) == 0:
            return False
        
        # Les noms de navires ne sont PAS des conditions météo
        weather_keywords = ["wind", "wave", "current", "tide", "vent", "houle", "courant", "marée"]
        weather_matches = sum(1 for text in sample 
                            if any(keyword in str(text).lower() for keyword in weather_keywords))
        
        # Les noms de navires ne sont PAS des valeurs numériques simples
        numeric_pattern = re.compile(r'^\d+[.,]?\d*\s*(m|kt|s|°)?$')
        numeric_matches = sum(1 for text in sample if numeric_pattern.match(str(text).strip()))
        
        # Rejeter si trop de valeurs météo ou numériques
        total_invalid = weather_matches + numeric_matches
        return total_invalid < len(sample) * 0.5
    
    @staticmethod
    def validate_resultat(series) -> bool:
        """Valide que la série contient des résultats"""
        sample = series.dropna().astype(str).head(10)
        if len(sample) == 0:
            return False
        
        valid_count = 0
        for value in sample:
            value_str = str(value).lower().strip()
            if value_str in ['0', '1', 'pass', 'fail', 'ok', 'nok'] or \
               any(word in value_str for word in ['success', 'fail', 'réussi', 'échec']):
                valid_count += 1
        
        return valid_count >= len(sample) * 0.6
    
    @staticmethod
    def validate_date(series) -> bool:
        """Valide que la série contient des dates"""
        sample = series.dropna().astype(str).head(10)
        if len(sample) == 0:
            return False
        
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}/\d{1,2}/\d{4}'
        ]
        
        valid_count = 0
        for value in sample:
            if any(re.search(pattern, str(value)) for pattern in date_patterns):
                valid_count += 1
        
        return valid_count >= len(sample) * 0.6
    
    @staticmethod
    def validate_heure(series) -> bool:
        """Valide que la série contient des heures"""
        sample = series.dropna().astype(str).head(10)
        if len(sample) == 0:
            return False
        
        time_patterns = [
            r'\d{1,2}:\d{2}',
            r'\d{1,2}h\d{2}',
            r'\d+\s*(min|h)'
        ]
        
        valid_count = 0
        for value in sample:
            if any(re.search(pattern, str(value).lower()) for pattern in time_patterns):
                valid_count += 1
        
        return valid_count >= len(sample) * 0.6
    
    @classmethod
    def get_validator_for_field(cls, field_type: str):
        """Retourne le validateur approprié pour un type de champ"""
        validators_map = {
            "numero_essai": cls.validate_numero_essai,
            "vent": cls.validate_vent,
            "houle": cls.validate_houle,
            "courant": cls.validate_courant,
            "maree": cls.validate_maree,
            "commentaire": cls.validate_commentaire,
            "navire": cls.validate_navire,
            "resultat": cls.validate_resultat,
            "date_simulation": cls.validate_date,
            "heure_simulation": cls.validate_heure,
        }
        
        return validators_map.get(field_type)
    
    @classmethod
    def validate_field_content(cls, series, field_type: str) -> bool:
        """Méthode unifiée pour valider le contenu d'un champ"""
        validator = cls.get_validator_for_field(field_type)
        if validator:
            try:
                return validator(series)
            except Exception:
                return False
        return False


class ExcelMappingValidators:
    """Validateurs pour le mapping des colonnes Excel"""
    
    @staticmethod
    def validate_final_mapping(df, mapped_columns: Dict[str, str]) -> List[str]:
        """Valide le mapping final avant traitement"""
        errors = []
        
        # Vérifier que toutes les colonnes mappées existent
        for field, excel_col in mapped_columns.items():
            if excel_col not in df.columns:
                errors.append(f"Colonne '{excel_col}' mappée pour '{field}' introuvable")
        
        # Vérifier les champs obligatoires
        required_fields = ["numero_essai"]
        for field in required_fields:
            if field not in mapped_columns:
                errors.append(f"Champ obligatoire '{field}' non mappé")
        
        # Vérifier les doublons
        used_columns = list(mapped_columns.values())
        duplicates = [col for col in used_columns if used_columns.count(col) > 1]
        if duplicates:
            errors.append(f"Colonnes utilisées plusieurs fois : {', '.join(set(duplicates))}")
        
        return errors
    
    @staticmethod
    def validate_field_name(field_name: str) -> bool:
        """Valide le nom d'un champ personnalisé"""
        if not field_name:
            return False
        
        # Doit être un identifiant Python valide
        if not re.match(r'^[a-z][a-z0-9_]*$', field_name):
            return False
        
        # Ne doit pas être un mot-clé Python
        python_keywords = {
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del',
            'elif', 'else', 'except', 'exec', 'finally', 'for', 'from', 'global',
            'if', 'import', 'in', 'is', 'lambda', 'not', 'or', 'pass', 'print',
            'raise', 'return', 'try', 'while', 'with', 'yield'
        }
        
        if field_name in python_keywords:
            return False
        
        # Ne doit pas être trop long
        if len(field_name) > 50:
            return False
        
        return True
    
    @staticmethod
    def validate_mapping_candidate(field_name: str, excel_col: str, score: float) -> bool:
        """Valide qu'un candidat de mapping est logique"""
        
        def normalize_text(text: str) -> str:
            """Normalise un texte pour la comparaison"""
            if not text:
                return ""
            
            normalized = str(text).lower()
            
            # Remplacements spécifiques pour les accents
            replacements = {
                'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
                'à': 'a', 'á': 'a', 'â': 'a', 'ä': 'a',
                'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
                'ò': 'o', 'ó': 'o', 'ô': 'o', 'ö': 'o',
                'ç': 'c', 'ñ': 'n', 'œ': 'oe', 'æ': 'ae'
            }
            
            for accented, normal in replacements.items():
                normalized = normalized.replace(accented, normal)
            
            # Supprimer caractères non alphanumériques
            normalized = re.sub(r'[^a-z0-9]', '', normalized)
            return normalized
        
        # Normaliser les noms pour comparaison
        col_normalized = normalize_text(excel_col)
        
        # RÈGLES D'EXCLUSION STRICTES
        
        # 1. "Current" ne peut pas être "commentaire"
        if field_name == "commentaire" and "current" in col_normalized:
            return False
        
        # 2. "Comments" ne peut pas être "courant"  
        if field_name == "courant" and "comment" in col_normalized:
            return False
        
        # 3. "Condition" ne peut pas être "navire"
        if field_name == "navire" and "condition" in col_normalized:
            return False
        
        # 4. Validation par longueur de nom (anti-confusion)
        if field_name == "commentaire":
            # Les commentaires doivent venir de colonnes avec "comment" dans le nom
            if "comment" not in col_normalized and score > 0.8:
                return False
        
        # 5. Validation sémantique stricte pour les champs critiques
        critical_fields = {
            "numero_essai": ["test", "essai", "trial", "num", "id"],
            "courant": ["current", "courant", "drift"],
            "commentaire": ["comment", "observation", "note", "remark"],
            "vent": ["wind", "vent"],
            "houle": ["wave", "houle", "swell"]
        }
        
        if field_name in critical_fields:
            required_keywords = critical_fields[field_name]
            has_keyword = any(keyword in col_normalized for keyword in required_keywords)
            
            # Si score très élevé mais pas de mot-clé => suspect
            if score > 0.9 and not has_keyword:
                return False
        
        return True


class ExcelDataValidators:
    """Validateurs pour les données extraites d'Excel"""
    
    @staticmethod
    def validate_simulation_data(simulation_data: Dict[str, Any]) -> List[str]:
        """Valide les données d'une simulation"""
        errors = []
        
        # Vérifier les champs obligatoires
        required_fields = ["id", "numero_essai_original"]
        for field in required_fields:
            if field not in simulation_data or not simulation_data[field]:
                errors.append(f"Champ obligatoire manquant : {field}")
        
        # Valider le numéro d'essai
        if "numero_essai_original" in simulation_data:
            numero = simulation_data["numero_essai_original"]
            if not numero or not str(numero).strip():
                errors.append("Numéro d'essai vide ou invalide")
        
        # Valider le résultat
        if "resultat" in simulation_data:
            resultat = simulation_data["resultat"]
            valid_results = ["Réussite", "Échec", "Non défini"]
            if resultat not in valid_results:
                errors.append(f"Résultat invalide : {resultat}. Doit être : {', '.join(valid_results)}")
        
        return errors
    
    @staticmethod
    def validate_extracted_simulations(simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Valide une liste de simulations extraites"""
        validation_result = {
            "valid_count": 0,
            "invalid_count": 0,
            "errors": [],
            "warnings": []
        }
        
        if not simulations:
            validation_result["errors"].append("Aucune simulation extraite")
            return validation_result
        
        for i, sim in enumerate(simulations):
            sim_errors = ExcelDataValidators.validate_simulation_data(sim)
            if sim_errors:
                validation_result["invalid_count"] += 1
                for error in sim_errors:
                    validation_result["errors"].append(f"Simulation {i+1}: {error}")
            else:
                validation_result["valid_count"] += 1
        
        # Avertissements généraux
        if validation_result["invalid_count"] > 0:
            validation_result["warnings"].append(
                f"{validation_result['invalid_count']} simulation(s) avec erreurs sur {len(simulations)} total"
            )
        
        return validation_result


# =============================================================================
# FONCTIONS UTILITAIRES EXCEL AJOUTÉES
# =============================================================================

def test_content_validation(series, validator_func) -> bool:
    """Teste la validation du contenu de manière sécurisée"""
    try:
        return validator_func(series)
    except Exception:
        # En cas d'erreur, retourner False mais ne pas faire planter
        return False


def normalize_field_name(field_name: str) -> str:
    """Normalise un nom de champ pour la validation"""
    if not field_name:
        return ""
    
    # Nettoyer et normaliser
    normalized = field_name.lower().strip()
    
    # Remplacer les caractères spéciaux par des underscores
    normalized = re.sub(r'[^a-z0-9]', '_', normalized)
    
    # Supprimer les underscores multiples
    normalized = re.sub(r'_+', '_', normalized)
    
    # Supprimer les underscores en début/fin
    normalized = normalized.strip('_')
    
    # Traductions courantes
    translations = {
        'entrance': 'entree',
        'entry': 'entree',
        'exit': 'sortie',
        'departure': 'sortie',
        'captain': 'capitaine',
        'company': 'compagnie',
        'visibility': 'visibilite',
        'duration': 'duree',
        'speed': 'vitesse',
        'distance': 'distance',
        'time': 'heure',
        'date': 'date',
        'note': 'note',
        'grade': 'note',
        'rating': 'evaluation'
    }
    
    # Appliquer les traductions
    for eng, fr in translations.items():
        if eng in normalized:
            normalized = normalized.replace(eng, fr)
    
    # S'assurer qu'on a au moins quelque chose
    if not normalized:
        normalized = "champ_inconnu"
    
    return normalized


# =============================================================================
# CLASSES EXISTANTES - CONSERVÉES
# =============================================================================

class ReportValidator:
    """Validateur principal pour les rapports de manœuvrabilité"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_report(self, data: dict) -> bool:
        """Valide si le rapport contient tous les champs requis"""
        self._reset_validation()
        
        # Validation des sections principales
        self._validate_metadata(data.get("metadonnees", {}))
        self._validate_introduction(data.get("introduction", {}))
        self._validate_ships(data.get("donnees_navires", {}))
        self._validate_simulations(data.get("simulations", {}))
        self._validate_conclusion(data.get("conclusion", ""))
        self._validate_annexes(data.get("annexes", {}))
        
        # Afficher les erreurs
        self._display_validation_results()
        
        return len(self.errors) == 0
    
    def _reset_validation(self):
        """Remet à zéro les listes d'erreurs et avertissements"""
        self.errors = []
        self.warnings = []
    
    def _validate_metadata(self, metadata: dict):
        """Valide les métadonnées obligatoires"""
        for field in Config.REQUIRED_FIELDS:
            if not self._is_filled(metadata.get(field)):
                self.errors.append(f"Champ requis manquant : {field}")
        
        # Validation des révisions
        revisions = metadata.get("historique_revisions", [])
        if not revisions:
            self.warnings.append("Aucune révision définie")
        else:
            for i, rev in enumerate(revisions):
                if not rev.get("version"):
                    self.warnings.append(f"Version manquante pour la révision {i+1}")
    
    def _validate_introduction(self, introduction: dict):
        """Valide l'introduction"""
        if not self._is_filled(introduction.get("guidelines")):
            self.errors.append("Champ requis manquant : éléments à inclure dans l'introduction")
        
        if not self._is_filled(introduction.get("objectifs")):
            self.errors.append("Champ requis manquant : objectifs de l'étude")
        
        # Vérifier la longueur minimale
        guidelines = introduction.get("guidelines", "")
        if len(guidelines.strip()) < 50:
            self.warnings.append("Introduction très courte (< 50 caractères)")
    
    def _validate_ships(self, navires_data: dict):
        """Valide les données des navires"""
        navires = navires_data.get("navires", {}).get("navires", [])
        
        if not navires:
            self.errors.append("Au moins un navire doit être défini")
            return
        
        # Validation de chaque navire
        for i, navire in enumerate(navires):
            self._validate_single_ship(navire, i+1)
        
        # Validation des remorqueurs
        remorqueurs = navires_data.get("remorqueurs", {}).get("remorqueurs", [])
        if not remorqueurs:
            self.warnings.append("Aucun remorqueur défini")
    
    def _validate_single_ship(self, navire: dict, index: int):
        """Valide un navire individuel"""
        required_ship_fields = ["nom", "type", "longueur", "largeur"]
        
        for field in required_ship_fields:
            if not navire.get(field):
                self.warnings.append(f"Navire {index}: {field} manquant")
        
        # Validation des dimensions
        longueur = navire.get("longueur", 0)
        largeur = navire.get("largeur", 0)
        
        if longueur <= 0:
            self.warnings.append(f"Navire {index}: longueur invalide")
        if largeur <= 0:
            self.warnings.append(f"Navire {index}: largeur invalide")
        if longueur > 0 and largeur > 0 and longueur < largeur:
            self.warnings.append(f"Navire {index}: longueur < largeur (suspect)")
    
    def _validate_simulations(self, simulations_data: dict):
        """Valide les données de simulation"""
        simulations = simulations_data.get("simulations", [])
        
        if not simulations:
            self.errors.append("Au moins une simulation doit être définie")
            return
        
        # Statistiques des simulations
        total = len(simulations)
        avec_resultat = sum(1 for s in simulations if s.get("resultat") != "Non défini")
        reussites = sum(1 for s in simulations if s.get("resultat") == "Réussite")
        
        if avec_resultat == 0:
            self.warnings.append("Aucune simulation n'a de résultat défini")
        elif avec_resultat < total:
            self.warnings.append(f"{total - avec_resultat} simulations sans résultat")
        
        # Vérifier les champs essentiels
        sans_navire = sum(1 for s in simulations if not s.get("navire"))
        sans_commentaire = sum(1 for s in simulations if not s.get("commentaire_pilote"))
        
        if sans_navire > 0:
            self.warnings.append(f"{sans_navire} simulations sans navire spécifié")
        if sans_commentaire > 0:
            self.warnings.append(f"{sans_commentaire} simulations sans commentaire")
    
    def _validate_conclusion(self, conclusion: str):
        """Valide la conclusion"""
        if not self._is_filled(conclusion):
            self.errors.append("Champ requis manquant : conclusion")
        elif len(conclusion.strip()) < 100:
            self.warnings.append("Conclusion très courte (< 100 caractères)")
    
    def _validate_annexes(self, annexes_data: dict):
        """Valide les annexes"""
        if not annexes_data or annexes_data.get("type") == "none":
            self.warnings.append("Aucune annexe définie")
            return
        
        annexes_type = annexes_data.get("type", "")
        
        if annexes_type == "automatic":
            self._validate_automatic_annexes(annexes_data)
        elif annexes_type == "manual":
            self._validate_manual_annexes(annexes_data)
        else:
            self.warnings.append(f"Type d'annexe non reconnu : {annexes_type}")
    
    def _validate_automatic_annexes(self, annexes_data: dict):
        """Valide les annexes automatiques"""
        annexes_content = annexes_data.get("annexes", {})
        
        if not annexes_content:
            self.warnings.append("Annexes automatiques vides")
            return
        
        # Vérifier le tableau complet
        tableau = annexes_content.get("tableau_complet", {})
        simulations = tableau.get("simulations", [])
        
        if not simulations:
            self.warnings.append("Tableau récapitulatif vide")
        
        # Vérifier les essais détaillés
        essais = annexes_content.get("essais_detailles", [])
        if essais:
            images_manquantes = sum(1 for e in essais if not e.get("images"))
            if images_manquantes > 0:
                self.warnings.append(f"{images_manquantes} essais sans images")
    
    def _validate_manual_annexes(self, annexes_data: dict):
        """Valide les annexes manuelles"""
        organized_files = annexes_data.get("organized_files", {})
        
        if not organized_files:
            self.warnings.append("Annexes manuelles vides")
            return
        
        total_files = (
            len(organized_files.get("figures", [])) +
            len(organized_files.get("tableaux", [])) +
            len(organized_files.get("documents", []))
        )
        
        if total_files == 0:
            self.warnings.append("Aucun fichier dans les annexes manuelles")
    
    def _is_filled(self, value: Any) -> bool:
        """Vérifie si une valeur n'est pas vide"""
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ""
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return bool(value)
    
    def _display_validation_results(self):
        """Affiche les résultats de validation"""
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        total_issues = error_count + warning_count
        
        if total_issues == 0:
            return
        
        # Message de résumé en une ligne
        if error_count > 0:
            st.error(f"❌ **{error_count} erreurs, {warning_count} avertissements** - Cliquez pour voir les détails")
        else:
            st.warning(f"⚠️ **{warning_count} avertissements** - Cliquez pour voir les détails")
        
        # Détails en expander
        with st.expander("📋 Détails de validation", expanded=False):
            for error in self.errors:
                st.error(f"❌ {error}")
            for warning in self.warnings:
                st.warning(f"⚠️ {warning}")
        '''        
        # Afficher les erreurs
        for error in self.errors:
            st.error(f"❌ {error}")
        
        # Afficher les avertissements
        for warning in self.warnings:
            st.warning(f"⚠️ {warning}")
        
        # Résumé
        if not self.errors and not self.warnings:
            print("✅ Validation parfaite - Aucun problème détecté")
        elif not self.errors:
            print(f"ℹ️ Validation réussie avec {len(self.warnings)} avertissement(s)")
        '''

class DataValidator:
    """Validateur pour différents types de données"""
    
    @staticmethod
    def validate_image_file(file_path: str) -> Dict[str, Any]:
        """Valide un fichier image"""
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "info": {}
        }
        
        if not os.path.exists(file_path):
            result["errors"].append("Fichier non trouvé")
            return result
        
        # Vérifier l'extension
        if not validate_image_format(file_path):
            result["errors"].append("Format d'image non supporté")
        
        # Vérifier la taille
        file_size = os.path.getsize(file_path)
        if not validate_file_size(file_size):
            result["errors"].append(f"Fichier trop volumineux ({file_size / 1024 / 1024:.1f} MB)")
        
        # Tester l'ouverture de l'image
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                img.verify()
                result["info"]["format"] = img.format
                result["info"]["size"] = img.size
                result["info"]["mode"] = img.mode
        except Exception as e:
            result["errors"].append(f"Image corrompue : {str(e)}")
        
        result["valid"] = len(result["errors"]) == 0
        return result
    
    @staticmethod
    def validate_excel_file(file_path: str) -> Dict[str, Any]:
        """Valide un fichier Excel - VERSION ENRICHIE"""
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "info": {}
        }
        
        if not os.path.exists(file_path):
            result["errors"].append("Fichier non trouvé")
            return result
        
        try:
            import pandas as pd
            
            # Lire le fichier
            excel_data = pd.read_excel(file_path, sheet_name=None)
            
            result["info"]["sheets"] = list(excel_data.keys())
            result["info"]["total_sheets"] = len(excel_data)
            
            # Analyser chaque feuille
            for sheet_name, df in excel_data.items():
                if df.empty:
                    result["warnings"].append(f"Feuille '{sheet_name}' vide")
                else:
                    result["info"][f"rows_{sheet_name}"] = len(df)
                    result["info"][f"columns_{sheet_name}"] = len(df.columns)
                    
                    # ✅ NOUVELLE VALIDATION - Utiliser les validateurs Excel
                    sheet_validation = DataValidator._validate_excel_sheet_content(df, sheet_name)
                    if sheet_validation["warnings"]:
                        result["warnings"].extend(sheet_validation["warnings"])
                    if sheet_validation["potential_fields"]:
                        result["info"][f"potential_fields_{sheet_name}"] = sheet_validation["potential_fields"]
            
            result["valid"] = True
            
        except Exception as e:
            result["errors"].append(f"Erreur lecture Excel : {str(e)}")
        
        return result
    
    @staticmethod
    def _validate_excel_sheet_content(df, sheet_name: str) -> Dict[str, Any]:
        """✅ NOUVELLE - Valide le contenu d'une feuille Excel avec les validateurs"""
        validation_result = {
            "warnings": [],
            "potential_fields": {}
        }
        
        # Tester chaque colonne avec les validateurs Excel
        for col in df.columns:
            series = df[col]
            
            # Tester avec chaque validateur pour identifier le type potentiel
            field_types_detected = []
            
            for field_type in ["numero_essai", "vent", "houle", "courant", "maree", 
                              "commentaire", "navire", "resultat"]:
                if ExcelContentValidators.validate_field_content(series, field_type):
                    field_types_detected.append(field_type)
            
            if field_types_detected:
                validation_result["potential_fields"][col] = field_types_detected
            elif series.dropna().empty:
                validation_result["warnings"].append(f"Feuille '{sheet_name}': Colonne '{col}' entièrement vide")
        
        return validation_result


# Fonctions utilitaires pour la compatibilité avec l'ancien code
def validate_report(data: dict) -> bool:
    """Fonction de compatibilité pour valider un rapport"""
    validator = ReportValidator()
    return validator.validate_report(data)

  
def is_filled(value: Any) -> bool:
    """Fonction de compatibilité pour vérifier si une valeur est remplie"""
    validator = ReportValidator()
    return validator._is_filled(value)


# =============================================================================
# NOUVELLES FONCTIONS DE VALIDATION EXCEL POUR INTÉGRATION
# =============================================================================

def validate_excel_mapping(df, mapped_columns: Dict[str, str]) -> Dict[str, Any]:
    """
    ✅ NOUVELLE - Fonction principale pour valider un mapping Excel
    
    Args:
        df: DataFrame pandas
        mapped_columns: Dictionnaire {champ_app: colonne_excel}
    
    Returns:
        Dictionnaire avec résultats de validation
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "field_validations": {}
    }
    
    # Validation du mapping
    mapping_errors = ExcelMappingValidators.validate_final_mapping(df, mapped_columns)
    if mapping_errors:
        validation_result["errors"].extend(mapping_errors)
        validation_result["valid"] = False
    
    # Validation du contenu de chaque champ mappé
    for field, excel_col in mapped_columns.items():
        if excel_col in df.columns:
            series = df[excel_col]
            
            # Valider le contenu avec le validateur approprié
            is_content_valid = ExcelContentValidators.validate_field_content(series, field)
            
            validation_result["field_validations"][field] = {
                "excel_column": excel_col,
                "content_valid": is_content_valid,
                "sample_values": series.dropna().head(3).tolist() if not series.empty else []
            }
            
            if not is_content_valid:
                validation_result["warnings"].append(
                    f"Contenu suspect pour '{field}' dans colonne '{excel_col}'"
                )
    
    return validation_result


def validate_extracted_excel_data(simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    ✅ NOUVELLE - Valide les données extraites d'un fichier Excel
    
    Args:
        simulations: Liste des simulations extraites
    
    Returns:
        Résultats de validation détaillés
    """
    return ExcelDataValidators.validate_extracted_simulations(simulations)


def suggest_field_mapping(df) -> Dict[str, List[str]]:
    """
    ✅ NOUVELLE - Suggère des mappings pour les colonnes Excel
    
    Args:
        df: DataFrame pandas
    
    Returns:
        Dictionnaire {type_champ: [colonnes_candidates]}
    """
    suggestions = {}
    
    for field_type in ["numero_essai", "vent", "houle", "courant", "maree", 
                      "commentaire", "navire", "resultat"]:
        candidates = []
        
        for col in df.columns:
            series = df[col]
            if ExcelContentValidators.validate_field_content(series, field_type):
                candidates.append(col)
        
        if candidates:
            suggestions[field_type] = candidates
    
    return suggestions
