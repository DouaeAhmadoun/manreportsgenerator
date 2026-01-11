# =============================================================================
# forms/analysis_components/performance_analyzer.py
# Analyseur de performances pour les simulations de manœuvrabilité
# =============================================================================

from typing import Dict, Any, List
import streamlit as st


class PerformanceAnalyzer:
    """
    Analyseur de performances des simulations de manœuvrabilité.
    
    Responsabilités :
    - Analyse détaillée des performances par navire et manœuvre
    - Identification des tendances de performance
    - Analyse des causes d'échec
    - Génération de recommandations d'amélioration
    """
    
    def __init__(self):
        """Initialise l'analyseur de performances."""
        pass
    
    def analyze_ship_performance(self, simulations: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse les performances par type de navire.
        
        Args:
            simulations: Liste des simulations
            metrics: Métriques calculées
            
        Returns:
            Dict avec l'analyse des performances par navire
        """
        navires_data = metrics["simulations_par_navire"]
        analysis = {
            "best_ship": None,
            "worst_ship": None,
            "performance_levels": {},
            "recommendations": []
        }
        
        if not navires_data:
            return analysis
        
        # Calculer les niveaux de performance
        for navire, stats in navires_data.items():
            if stats["total"] > 0:
                success_rate = stats["reussies"] / stats["total"]
                
                analysis["performance_levels"][navire] = {
                    "success_rate": success_rate,
                    "total_tests": stats["total"],
                    "successes": stats["reussies"],
                    "failures": stats["echecs"],
                    "level": self._assess_performance_level(success_rate),
                    "icon": self._get_performance_icon(success_rate)
                }
        
        # Identifier le meilleur et le pire navire
        if analysis["performance_levels"]:
            best_navire = max(analysis["performance_levels"].items(), 
                            key=lambda x: x[1]["success_rate"])
            worst_navire = min(analysis["performance_levels"].items(), 
                             key=lambda x: x[1]["success_rate"])
            
            analysis["best_ship"] = {
                "name": best_navire[0],
                "success_rate": best_navire[1]["success_rate"],
                "stats": best_navire[1]
            }
            
            analysis["worst_ship"] = {
                "name": worst_navire[0],
                "success_rate": worst_navire[1]["success_rate"],
                "stats": worst_navire[1]
            }
            
            # Générer des recommandations
            analysis["recommendations"] = self._generate_ship_recommendations(analysis)
        
        return analysis
    
    def analyze_maneuver_performance(self, simulations: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse les performances par type de manœuvre.
        
        Args:
            simulations: Liste des simulations
            metrics: Métriques calculées
            
        Returns:
            Dict avec l'analyse des performances par manœuvre
        """
        manoeuvres_data = metrics["simulations_par_manoeuvre"]
        analysis = {
            "best_maneuver": None,
            "worst_maneuver": None,
            "performance_levels": {},
            "complexity_analysis": {},
            "recommendations": []
        }
        
        if not manoeuvres_data:
            return analysis
        
        # Calculer les niveaux de performance par manœuvre
        for manoeuvre, stats in manoeuvres_data.items():
            if stats["total"] > 0:
                success_rate = stats["reussies"] / stats["total"]
                
                analysis["performance_levels"][manoeuvre] = {
                    "success_rate": success_rate,
                    "total_tests": stats["total"],
                    "successes": stats["reussies"],
                    "failures": stats["echecs"],
                    "level": self._assess_performance_level(success_rate),
                    "icon": self._get_performance_icon(success_rate),
                    "complexity": self._assess_maneuver_complexity(manoeuvre, success_rate, stats["total"])
                }
        
        # Identifier la meilleure et la pire manœuvre
        if analysis["performance_levels"]:
            best_maneuver = max(analysis["performance_levels"].items(), 
                              key=lambda x: x[1]["success_rate"])
            worst_maneuver = min(analysis["performance_levels"].items(), 
                               key=lambda x: x[1]["success_rate"])
            
            analysis["best_maneuver"] = {
                "name": best_maneuver[0],
                "success_rate": best_maneuver[1]["success_rate"],
                "stats": best_maneuver[1]
            }
            
            analysis["worst_maneuver"] = {
                "name": worst_maneuver[0],
                "success_rate": worst_maneuver[1]["success_rate"],
                "stats": worst_maneuver[1]
            }
            
            # Analyser la complexité des manœuvres
            analysis["complexity_analysis"] = self._analyze_maneuver_complexity(analysis["performance_levels"])
            
            # Générer des recommandations
            analysis["recommendations"] = self._generate_maneuver_recommendations(analysis)
        
        return analysis
    
    def identify_performance_trends(self, simulations: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[str]:
        """
        Identifie les tendances de performance globales.
        
        Args:
            simulations: Liste des simulations
            metrics: Métriques calculées
            
        Returns:
            Liste des tendances identifiées
        """
        trends = []
        
        # Analyser les tendances par navire
        navires_data = metrics["simulations_par_navire"]
        if navires_data:
            ship_analysis = self.analyze_ship_performance(simulations, metrics)
            
            if ship_analysis["best_ship"]:
                best_rate = ship_analysis["best_ship"]["success_rate"] * 100
                best_name = ship_analysis["best_ship"]["name"].replace('Porte-conteneurs Type ', '')
                trends.append(f"Meilleure performance: {best_name} ({best_rate:.1f}%)")
            
            if ship_analysis["worst_ship"] and len(navires_data) > 1:
                worst_rate = ship_analysis["worst_ship"]["success_rate"] * 100
                worst_name = ship_analysis["worst_ship"]["name"].replace('Porte-conteneurs Type ', '')
                if worst_rate < 60:
                    trends.append(f"Performance à améliorer: {worst_name} ({worst_rate:.1f}%)")
        
        # Analyser les tendances par manœuvre
        manoeuvres_data = metrics["simulations_par_manoeuvre"]
        if manoeuvres_data:
            maneuver_analysis = self.analyze_maneuver_performance(simulations, metrics)
            
            if maneuver_analysis["worst_maneuver"]:
                worst_rate = maneuver_analysis["worst_maneuver"]["success_rate"] * 100
                if worst_rate < 70:
                    trends.append(f"Manœuvre la plus difficile: {maneuver_analysis['worst_maneuver']['name']} ({worst_rate:.1f}%)")
        
        # Analyser les conditions problématiques
        from .metrics_calculator import MetricsCalculator
        calculator = MetricsCalculator()
        critical_conditions = calculator.identify_critical_conditions(simulations)
        
        if critical_conditions:
            most_critical = max(critical_conditions.items(), 
                              key=lambda x: x[1]["echecs"] / max(x[1]["total"], 1))
            critical_rate = (most_critical[1]["echecs"] / most_critical[1]["total"]) * 100
            trends.append(f"Condition la plus critique: {most_critical[0]} ({critical_rate:.1f}% d'échecs)")
        
        # Tendance générale
        taux_global = metrics["taux_reussite"] * 100
        if taux_global >= 80:
            trends.append("Tendance générale: Performance excellente (≥80%)")
        elif taux_global >= 60:
            trends.append("Tendance générale: Performance satisfaisante (60-80%)")
        else:
            trends.append("Tendance générale: Performance nécessitant des améliorations (<60%)")
        
        # Analyser la distribution des échecs
        echecs = [s for s in simulations if s.get("resultat") == "Échec"]
        if echecs:
            failure_analysis = self.analyze_failure_causes(echecs)
            if failure_analysis["main_causes"]:
                main_cause = max(failure_analysis["main_causes"].items(), key=lambda x: x[1])
                trends.append(f"Cause principale d'échec: {main_cause[0]} ({main_cause[1]} cas)")
        
        return trends
    
    def analyze_failure_causes(self, failures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse détaillée des causes d'échec.
        
        Args:
            failures: Liste des simulations échouées
            
        Returns:
            Dict avec l'analyse des causes d'échec
        """
        analysis = {
            "total_failures": len(failures),
            "main_causes": {},
            "environmental_factors": {},
            "technical_factors": {},
            "operational_factors": {},
            "detailed_analysis": [],
            "recommendations": []
        }
        
        if not failures:
            return analysis
        
        # Mapping des mots-clés vers les causes
        keywords_mapping = {
            "Vent fort": ["vent", "wind", "25", "30", "35", "rafale"],
            "Houle importante": ["houle", "wave", "vague", "3m", "2.5m"],
            "Courant fort": ["courant", "current", "dérive", "drift"],
            "Visibilité réduite": ["visibilité", "visibility", "brouillard", "fog"],
            "Problème technique": ["panne", "failure", "défaillance", "unavailable"],
            "Manœuvre complexe": ["difficile", "tight", "serré", "complex"],
            "Vitesse excessive": ["speed", "vitesse", "excessive", "trop rapide"],
            "Contrôle perdu": ["control", "contrôle", "incontrôlable", "uncontrollable"]
        }
        
        # Analyser chaque échec
        for sim in failures:
            commentaire = sim.get("commentaire_pilote", "").lower()
            failure_detail = {
                "test_id": sim.get("numero_essai_original", "N/A"),
                "ship": sim.get("navire", "N/A"),
                "maneuver": sim.get("manoeuvre", "N/A"),
                "conditions": sim.get("conditions_env", {}),
                "identified_causes": [],
                "severity": "moderate"
            }
            
            # Identifier les causes
            for cause, keywords in keywords_mapping.items():
                if any(keyword.lower() in commentaire for keyword in keywords):
                    analysis["main_causes"][cause] = analysis["main_causes"].get(cause, 0) + 1
                    failure_detail["identified_causes"].append(cause)
                    
                    # Catégoriser la cause
                    if cause in ["Vent fort", "Houle importante", "Courant fort", "Visibilité réduite"]:
                        analysis["environmental_factors"][cause] = analysis["environmental_factors"].get(cause, 0) + 1
                    elif cause in ["Problème technique"]:
                        analysis["technical_factors"][cause] = analysis["technical_factors"].get(cause, 0) + 1
                    else:
                        analysis["operational_factors"][cause] = analysis["operational_factors"].get(cause, 0) + 1
            
            # Évaluer la sévérité
            if len(failure_detail["identified_causes"]) > 2:
                failure_detail["severity"] = "severe"
            elif any("critique" in commentaire or "danger" in commentaire for word in [commentaire]):
                failure_detail["severity"] = "severe"
            
            analysis["detailed_analysis"].append(failure_detail)
        
        # Générer des recommandations
        analysis["recommendations"] = self._generate_failure_recommendations(analysis)
        
        return analysis
    
    def get_performance_summary(self, simulations: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un résumé complet des performances.
        
        Args:
            simulations: Liste des simulations
            metrics: Métriques calculées
            
        Returns:
            Dict avec le résumé complet des performances
        """
        ship_analysis = self.analyze_ship_performance(simulations, metrics)
        maneuver_analysis = self.analyze_maneuver_performance(simulations, metrics)
        trends = self.identify_performance_trends(simulations, metrics)
        
        echecs = [s for s in simulations if s.get("resultat") == "Échec"]
        failure_analysis = self.analyze_failure_causes(echecs)
        
        summary = {
            "overall_performance": {
                "success_rate": metrics["taux_reussite"],
                "total_tests": metrics["nb_essais"],
                "level": self._assess_performance_level(metrics["taux_reussite"]),
                "grade": self._calculate_performance_grade(metrics["taux_reussite"])
            },
            "ship_performance": ship_analysis,
            "maneuver_performance": maneuver_analysis,
            "failure_analysis": failure_analysis,
            "trends": trends,
            "key_insights": self._extract_key_insights(ship_analysis, maneuver_analysis, failure_analysis),
            "action_items": self._generate_action_items(ship_analysis, maneuver_analysis, failure_analysis)
        }
        
        return summary
    
    def _assess_performance_level(self, success_rate: float) -> str:
        """Évalue le niveau de performance."""
        if success_rate >= 0.8:
            return "excellent"
        elif success_rate >= 0.6:
            return "satisfaisant"
        elif success_rate >= 0.4:
            return "moyen"
        else:
            return "critique"
    
    def _get_performance_icon(self, success_rate: float) -> str:
        """Retourne l'icône appropriée selon le taux de réussite."""
        if success_rate >= 0.8:
            return "🟢"
        elif success_rate >= 0.6:
            return "🟡"
        else:
            return "🔴"
    
    def _assess_maneuver_complexity(self, maneuver: str, success_rate: float, total_tests: int) -> str:
        """Évalue la complexité d'une manœuvre."""
        # Manœuvres connues pour être complexes
        complex_maneuvers = ["evitage", "urgence", "vent contraire", "marée adverse"]
        
        # Critères de complexité
        is_complex_name = any(keyword in maneuver.lower() for keyword in complex_maneuvers)
        low_success_rate = success_rate < 0.7
        sufficient_tests = total_tests >= 3
        
        if is_complex_name or (low_success_rate and sufficient_tests):
            return "complexe"
        elif success_rate > 0.9:
            return "simple"
        else:
            return "modérée"
    
    def _analyze_maneuver_complexity(self, performance_levels: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyse la complexité des manœuvres."""
        complexity_analysis = {
            "simple": [],
            "modérée": [],
            "complexe": []
        }
        
        for maneuver, stats in performance_levels.items():
            complexity = stats["complexity"]
            complexity_analysis[complexity].append({
                "name": maneuver,
                "success_rate": stats["success_rate"],
                "total_tests": stats["total_tests"]
            })
        
        return complexity_analysis
    
    def _generate_ship_recommendations(self, ship_analysis: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur l'analyse des navires."""
        recommendations = []
        
        if ship_analysis["worst_ship"]:
            worst_rate = ship_analysis["worst_ship"]["success_rate"]
            worst_name = ship_analysis["worst_ship"]["name"]
            
            if worst_rate < 0.5:
                recommendations.append(f"Réviser les procédures de manœuvre pour {worst_name}")
                recommendations.append(f"Formations supplémentaires requises pour {worst_name}")
            elif worst_rate < 0.7:
                recommendations.append(f"Optimiser les configurations de remorqueurs pour {worst_name}")
        
        # Recommandations générales
        performance_levels = ship_analysis["performance_levels"]
        critical_ships = [name for name, stats in performance_levels.items() 
                         if stats["success_rate"] < 0.6]
        
        if len(critical_ships) > 1:
            recommendations.append("Analyser les facteurs communs aux navires en difficulté")
        
        return recommendations
    
    def _generate_maneuver_recommendations(self, maneuver_analysis: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur l'analyse des manœuvres."""
        recommendations = []
        
        complexity_analysis = maneuver_analysis["complexity_analysis"]
        
        if complexity_analysis["complexe"]:
            complex_maneuvers = complexity_analysis["complexe"]
            for maneuver in complex_maneuvers:
                if maneuver["success_rate"] < 0.6:
                    recommendations.append(f"Développer des procédures spécifiques pour {maneuver['name']}")
        
        if maneuver_analysis["worst_maneuver"]:
            worst_rate = maneuver_analysis["worst_maneuver"]["success_rate"]
            if worst_rate < 0.5:
                recommendations.append("Réviser les protocoles de sécurité pour les manœuvres critiques")
        
        return recommendations
    
    def _generate_failure_recommendations(self, failure_analysis: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur l'analyse des échecs."""
        recommendations = []
        
        main_causes = failure_analysis["main_causes"]
        environmental_factors = failure_analysis["environmental_factors"]
        technical_factors = failure_analysis["technical_factors"]
        
        # Recommandations environnementales
        if environmental_factors:
            most_common_env = max(environmental_factors.items(), key=lambda x: x[1])
            if most_common_env[1] >= 3:
                if "Vent fort" in most_common_env[0]:
                    recommendations.append("Établir des seuils d'interdiction de manœuvre par vent fort")
                elif "Houle importante" in most_common_env[0]:
                    recommendations.append("Revoir les critères d'acceptabilité de la houle")
        
        # Recommandations techniques
        if technical_factors:
            recommendations.append("Améliorer la maintenance préventive des équipements")
            recommendations.append("Mettre en place des procédures de secours")
        
        # Recommandations générales
        if failure_analysis["total_failures"] > len(main_causes) * 2:
            recommendations.append("Analyser les facteurs non identifiés automatiquement")
        
        return recommendations
    
    def _extract_key_insights(self, ship_analysis: Dict, maneuver_analysis: Dict, failure_analysis: Dict) -> List[str]:
        """Extrait les insights clés de toutes les analyses."""
        insights = []
        
        # Insights sur les navires
        if ship_analysis["best_ship"] and ship_analysis["worst_ship"]:
            best_rate = ship_analysis["best_ship"]["success_rate"] * 100
            worst_rate = ship_analysis["worst_ship"]["success_rate"] * 100
            gap = best_rate - worst_rate
            
            if gap > 30:
                insights.append(f"Écart de performance significatif entre navires ({gap:.1f}%)")
        
        # Insights sur les manœuvres
        if maneuver_analysis["complexity_analysis"]:
            complex_count = len(maneuver_analysis["complexity_analysis"]["complexe"])
            if complex_count > 0:
                insights.append(f"{complex_count} manœuvre(s) identifiée(s) comme complexe(s)")
        
        # Insights sur les échecs
        if failure_analysis["environmental_factors"]:
            env_failures = sum(failure_analysis["environmental_factors"].values())
            total_failures = failure_analysis["total_failures"]
            if total_failures > 0:
                env_percentage = (env_failures / total_failures) * 100
                if env_percentage > 60:
                    insights.append(f"Facteurs environnementaux dominent les échecs ({env_percentage:.1f}%)")
        
        return insights
    
    def _generate_action_items(self, ship_analysis: Dict, maneuver_analysis: Dict, failure_analysis: Dict) -> List[Dict[str, str]]:
        """Génère des actions prioritaires."""
        actions = []
        
        # Actions prioritaires basées sur les analyses
        if ship_analysis["worst_ship"] and ship_analysis["worst_ship"]["success_rate"] < 0.5:
            actions.append({
                "priority": "high",
                "category": "training",
                "action": f"Formation urgente requise pour {ship_analysis['worst_ship']['name']}",
                "timeline": "immédiat"
            })
        
        if failure_analysis["technical_factors"]:
            actions.append({
                "priority": "medium",
                "category": "maintenance",
                "action": "Audit des équipements techniques",
                "timeline": "1 mois"
            })
        
        if maneuver_analysis["complexity_analysis"]["complexe"]:
            actions.append({
                "priority": "medium",
                "category": "procedures",
                "action": "Développement de procédures pour manœuvres complexes",
                "timeline": "3 mois"
            })
        
        return actions
    
    def _calculate_performance_grade(self, success_rate: float) -> str:
        """Calcule une note de performance."""
        if success_rate >= 0.9:
            return "A+"
        elif success_rate >= 0.8:
            return "A"
        elif success_rate >= 0.7:
            return "B"
        elif success_rate >= 0.6:
            return "C"
        elif success_rate >= 0.5:
            return "D"
        else:
            return "F"
