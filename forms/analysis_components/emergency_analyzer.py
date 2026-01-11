# =============================================================================
# forms/analysis_components/emergency_analyzer.py
# Analyseur de scénarios d'urgence pour les simulations de manœuvrabilité
# =============================================================================

from typing import Dict, Any, List


class EmergencyScenarioAnalyzer:
    """
    Analyseur spécialisé pour les scénarios d'urgence dans les simulations de manœuvrabilité.
    
    Responsabilités :
    - Classification des types de scénarios d'urgence
    - Analyse des taux de réussite par type d'urgence
    - Extraction des leçons apprises
    - Génération de recommandations spécifiques aux urgences
    - Évaluation des risques et facteurs critiques
    """
    
    def __init__(self):
        """Initialise l'analyseur de scénarios d'urgence."""
        # Mots-clés pour identifier les types d'urgence
        self.emergency_keywords = {
            "Panne d'équipement": [
                "thruster", "propulseur", "engine", "moteur", "panne", 
                "failure", "unavailable", "défaillance", "breakdown", "malfunction"
            ],
            "Conditions météo extrêmes": [
                "30 knt", "35 knt", "40 knt", "3m", "4m", "storm", "tempête", 
                "extrême", "severe", "extreme", "gale", "forte houle"
            ],
            "Near miss / Quasi-accident": [
                "near miss", "tight", "serré", "close", "proximity", 
                "10 meters", "10m", "collision", "quasi", "évitement"
            ],
            "Problème de manœuvre": [
                "abort", "abandon", "impossible", "uncontrollable", "incontrôlable",
                "lost control", "déviation", "trajectory"
            ],
            "Défaillance remorqueur": [
                "tug", "remorqueur", "assistance", "pull", "push", "towline",
                "cable", "remorquage", "towing"
            ],
            "Visibilité réduite": [
                "visibility", "visibilité", "fog", "brouillard", "mist",
                "poor visibility", "réduite"
            ],
            "Problème de communication": [
                "communication", "radio", "contact", "signal", "frequency",
                "misunderstanding", "malentendu"
            ]
        }
    
    def analyze_emergency_scenarios(self, simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse complète des scénarios d'urgence.
        
        Args:
            simulations: Liste de toutes les simulations
            
        Returns:
            Dict avec l'analyse complète des scénarios d'urgence
        """
        # Identifier les scénarios d'urgence
        emergency_scenarios = [s for s in simulations if s.get("is_emergency_scenario", False)]
        
        if not emergency_scenarios:
            return self._get_empty_emergency_analysis()
        
        # Analyse de base
        basic_stats = self._calculate_basic_emergency_stats(emergency_scenarios)
        
        # Classification par type
        classified_scenarios = self.classify_emergency_scenarios(emergency_scenarios)
        
        # Analyse détaillée par type
        type_analysis = self._analyze_by_emergency_type(classified_scenarios)
        
        # Facteurs de risque
        risk_factors = self._identify_risk_factors(emergency_scenarios)
        
        # Leçons apprises
        lessons_learned = self.extract_emergency_lessons(emergency_scenarios)
        
        # Recommandations
        recommendations = self.generate_emergency_recommendations(emergency_scenarios, basic_stats["success_rate"])
        
        # Matrice de criticité
        criticality_matrix = self._build_criticality_matrix(classified_scenarios)
        
        return {
            "basic_stats": basic_stats,
            "classified_scenarios": classified_scenarios,
            "type_analysis": type_analysis,
            "risk_factors": risk_factors,
            "lessons_learned": lessons_learned,
            "recommendations": recommendations,
            "criticality_matrix": criticality_matrix,
            "summary": self._generate_emergency_summary(basic_stats, type_analysis, risk_factors)
        }
    
    def classify_emergency_scenarios(self, emergency_scenarios: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Classifie les scénarios d'urgence par type.
        
        Args:
            emergency_scenarios: Liste des scénarios d'urgence
            
        Returns:
            Dict avec les scénarios classifiés par type
        """
        classified = {emergency_type: [] for emergency_type in self.emergency_keywords.keys()}
        classified["Autres urgences"] = []
        
        for scenario in emergency_scenarios:
            commentaire = scenario.get("commentaire_pilote", "").lower()
            scenario_classified = False
            
            # Vérifier chaque type d'urgence avec score de confiance
            best_match = {"type": None, "score": 0}
            
            for urgence_type, keywords in self.emergency_keywords.items():
                # Calculer un score basé sur le nombre de mots-clés trouvés
                matches = sum(1 for keyword in keywords if keyword.lower() in commentaire)
                confidence_score = matches / len(keywords) if keywords else 0
                
                if matches > 0 and confidence_score > best_match["score"]:
                    best_match = {"type": urgence_type, "score": confidence_score}
            
            # Classer selon le meilleur match
            if best_match["type"] and best_match["score"] > 0:
                # Enrichir le scenario avec des métadonnées
                enriched_scenario = {
                    **scenario,
                    "emergency_type": best_match["type"],
                    "confidence_score": best_match["score"],
                    "identified_keywords": self._extract_matching_keywords(commentaire, best_match["type"])
                }
                classified[best_match["type"]].append(enriched_scenario)
                scenario_classified = True
            
            # Si non classifié, mettre dans "Autres"
            if not scenario_classified:
                enriched_scenario = {
                    **scenario,
                    "emergency_type": "Autres urgences",
                    "confidence_score": 0.0,
                    "identified_keywords": []
                }
                classified["Autres urgences"].append(enriched_scenario)
        
        # Supprimer les catégories vides
        return {k: v for k, v in classified.items() if v}
    
    def extract_emergency_lessons(self, emergency_scenarios: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Extrait les leçons apprises des scénarios d'urgence.
        
        Args:
            emergency_scenarios: Liste des scénarios d'urgence
            
        Returns:
            Dict avec les leçons classifiées par catégorie
        """
        lessons = {
            "Facteurs de succès": [],
            "Causes d'échec": [],
            "Bonnes pratiques": [],
            "Points d'amélioration": [],
            "Facteurs environnementaux": [],
            "Facteurs humains": []
        }
        
        # Mots-clés pour identifier les leçons
        success_keywords = [
            "coordination", "control", "contrôle", "assistance", "help", "aide",
            "procedure", "procédure", "communication", "anticipation", "preparation"
        ]
        
        failure_keywords = [
            "wind", "vent", "unavailable", "panne", "speed", "vitesse", 
            "confusion", "delay", "retard", "miscommunication"
        ]
        
        practice_keywords = [
            "checklist", "protocol", "protocole", "backup", "secours", 
            "training", "formation", "drill", "exercice"
        ]
        
        # Analyser les scénarios réussis
        successful_scenarios = [s for s in emergency_scenarios if s.get("resultat") == "Réussite"]
        for scenario in successful_scenarios:
            commentaire = scenario.get("commentaire_pilote", "").lower()
            
            # Facteurs de succès
            for keyword in success_keywords:
                if keyword in commentaire:
                    if keyword in ["coordination", "control", "contrôle"]:
                        lessons["Facteurs de succès"].append("Coordination efficace entre pilote et remorqueurs")
                    elif keyword in ["assistance", "help", "aide"]:
                        lessons["Facteurs de succès"].append("Assistance adéquate des remorqueurs")
                    elif keyword in ["procedure", "procédure"]:
                        lessons["Bonnes pratiques"].append("Respect des procédures d'urgence")
                    elif keyword in ["communication"]:
                        lessons["Facteurs de succès"].append("Communication claire et efficace")
                    elif keyword in ["anticipation"]:
                        lessons["Bonnes pratiques"].append("Anticipation des problèmes potentiels")
        
        # Analyser les échecs
        failed_scenarios = [s for s in emergency_scenarios if s.get("resultat") == "Échec"]
        for scenario in failed_scenarios:
            commentaire = scenario.get("commentaire_pilote", "").lower()
            conditions_env = scenario.get("conditions_env", {})
            
            # Causes d'échec
            for keyword in failure_keywords:
                if keyword in commentaire:
                    if keyword in ["wind", "vent"]:
                        lessons["Facteurs environnementaux"].append("Conditions de vent défavorables")
                    elif keyword in ["unavailable", "panne"]:
                        lessons["Causes d'échec"].append("Équipement non disponible au moment critique")
                    elif keyword in ["speed", "vitesse"]:
                        lessons["Facteurs humains"].append("Contrôle de vitesse insuffisant")
                    elif keyword in ["confusion", "miscommunication"]:
                        lessons["Facteurs humains"].append("Problèmes de communication")
            
            # Analyser les conditions environnementales
            for condition_type, condition_value in conditions_env.items():
                if condition_value:
                    if any(extreme in condition_value.lower() for extreme in ["30", "35", "3m", "4m"]):
                        lessons["Facteurs environnementaux"].append(f"Conditions {condition_type} extrêmes")
        
        # Identifier les bonnes pratiques à partir des commentaires
        all_comments = [s.get("commentaire_pilote", "") for s in emergency_scenarios]
        combined_text = " ".join(all_comments).lower()
        
        for keyword in practice_keywords:
            if keyword in combined_text:
                if keyword in ["checklist", "protocol", "protocole"]:
                    lessons["Bonnes pratiques"].append("Utilisation de checklists et protocoles")
                elif keyword in ["backup", "secours"]:
                    lessons["Bonnes pratiques"].append("Préparation de solutions de secours")
                elif keyword in ["training", "formation", "drill", "exercice"]:
                    lessons["Points d'amélioration"].append("Formation et exercices d'urgence")
        
        # Supprimer les doublons
        for lesson_type in lessons:
            lessons[lesson_type] = list(set(lessons[lesson_type]))
        
        return lessons
    
    def generate_emergency_recommendations(self, emergency_scenarios: List[Dict[str, Any]], success_rate: float) -> List[Dict[str, str]]:
        """
        Génère des recommandations spécifiques aux scénarios d'urgence.
        
        Args:
            emergency_scenarios: Liste des scénarios d'urgence
            success_rate: Taux de réussite global des urgences
            
        Returns:
            Liste de recommandations avec priorité et catégorie
        """
        recommendations = []
        
        # Analyser les types d'urgence présents
        classified_scenarios = self.classify_emergency_scenarios(emergency_scenarios)
        
        # Recommandations basées sur le taux de réussite
        if success_rate < 0.5:
            recommendations.append({
                "priority": "critical",
                "category": "procedures",
                "title": "Révision urgente des procédures d'urgence",
                "description": "Le faible taux de réussite nécessite une révision complète des procédures",
                "timeline": "immédiat"
            })
        elif success_rate < 0.75:
            recommendations.append({
                "priority": "high",
                "category": "training",
                "title": "Formation renforcée pour les situations d'urgence",
                "description": "Améliorer la formation des pilotes pour la gestion des urgences",
                "timeline": "1 mois"
            })
        
        # Recommandations spécifiques par type d'urgence
        for emergency_type, scenarios in classified_scenarios.items():
            if len(scenarios) >= 2:  # Au moins 2 cas
                type_success_rate = sum(1 for s in scenarios if s.get("resultat") == "Réussite") / len(scenarios)
                
                if emergency_type == "Panne d'équipement" and type_success_rate < 0.6:
                    recommendations.append({
                        "priority": "high",
                        "category": "equipment",
                        "title": "Protocoles de secours pour pannes d'équipement",
                        "description": "Développer des procédures spécifiques en cas de panne",
                        "timeline": "2 mois"
                    })
                
                elif emergency_type == "Conditions météo extrêmes":
                    recommendations.append({
                        "priority": "medium",
                        "category": "operations",
                        "title": "Seuils d'interdiction météorologique",
                        "description": "Établir des critères stricts selon les conditions météo",
                        "timeline": "1 mois"
                    })
                
                elif emergency_type == "Défaillance remorqueur":
                    recommendations.append({
                        "priority": "high",
                        "category": "equipment",
                        "title": "Remorqueurs de secours",
                        "description": "Prévoir des remorqueurs supplémentaires en conditions critiques",
                        "timeline": "3 mois"
                    })
                
                elif emergency_type == "Problème de communication":
                    recommendations.append({
                        "priority": "medium",
                        "category": "procedures",
                        "title": "Protocoles de communication d'urgence",
                        "description": "Améliorer les procédures de communication",
                        "timeline": "1 mois"
                    })
        
        # Recommandations générales
        general_recommendations = [
            {
                "priority": "medium",
                "category": "training",
                "title": "Exercices de simulation d'urgence",
                "description": "Mettre en place des exercices réguliers",
                "timeline": "3 mois"
            },
            {
                "priority": "low",
                "category": "documentation",
                "title": "Documentation des cas d'urgence",
                "description": "Créer une base de données des incidents",
                "timeline": "6 mois"
            }
        ]
        
        recommendations.extend(general_recommendations)
        
        # Trier par priorité
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return recommendations
    
    def get_emergency_statistics(self, simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule les statistiques détaillées des scénarios d'urgence.
        
        Args:
            simulations: Liste de toutes les simulations
            
        Returns:
            Dict avec les statistiques détaillées
        """
        emergency_scenarios = [s for s in simulations if s.get("is_emergency_scenario", False)]
        total_simulations = len(simulations)
        
        if not emergency_scenarios:
            return {
                "total_emergencies": 0,
                "emergency_rate": 0.0,
                "success_rate": 0.0,
                "severity_distribution": {},
                "frequency_by_type": {}
            }
        
        # Statistiques de base
        total_emergencies = len(emergency_scenarios)
        emergency_rate = total_emergencies / total_simulations if total_simulations > 0 else 0
        successful_emergencies = sum(1 for s in emergency_scenarios if s.get("resultat") == "Réussite")
        success_rate = successful_emergencies / total_emergencies if total_emergencies > 0 else 0
        
        # Classification et analyse
        classified = self.classify_emergency_scenarios(emergency_scenarios)
        
        # Distribution de sévérité (basée sur les mots-clés)
        severity_distribution = self._calculate_severity_distribution(emergency_scenarios)
        
        # Fréquence par type
        frequency_by_type = {
            emergency_type: {
                "count": len(scenarios),
                "percentage": (len(scenarios) / total_emergencies) * 100,
                "success_rate": (sum(1 for s in scenarios if s.get("resultat") == "Réussite") / len(scenarios)) * 100 if scenarios else 0
            }
            for emergency_type, scenarios in classified.items()
        }
        
        return {
            "total_emergencies": total_emergencies,
            "emergency_rate": emergency_rate,
            "success_rate": success_rate,
            "severity_distribution": severity_distribution,
            "frequency_by_type": frequency_by_type,
            "classified_scenarios": classified
        }
    
    def _calculate_basic_emergency_stats(self, emergency_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule les statistiques de base des scénarios d'urgence."""
        if not emergency_scenarios:
            return {"total": 0, "successes": 0, "failures": 0, "success_rate": 0.0}
        
        total = len(emergency_scenarios)
        successes = sum(1 for s in emergency_scenarios if s.get("resultat") == "Réussite")
        failures = sum(1 for s in emergency_scenarios if s.get("resultat") == "Échec")
        success_rate = successes / total if total > 0 else 0.0
        
        return {
            "total": total,
            "successes": successes,
            "failures": failures,
            "success_rate": success_rate
        }
    
    def _analyze_by_emergency_type(self, classified_scenarios: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """Analyse détaillée par type d'urgence."""
        type_analysis = {}
        
        for emergency_type, scenarios in classified_scenarios.items():
            if scenarios:
                successes = sum(1 for s in scenarios if s.get("resultat") == "Réussite")
                total = len(scenarios)
                success_rate = successes / total if total > 0 else 0
                
                # Analyser la sévérité moyenne
                avg_confidence = sum(s.get("confidence_score", 0) for s in scenarios) / total
                
                # Identifier les conditions communes
                common_conditions = self._find_common_conditions(scenarios)
                
                type_analysis[emergency_type] = {
                    "total_scenarios": total,
                    "success_rate": success_rate,
                    "avg_confidence": avg_confidence,
                    "common_conditions": common_conditions,
                    "severity": self._assess_type_severity(emergency_type, success_rate),
                    "scenarios": scenarios
                }
        
        return type_analysis
    
    def _identify_risk_factors(self, emergency_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identifie les facteurs de risque dans les scénarios d'urgence."""
        risk_factors = {
            "environmental": {},
            "operational": {},
            "technical": {},
            "human": {}
        }
        
        for scenario in emergency_scenarios:
            conditions_env = scenario.get("conditions_env", {})
            commentaire = scenario.get("commentaire_pilote", "").lower()
            
            # Facteurs environnementaux
            for condition_type, condition_value in conditions_env.items():
                if condition_value and any(extreme in condition_value for extreme in ["30", "35", "3", "4"]):
                    key = f"{condition_type}: {condition_value}"
                    risk_factors["environmental"][key] = risk_factors["environmental"].get(key, 0) + 1
            
            # Facteurs techniques
            if any(tech in commentaire for tech in ["panne", "failure", "unavailable"]):
                risk_factors["technical"]["equipment_failure"] = risk_factors["technical"].get("equipment_failure", 0) + 1
            
            # Facteurs humains
            if any(human in commentaire for human in ["confusion", "delay", "miscommunication"]):
                risk_factors["human"]["communication_issues"] = risk_factors["human"].get("communication_issues", 0) + 1
            
            # Facteurs opérationnels
            maneuver = scenario.get("manoeuvre", "")
            if "urgence" in maneuver.lower() or "évitement" in maneuver.lower():
                risk_factors["operational"]["complex_maneuver"] = risk_factors["operational"].get("complex_maneuver", 0) + 1
        
        return risk_factors
    
    def _build_criticality_matrix(self, classified_scenarios: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, str]]:
        """Construit une matrice de criticité des types d'urgence."""
        matrix = {}
        
        for emergency_type, scenarios in classified_scenarios.items():
            if scenarios:
                total = len(scenarios)
                failures = sum(1 for s in scenarios if s.get("resultat") == "Échec")
                failure_rate = failures / total if total > 0 else 0
                
                # Évaluer la criticité
                if failure_rate > 0.7:
                    criticality = "critique"
                    color = "🔴"
                elif failure_rate > 0.4:
                    criticality = "élevée"
                    color = "🟡"
                else:
                    criticality = "modérée"
                    color = "🟢"
                
                matrix[emergency_type] = {
                    "criticality": criticality,
                    "color": color,
                    "failure_rate": failure_rate,
                    "total_cases": total
                }
        
        return matrix
    
    def _generate_emergency_summary(self, basic_stats: Dict[str, Any], type_analysis: Dict[str, Dict[str, Any]], risk_factors: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un résumé exécutif des scénarios d'urgence."""
        # Identifier le type le plus problématique
        most_critical_type = None
        lowest_success_rate = 1.0
        
        for emergency_type, analysis in type_analysis.items():
            if analysis["success_rate"] < lowest_success_rate:
                lowest_success_rate = analysis["success_rate"]
                most_critical_type = emergency_type
        
        # Identifier le facteur de risque principal
        all_risk_counts = {}
        for category, risks in risk_factors.items():
            for risk, count in risks.items():
                all_risk_counts[f"{category}: {risk}"] = count
        
        main_risk_factor = max(all_risk_counts.items(), key=lambda x: x[1]) if all_risk_counts else None
        
        return {
            "overall_assessment": self._assess_overall_emergency_performance(basic_stats["success_rate"]),
            "most_critical_type": most_critical_type,
            "main_risk_factor": main_risk_factor,
            "total_scenarios": basic_stats["total"],
            "success_rate": basic_stats["success_rate"],
            "key_insights": self._extract_emergency_insights(basic_stats, type_analysis, risk_factors)
        }
    
    def _extract_matching_keywords(self, commentaire: str, emergency_type: str) -> List[str]:
        """Extrait les mots-clés correspondants trouvés dans le commentaire."""
        if emergency_type not in self.emergency_keywords:
            return []
        
        keywords = self.emergency_keywords[emergency_type]
        found_keywords = [keyword for keyword in keywords if keyword.lower() in commentaire.lower()]
        return found_keywords
    
    def _calculate_severity_distribution(self, emergency_scenarios: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calcule la distribution de sévérité des scénarios."""
        severity_keywords = {
            "critique": ["critical", "severe", "dangerous", "critique", "sévère", "danger"],
            "élevée": ["high", "important", "significant", "élevé", "important"],
            "modérée": ["moderate", "medium", "modéré", "moyen"]
        }
        
        distribution = {"critique": 0, "élevée": 0, "modérée": 0}
        
        for scenario in emergency_scenarios:
            commentaire = scenario.get("commentaire_pilote", "").lower()
            severity_assigned = False
            
            for severity, keywords in severity_keywords.items():
                if any(keyword in commentaire for keyword in keywords):
                    distribution[severity] += 1
                    severity_assigned = True
                    break
            
            # Si aucune sévérité identifiée, classer comme modérée
            if not severity_assigned:
                distribution["modérée"] += 1
        
        return distribution
    
    def _find_common_conditions(self, scenarios: List[Dict[str, Any]]) -> Dict[str, int]:
        """Trouve les conditions communes dans un groupe de scénarios."""
        common_conditions = {}
        
        for scenario in scenarios:
            conditions_env = scenario.get("conditions_env", {})
            for condition_type, condition_value in conditions_env.items():
                if condition_value:
                    key = f"{condition_type}: {condition_value}"
                    common_conditions[key] = common_conditions.get(key, 0) + 1
        
        # Retourner seulement les conditions présentes dans au moins 2 scénarios
        return {k: v for k, v in common_conditions.items() if v >= 2}
    
    def _assess_type_severity(self, emergency_type: str, success_rate: float) -> str:
        """Évalue la sévérité d'un type d'urgence."""
        # Certains types sont intrinsèquement plus sévères
        high_severity_types = ["Near miss / Quasi-accident", "Panne d'équipement"]
        
        if emergency_type in high_severity_types or success_rate < 0.4:
            return "élevée"
        elif success_rate < 0.7:
            return "modérée"
        else:
            return "faible"
    
    def _assess_overall_emergency_performance(self, success_rate: float) -> str:
        """Évalue la performance globale en gestion d'urgence."""
        if success_rate >= 0.8:
            return "excellente"
        elif success_rate >= 0.6:
            return "satisfaisante"
        elif success_rate >= 0.4:
            return "préoccupante"
        else:
            return "critique"
    
    def _extract_emergency_insights(self, basic_stats: Dict[str, Any], type_analysis: Dict[str, Dict[str, Any]], risk_factors: Dict[str, Any]) -> List[str]:
        """Extrait les insights clés des analyses d'urgence."""
        insights = []
        
        # Insight sur le nombre de scénarios
        if basic_stats["total"] > 10:
            insights.append(f"Nombre élevé de scénarios d'urgence ({basic_stats['total']})")
        
        # Insight sur la diversité des types
        if len(type_analysis) > 3:
            insights.append(f"Grande diversité de types d'urgence ({len(type_analysis)} types)")
        
        # Insight sur les facteurs de risque
        total_environmental = sum(risk_factors["environmental"].values())
        total_technical = sum(risk_factors["technical"].values())
        
        if total_environmental > total_technical:
            insights.append("Facteurs environnementaux dominent les urgences")
        elif total_technical > total_environmental:
            insights.append("Facteurs techniques dominent les urgences")
        
        return insights
    
    def _get_empty_emergency_analysis(self) -> Dict[str, Any]:
        """Retourne une analyse vide quand il n'y a pas de scénarios d'urgence."""
        return {
            "basic_stats": {"total": 0, "successes": 0, "failures": 0, "success_rate": 0.0},
            "classified_scenarios": {},
            "type_analysis": {},
            "risk_factors": {"environmental": {}, "operational": {}, "technical": {}, "human": {}},
            "lessons_learned": {"Facteurs de succès": [], "Causes d'échec": [], "Bonnes pratiques": [], "Points d'amélioration": [], "Facteurs environnementaux": [], "Facteurs humains": []},
            "recommendations": [],
            "criticality_matrix": {},
            "summary": {
                "overall_assessment": "non évaluable",
                "most_critical_type": None,
                "main_risk_factor": None,
                "total_scenarios": 0,
                "success_rate": 0.0,
                "key_insights": ["Aucun scénario d'urgence identifié"]
            }
        }
    