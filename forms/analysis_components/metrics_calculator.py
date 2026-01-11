# =============================================================================
# forms/analysis_components/metrics_calculator.py
# Calculateur de métriques pour les simulations de manœuvrabilité
# =============================================================================

from typing import Dict, Any, List
from collections import Counter


class MetricsCalculator:
    """
    Calculateur de métriques des simulations de manœuvrabilité.
    
    Responsabilités :
    - Calculs de base (taux de réussite, échecs, etc.)
    - Métriques par navire et par manœuvre
    - Analyse des conditions environnementales
    - Identification des conditions critiques
    """
    
    def calculate_basic_metrics(self, simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule les métriques de base des simulations.
        
        Args:
            simulations: Liste des simulations à analyser
            
        Returns:
            Dict contenant les métriques de base
        """
        if not simulations:
            return self._get_empty_metrics()
        
        # Comptages de base
        nb_essais = len(simulations)
        nb_reussis = sum(1 for sim in simulations if sim.get("resultat") == "Réussite")
        nb_echecs = sum(1 for sim in simulations if sim.get("resultat") == "Échec")
        nb_non_definis = sum(1 for sim in simulations if sim.get("resultat") == "Non défini")
        nb_urgences = sum(1 for sim in simulations if sim.get("is_emergency_scenario", False))
        
        # Taux
        taux_reussite = nb_reussis / nb_essais if nb_essais > 0 else 0.0
        taux_echec = nb_echecs / nb_essais if nb_essais > 0 else 0.0
        
        # Analyses par catégorie
        simulations_par_navire = self.calculate_performance_by_ship(simulations)
        simulations_par_manoeuvre = self.calculate_performance_by_maneuver(simulations)
        conditions_frequentes = self._analyze_frequent_conditions(simulations)
        
        return {
            "nb_essais": nb_essais,
            "nb_reussis": nb_reussis,
            "nb_echecs": nb_echecs,
            "nb_non_definis": nb_non_definis,
            "nb_urgences": nb_urgences,
            "taux_reussite": taux_reussite,
            "taux_echec": taux_echec,
            "simulations_par_navire": simulations_par_navire,
            "simulations_par_manoeuvre": simulations_par_manoeuvre,
            "conditions_frequentes": conditions_frequentes
        }
    
    def calculate_performance_by_ship(self, simulations: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """
        Calcule les performances par type de navire.
        
        Args:
            simulations: Liste des simulations
            
        Returns:
            Dict avec les stats par navire {navire: {total, reussies, echecs}}
        """
        simulations_par_navire = {}
        
        for sim in simulations:
            navire = sim.get("navire", "Non spécifié")
            
            if navire not in simulations_par_navire:
                simulations_par_navire[navire] = {"total": 0, "reussies": 0, "echecs": 0}
            
            simulations_par_navire[navire]["total"] += 1
            
            resultat = sim.get("resultat")
            if resultat == "Réussite":
                simulations_par_navire[navire]["reussies"] += 1
            elif resultat == "Échec":
                simulations_par_navire[navire]["echecs"] += 1
        
        return simulations_par_navire
    
    def calculate_performance_by_maneuver(self, simulations: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """
        Calcule les performances par type de manœuvre.
        
        Args:
            simulations: Liste des simulations
            
        Returns:
            Dict avec les stats par manœuvre {manoeuvre: {total, reussies, echecs}}
        """
        simulations_par_manoeuvre = {}
        
        for sim in simulations:
            manoeuvre = sim.get("manoeuvre", "Non spécifiée")
            
            if manoeuvre not in simulations_par_manoeuvre:
                simulations_par_manoeuvre[manoeuvre] = {"total": 0, "reussies": 0, "echecs": 0}
            
            simulations_par_manoeuvre[manoeuvre]["total"] += 1
            
            resultat = sim.get("resultat")
            if resultat == "Réussite":
                simulations_par_manoeuvre[manoeuvre]["reussies"] += 1
            elif resultat == "Échec":
                simulations_par_manoeuvre[manoeuvre]["echecs"] += 1
        
        return simulations_par_manoeuvre
    
    def analyze_environmental_conditions(self, simulations: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Analyse détaillée des conditions environnementales.
        
        Args:
            simulations: Liste des simulations
            
        Returns:
            Dict organisé par type de condition {vent: {condition: {total, echecs}}}
        """
        conditions_analysis = {
            "vent": {},
            "houle": {},
            "courant": {},
            "maree": {}
        }
        
        for sim in simulations:
            conditions_env = sim.get("conditions_env", {})
            resultat = sim.get("resultat")
            
            for condition_type in ["vent", "houle", "courant", "maree"]:
                condition_value = conditions_env.get(condition_type, "")
                
                if condition_value and condition_value.strip():
                    if condition_value not in conditions_analysis[condition_type]:
                        conditions_analysis[condition_type][condition_value] = {"total": 0, "echecs": 0}
                    
                    conditions_analysis[condition_type][condition_value]["total"] += 1
                    
                    if resultat == "Échec":
                        conditions_analysis[condition_type][condition_value]["echecs"] += 1
        
        return conditions_analysis
    
    def identify_critical_conditions(self, simulations: List[Dict[str, Any]], threshold: float = 0.3) -> Dict[str, Dict[str, int]]:
        """
        Identifie les conditions environnementales critiques.
        
        Args:
            simulations: Liste des simulations
            threshold: Seuil de taux d'échec pour considérer une condition comme critique
            
        Returns:
            Dict des conditions critiques avec leurs statistiques
        """
        conditions_analysis = {}
        
        for sim in simulations:
            conditions_env = sim.get("conditions_env", {})
            resultat = sim.get("resultat")
            
            for condition_type, condition_value in conditions_env.items():
                if condition_value and condition_value.strip():
                    key = f"{condition_type}: {condition_value}"
                    
                    if key not in conditions_analysis:
                        conditions_analysis[key] = {"total": 0, "echecs": 0}
                    
                    conditions_analysis[key]["total"] += 1
                    if resultat == "Échec":
                        conditions_analysis[key]["echecs"] += 1
        
        # Filtrer pour ne garder que les conditions critiques
        critical_conditions = {}
        for condition, stats in conditions_analysis.items():
            if stats["total"] >= 2:  # Au moins 2 occurrences
                taux_echec = stats["echecs"] / stats["total"]
                if taux_echec > threshold:  # Au-dessus du seuil
                    critical_conditions[condition] = stats
        
        return critical_conditions
    
    def calculate_success_rate_by_category(self, simulations: List[Dict[str, Any]], category_field: str) -> Dict[str, float]:
        """
        Calcule le taux de réussite par catégorie donnée.
        
        Args:
            simulations: Liste des simulations
            category_field: Champ à utiliser pour la catégorisation
            
        Returns:
            Dict avec les taux de réussite par catégorie
        """
        categories = {}
        
        for sim in simulations:
            category = sim.get(category_field, "Non spécifié")
            
            if category not in categories:
                categories[category] = {"total": 0, "reussites": 0}
            
            categories[category]["total"] += 1
            if sim.get("resultat") == "Réussite":
                categories[category]["reussites"] += 1
        
        # Calculer les taux de réussite
        success_rates = {}
        for category, stats in categories.items():
            if stats["total"] > 0:
                success_rates[category] = stats["reussites"] / stats["total"]
            else:
                success_rates[category] = 0.0
        
        return success_rates
    
    def get_most_frequent_conditions(self, simulations: List[Dict[str, Any]], top_n: int = 5) -> Dict[str, List[tuple]]:
        """
        Obtient les conditions les plus fréquemment testées.
        
        Args:
            simulations: Liste des simulations
            top_n: Nombre de conditions à retourner par type
            
        Returns:
            Dict avec les top conditions par type {type: [(condition, count)]}
        """
        condition_types = ["vent", "houle", "courant", "maree"]
        most_frequent = {}
        
        for condition_type in condition_types:
            conditions = []
            
            for sim in simulations:
                conditions_env = sim.get("conditions_env", {})
                condition_value = conditions_env.get(condition_type, "")
                
                if condition_value and condition_value.strip():
                    conditions.append(condition_value)
            
            # Compter et trier
            if conditions:
                counter = Counter(conditions)
                most_frequent[condition_type] = counter.most_common(top_n)
            else:
                most_frequent[condition_type] = []
        
        return most_frequent
    
    def calculate_time_and_distance_metrics(self, simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule les métriques de temps et distance si disponibles.
        
        Args:
            simulations: Liste des simulations
            
        Returns:
            Dict avec les métriques de temps/distance
        """
        metrics = {
            "has_time_data": False,
            "has_distance_data": False,
            "average_duration": None,
            "average_distance": None,
            "min_duration": None,
            "max_duration": None,
            "min_distance": None,
            "max_distance": None
        }
        
        # Extraire les données de temps et distance si disponibles
        durations = []
        distances = []
        
        for sim in simulations:
            # Chercher dans différents champs possibles
            duration = sim.get("duree") or sim.get("temps") or sim.get("duration")
            distance = sim.get("distance") or sim.get("distance_parcourue")
            
            if duration and isinstance(duration, (int, float)):
                durations.append(duration)
            
            if distance and isinstance(distance, (int, float)):
                distances.append(distance)
        
        # Calculer les métriques de temps
        if durations:
            metrics["has_time_data"] = True
            metrics["average_duration"] = sum(durations) / len(durations)
            metrics["min_duration"] = min(durations)
            metrics["max_duration"] = max(durations)
        
        # Calculer les métriques de distance
        if distances:
            metrics["has_distance_data"] = True
            metrics["average_distance"] = sum(distances) / len(distances)
            metrics["min_distance"] = min(distances)
            metrics["max_distance"] = max(distances)
        
        return metrics
    
    def _analyze_frequent_conditions(self, simulations: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """
        Analyse les conditions environnementales fréquentes.
        
        Args:
            simulations: Liste des simulations
            
        Returns:
            Dict des conditions fréquentes par type
        """
        conditions_frequentes = {"vent": {}, "houle": {}, "courant": {}, "maree": {}}
        
        for sim in simulations:
            conditions_env = sim.get("conditions_env", {})
            
            for condition_type in ["vent", "houle", "courant", "maree"]:
                condition_value = conditions_env.get(condition_type, "")
                
                if condition_value and condition_value != "":
                    if condition_value not in conditions_frequentes[condition_type]:
                        conditions_frequentes[condition_type][condition_value] = 0
                    conditions_frequentes[condition_type][condition_value] += 1
        
        return conditions_frequentes
    
    def _get_empty_metrics(self) -> Dict[str, Any]:
        """
        Retourne des métriques vides pour le cas où il n'y a pas de simulations.
        
        Returns:
            Dict avec des métriques vides
        """
        return {
            "nb_essais": 0,
            "nb_reussis": 0,
            "nb_echecs": 0,
            "nb_non_definis": 0,
            "nb_urgences": 0,
            "taux_reussite": 0.0,
            "taux_echec": 0.0,
            "simulations_par_navire": {},
            "simulations_par_manoeuvre": {},
            "conditions_frequentes": {}
        }
    
    def get_performance_summary(self, simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Obtient un résumé complet des performances.
        
        Args:
            simulations: Liste des simulations
            
        Returns:
            Dict avec un résumé complet des métriques
        """
        basic_metrics = self.calculate_basic_metrics(simulations)
        critical_conditions = self.identify_critical_conditions(simulations)
        time_distance_metrics = self.calculate_time_and_distance_metrics(simulations)
        
        # Analyser les tendances de performance
        best_ship = None
        worst_ship = None
        
        if basic_metrics["simulations_par_navire"]:
            ships_performance = {}
            
            for ship, stats in basic_metrics["simulations_par_navire"].items():
                if stats["total"] > 0:
                    success_rate = stats["reussies"] / stats["total"]
                    ships_performance[ship] = success_rate
            
            if ships_performance:
                best_ship = max(ships_performance, key=ships_performance.get)
                worst_ship = min(ships_performance, key=ships_performance.get)
        
        return {
            **basic_metrics,
            "critical_conditions": critical_conditions,
            "time_distance_metrics": time_distance_metrics,
            "best_performing_ship": best_ship,
            "worst_performing_ship": worst_ship,
            "has_critical_conditions": len(critical_conditions) > 0,
            "overall_performance_level": self._assess_overall_performance(basic_metrics["taux_reussite"])
        }
    
    def _assess_overall_performance(self, success_rate: float) -> str:
        """
        Évalue le niveau de performance global.
        
        Args:
            success_rate: Taux de réussite global
            
        Returns:
            Niveau de performance (excellent, satisfaisant, critique)
        """
        if success_rate >= 0.8:
            return "excellent"
        elif success_rate >= 0.6:
            return "satisfaisant"
        else:
            return "critique"
