# =============================================================================
# utils/excel_common.py - Extraction des VRAIES duplications
# Fonctions communes entre mapping_workflow.py et simulations_form.py
# =============================================================================

import pandas as pd
import re
from typing import Dict, Any, List, Optional
from datetime import datetime


class ExcelColumnDetector:
    """
    Détecteur de colonnes Excel - EXTRAIT de mapping_workflow.py ET simulations_form.py
    """
    
    # Patterns de détection consolidés des deux fichiers
    DETECTION_PATTERNS = {
        "numero_essai": ["test", "essai", "trial", "n°", "num", "numero", "id"],
        "navire": ["navire", "ship", "vessel", "boat"],
        "manoeuvre": ["manoeuvre", "maneuver", "manœuvre"],
        "vent": ["vent", "wind"],
        "houle": ["houle", "wave", "swell"],
        "courant": ["courant", "current"],
        "maree": ["maree", "marée", "tide"],
        "condition": ["condition", "état", "etat", "status", "state"],
        "commentaire": ["commentaire", "comment", "remark", "note"],
        "resultat": ["resultat", "result", "résultat", "outcome"],
        "remorqueurs": ["remorqueur", "tug"],
        "poste": ["poste", "berth", "dock"],
        "pilote": ["pilote", "pilot", "instructor"],
        "etat_chargement": ["charge", "chargement", "load", "laden", "ballast"],
        "bord": ["bord", "côté", "side", "port", "starboard"],
        "entree": ["entrance", "entry", "entrée", "entree"]
    }
    
    @staticmethod
    def detect_standard_columns(excel_columns: List[str], df: pd.DataFrame = None) -> Dict[str, str]:
        """
        Détecte automatiquement les colonnes standard
        """
        detected = {}
    
        for excel_col in excel_columns:
            # Obtenir la série si DataFrame disponible
            series = df[excel_col] if (df is not None and excel_col in df.columns) else None
            
            # ✅ LOGIQUE CORRECTE : appeler la fonction pour 1 colonne
            field_type = suggest_field_for_column(excel_col, series)
            
            # Assigner si pas de conflit
            if field_type and field_type not in detected:
                detected[field_type] = excel_col
        
        return detected
    
    @staticmethod
    def detect_field_by_content(excel_col: str, series: pd.Series) -> tuple[str, int]:
        """
        Détecte le type de champ par analyse du contenu
        Retourne (field_type, confidence_score)
        """
        if series.empty or series.dropna().empty:
            return ("", 0)
        
        # Échantillon de données non nulles
        sample = series.dropna().astype(str).head(20)
        sample_values = [str(v).strip().lower() for v in sample]
        
        # === DÉTECTION RÉSULTAT (0/1, Success/Fail) ===
        
        # Pattern binaire strict : que des 0 et 1
        binary_count = sum(1 for v in sample_values if v in ['0', '1', '0.0', '1.0'])
        if binary_count > len(sample) * 0.8:  # 80%+ sont binaires
            return ("resultat", 95)
        
        # Pattern succès/échec textuel
        success_words = ['success', 'pass', 'ok', 'réussi', 'réussite', 'concluant', 'good']
        fail_words = ['fail', 'failure', 'nok', 'échec', 'échoué', 'bad', 'error']
        
        success_count = sum(1 for v in sample_values if any(word in v for word in success_words))
        fail_count = sum(1 for v in sample_values if any(word in v for word in fail_words))
        
        if (success_count + fail_count) > len(sample) * 0.6:  # 60%+ sont des résultats
            return ("resultat", 85)
        
        # === DÉTECTION NUMÉRO D'ESSAI (Séquences numériques) ===
        
        # Vérifier si c'est une séquence numérique
        numeric_count = 0
        sequence_like = 0
        
        for v in sample_values:
            # Nettoyer pour garder que les chiffres
            clean_v = ''.join(c for c in v if c.isdigit())
            if clean_v:
                numeric_count += 1
                # Vérifier si ça ressemble à un ID/numéro d'essai
                if len(clean_v) <= 4 and clean_v.isdigit():  # Courts numéros
                    sequence_like += 1
        
        if numeric_count > len(sample) * 0.8 and sequence_like > len(sample) * 0.6:
            return ("numero_essai", 80)
        
        # === DÉTECTION CONDITIONS MÉTÉO (Patterns spécifiques) ===
        
        # Vent : vitesse + direction
        wind_patterns = [
            r'\d+\s*(kt|kts|nds|mph|kmh)',  # "25 kts"
            r'[nsew]{1,3}\s*\d+',           # "nw 25"
            r'\d+\s*[nsew]{1,3}',           # "25 nw"
            r'calm|calme|nul'               # Conditions calmes
        ]
        
        wind_matches = sum(1 for v in sample_values 
                        if any(re.search(pattern, v, re.IGNORECASE) for pattern in wind_patterns))
        
        if wind_matches > len(sample) * 0.5:
            return ("vent", 85)
        
        # Houle : hauteur en mètres
        wave_patterns = [
            r'\d+[.,]?\d*\s*m',         # "2.5m" ou "3m"
            r'\d+[.,]?\d*/\d+',         # "2.5/12" (hauteur/période)
            r'wave|houle|swell'         # Mots-clés explicites
        ]
        
        wave_matches = sum(1 for v in sample_values 
                        if any(re.search(pattern, v, re.IGNORECASE) for pattern in wave_patterns))
        
        if wave_matches > len(sample) * 0.5:
            return ("houle", 85)
        
        # Courant : vitesse en nœuds
        current_patterns = [
            r'\d+[.,]?\d*\s*(kt|kts|nds)',  # "1.5 kts"
            r'nul|null|negligible|faible',   # Courant nul
            r'flood|ebb|flot|jusant'         # Types de courant
        ]
        
        current_matches = sum(1 for v in sample_values 
                            if any(re.search(pattern, v, re.IGNORECASE) for pattern in current_patterns))
        
        if current_matches > len(sample) * 0.5:
            return ("courant", 80)
        
        # Marée : niveaux
        tide_patterns = [
            r'[+\-]?\d+[.,]?\d*\s*m',   # "+2.14m" ou "-0.5m"
            r'pm|bm|hw|lw',             # Pleine mer, Basse mer
            r'[+\-]?\d+[.,]?\d*$'       # Nombres avec signe
        ]
        
        tide_matches = sum(1 for v in sample_values 
                        if any(re.search(pattern, v, re.IGNORECASE) for pattern in tide_patterns))
        
        if tide_matches > len(sample) * 0.5:
            return ("maree", 80)
        
        # === DÉTECTION COMMENTAIRES (Texte long) ===
        
        # Texte long = probablement commentaires
        long_text_count = sum(1 for v in sample_values if len(v) > 30)
        
        # Vocabulaire du domaine maritime
        maritime_words = ['manœuvre', 'manoeuvre', 'accostage', 'appareillage', 'pilote', 
                        'remorqueur', 'navire', 'port', 'quai', 'simulation']
        
        maritime_matches = sum(1 for v in sample_values 
                            if any(word in v for word in maritime_words))
        
        if long_text_count > len(sample) * 0.6 or maritime_matches > len(sample) * 0.3:
            return ("commentaire", 75)
        
        # === DÉTECTION NAVIRE (Noms propres) ===
        
        # Éviter les valeurs numériques (pas des noms de navires)
        non_numeric = sum(1 for v in sample_values if not v.replace('.', '').replace(',', '').isdigit())
        
        # Éviter les conditions météo dans les noms de navires
        weather_words = ['wind', 'wave', 'current', 'kt', 'kts', 'm/s']
        non_weather = sum(1 for v in sample_values 
                        if not any(word in v for word in weather_words))
        
        # Noms de navires = texte non-numérique, non-météo, longueur raisonnable
        reasonable_length = sum(1 for v in sample_values if 3 <= len(v) <= 30)
        
        if (non_numeric > len(sample) * 0.8 and 
            non_weather > len(sample) * 0.8 and 
            reasonable_length > len(sample) * 0.7):
            return ("navire", 65)
        
        # === DÉTECTION CONDITIONS SPÉCIALES ===
        
        # Mots-clés de conditions particulières
        condition_words = ['urgence', 'emergency', 'normale', 'normal', 'spéciale', 'special', 
                        'critique', 'standard', 'test', 'essai']
        
        condition_matches = sum(1 for v in sample_values 
                            if any(word in v for word in condition_words))
        
        if condition_matches > len(sample) * 0.4:
            return ("condition", 70)
        
        # Aucun pattern reconnu
        return ("", 0)
    
    @staticmethod
    def calculate_detection_confidence(field: str, excel_col: str) -> int:
        """Calcule la confiance de détection. Retourne un score de 0 à 100"""
        try:
            # Normalisation
            col_clean = excel_col.lower().replace(' ', '').replace('_', '').replace('-', '')
            
            # Mots-clés principaux par champ
            keywords = {
                "numero_essai": ["test", "essai", "trial", "n°", "no", "num", "numero", "id"],
                "condition": ["condition", "etat", "état", "status", "state"],
                "navire": ["navire", "ship", "vessel", "boat"],
                "vent": ["vent", "wind"],
                "houle": ["houle", "wave", "swell"],
                "courant": ["courant", "current", "flow"],
                "maree": ["marée", "maree", "tide", "level"],
                "commentaire": ["commentaire", "comment", "observation", "note", "remark"],
                "resultat": ["résultat", "resultat", "result", "outcome"],
                "manoeuvre": ["manœuvre", "manoeuvre", "maneuver"],
                "remorqueurs": ["remorqueur", "tug"],
                "poste": ["poste", "berth", "quai"],
                "pilote": ["pilote", "pilot"],
                "etat_chargement": ["charge", "chargement", "load", "ballast"],
                "bord": ["bord", "côté", "side"],
                "entree": ["entrance", "entrée", "entree", "entry"]
            }
            
            # Incompatibilités (évite les faux positifs)
            incompatible = {
                "courant": ["comment", "note", "observation"],  # Current ≠ Commentaire
                "commentaire": ["current", "wind", "wave"],     # Comment ≠ Conditions météo
                "navire": ["condition", "weather", "wind"],     # Ship ≠ Conditions
                "condition": ["comment", "note", "observation"] # Condition ≠ Commentaire
            }
            
            if field not in keywords:
                return 0
            
            # 1. Vérifier incompatibilités → Score 0
            if field in incompatible:
                for incomp in incompatible[field]:
                    if incomp in col_clean:
                        return 0
            
            # 2. Chercher correspondances
            best_score = 0
            for keyword in keywords[field]:
                keyword_clean = keyword.replace(' ', '').replace('_', '').replace('-', '')
                
                if keyword_clean == col_clean:
                    # Correspondance exacte
                    return 100
                elif keyword_clean in col_clean:
                    # Correspondance partielle - score selon qualité
                    if len(keyword_clean) >= 4:  # Mots longs = plus fiables
                        score = 85
                    else:  # Mots courts = moins fiables  
                        score = 70
                    
                    # Bonus si en début/fin
                    if col_clean.startswith(keyword_clean) or col_clean.endswith(keyword_clean):
                        score += 10
                    
                    best_score = max(best_score, min(score, 100))
            
            return best_score
            
        except Exception:
            return 0
    
    @staticmethod
    def suggest_field_for_column(column_name: str, series: Optional[pd.Series] = None, df: Optional[pd.DataFrame] = None) -> str:
        """Suggère un champ application pour une colonne Excel"""
        # 1. Test nom
        best_field, best_score = "", 0
        if column_name.strip() and not column_name.lower().startswith('unnamed'):
            for field in ["numero_essai", "condition", "navire", "vent", "houle", "courant", 
                        "maree", "commentaire", "resultat", "manoeuvre", "remorqueurs", 
                        "poste", "pilote", "etat_chargement", "bord", "entree"]:
                score = calculate_detection_confidence(field, column_name)
                if score > best_score:
                    best_score = score
                    best_field = field
        
        # 2. Test contenu (si série fournie)
        if series is not None:
            content_field, content_score = ExcelColumnDetector.analyze_column_content(series)
            if content_score > best_score:
                best_field = content_field
                best_score = content_score
        
        return best_field if best_score >= 60 else ""

    @staticmethod
    def analyze_column_content(series: pd.Series) -> tuple[str, int]:
        """
        Analyse le CONTENU d'une colonne pour déterminer son type
        Retourne (field_type, confidence_score)
        """
        if series.empty or series.dropna().empty:
            return ("", 0)
        
        # Échantillon de données
        sample = series.dropna().astype(str).head(20)
        sample_values = [str(v).strip().lower() for v in sample]
        
        # === TESTS DE CONTENU ===
        
        # 1. RÉSULTAT : Valeurs binaires (0/1)
        binary_count = sum(1 for v in sample_values if v in ['0', '1', '0.0', '1.0'])
        if binary_count > len(sample) * 0.9:
            return ("resultat", 95)
        
        # 2. RÉSULTAT : Mots succès/échec
        success_words = ['success', 'pass', 'ok', 'réussi', 'réussite', 'concluant']
        fail_words = ['fail', 'failure', 'nok', 'échec', 'échoué']
        result_words = sum(1 for v in sample_values 
                        if any(word in v for word in success_words + fail_words))
        if result_words > len(sample) * 0.6:
            return ("resultat", 85)
        
        # 3. NUMÉRO D'ESSAI : Séquence numérique courte
        numeric_count = sum(1 for v in sample_values if v.isdigit() and len(v) <= 3)
        if numeric_count > len(sample) * 0.8:
            return ("numero_essai", 80)
        
        # 4. COMMENTAIRE : Texte long
        long_text = sum(1 for v in sample_values if len(v) > 30)
        if long_text > len(sample) * 0.6:
            return ("commentaire", 75)
        
        # 5. CONDITIONS MÉTÉO : Patterns simples
        all_text = ' '.join(sample_values)
        if any(w in all_text for w in ['kt', 'kts', 'wind', 'vent', 'nds']):
            return ("vent", 70)
        if any(w in all_text for w in ['m/', 'wave', 'houle', 'swell']):
            return ("houle", 70)
        if any(w in all_text for w in ['nul', 'current', 'courant']):
            return ("courant", 70)
        if any(w in all_text for w in ['+', '-', 'm', 'mzh', 'tide', 'marée']):
            return ("maree", 70)
        
        return ("", 0)


    @staticmethod
    def detect_columns_smart(excel_columns: List[str], df: Optional[pd.DataFrame] = None) -> Dict[str, str]:
        """
        Fonction UNIQUE qui remplace detect_standard_columns ET suggest_field_for_column
        
        Usage:
        - Pour toutes les colonnes: detect_columns_smart(df.columns.tolist(), df)
        - Pour une colonne: detect_columns_smart(['ma_colonne'], mini_df)['ma_colonne']
        """
        detected = {}
        
        for excel_col in excel_columns:
            best_field = ""
            best_score = 0
            
            # 1. DÉTECTION PAR NOM (si nom significatif)
            if excel_col.strip() and not excel_col.lower().startswith('unnamed'):
                # Test avec votre fonction existante
                for field in ["numero_essai", "condition", "navire", "vent", "houle", "courant", 
                            "maree", "commentaire", "resultat", "manoeuvre", "remorqueurs", 
                            "poste", "pilote", "etat_chargement", "bord", "entree"]:
                    score = calculate_detection_confidence(field, excel_col)
                    if score > best_score:
                        best_score = score
                        best_field = field
            
            # 2. DÉTECTION PAR CONTENU (si DataFrame disponible)
            if df is not None and excel_col in df.columns:
                content_field, content_score = ExcelColumnDetector.analyze_column_content(df[excel_col])
                
                # Privilégier le contenu pour colonnes sans nom OU si score contenu > nom
                if (not excel_col.strip() or excel_col.lower().startswith('unnamed') or 
                    content_score > best_score):
                    if content_score >= 60:
                        best_field = content_field
                        best_score = content_score
            
            # 3. ASSIGNER si score suffisant et pas de conflit
            if best_score >= 60 and best_field and best_field not in detected:
                detected[best_field] = excel_col
        
        return detected

class ExcelMappingValidator:
    """
    Validateur de mapping Excel - EXTRAIT des deux fichiers
    
    DUPLICATION IDENTIFIÉE :
    - mapping_workflow.py lignes ~500-600 : _validate_mapping_basic()
    - simulations_form.py lignes ~400-500 : _validate_mapping_completeness()
    """
    
    @staticmethod
    def validate_mapping_basic(mapping: Dict[str, str], df: pd.DataFrame) -> List[str]:
        """
        Validation de base du mapping
        
        CONSOLIDATION de :
        - mapping_workflow.py : _validate_mapping_basic()
        - simulations_form.py : _validate_mapping_completeness() (partie erreurs)
        """
        errors = []
        
        # Champ obligatoire
        if "numero_essai" not in mapping:
            errors.append("Le champ 'N° d'essai' est obligatoire")
        
        # Vérifier l'existence des colonnes
        for field, excel_col in mapping.items():
            if excel_col not in df.columns:
                errors.append(f"Colonne '{excel_col}' introuvable pour '{field}'")
        
        # Vérifier les doublons
        used_columns = list(mapping.values())
        duplicates = [col for col in used_columns if used_columns.count(col) > 1]
        if duplicates:
            errors.append(f"Colonnes utilisées plusieurs fois: {', '.join(set(duplicates))}")
        
        return errors
    
    @staticmethod
    def validate_mapping_completeness(mapping: Dict[str, str]) -> List[str]:
        """
        Validation de complétude (avertissements)
        
        EXTRAIT de simulations_form.py : _validate_mapping_completeness() (partie warnings)
        """
        messages = []
        
        # Champs recommandés
        recommended_fields = ["navire", "manoeuvre", "commentaire"]
        missing_recommended = [f for f in recommended_fields if f not in mapping]
        
        if missing_recommended:
            messages.append(f"⚠️ Champs recommandés manquants: {', '.join(missing_recommended)}")
        
        # Message de succès
        if "numero_essai" in mapping:
            messages.append("✅ Mapping valide et prêt pour le traitement")
        
        return messages



class ExcelDataProcessor:
    """Processeur de données Excel"""
    
    @staticmethod
    def get_clean_value(value, auto_clean: bool = True) -> str:
        """Récupère et nettoie une valeur"""
        if pd.isna(value):
            return ""
        
        return ExcelDataProcessor.clean_value(str(value), auto_clean)
    
    @staticmethod
    def get_clean_value_from_row(row: pd.Series, excel_col: str, auto_clean: bool = True) -> str:
        """Récupère et nettoie une valeur depuis une row pandas"""
        if excel_col not in row.index:
            return ""
        
        value = row[excel_col]
        
        if pd.isna(value):
            return ""
        
        return ExcelDataProcessor.clean_value(str(value), auto_clean)
    
    @staticmethod
    def clean_value(value: str, auto_clean: bool = True) -> str:
        """Nettoie une valeur selon les options"""
        if not auto_clean:
            return value
        
        # Nettoyage basique
        cleaned = str(value).strip()
        
        # Supprimer les retours à la ligne multiples
        cleaned = cleaned.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
        
        # Supprimer les espaces multiples
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    @staticmethod
    def detect_simulation_result(simulation: Dict[str, Any], mapping: Dict[str, str], row: pd.Series) -> str:
        """
        Détecte automatiquement le résultat d'une simulation
        
        CONSOLIDATION de :
        - mapping_workflow.py : _detect_simulation_result()
        - simulations_form.py : _detect_simulation_result()
        """
        # Méthode 1: Colonne résultat explicite
        if "resultat" in mapping:
            result_value = ExcelDataProcessor.get_clean_value(row[mapping["resultat"]], True)
            if result_value:
                parsed_result = ExcelDataProcessor.parse_explicit_result(result_value)
                if parsed_result != "Non défini":
                    return parsed_result
        
        # Méthode 2: Analyse du commentaire
        comment = simulation.get("commentaire_pilote", "")
        if comment and len(comment.strip()) > 5:
            return ExcelDataProcessor.detect_result_from_comment(comment)
        
        return "Non défini"
    
    @staticmethod
    def parse_explicit_result(result_value: str) -> str:
        """
        Parse un résultat explicite depuis une colonne
        
        EXTRAIT de mapping_workflow.py : _parse_explicit_result()
        """
        value_lower = str(result_value).lower().strip()
        
        # Valeurs numériques
        if value_lower in ['1', '1.0']:
            return "Réussite"
        elif value_lower in ['0', '0.0']:
            return "Échec"
        
        # Valeurs textuelles
        success_values = ['success', 'pass', 'ok', 'réussi', 'réussite', 'concluant', 'true', 'yes', 'oui']
        failure_values = ['fail', 'failure', 'nok', 'échec', 'échoué', 'false', 'no', 'non']
        
        if value_lower in success_values:
            return "Réussite"
        elif value_lower in failure_values:
            return "Échec"
        
        return "Non défini"
    
    @staticmethod
    def detect_result_from_comment(comment: str) -> str:
        """Détecte le résultat depuis un commentaire"""
        comment_lower = comment.lower()
        
        # Mots-clés de succès
        success_keywords = [
            "réussi", "concluant", "succès", "bon", "satisfaisant", 
            "correct", "parfait", "excellent", "sans problème", "sans difficulté"
        ]
        
        # Mots-clés d'échec
        failure_keywords = [
            "échec", "échoué", "impossible", "problème", "difficulté", 
            "incident", "collision", "erreur", "abandon", "interrompu"
        ]
        
        # Phrases spécifiques
        if any(phrase in comment_lower for phrase in ["manœuvre concluante", "manoeuvre concluante", "bon déroulement"]):
            return "Réussite"
        
        if any(phrase in comment_lower for phrase in ["manœuvre échouée", "manoeuvre échouée"]):
            return "Échec"
        
        # Comptage des mots-clés
        success_count = sum(1 for word in success_keywords if word in comment_lower)
        failure_count = sum(1 for word in failure_keywords if word in comment_lower)
        
        if success_count > failure_count and success_count > 0:
            return "Réussite"
        elif failure_count > success_count and failure_count > 0:
            return "Échec"
        
        return "Non défini"
    
    @staticmethod
    def detect_emergency_scenarios(df: pd.DataFrame) -> set:
        """Détecte les scénarios d'urgence"""
        emergency_rows = set()
        
        # Détection basique par mots-clés dans toutes les colonnes
        for col in df.columns:
            if df[col].dtype == 'object':  # Colonnes texte seulement
                for index, row in df.iterrows():
                    value = str(row[col]).lower()
                    if any(keyword in value for keyword in ["urgence", "emergency", "panne", "incident", "critique"]):
                        emergency_rows.add(index)
        
        return emergency_rows
    
    @staticmethod
    def get_custom_fields(mapping: Dict[str, str]) -> List[str]:
        """
        Identifie les champs personnalisés dans le mapping
        
        CONSOLIDATION de :
        - mapping_workflow.py : _get_custom_fields()
        - simulations_form.py : _get_custom_fields()
        """
        standard_fields = [
            "numero_essai", "navire", "etat_chargement", "manoeuvre", 
            "vent", "houle", "courant", "maree", "condition", 
            "remorqueurs", "poste", "bord", "entree", "pilote", 
            "commentaire", "resultat"
        ]
        
        return [field for field in mapping.keys() if field not in standard_fields]
    
    @staticmethod
    def calculate_processing_stats(simulations: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calcule les statistiques de traitement
        
        EXTRAIT de mapping_workflow.py et simulations_form.py
        """
        stats = {
            "total": len(simulations),
            "reussites": sum(1 for s in simulations if s.get("resultat") == "Réussite"),
            "echecs": sum(1 for s in simulations if s.get("resultat") == "Échec"),
            "non_definis": sum(1 for s in simulations if s.get("resultat") == "Non défini"),
            "urgences": sum(1 for s in simulations if s.get("is_emergency_scenario", False)),
            "conditions_renseignees": sum(1 for s in simulations if s.get("condition", "").strip())
        }
        
        return stats


class ExcelCustomFieldHelper:
    """
    Helper pour les champs personnalisés - EXTRAIT des deux fichiers
    
    DUPLICATION IDENTIFIÉE :
    - mapping_workflow.py lignes ~400-500 : _suggest_custom_name(), _validate_custom_name()
    - simulations_form.py lignes ~300-400 : _suggest_custom_field_name(), _validate_custom_field_name()
    """
    
    @staticmethod
    def suggest_custom_name(excel_col: str) -> str:
        """
        Suggère un nom pour un champ personnalisé
        
        CONSOLIDATION de :
        - mapping_workflow.py : _suggest_custom_name()
        - simulations_form.py : _suggest_custom_field_name()
        """
        name = excel_col.lower().strip()
        name = re.sub(r'[^a-z0-9]', '_', name)
        name = re.sub(r'_+', '_', name).strip('_')
        
        # Traductions courantes
        translations = {
            'entrance': 'entree',
            'entry': 'entree',
            'captain': 'capitaine',
            'visibility': 'visibilite',
            'duration': 'duree',
            'speed': 'vitesse',
            'time': 'heure',
            'date': 'date'
        }
        
        for eng, fr in translations.items():
            if eng in name:
                name = name.replace(eng, fr)
        
        return name if name else "champ_personnalise"
    
    @staticmethod
    def validate_custom_name(name: str) -> bool:
        """
        Valide un nom de champ personnalisé
        
        CONSOLIDATION de :
        - mapping_workflow.py : _validate_custom_name()
        - simulations_form.py : _validate_custom_field_name()
        """
        if not name:
            return False
        
        # Format valide (lettres, chiffres, underscores)
        if not re.match(r'^[a-z][a-z0-9_]*$', name):
            return False
        
        # Pas trop long
        if len(name) > 50:
            return False
        
        return True


class ExcelImportManager:
    """Gestionnaire unifié pour l'import Excel - SANS changer l'interface"""
    
    @staticmethod
    def process_excel_file_with_mapping(df, mapping, options):
        """Traite un fichier Excel avec mapping - logique unifiée"""
        # Code extrait des deux fichiers


def perform_detailed_validation(df: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, Any]:
        """Validation détaillée du mapping et des données"""
        
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "info": [],
            "stats": {}
        }
        
        # 1. Validation de base
        basic_errors = validate_mapping_basic(mapping, df)
        results["errors"].extend(basic_errors)
        if basic_errors:
            results["is_valid"] = False
        
        # 2. Validation du contenu des colonnes clés
        if "numero_essai" in mapping and mapping["numero_essai"] in df.columns:
            essai_col = mapping["numero_essai"]
            valid_essais = df[essai_col].notna().sum()
            total_rows = len(df)
            
            if valid_essais == 0:
                results["errors"].append("Colonne numéro d'essai complètement vide")
                results["is_valid"] = False
            elif valid_essais < total_rows * 0.5:
                results["warnings"].append(f"Beaucoup de numéros d'essai manquants: {valid_essais}/{total_rows}")
            
            results["stats"]["lignes_valides"] = valid_essais
        
        # 3. Validation spéciale pour le nouveau champ Condition
        if "condition" in mapping and mapping["condition"] in df.columns:
            condition_col = mapping["condition"]
            condition_values = df[condition_col].notna().sum()
            
            results["info"].append(f"🆕 Champ 'Condition' détecté: {condition_values} valeurs")
            
            # Analyser les types de conditions
            if condition_values > 0:
                unique_conditions = df[condition_col].dropna().nunique()
                results["info"].append(f"📊 {unique_conditions} type(s) de condition(s) différente(s)")
                
                # Détecter les conditions d'urgence
                emergency_conditions = df[condition_col].dropna().str.lower().str.contains(
                    'urgence|emergency|critique|panne', na=False
                ).sum()
                
                if emergency_conditions > 0:
                    results["info"].append(f"🚨 {emergency_conditions} condition(s) d'urgence détectée(s)")
        
        # 4. Statistiques générales
        results["stats"]["total_lignes"] = len(df)
        results["stats"]["colonnes_mappees"] = len(mapping)
        results["stats"]["completude_moyenne"] = (df.notna().sum().sum() / (len(df) * len(df.columns))) * 100
        
        return results

    
# =============================================================================
# FONCTIONS DE COMPATIBILITÉ pour remplacer les appels directs
# =============================================================================

def suggest_field_for_column(column_name: str, series: Optional[pd.Series] = None) -> str:
    """Fonction de compatibilité"""
    return ExcelColumnDetector.suggest_field_for_column(column_name, series)

def detect_standard_columns(excel_columns: List[str], df: pd.DataFrame = None) -> Dict[str, str]:
    """Fonction de compatibilité"""
    return ExcelColumnDetector.detect_standard_columns(excel_columns, df)


def calculate_detection_confidence(field: str, excel_col: str) -> int:
    """Fonction de compatibilité"""
    return ExcelColumnDetector.calculate_detection_confidence(field, excel_col)


def validate_mapping_basic(mapping: Dict[str, str], df: pd.DataFrame) -> List[str]:
    """Fonction de compatibilité"""
    return ExcelMappingValidator.validate_mapping_basic(mapping, df)


def get_clean_value(value, auto_clean: bool = True) -> str:
    """Fonction de compatibilitéE"""
    return ExcelDataProcessor.clean_value(value, auto_clean)

def detect_simulation_result(simulation: Dict[str, Any], mapping: Dict[str, str], row: pd.Series) -> str:
    """Fonction de compatibilité"""
    return ExcelDataProcessor.detect_simulation_result(simulation, mapping, row)


def detect_emergency_scenarios(df: pd.DataFrame) -> set:
    """Fonction de compatibilité"""
    return ExcelDataProcessor.detect_emergency_scenarios(df)


def get_custom_fields(mapping: Dict[str, str]) -> List[str]:
    """Fonction de compatibilité"""
    return ExcelDataProcessor.get_custom_fields(mapping)


def suggest_custom_name(excel_col: str) -> str:
    """Fonction de compatibilité"""
    return ExcelCustomFieldHelper.suggest_custom_name(excel_col)


def validate_custom_name(name: str) -> bool:
    """Fonction de compatibilité"""
    return ExcelCustomFieldHelper.validate_custom_name(name)

def process_excel_file_with_mapping(df, mapping, options):
    """Fonction de compatibilité"""
    return ExcelImportManager.process_excel_file_with_mapping(df, mapping, options)

def parse_explicit_result(result_value: str) -> str:
    """Fonction de compatibilité"""
    return ExcelDataProcessor.parse_explicit_result(result_value)
