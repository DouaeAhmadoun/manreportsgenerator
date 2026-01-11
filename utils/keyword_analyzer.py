#!/usr/bin/env python3
"""
Analyseur intelligent de commentaires par mots-clés et patterns
Plus fiable que l'IA pour ce cas d'usage spécifique
"""

import re
from typing import List, Dict

class SmartKeywordAnalyzer:
    """Analyseur intelligent basé sur des patterns linguistiques"""
    
    def __init__(self):
        # === PATTERNS FRANÇAIS ===
        # Patterns de réussite français (par ordre de priorité)
        self.success_patterns_fr = [
            # Phrases complètes (priorité maximale)
            r"manœuvre\s+(réussie?|reussie?|concluante?|terminée?|accomplie?)",
            r"(bon|excellent|parfait)\s+déroulement",
            r"(réalisée?|effectuée?|menée?)\s+(avec\s+succès|sans\s+(problème|difficulté|incident))",
            r"objectifs?\s+(atteints?|réalisés?)",
            r"accostage\s+(réussi|parfait|en\s+douceur)",
            r"appareillage\s+(réussi|sans\s+problème)",
            
            # Mots-clés forts
            r"\b(réussite|succès|concluant|satisfaisant)\b",
            r"\bsans\s+(difficulté|problème|incident|souci)\b",
            r"\b(maîtrisé|contrôlé|fluide|aisé)\b",
            r"\b(parfait|optimal|correct|acceptable)\b"
        ]
        
        # Patterns d'échec français (par ordre de priorité)
        self.failure_patterns_fr = [
            # Phrases complètes (priorité maximale)
            r"manœuvre\s+(échouée?|abandonnée?|ratée?|impossible)",
            r"(échec|abandon)\s+(de\s+la\s+)?manœuvre",
            r"impossible\s+(de|d')\s+(contrôler|réaliser|effectuer)",
            r"(collision|incident|problème)\s+(grave|majeur)",
            r"(touché|heurté|endommagé)",
            r"(danger|risque)\s+(imminent|critique)",
            
            # Expressions négatives
            r"\b(échec|échoué|raté|manqué)\b",
            r"\b(impossible|irréalisable|infaisable)\b", 
            r"\b(abandonné|annulé|interrompu)\b",
            r"\b(problème|difficulté|incident)\s+(majeur|grave|critique)\b",
            r"\b(collision|contact|choc)\b"
        ]
        
        # === PATTERNS ANGLAIS ===
        # Patterns de réussite anglais
        self.success_patterns_en = [
            # Phrases complètes
            r"maneuver\s+(successful|completed|accomplished|achieved)",
            r"manoeuver\s+(successful|completed|accomplished|achieved)",
            r"(good|excellent|perfect)\s+(execution|performance)",
            r"(completed|performed|executed)\s+(successfully|without\s+(issue|problem|difficulty))",
            r"objectives?\s+(achieved|reached|met)",
            r"(docking|berthing)\s+(successful|smooth|perfect)",
            r"(departure|undocking)\s+(successful|smooth)",
            
            # Mots-clés forts
            r"\b(success|successful|accomplished|achieved)\b",
            r"\bwithout\s+(difficulty|problem|issue|incident)\b",
            r"\b(controlled|mastered|smooth|easy)\b",
            r"\b(perfect|optimal|correct|acceptable|good)\b"
        ]
        
        # Patterns d'échec anglais
        self.failure_patterns_en = [
            # Phrases complètes
            r"maneuver\s+(failed|aborted|impossible|unsuccessful)",
            r"manoeuver\s+(failed|aborted|impossible|unsuccessful)",
            r"(failure|abort)\s+of\s+(the\s+)?maneuver",
            r"unable\s+to\s+(control|perform|execute)",
            r"(collision|incident|problem)\s+(serious|major|critical)",
            r"(hit|struck|damaged|contacted)",
            r"(danger|risk)\s+(imminent|critical)",
            
            # Expressions négatives
            r"\b(failure|failed|missed|unsuccessful)\b",
            r"\b(impossible|unfeasible|unachievable)\b",
            r"\b(aborted|cancelled|interrupted|stopped)\b",
            r"\b(problem|difficulty|incident)\s+(major|serious|critical)\b",
            r"\b(collision|contact|impact|crash)\b"
        ]
        
        # Contexte positif/négatif (bilingue)
        self.positive_context = [
            # Français
            "réussi", "parfait", "fluide", "maîtrisé", "contrôlé",
            "satisfaisant", "acceptable", "correct", "bon", "excellent",
            "aisé", "facile", "normal", "standard", "optimal",
            # Anglais
            "successful", "perfect", "smooth", "controlled", "mastered",
            "satisfactory", "acceptable", "correct", "good", "excellent",
            "easy", "normal", "standard", "optimal"
        ]
        
        self.negative_context = [
            # Français
            "difficile", "compliqué", "critique", "dangereux", "risqué",
            "problématique", "limite", "serré", "tendu", "stress",
            # Anglais
            "difficult", "complicated", "critical", "dangerous", "risky",
            "problematic", "limited", "tight", "tense", "stressed"
        ]
        
        # Patterns maritimes spécialisés (bilingue)
        self.maritime_success = [
            # Français
            r"(accostage|amarrage)\s+en\s+douceur",
            r"(mouillage|ancrage)\s+réussi",
            r"(évitage|dépassement)\s+sans\s+problème",
            r"vitesse\s+contrôlée",
            r"trajectoire\s+(maintenue|correcte)",
            r"gouvernail\s+efficace",
            # Anglais
            r"(docking|berthing)\s+(smooth|gentle)",
            r"(anchoring|mooring)\s+successful",
            r"(overtaking|passing)\s+without\s+(problem|issue)",
            r"speed\s+(controlled|under\s+control)",
            r"(course|trajectory)\s+(maintained|correct)",
            r"(rudder|steering)\s+effective"
        ]
        
        self.maritime_failure = [
            # Français
            r"(dérive|abattée)\s+(incontrôlée?|excessive)",
            r"(gouvernail|moteur|propulsion)\s+(inefficace|en\s+panne)",
            r"vitesse\s+(excessive|incontrôlée)",
            r"trajectoire\s+(déviée|incorrecte)",
            r"(amarres|défenses)\s+rompues?",
            # Anglais
            r"(drift|set)\s+(uncontrolled|excessive)",
            r"(rudder|engine|propulsion)\s+(ineffective|failed|broken)",
            r"speed\s+(excessive|uncontrolled|out\s+of\s+control)",
            r"(course|trajectory)\s+(deviated|incorrect|wrong)",
            r"(lines|fenders)\s+(broken|failed)"
        ]
        
        print("🧠 Analyseur bilingue (FR/EN) initialisé avec logique conservative")
    
    def _clean_comment(self, comment: str) -> str:
        """Nettoie et normalise le commentaire"""
        if not comment:
            return ""
        
        # Convertir en minuscules
        comment = comment.lower()
        
        # Normaliser les caractères spéciaux
        comment = re.sub(r'[''`]', "'", comment)
        comment = re.sub(r'[""«»]', '"', comment)
        comment = re.sub(r'\s+', ' ', comment)  # Espaces multiples
        
        return comment.strip()
    
    def _check_patterns(self, comment: str, patterns_fr: List[str], patterns_en: List[str]) -> List[Dict]:
        """Vérifie les patterns français et anglais et retourne les matches avec scores"""
        matches = []
        
        # Vérifier patterns français
        for i, pattern in enumerate(patterns_fr):
            if re.search(pattern, comment, re.IGNORECASE):
                score = len(patterns_fr) - i + 10  # Bonus pour français (langue principale)
                matches.append({
                    "pattern": pattern,
                    "score": score,
                    "language": "fr",
                    "match": re.search(pattern, comment, re.IGNORECASE).group()
                })
        
        # Vérifier patterns anglais
        for i, pattern in enumerate(patterns_en):
            if re.search(pattern, comment, re.IGNORECASE):
                score = len(patterns_en) - i  # Score normal pour anglais
                matches.append({
                    "pattern": pattern,
                    "score": score,
                    "language": "en",
                    "match": re.search(pattern, comment, re.IGNORECASE).group()
                })
        
        return matches
    
    def _calculate_context_score(self, comment: str) -> float:
        """Calcule un score de contexte général"""
        
        positive_count = sum(1 for word in self.positive_context if word in comment)
        negative_count = sum(1 for word in self.negative_context if word in comment)
        
        # Score entre -1 (très négatif) et +1 (très positif)
        total = positive_count + negative_count
        if total == 0:
            return 0
        
        return (positive_count - negative_count) / total
    
    def analyze_comment(self, comment: str) -> int:
        """
        Analyse intelligente d'un commentaire (FR/EN) avec logique conservative
        
        Returns:
            1: Réussite (très confiant)
            0: Échec (très confiant)
            -1: Non défini/incertain (doute)
        """
        if not comment or len(comment.strip()) < 5:
            return -1
        
        cleaned_comment = self._clean_comment(comment)
        
        # 1. Vérifier les patterns de succès (FR + EN)
        success_matches = self._check_patterns(
            cleaned_comment, 
            self.success_patterns_fr, 
            self.success_patterns_en
        )
        success_matches.extend(self._check_patterns(
            cleaned_comment, 
            self.maritime_success, 
            self.maritime_success  # Patterns maritimes déjà bilingues
        ))
        
        # 2. Vérifier les patterns d'échec (FR + EN)
        failure_matches = self._check_patterns(
            cleaned_comment, 
            self.failure_patterns_fr, 
            self.failure_patterns_en
        )
        failure_matches.extend(self._check_patterns(
            cleaned_comment, 
            self.maritime_failure, 
            self.maritime_failure  # Patterns maritimes déjà bilingues
        ))
        
        # 3. Calculer les scores
        success_score = sum(match["score"] for match in success_matches)
        failure_score = sum(match["score"] for match in failure_matches)
        
        # 4. Score de contexte général
        context_score = self._calculate_context_score(cleaned_comment)
        
        # 5. LOGIQUE CONSERVATIVE - Patterns spéciaux (haute priorité)
        
        # Phrases de succès très claires (FR/EN)
        clear_success_patterns = [
            r"manœuvre\s+(réussie?|concluante?)",
            r"maneuver\s+(successful|completed)",
            r"manoeuver\s+(successful|completed)",
            r"(réalisée?|completed)\s+(avec\s+succès|successfully)",
            r"(bon|good|excellent)\s+déroulement",
            r"sans\s+(problème|difficulté|incident)",
            r"without\s+(problem|difficulty|issue)"
        ]
        
        # Phrases d'échec très claires (FR/EN)
        clear_failure_patterns = [
            r"manœuvre\s+(échouée?|abandonnée?)",
            r"maneuver\s+(failed|aborted)",
            r"manoeuver\s+(failed|aborted)",
            r"impossible\s+(de|d'|to)\s+(contrôler|control)",
            r"(échec|failure)\s+(de\s+la\s+|of\s+the\s+)?manœuvre",
            r"(collision|incident|accident)",
            r"(abandon|abort)"
        ]
        
        # Vérifier les patterns très clairs
        for pattern in clear_success_patterns:
            if re.search(pattern, cleaned_comment, re.IGNORECASE):
                return 1
        
        for pattern in clear_failure_patterns:
            if re.search(pattern, cleaned_comment, re.IGNORECASE):
                return 0
        
        # 6. LOGIQUE CONSERVATIVE - Seuils plus élevés
        score_difference = abs(success_score - failure_score)
        
        # Il faut une différence significative pour être sûr
        MIN_SCORE_DIFFERENCE = 8  # Seuil plus conservateur
        MIN_ABSOLUTE_SCORE = 5    # Score minimum requis
        
        if success_score >= MIN_ABSOLUTE_SCORE and score_difference >= MIN_SCORE_DIFFERENCE and success_score > failure_score:
            return 1
        elif failure_score >= MIN_ABSOLUTE_SCORE and score_difference >= MIN_SCORE_DIFFERENCE and failure_score > success_score:
            return 0
        else:
            # En cas de doute, vérifier le contexte avec seuils élevés
            if context_score > 0.7 and success_score > 0:  # Très positif
                return 1
            elif context_score < -0.7 and failure_score > 0:  # Très négatif
                return 0
            else:
                # En cas de doute → NON DÉFINI
                return -1
    
    def analyze_with_explanation(self, comment: str) -> Dict:
        """Analyse avec explication détaillée (pour debug)"""
        if not comment:
            return {"result": -1, "explanation": "Commentaire vide"}
        
        cleaned_comment = self._clean_comment(comment)
        
        success_matches = self._check_patterns(
            cleaned_comment, 
            self.success_patterns_fr, 
            self.success_patterns_en
        )
        success_matches.extend(self._check_patterns(
            cleaned_comment, 
            self.maritime_success, 
            self.maritime_success
        ))
        
        failure_matches = self._check_patterns(
            cleaned_comment, 
            self.failure_patterns_fr, 
            self.failure_patterns_en
        )
        failure_matches.extend(self._check_patterns(
            cleaned_comment, 
            self.maritime_failure, 
            self.maritime_failure
        ))
        
        success_score = sum(match["score"] for match in success_matches)
        failure_score = sum(match["score"] for match in failure_matches)
        context_score = self._calculate_context_score(cleaned_comment)
        
        result = self.analyze_comment(comment)
        
        return {
            "result": result,
            "success_score": success_score,
            "failure_score": failure_score,
            "context_score": context_score,
            "success_matches": [f"{m['match']} ({m.get('language', '?')})" for m in success_matches],
            "failure_matches": [f"{m['match']} ({m.get('language', '?')})" for m in failure_matches],
            "explanation": self._get_explanation(result, success_score, failure_score, context_score),
            "language_detected": self._detect_language(cleaned_comment)
        }
    
    def _detect_language(self, comment: str) -> str:
        """Détecte la langue du commentaire (approximatif)"""
        # Mots-clés français typiques
        fr_keywords = ["manœuvre", "sans", "avec", "réalisé", "échoué", "difficulté"]
        # Mots-clés anglais typiques  
        en_keywords = ["maneuver", "manoeuver", "without", "with", "performed", "failed", "difficulty"]
        
        fr_count = sum(1 for word in fr_keywords if word in comment.lower())
        en_count = sum(1 for word in en_keywords if word in comment.lower())
        
        if fr_count > en_count:
            return "français"
        elif en_count > fr_count:
            return "anglais"
        else:
            return "indéterminé"
    
    def _get_explanation(self, result: int, success_score: float, failure_score: float, context_score: float) -> str:
        """Génère une explication du résultat"""
        if result == 1:
            return f"Réussite détectée (succès: {success_score}, échec: {failure_score}, contexte: {context_score:.2f})"
        elif result == 0:
            return f"Échec détecté (succès: {success_score}, échec: {failure_score}, contexte: {context_score:.2f})"
        else:
            return f"Incertain (succès: {success_score}, échec: {failure_score}, contexte: {context_score:.2f})"

# Interfaces compatibles avec votre code existant
def ai_analyze_comment(comment: str) -> str:
    """Interface compatible avec le code existant"""
    analyzer = SmartKeywordAnalyzer()
    result = analyzer.analyze_comment(comment)
    
    if result == 1:
        return "Réussite"
    elif result == 0:
        return "Échec"
    else:
        return "Non défini"

def analyze_simulation_comments(simulations: list, use_rate_limit: bool = True) -> list:
    """Analyse rapide de tous les commentaires"""
    analyzer = SmartKeywordAnalyzer()
    updated_simulations = []
    
    print(f"🧠 Analyse intelligente de {len(simulations)} commentaires...")
    
    for sim in simulations:
        updated_sim = sim.copy()
        comment = sim.get("commentaire_pilote", "")
        
        if comment and comment.strip():
            result = analyzer.analyze_comment(comment)
            
            if result == 1:
                updated_sim["resultat"] = "Réussite"
                updated_sim["resultat_source"] = "Analyse intelligente"
                print(f"✅ Simulation {sim.get('id', '?')}: Réussite")
            elif result == 0:
                updated_sim["resultat"] = "Échec"
                updated_sim["resultat_source"] = "Analyse intelligente"
                print(f"❌ Simulation {sim.get('id', '?')}: Échec")
            else:
                updated_sim["resultat"] = "Non défini"
                updated_sim["resultat_source"] = "Analyse intelligente"
                print(f"⚠️ Simulation {sim.get('id', '?')}: Non défini")
        else:
            updated_sim["resultat"] = "Non défini"
            updated_sim["resultat_source"] = "Aucun commentaire"
        
        updated_simulations.append(updated_sim)
    
    return updated_simulations
