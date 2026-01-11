import streamlit as st
from typing import Dict, Any, List


class AnalysisRenderer:
    """
    Gestionnaire de rendu pour les analyses de manœuvrabilité.
    
    Responsabilités :
    - Rendu des métriques et statistiques
    - Affichage des analyses de performance
    - Rendu des scénarios d'urgence
    - Visualisation des conditions critiques
    - Génération des tableaux de bord
    """
    
    def __init__(self):
        """Initialise le gestionnaire de rendu."""
        pass
    
    def render_metrics_display(self, metrics: Dict[str, Any]) -> None:
        """
        Affiche les métriques principales.
        
        Args:
            metrics: Dict contenant les métriques calculées
        """        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Nombre d'essais", metrics["nb_essais"])
            
        with col2:
            st.metric("Essais réussis", metrics["nb_reussis"])
                
        with col3:
            success_rate = metrics['taux_reussite']
            st.metric("Taux de réussite", f"{success_rate:.1%}")
                
        with col4:
            st.metric("Scénarios d'urgence", metrics["nb_urgences"])
        
        # Indicateur de performance global
        self._render_performance_indicator(success_rate)
    
    def render_performance_analysis(self, ship_analysis: Dict[str, Any], maneuver_analysis: Dict[str, Any], trends: List[str]) -> None:
        """
        Rend l'analyse des performances.
        
        Args:
            ship_analysis: Analyse des performances par navire
            maneuver_analysis: Analyse des performances par manœuvre
            trends: Liste des tendances identifiées
        """        
        # Onglets pour organiser l'analyse
        tab1, tab2, tab3 = st.tabs(["🚢 Par navire", "🔄 Par manœuvre", "📊 Tendances"])
        
        with tab1:
            self._render_ship_performance(ship_analysis)
        
        with tab2:
            self._render_maneuver_performance(maneuver_analysis)
        
        with tab3:
            self._render_performance_trends(trends, ship_analysis, maneuver_analysis)
    
    def render_failure_analysis(self, failure_analysis: Dict[str, Any], echecs: List[Dict[str, Any]]) -> None:
        """
        Rend l'analyse des échecs.
        
        Args:
            failure_analysis: Analyse détaillée des échecs
            echecs: Liste des simulations échouées
        """
        if failure_analysis["total_failures"] == 0:
            st.success("✅ Aucun échec identifié dans les simulations")
            return
                
        # Vue d'ensemble des échecs
        self._render_failure_overview(failure_analysis)
        
        # Analyse détaillée par catégorie
        with st.expander("🔍 Analyse détaillée des causes", expanded=True):
            self._render_failure_categories(failure_analysis)
        
        # Échecs critiques
        if failure_analysis["detailed_analysis"]:
            self._render_critical_failures(failure_analysis["detailed_analysis"])
        
        # Recommandations
        if failure_analysis["recommendations"]:
            self._render_failure_recommendations(failure_analysis["recommendations"])
    
    def render_emergency_analysis(self, emergency_analysis: Dict[str, Any]) -> None:
        """
        Rend l'analyse des scénarios d'urgence.
        
        Args:
            emergency_analysis: Analyse complète des scénarios d'urgence
        """
        basic_stats = emergency_analysis["basic_stats"]
        
        if basic_stats["total"] == 0:
            self._render_no_emergency_scenarios()
            return
                
        # Vue d'ensemble
        self._render_emergency_overview(basic_stats)
        
        # Matrice de criticité
        if emergency_analysis["criticality_matrix"]:
            self._render_criticality_matrix(emergency_analysis["criticality_matrix"])
        
        # Analyse par type
        if emergency_analysis["classified_scenarios"]:
            self._render_emergency_types_analysis(emergency_analysis["classified_scenarios"], emergency_analysis["type_analysis"])
        
        # Facteurs de risque
        if any(emergency_analysis["risk_factors"].values()):
            self._render_risk_factors(emergency_analysis["risk_factors"])
        
        # Leçons apprises et recommandations
        col1, col2 = st.columns(2)
        with col1:
            self._render_emergency_lessons(emergency_analysis["lessons_learned"])
        with col2:
            self._render_emergency_recommendations(emergency_analysis["recommendations"])
    
    def render_environmental_conditions(self, conditions_analysis: Dict[str, Dict[str, Dict[str, int]]]) -> None:
        """
        Rend l'analyse des conditions environnementales.
        
        Args:
            conditions_analysis: Analyse des conditions par type
        """        
        condition_types = ["vent", "houle", "courant", "maree"]
        
        for i, condition_type in enumerate(condition_types):
            if condition_type in conditions_analysis and conditions_analysis[condition_type]:
                st.write(f"**{condition_type.title()}**")
                
                conditions_data = conditions_analysis[condition_type]
                
                # Créer une liste triée des conditions
                condition_list = []
                for condition, stats in conditions_data.items():
                    if stats["total"] >= 2:  # Au moins 2 occurrences
                        failure_rate = (stats["echecs"] / stats["total"]) * 100
                        condition_list.append({
                            "condition": condition,
                            "total": stats["total"],
                            "failures": stats["echecs"],
                            "failure_rate": failure_rate,
                            "criticality": self._assess_condition_criticality(failure_rate)
                        })
                
                if condition_list:
                    # Trier par taux d'échec décroissant
                    condition_list.sort(key=lambda x: x["failure_rate"], reverse=True)
                    
                    # Afficher les conditions les plus critiques
                    for cond in condition_list[:5]:  # Top 5
                        self._render_condition_item(cond)
                
                if i < len(condition_types) - 1:
                    st.write("---")
    
    def render_detailed_distribution(self, simulations: List[Dict[str, Any]], frequent_conditions: Dict[str, List[tuple]]) -> None:
        """
        Rend la répartition détaillée des simulations.
        
        Args:
            simulations: Liste des simulations
            frequent_conditions: Conditions les plus fréquentes par type
        """        
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_load_state_distribution(simulations)
            self._render_tugboat_configuration(simulations)
        
        with col2:
            self._render_frequent_conditions(frequent_conditions, simulations)
            self._render_berth_distribution(simulations)
    
    def render_content_analysis(self, text: str) -> None:
        """
        Rend l'analyse du contenu textuel.
        
        Args:
            text: Texte à analyser
        """
        if not text:
            st.info("Aucun contenu à analyser")
            return
        
        # Analyse de base
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        words = text.split()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📊 Structure du texte**")
            st.metric("Phrases", len(sentences))
            if sentences:
                st.metric("Caractères/phrase", round(len(text) / len(sentences)))
                st.metric("Mots/phrase", round(len(words) / len(sentences)))
        
        with col2:
            st.write("**🏷️ Analyse terminologique**")
            technical_terms = [
                'manœuvrabilité', 'navires', 'remorqueurs', 'simulations', 
                'conditions', 'critiques', 'faisabilité', 'taux'
            ]
            
            found_terms = sum(1 for term in technical_terms if term.lower() in text.lower())
            st.metric("Termes techniques", f"{found_terms}/{len(technical_terms)}")
            
            # Afficher les termes trouvés
            detected_terms = [term for term in technical_terms if term.lower() in text.lower()]
            if detected_terms:
                st.write("**Termes détectés:**")
                st.write(", ".join(detected_terms))
        
        # Analyse de qualité
        self._render_text_quality_analysis(text, sentences, words)
    
    def render_dashboard_summary(self, metrics: Dict[str, Any], ship_analysis: Dict[str, Any], emergency_stats: Dict[str, Any]) -> None:
        """
        Rend un tableau de bord résumé.
        
        Args:
            metrics: Métriques principales
            ship_analysis: Analyse des navires
            emergency_stats: Statistiques d'urgence
        """
        st.subheader("🎯 Tableau de bord exécutif", divider=True)
        
        # KPIs principaux
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            success_rate = metrics["taux_reussite"]
            delta_color = "normal" if success_rate >= 0.8 else "inverse"
            st.metric(
                "Performance globale", 
                f"{success_rate:.1%}",
                delta=self._calculate_performance_delta(success_rate),
                delta_color=delta_color
            )
        
        with col2:
            st.metric("Tests réalisés", metrics["nb_essais"])
        
        with col3:
            if ship_analysis.get("best_ship"):
                best_rate = ship_analysis["best_ship"]["success_rate"]
                st.metric("Meilleur navire", f"{best_rate:.1%}")
            else:
                st.metric("Meilleur navire", "N/A")
        
        with col4:
            emergency_rate = emergency_stats.get("emergency_rate", 0)
            st.metric("Taux d'urgence", f"{emergency_rate:.1%}")
        
        with col5:
            grade = self._calculate_overall_grade(success_rate)
            st.metric("Note globale", grade)
        
        # Alertes et recommandations prioritaires
        self._render_priority_alerts(metrics, ship_analysis, emergency_stats)
    
    def _render_performance_indicator(self, success_rate: float) -> None:
        """Affiche l'indicateur de performance global."""
        if success_rate >= 0.8:
            st.success(f"🟢 Performance excellente ({success_rate:.1%})")
        elif success_rate >= 0.6:
            st.info(f"🟡 Performance satisfaisante ({success_rate:.1%})")
        else:
            st.error(f"🔴 Performance nécessitant des améliorations ({success_rate:.1%})")
    
    def _render_ship_performance(self, ship_analysis: Dict[str, Any]) -> None:
        """Rend l'analyse des performances par navire."""
        if not ship_analysis.get("performance_levels"):
            st.info("Aucune donnée de performance par navire disponible")
            return
        
        st.write("**🚢 Performance par type de navire**")
        
        # Tri par taux de réussite décroissant
        sorted_ships = sorted(
            ship_analysis["performance_levels"].items(),
            key=lambda x: x[1]["success_rate"],
            reverse=True
        )
        
        for navire, stats in sorted_ships:
            success_rate = stats["success_rate"] * 100
            icon = stats["icon"]
            level = stats["level"]
            
            display_name = navire.replace('Porte-conteneurs Type ', '')
            
            col1, col2, col3 = st.columns([3, 1, 2])
            with col1:
                st.write(f"{icon} **{display_name}**")
            with col2:
                st.write(f"{stats['successes']}/{stats['total_tests']}")
            with col3:
                st.progress(success_rate / 100, text=f"{success_rate:.1f}% - {level}")
        
        # Recommandations si disponibles
        if ship_analysis.get("recommendations"):
            st.write("**💡 Recommandations:**")
            for rec in ship_analysis["recommendations"]:
                st.warning(f"⚠️ {rec}")
    
    def _render_maneuver_performance(self, maneuver_analysis: Dict[str, Any]) -> None:
        """Rend l'analyse des performances par manœuvre."""
        if not maneuver_analysis.get("performance_levels"):
            st.info("Aucune donnée de performance par manœuvre disponible")
            return
        
        st.write("**🔄 Performance par type de manœuvre**")
        
        # Tri par taux de réussite décroissant
        sorted_maneuvers = sorted(
            maneuver_analysis["performance_levels"].items(),
            key=lambda x: x[1]["success_rate"],
            reverse=True
        )
        
        for manoeuvre, stats in sorted_maneuvers:
            success_rate = stats["success_rate"] * 100
            icon = stats["icon"]
            complexity = stats["complexity"]
            
            col1, col2, col3 = st.columns([3, 1, 2])
            with col1:
                st.write(f"{icon} **{manoeuvre}**")
            with col2:
                st.write(f"{stats['successes']}/{stats['total_tests']}")
            with col3:
                st.progress(success_rate / 100, text=f"{success_rate:.1f}% - {complexity}")
        
        # Analyse de complexité
        if maneuver_analysis.get("complexity_analysis"):
            with st.expander("🔍 Analyse de complexité"):
                complexity_analysis = maneuver_analysis["complexity_analysis"]
                
                for complexity_level, maneuvers in complexity_analysis.items():
                    if maneuvers:
                        st.write(f"**Manœuvres {complexity_level}s:**")
                        for maneuver in maneuvers:
                            st.write(f"• {maneuver['name']}: {maneuver['success_rate']:.1%}")
    
    def _render_performance_trends(self, trends: List[str], ship_analysis: Dict[str, Any], maneuver_analysis: Dict[str, Any]) -> None:
        """Rend les tendances de performance."""
        st.write("**📊 Tendances identifiées**")
        
        if trends:
            for trend in trends:
                st.info(f"💡 {trend}")
        else:
            st.info("Aucune tendance particulière identifiée")
        
        # Résumé des meilleures et pires performances
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🏆 Meilleures performances**")
            if ship_analysis.get("best_ship"):
                best_ship = ship_analysis["best_ship"]
                st.metric(
                    "Navire",
                    best_ship["name"].replace('Porte-conteneurs Type ', ''),
                    f"{best_ship['success_rate']:.1%}"
                )
            
            if maneuver_analysis.get("best_maneuver"):
                best_maneuver = maneuver_analysis["best_maneuver"]
                st.metric(
                    "Manœuvre",
                    best_maneuver["name"],
                    f"{best_maneuver['success_rate']:.1%}"
                )
        
        with col2:
            st.write("**⚠️ Points d'attention**")
            if ship_analysis.get("worst_ship"):
                worst_ship = ship_analysis["worst_ship"]
                if worst_ship["success_rate"] < 0.7:
                    st.metric(
                        "Navire à améliorer",
                        worst_ship["name"].replace('Porte-conteneurs Type ', ''),
                        f"{worst_ship['success_rate']:.1%}"
                    )
            
            if maneuver_analysis.get("worst_maneuver"):
                worst_maneuver = maneuver_analysis["worst_maneuver"]
                if worst_maneuver["success_rate"] < 0.7:
                    st.metric(
                        "Manœuvre difficile",
                        worst_maneuver["name"],
                        f"{worst_maneuver['success_rate']:.1%}"
                    )
    
    def _render_failure_overview(self, failure_analysis: Dict[str, Any]) -> None:
        """Rend la vue d'ensemble des échecs."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total échecs", failure_analysis["total_failures"])
        
        with col2:
            env_count = sum(failure_analysis["environmental_factors"].values())
            st.metric("Facteurs env.", env_count)
        
        with col3:
            tech_count = sum(failure_analysis["technical_factors"].values())
            st.metric("Facteurs tech.", tech_count)
        
        with col4:
            op_count = sum(failure_analysis["operational_factors"].values())
            st.metric("Facteurs op.", op_count)
    
    def _render_failure_categories(self, failure_analysis: Dict[str, Any]) -> None:
        """Rend l'analyse des échecs par catégorie."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**🌊 Facteurs environnementaux**")
            if failure_analysis["environmental_factors"]:
                for factor, count in failure_analysis["environmental_factors"].items():
                    percentage = (count / failure_analysis["total_failures"]) * 100
                    st.write(f"• {factor}: {count} ({percentage:.1f}%)")
            else:
                st.write("Aucun facteur environnemental identifié")
        
        with col2:
            st.write("**🔧 Facteurs techniques**")
            if failure_analysis["technical_factors"]:
                for factor, count in failure_analysis["technical_factors"].items():
                    percentage = (count / failure_analysis["total_failures"]) * 100
                    st.write(f"• {factor}: {count} ({percentage:.1f}%)")
            else:
                st.write("Aucun facteur technique identifié")
        
        with col3:
            st.write("**⚙️ Facteurs opérationnels**")
            if failure_analysis["operational_factors"]:
                for factor, count in failure_analysis["operational_factors"].items():
                    percentage = (count / failure_analysis["total_failures"]) * 100
                    st.write(f"• {factor}: {count} ({percentage:.1f}%)")
            else:
                st.write("Aucun facteur opérationnel identifié")
    
    def _render_critical_failures(self, detailed_analysis: List[Dict[str, Any]]) -> None:
        """Rend les échecs critiques."""
        severe_failures = [f for f in detailed_analysis if f["severity"] == "severe"]
        
        if not severe_failures:
            return
        
        st.write("**🚨 Échecs critiques**")
        
        for i, failure in enumerate(severe_failures):
            with st.expander(f"Échec critique #{failure['test_id']} - {failure['ship']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Conditions:**")
                    for key, value in failure["conditions"].items():
                        if value:
                            st.write(f"• {key.title()}: {value}")
                
                with col2:
                    st.write("**Causes identifiées:**")
                    for cause in failure["identified_causes"]:
                        st.write(f"• {cause}")
                    
                    st.write(f"**Manœuvre:** {failure['maneuver']}")
                    st.write(f"**Sévérité:** {failure['severity']}")
    
    def _render_failure_recommendations(self, recommendations: List[str]) -> None:
        """Rend les recommandations pour réduire les échecs."""
        st.write("**💡 Recommandations pour réduire les échecs**")
        for recommendation in recommendations:
            st.text(f"⚠️ {recommendation}")
    
    def _render_no_emergency_scenarios(self) -> None:
        """Rend l'affichage quand il n'y a pas de scénarios d'urgence."""
        st.info("✅ Aucun scénario d'urgence identifié dans les simulations")
        
        st.write("**💡 Critères pour identifier les scénarios d'urgence :**")
        criteria = [
            "Panne d'équipement (propulseurs, gouvernail, remorqueurs)",
            "Conditions météorologiques extrêmes",
            "Situations de 'near miss' ou quasi-accidents",
            "Manœuvres d'évitement d'urgence",
            "Défaillances techniques pendant la manœuvre",
            "Problèmes de communication critiques"
        ]
        
        for criterion in criteria:
            st.write(f"• {criterion}")
    
    def _render_emergency_overview(self, basic_stats: Dict[str, Any]) -> None:
        """Rend la vue d'ensemble des scénarios d'urgence."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Scénarios réussis", basic_stats["successes"])
        
        with col2:
            st.metric("Scénarios échoués", basic_stats["failures"])
        
        with col3:
            success_rate = basic_stats["success_rate"] * 100
            st.metric("Taux de réussite", f"{success_rate:.1f}%")
    
    def _render_criticality_matrix(self, criticality_matrix: Dict[str, Dict[str, str]]) -> None:
        """Rend la matrice de criticité."""
        st.write("**🎯 Matrice de criticité par type d'urgence**")
        
        for emergency_type, data in criticality_matrix.items():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"{data['color']} **{emergency_type}**")
            with col2:
                st.write(f"{data['failure_rate']:.1%}")
            with col3:
                st.write(f"{data['total_cases']} cas")
    
    def _render_emergency_types_analysis(self, classified_scenarios: Dict[str, List[Dict[str, Any]]], type_analysis: Dict[str, Dict[str, Any]]) -> None:
        """Rend l'analyse par type de scénario d'urgence."""
        st.write("**📋 Analyse par type de scénario**")
        
        for emergency_type, scenarios in classified_scenarios.items():
            analysis = type_analysis.get(emergency_type, {})
            
            with st.expander(f"🚨 {emergency_type} ({len(scenarios)} scénario(s))", expanded=False):
                if analysis:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Taux de réussite", f"{analysis['success_rate']:.1%}")
                    with col2:
                        st.metric("Sévérité", analysis["severity"])
                    with col3:
                        st.metric("Confiance", f"{analysis['avg_confidence']:.1%}")
                
                # Conditions communes
                if analysis.get("common_conditions"):
                    st.write("**Conditions communes:**")
                    for condition, count in analysis["common_conditions"].items():
                        st.write(f"• {condition}: {count} cas")
    
    def _render_risk_factors(self, risk_factors: Dict[str, Any]) -> None:
        """Rend les facteurs de risque."""
        st.write("**⚠️ Facteurs de risque identifiés**")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🌊 Environnemental", "⚙️ Opérationnel", "🔧 Technique", "👥 Humain"])
        
        categories = [
            (tab1, "environmental", "🌊"),
            (tab2, "operational", "⚙️"),
            (tab3, "technical", "🔧"),
            (tab4, "human", "👥")
        ]
        
        for tab, category, icon in categories:
            with tab:
                factors = risk_factors.get(category, {})
                if factors:
                    for factor, count in sorted(factors.items(), key=lambda x: x[1], reverse=True):
                        st.write(f"{icon} **{factor}**: {count} occurrences")
                else:
                    st.info(f"Aucun facteur de risque {category} identifié")
    
    def _render_emergency_lessons(self, lessons_learned: Dict[str, List[str]]) -> None:
        """Rend les leçons apprises."""
        st.write("**📚 Leçons apprises**")
        
        for lesson_type, lessons in lessons_learned.items():
            if lessons:
                with st.expander(f"📄 {lesson_type}"):
                    for lesson in lessons:
                        st.write(f"• {lesson}")
    
    def _render_emergency_recommendations(self, recommendations: List[Dict[str, str]]) -> None:
        """Rend les recommandations d'urgence."""
        st.write("**🎯 Recommandations prioritaires**")
        
        if not recommendations:
            st.info("Aucune recommandation spécifique générée")
            return
        
        # Grouper par priorité
        priority_groups = {"critical": [], "high": [], "medium": [], "low": []}
        for rec in recommendations:
            priority = rec.get("priority", "medium")
            priority_groups[priority].append(rec)
        
        # Afficher par ordre de priorité
        priority_icons = {"critical": "🔥", "high": "⚠️", "medium": "💡", "low": "ℹ️"}
        
        for priority, recs in priority_groups.items():
            if recs:
                st.write(f"**{priority_icons[priority]} Priorité {priority}:**")
                for rec in recs:
                    with st.expander(f"{rec['title']} ({rec['timeline']})"):
                        st.write(rec['description'])
                        st.caption(f"Catégorie: {rec['category']}")
    
    def _render_condition_item(self, condition: Dict[str, Any]) -> None:
        """Rend un élément de condition critique."""
        col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
        
        with col1:
            st.write(condition["condition"])
        with col2:
            st.write(f"{condition['failures']}/{condition['total']}")
        with col3:
            st.write(f"{condition['failure_rate']:.1f}%")
        with col4:
            criticality_info = condition["criticality"]
            st.write(criticality_info["label"])
    
    def _render_load_state_distribution(self, simulations: List[Dict[str, Any]]) -> None:
        """Rend la répartition par état de charge."""
        st.write("**⚖️ Répartition par état de charge**")
        
        # Calculer la répartition
        load_states = {}
        for sim in simulations:
            state = sim.get("etat_chargement", "Non spécifié")
            if state not in load_states:
                load_states[state] = {"total": 0, "successes": 0}
            load_states[state]["total"] += 1
            if sim.get("resultat") == "Réussite":
                load_states[state]["successes"] += 1
        
        for state, stats in load_states.items():
            if stats["total"] > 0:
                success_rate = (stats["successes"] / stats["total"]) * 100
                st.metric(
                    label=state,
                    value=f"{success_rate:.1f}%",
                    delta=f"{stats['successes']}/{stats['total']}"
                )
    
    def _render_tugboat_configuration(self, simulations: List[Dict[str, Any]]) -> None:
        """Rend la configuration des remorqueurs."""
        st.write("**🚤 Configuration des remorqueurs**")
        
        configs = {}
        for sim in simulations:
            config = sim.get("remorqueurs", "Non spécifié")
            configs[config] = configs.get(config, 0) + 1
        
        for config, count in sorted(configs.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(simulations)) * 100
            st.write(f"• {config}: {count} ({percentage:.1f}%)")
    
    def _render_frequent_conditions(self, frequent_conditions: Dict[str, List[tuple]], simulations: List[Dict[str, Any]]) -> None:
        """Rend les conditions les plus fréquentes."""
        st.write("**📈 Conditions les plus testées**")
        
        for condition_type, conditions in frequent_conditions.items():
            if conditions:
                st.write(f"*{condition_type.title()}:*")
                for condition, count in conditions:
                    percentage = (count / len(simulations)) * 100
                    st.write(f"• {condition}: {count} ({percentage:.1f}%)")
    
    def _render_berth_distribution(self, simulations: List[Dict[str, Any]]) -> None:
        """Rend la répartition par poste d'accostage."""
        st.write("**⚓ Répartition par poste**")
        
        berths = {}
        for sim in simulations:
            berth = sim.get("poste", "Non spécifié")
            berths[berth] = berths.get(berth, 0) + 1
        
        for berth, count in sorted(berths.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(simulations)) * 100
            st.write(f"• {berth}: {count} ({percentage:.1f}%)")
    
    def _render_text_quality_analysis(self, text: str, sentences: List[str], words: List[str]) -> None:
        """Rend l'analyse de qualité du texte."""
        with st.expander("📝 Analyse de qualité du texte"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Analyse de lisibilité
                avg_sentence_length = len(words) / len(sentences) if sentences else 0
                avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
                
                st.write("**📖 Lisibilité**")
                st.metric("Mots/phrase", f"{avg_sentence_length:.1f}")
                st.metric("Caractères/mot", f"{avg_word_length:.1f}")
                
                # Évaluation de complexité
                if avg_sentence_length > 20:
                    st.warning("⚠️ Phrases potentiellement trop longues")
                elif avg_sentence_length < 8:
                    st.info("ℹ️ Phrases courtes - bon pour la lisibilité")
                else:
                    st.success("✅ Longueur de phrases optimale")
            
            with col2:
                # Analyse de densité informationnelle
                unique_words = len(set(word.lower() for word in words))
                density = unique_words / len(words) if words else 0
                
                st.write("**🎯 Densité informationnelle**")
                st.metric("Mots uniques", unique_words)
                st.metric("Densité lexicale", f"{density:.1%}")
                
                if density > 0.7:
                    st.success("✅ Contenu riche et varié")
                elif density > 0.5:
                    st.info("ℹ️ Contenu moyennement varié")
                else:
                    st.warning("⚠️ Vocabulaire limité ou répétitif")
    
    def _render_priority_alerts(self, metrics: Dict[str, Any], ship_analysis: Dict[str, Any], emergency_stats: Dict[str, Any]) -> None:
        """Rend les alertes prioritaires."""
        alerts = []
        
        # Alerte sur performance globale
        if metrics["taux_reussite"] < 0.6:
            alerts.append({
                "level": "error",
                "message": f"Performance globale critique ({metrics['taux_reussite']:.1%})"
            })
        
        # Alerte sur navires problématiques
        if ship_analysis.get("worst_ship") and ship_analysis["worst_ship"]["success_rate"] < 0.5:
            worst_ship = ship_analysis["worst_ship"]["name"].replace('Porte-conteneurs Type ', '')
            alerts.append({
                "level": "warning",
                "message": f"Navire {worst_ship} nécessite une attention particulière ({ship_analysis['worst_ship']['success_rate']:.1%})"
            })
        
        # Alerte sur urgences
        if emergency_stats.get("emergency_rate", 0) > 0.2:
            alerts.append({
                "level": "warning",
                "message": f"Taux élevé de scénarios d'urgence ({emergency_stats['emergency_rate']:.1%})"
            })
        
        # Afficher les alertes
        if alerts:
            st.write("**🚨 Alertes prioritaires**")
            for alert in alerts:
                if alert["level"] == "error":
                    st.error(alert["message"])
                elif alert["level"] == "warning":
                    st.warning(alert["message"])
                else:
                    st.info(alert["message"])
        else:
            st.success("✅ Aucune alerte critique détectée")
    
    def _assess_condition_criticality(self, failure_rate: float) -> Dict[str, str]:
        """Évalue la criticité d'une condition."""
        if failure_rate > 50:
            return {"label": "🔴 Critique", "color": "red"}
        elif failure_rate > 25:
            return {"label": "🟡 Attention", "color": "orange"}
        else:
            return {"label": "🟢 Acceptable", "color": "green"}
    
    def _calculate_performance_delta(self, success_rate: float) -> str:
        """Calcule le delta de performance par rapport à un seuil."""
        target = 0.8  # Seuil cible de 80%
        delta = success_rate - target
        
        if abs(delta) < 0.05:  # Dans les 5% du seuil
            return "Objectif atteint"
        elif delta > 0:
            return f"+{delta:.1%} vs objectif"
        else:
            return f"{delta:.1%} vs objectif"
    
    def _calculate_overall_grade(self, success_rate: float) -> str:
        """Calcule une note globale."""
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
    
    def render_export_summary(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un résumé structuré pour l'export.
        
        Args:
            metrics: Métriques principales
        Returns:
            Dict structuré pour l'export
        """
        export_data = {
            "executive_summary": {
                "total_tests": metrics["nb_essais"],
                "success_rate": metrics["taux_reussite"],
                "grade": self._calculate_overall_grade(metrics["taux_reussite"]),
                "emergency_scenarios": metrics["nb_urgences"]
            },
            "key_findings": [],
            "recommendations": [],
            "performance_by_category": {},
            "risk_assessment": "low"  # low, medium, high, critical
        }
        
        # Évaluation des risques
        if metrics["taux_reussite"] < 0.5:
            export_data["risk_assessment"] = "critical"
        elif metrics["taux_reussite"] < 0.7:
            export_data["risk_assessment"] = "high"
        elif metrics["nb_urgences"] > metrics["nb_essais"] * 0.2:
            export_data["risk_assessment"] = "medium"
        
        # Extraction des principales conclusions
        if metrics["taux_reussite"] >= 0.8:
            export_data["key_findings"].append("Performance globale excellente")
        elif metrics["taux_reussite"] < 0.6:
            export_data["key_findings"].append("Performance globale nécessitant des améliorations")
        
        return export_data
    
    def render_comparison_analysis(self, current_metrics: Dict[str, Any], baseline_metrics: Dict[str, Any] = None) -> None:
        """
        Rend une analyse comparative avec des données de référence.
        
        Args:
            current_metrics: Métriques actuelles
            baseline_metrics: Métriques de référence (optionnel)
        """
        if not baseline_metrics:
            st.info("Aucune donnée de référence disponible pour la comparaison")
            return
        
        st.subheader("📈 Analyse comparative", divider=True)
        
        # Comparaison des métriques principales
        col1, col2, col3 = st.columns(3)
        
        metrics_to_compare = [
            ("taux_reussite", "Taux de réussite", "{:.1%}"),
            ("nb_essais", "Nombre d'essais", "{}"),
            ("nb_urgences", "Scénarios d'urgence", "{}")
        ]
        
        for i, (metric_key, metric_label, format_str) in enumerate(metrics_to_compare):
            current_value = current_metrics.get(metric_key, 0)
            baseline_value = baseline_metrics.get(metric_key, 0)
            
            if baseline_value > 0:
                delta = current_value - baseline_value
                delta_pct = (delta / baseline_value) * 100
                
                with [col1, col2, col3][i]:
                    st.metric(
                        metric_label,
                        format_str.format(current_value),
                        delta=f"{delta_pct:+.1f}%" if metric_key == "taux_reussite" else f"{delta:+.0f}"
                    )
        
        # Analyse des tendances
        self._render_trend_analysis(current_metrics, baseline_metrics)
    
    def _render_trend_analysis(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> None:
        """Rend l'analyse des tendances."""
        st.write("**📊 Analyse des tendances**")
        
        trends = []
        
        # Tendance du taux de réussite
        current_success = current.get("taux_reussite", 0)
        baseline_success = baseline.get("taux_reussite", 0)
        
        if baseline_success > 0:
            success_change = current_success - baseline_success
            if abs(success_change) > 0.05:  # Changement significatif > 5%
                direction = "amélioration" if success_change > 0 else "dégradation"
                trends.append(f"{direction.title()} du taux de réussite: {success_change:+.1%}")
        
        # Tendance du nombre de tests
        current_tests = current.get("nb_essais", 0)
        baseline_tests = baseline.get("nb_essais", 0)
        
        if baseline_tests > 0:
            test_change = current_tests - baseline_tests
            if abs(test_change) >= 5:  # Changement significatif >= 5 tests
                direction = "augmentation" if test_change > 0 else "diminution"
                trends.append(f"{direction.title()} du nombre de tests: {test_change:+}")
        
        # Afficher les tendances
        if trends:
            for trend in trends:
                st.info(f"📈 {trend}")
        else:
            st.info("Aucune tendance significative détectée")
