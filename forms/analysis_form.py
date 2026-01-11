import streamlit as st
from typing import Dict, Any, List
from .base_form import BaseForm
from .analysis_components import (
    MetricsCalculator, 
    PerformanceAnalyzer, 
    EmergencyScenarioAnalyzer,
    AnalysisRenderer
)


class AnalysisForm(BaseForm):
    """
    Formulaire pour l'analyse des résultats de simulation + récapitulatif.
    """
    
    def __init__(self):
        super().__init__("analysis")
        
        # Injection de dépendance - Composants spécialisés
        self.calculator = MetricsCalculator()
        self.performance_analyzer = PerformanceAnalyzer()
        self.emergency_analyzer = EmergencyScenarioAnalyzer()
        self.renderer = AnalysisRenderer()
    
    def render(self, simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Rend le formulaire d'analyse avec les simulations.
        
        Args:
            simulations: Liste des simulations à analyser
            
        Returns:
            Dict avec les données d'analyse complètes
        """
        try:
            self.render_section_header(
                "📈 Statistiques et éléments pour l'analyse", 
                divider=True, 
                help_text="💡 Vous pouvez utiliser les données ci-dessous pour votre analyse"
            )
            
            # 1. CALCULS - Délégués au MetricsCalculator
            metrics = self.calculator.calculate_basic_metrics(simulations)
            
            # 2. MÉTRIQUES PRINCIPALES - RÉDUCTIBLE 📊
            with st.expander("📊 Métriques principales", expanded=True):
                self.renderer.render_metrics_display(metrics)
            
            # 3. ANALYSES AVANCÉES - RÉDUCTIBLE 🔬
            if simulations:
                with st.expander("🔬 Analyses avancées", expanded=False):
                    self._render_advanced_analysis_with_components(simulations, metrics)
            
            # 5. RÉCAPITULATIF - Toujours visible (le plus important)
            recapitulatif_data = self._render_summary_section()
            
            # 4. SAISIE UTILISATEUR - Toujours visible (le plus important)
            analysis_data = self._render_user_inputs(metrics)
            
            # 6. COMBINAISON DES DONNÉES
            complete_data = {
                **analysis_data,
                "recapitulatif_analyse": recapitulatif_data["recapitulatif_text"],
                "recapitulatif_metrics": recapitulatif_data["metrics"]
            }
            
            return complete_data
            
        except Exception as e:
            st.error(f"❌ Erreur dans le formulaire analyse : {str(e)}")
            return self._get_default_analysis()
    
    def _render_advanced_analysis_with_components(self, simulations: List[Dict[str, Any]], metrics: Dict[str, Any]) -> None:
        """
        Rend toutes les analyses avancées en utilisant les composants spécialisés.
        
        Args:
            simulations: Liste des simulations
            metrics: Métriques calculées
        """
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Performance", 
            "❌ Analyse des échecs", 
            "🚨 Scénarios d'urgence", 
            "🌊 Conditions environnementales critiques", 
            "🚢 Répartition détaillée"
        ])
        
        with tab1:
            ship_analysis = self.performance_analyzer.analyze_ship_performance(simulations, metrics)
            maneuver_analysis = self.performance_analyzer.analyze_maneuver_performance(simulations, metrics)
            trends = self.performance_analyzer.identify_performance_trends(simulations, metrics)
            self.renderer.render_performance_analysis(ship_analysis, maneuver_analysis, trends)
        
        with tab2:
            echecs = [s for s in simulations if s.get("resultat") == "Échec"]
            failure_analysis = self.performance_analyzer.analyze_failure_causes(echecs)
            self.renderer.render_failure_analysis(failure_analysis, echecs)
        
        with tab3:
            emergency_analysis = self.emergency_analyzer.analyze_emergency_scenarios(simulations)
            self.renderer.render_emergency_analysis(emergency_analysis)
        
        with tab4:
            conditions_analysis = self.calculator.analyze_environmental_conditions(simulations)
            self.renderer.render_environmental_conditions(conditions_analysis)
        
        with tab5:
            frequent_conditions = self.calculator.get_most_frequent_conditions(simulations, top_n=5) 
            self.renderer.render_detailed_distribution(simulations, frequent_conditions)
    
    def _render_user_inputs(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rend les champs de saisie spécifiques au formulaire.
        
        Cette méthode reste dans le formulaire car elle gère la saisie utilisateur
        spécifique à ce contexte d'analyse.
        
        Args:
            metrics: Métriques calculées
            
        Returns:
            Dict avec les données saisies par l'utilisateur
        """
        objectifs_evaluations_data = self._render_objectives_evaluation()

        st.subheader("✏️ Saisie de données complémentaires", divider=True)

        # Récupérer les valeurs par défaut
        defaults = self.get_defaults()
        
        col1, col2 = st.columns(2)
        with col1:
            # Conditions critiques identifiées
            conditions_critiques = self._render_conditions_critiques_input(defaults)
        with col2:
            # Distances et trajectoires
            distances_trajectoires = st.text_area(
                "🗺️ Distances et trajectoires",
                value=defaults.get("distances_trajectoires", 
                    "Distance parcourue moyenne: 2.8 milles du pilotage à l'accostage. "
                    "Temps moyen de manœuvre: 45 minutes."
                ),
                help="Informations sur les distances parcourues et temps de manœuvre",
                placeholder="Ex: Distance parcourue moyenne: 2.8 milles du pilotage à l'accostage. "
                        "Temps moyen de manœuvre: 45 minutes.",
                height=120
            )
                
        # Construire les données finales
        analysis_data = {
            "nombre_essais": metrics["nb_essais"],
            "taux_reussite": metrics["taux_reussite"],
            "conditions_critiques": conditions_critiques,
            "distances_trajectoires": distances_trajectoires,
            **objectifs_evaluations_data,
            # Ajouter les métriques détaillées pour compatibilité
            "metrics_detaillees": {
                "nb_reussis": metrics["nb_reussis"],
                "nb_echecs": metrics["nb_echecs"],
                "nb_urgences": metrics["nb_urgences"],
                "simulations_par_navire": metrics["simulations_par_navire"],
                "simulations_par_manoeuvre": metrics["simulations_par_manoeuvre"]
            }
        }
        
        return analysis_data
    
    def _render_summary_section(self) -> Dict[str, Any]:
        """
        Rend la section récapitulatif de l'analyse.
        
        Cette méthode reste dans le formulaire car elle gère l'état de session
        et la saisie utilisateur spécifique au récapitulatif.
        
        Returns:
            Dict avec le texte du récapitulatif et ses métriques
        """
        st.subheader("📋 Votre analyse", divider=True)
        
        # Récupérer la valeur existante depuis la session
        rapport_data = st.session_state.get("rapport_data", {})
        current_recapitulatif = (
            rapport_data.get("recapitulatif_analyse", "") or 
            rapport_data.get("conclusion", "")
        )
        
        # Zone de saisie du récapitulatif
        recapitulatif_text = st.text_area(
            "📝 Récapitulatif général de l'analyse",
            value=current_recapitulatif,
            height=120,
            placeholder=(
                "Ex: La présente étude de manœuvrabilité démontre la faisabilité des opérations "
                "portuaires pour les porte-conteneurs ... Le taux de réussite des simulations "
                "confirme que ..."
            ),
            help="Synthèse générale des résultats de votre analyse de manœuvrabilité"
        )
        
        recap_metrics = self._calculate_text_metrics(recapitulatif_text)        
        if recapitulatif_text:
            self._display_text_metrics(recap_metrics)
            
            # Analyse du contenu avec le renderer
            with st.expander("🔍 Analyse du contenu", expanded=False):
                self.renderer.render_content_analysis(recapitulatif_text)
        
        return {
            "recapitulatif_text": recapitulatif_text,
            "metrics": recap_metrics
        }
    
    def _render_conditions_critiques_input(self, defaults: Dict[str, Any]) -> List[str]:
        """
        Rend le champ de saisie des conditions critiques.
        
        Args:
            defaults: Valeurs par défaut
            
        Returns:
            Liste des conditions critiques
        """
        # Récupérer les conditions existantes
        rapport_data = st.session_state.get("rapport_data", {})
        existing_conditions = (
            rapport_data.get("analyse_synthese", {}).get("conditions_critiques", [])
        )
        conditions_text = "\n".join(existing_conditions) if existing_conditions else ""
        
        conditions_input = st.text_area(
            "⚠️ Conditions critiques identifiées",
            value=conditions_text,
            help="Seuils et conditions qui ont rendu les manœuvres difficiles ou impossibles (une condition par ligne)",
            placeholder="Ex:\nVent > 25 nœuds\nMarée basse < 2m\nHoule > 1.5m",
            height=120
        )
        
        # Convertir en liste
        conditions_list = [c.strip() for c in conditions_input.split("\n") if c.strip()]
        
        # Afficher le décompte
        if conditions_list:
            st.caption(f"📋 {len(conditions_list)} condition(s) critique(s) identifiée(s)")
        
        return conditions_list
    
    def _calculate_text_metrics(self, text: str) -> Dict[str, Any]:
        """
        Calcule les métriques d'un texte.
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dict avec les métriques du texte
        """
        if not text:
            return {"caracteres": 0, "mots": 0, "temps_lecture": 0}
        
        nb_caracteres = len(text)
        nb_mots = len(text.split())
        temps_lecture = max(1, nb_mots // 200)  # ~200 mots/min
        
        return {
            "caracteres": nb_caracteres,
            "mots": nb_mots,
            "temps_lecture": temps_lecture
        }
    
    def _display_text_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Affiche les métriques d'un texte.
        
        Args:
            metrics: Métriques calculées
        """
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption(f"✅ {metrics['caracteres']} caractères")
        with col2:
            st.caption(f"📄 {metrics['mots']} mots")
        with col3:
            st.caption(f"⏱️ ~{metrics['temps_lecture']} min de lecture")
    
    def _render_objectives_evaluation(self) -> Dict[str, Any]:
        """
        Rend la section d'évaluation des objectifs définis dans l'introduction.
        
        Cette méthode récupère les objectifs depuis l'introduction et crée
        des pavés de commentaire pour évaluer le degré de réalisation de chacun.
        
        Returns:
            Dict avec les évaluations des objectifs
        """
        st.subheader("🎯 Évaluation des objectifs de l'étude", divider=True)
        
        # Récupérer les objectifs depuis l'introduction
        rapport_data = st.session_state.get("rapport_data", {})
        introduction_data = rapport_data.get("introduction", {})
        objectifs_text = introduction_data.get("objectifs", "")
        
        if not objectifs_text.strip():
            st.info("💡 Aucun objectif défini dans l'introduction. Retournez à l'onglet Introduction pour en ajouter.")
            return {"objectifs_evaluations": {}}
        
        # Parser les objectifs (un par ligne)
        objectifs_list = [obj.strip() for obj in objectifs_text.split("\n") if obj.strip()]
        
        if not objectifs_list:
            st.info("💡 Objectifs non formatés correctement. Séparez chaque objectif par une ligne dans l'introduction.")
            return {"objectifs_evaluations": {}}
        
        st.info(f"📋 Évaluez la réalisation des {len(objectifs_list)} objectifs définis dans l'introduction")
        
        # Récupérer les évaluations existantes
        existing_evaluations = rapport_data.get("analyse_synthese", {}).get("objectifs_evaluations", {})
        
        evaluations = {}
        
        # Créer les pavés d'évaluation pour chaque objectif
        for i, objectif in enumerate(objectifs_list, 1):
            # Tronquer l'objectif pour l'affichage dans l'en-tête
            objectif_court = objectif[:80] + "..." if len(objectif) > 80 else objectif
            
            with st.expander(f"📌 Objectif {i}: {objectif_court}", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Afficher l'objectif complet
                    st.write("**Objectif :**")
                    st.write(f"*{objectif}*")
                
                with col2:
                    # Degré de réalisation (sélecteur rapide)
                    degre_options = [
                        "Non évalué",
                        "✅ Objectif atteint",
                        "🟡 Partiellement atteint", 
                        "🔴 Non atteint",
                        "➕ Dépassé"
                    ]
                    
                    # Récupérer la valeur existante
                    existing_degre = existing_evaluations.get(f"objectif_{i}", {}).get("degre_realisation", "Non évalué")
                    default_index = degre_options.index(existing_degre) if existing_degre in degre_options else 0
                    
                    degre_realisation = st.selectbox(
                        "Degré de réalisation",
                        degre_options,
                        index=default_index,
                        key=f"degre_obj_{i}"
                    )
                
                # Zone de commentaire détaillé
                existing_comment = existing_evaluations.get(f"objectif_{i}", {}).get("commentaire", "")
                
                commentaire = st.text_area(
                    "💬 Commentaire détaillé sur la réalisation",
                    value=existing_comment,
                    height=120,
                    placeholder=self._get_placeholder_for_degree(degre_realisation),
                    key=f"comment_obj_{i}",
                    help="Analysez comment cet objectif a été atteint grâce aux simulations et analyses"
                )
                
                # Métriques liées (optionnel)
                metrics_complement = st.text_input(
                    "📊 Métriques de support (optionnel)",
                    value=existing_evaluations.get(f"objectif_{i}", {}).get("metriques", ""),
                    placeholder="Ex: Taux de réussite 85%, 23 simulations validées...",
                    key=f"metrics_obj_{i}",
                    help="Données chiffrées qui appuient votre évaluation"
                )
                
                # Stocker l'évaluation
                evaluations[f"objectif_{i}"] = {
                    "objectif_texte": objectif,
                    "degre_realisation": degre_realisation,
                    "commentaire": commentaire,
                    "metriques": metrics_complement,
                    "ordre": i
                }
                
                # Affichage du résumé si rempli
                if commentaire.strip() or degre_realisation != "Non évalué":
                    with st.container():
                        if commentaire.strip():
                            char_count = len(commentaire.strip())
                            st.caption(f"**Commentaire:** {char_count} caractères")
        
        # Résumé global des évaluations
        self._render_objectives_summary(evaluations)
        
        return {"objectifs_evaluations": evaluations}

    def _get_placeholder_for_degree(self, degre: str) -> str:
        """
        Génère un placeholder contextuel selon le degré de réalisation.
        
        Args:
            degre: Degré de réalisation sélectionné
            
        Returns:
            Texte de placeholder adapté
        """
        placeholders = {
            "✅ Objectif atteint": "Ex: Les simulations démontrent que... Les résultats confirment...",
            "🟡 Partiellement atteint": "Ex: Objectif atteint dans 70% des cas, mais limité par... Des améliorations sont nécessaires pour...",
            "🔴 Non atteint": "Ex: Les simulations révèlent que... Les contraintes identifiées sont... Il faudra modifier...",
            "➕ Dépassé": "Ex: Non seulement l'objectif est atteint, mais en plus... Les résultats dépassent les attentes car...",
            "Non évalué": "Ex: Décrivez dans quelle mesure cet objectif a été atteint grâce à votre étude..."
        }
        
        return placeholders.get(degre, "Commentez la réalisation de cet objectif...")

    def _render_objectives_summary(self, evaluations: Dict[str, Any]) -> None:
        """
        Rend un résumé visuel des évaluations d'objectifs.
        
        Args:
            evaluations: Dict des évaluations d'objectifs
        """
        if not evaluations:
            return
        
        st.subheader("📊 Résumé des évaluations", divider=True)
        
        # Compter les degrés de réalisation
        degres_count = {}
        total_objectifs = len(evaluations)
        
        for eval_data in evaluations.values():
            degre = eval_data.get("degre_realisation", "Non évalué")
            degres_count[degre] = degres_count.get(degre, 0) + 1
        
        # Affichage en colonnes
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            atteints = degres_count.get("✅ Objectif atteint", 0)
            st.metric("Objectifs atteints", atteints, f"{atteints/total_objectifs*100:.0f}%" if total_objectifs > 0 else "0%")
        
        with col2:
            partiels = degres_count.get("🟡 Partiellement atteint", 0)
            st.metric("Partiellement", partiels, f"{partiels/total_objectifs*100:.0f}%" if total_objectifs > 0 else "0%")
        
        with col3:
            non_atteints = degres_count.get("🔴 Non atteint", 0)
            st.metric("Non atteints", non_atteints, f"{non_atteints/total_objectifs*100:.0f}%" if total_objectifs > 0 else "0%")
        
        with col4:
            depasses = degres_count.get("➕ Dépassé", 0)
            st.metric("Dépassés", depasses, f"{depasses/total_objectifs*100:.0f}%" if total_objectifs > 0 else "0%")
        
        # Barre de progression globale
        objectifs_evalues = sum(1 for eval_data in evaluations.values() 
                            if eval_data.get("degre_realisation", "Non évalué") != "Non évalué")
        
        progress = objectifs_evalues / total_objectifs if total_objectifs > 0 else 0
        st.progress(progress, text=f"Objectifs évalués: {objectifs_evalues}/{total_objectifs}")
        
        # Recommandations selon les résultats
        if progress < 0.5:
            st.warning("⚠️ Peu d'objectifs évalués. Complétez les évaluations pour une analyse exhaustive.")
        elif non_atteints > total_objectifs * 0.3:
            st.error("🔴 Plus de 30% des objectifs ne sont pas atteints. Révision des hypothèses recommandée.")
        elif atteints + depasses >= total_objectifs * 0.8:
            st.success("🎉 Plus de 80% des objectifs sont atteints ou dépassés. Excellent résultat !")
        else:
            st.info("📈 Résultats mitigés. Analysez les objectifs partiellement atteints pour des améliorations.")

    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """
        Retourne une analyse par défaut en cas d'erreur.
        
        Returns:
            Dict avec des valeurs par défaut
        """
        return {
            "nombre_essais": 0,
            "taux_reussite": 0.0,
            "conditions_critiques": [],
            "distances_trajectoires": "",
            "commentaire": "",
            "recapitulatif_analyse": "",
            "recapitulatif_metrics": {}
        }
    
    def get_analysis_summary(self, simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Génère un résumé complet de l'analyse pour l'export.
        
        Cette méthode publique permet d'obtenir toutes les analyses
        sans rendu Streamlit, utile pour l'export ou les tests.
        
        Args:
            simulations: Liste des simulations à analyser
            
        Returns:
            Dict avec le résumé complet de l'analyse
        """
        try:
            # Calculs de base
            metrics = self.calculator.calculate_basic_metrics(simulations)
            
            # Analyses spécialisées
            ship_analysis = self.performance_analyzer.analyze_ship_performance(simulations, metrics)
            maneuver_analysis = self.performance_analyzer.analyze_maneuver_performance(simulations, metrics)
            trends = self.performance_analyzer.identify_performance_trends(simulations, metrics)
            
            echecs = [s for s in simulations if s.get("resultat") == "Échec"]
            failure_analysis = self.performance_analyzer.analyze_failure_causes(echecs)
            
            emergency_analysis = self.emergency_analyzer.analyze_emergency_scenarios(simulations)
            emergency_stats = self.emergency_analyzer.get_emergency_statistics(simulations)
            
            conditions_analysis = self.calculator.analyze_environmental_conditions(simulations)
            
            # Résumé structuré
            summary = {
                "basic_metrics": metrics,
                "performance_analysis": {
                    "ships": ship_analysis,
                    "maneuvers": maneuver_analysis,
                    "trends": trends
                },
                "failure_analysis": failure_analysis,
                "emergency_analysis": emergency_analysis,
                "emergency_statistics": emergency_stats,
                "environmental_conditions": conditions_analysis,
                "overall_assessment": self._generate_overall_assessment(metrics, emergency_stats),
                "export_data": self.renderer.render_export_summary(metrics, {}),
                "generated_at": self._get_current_timestamp()
            }
            
            return summary
            
        except Exception as e:
            # Retour dégradé en cas d'erreur
            return {
                "error": str(e),
                "basic_metrics": self._get_default_analysis(),
                "generated_at": self._get_current_timestamp()
            }
    
    def _generate_overall_assessment(self, metrics: Dict[str, Any], emergency_stats: Dict[str, Any]) -> Dict[str, str]:
        """
        Génère une évaluation globale de l'analyse.
        
        Args:
            metrics: Métriques de base
            emergency_stats: Statistiques d'urgence
            
        Returns:
            Dict avec l'évaluation globale
        """
        success_rate = metrics["taux_reussite"]
        emergency_rate = emergency_stats.get("emergency_rate", 0)
        
        # Évaluation de la performance
        if success_rate >= 0.9:
            performance_level = "excellente"
            performance_color = "🟢"
        elif success_rate >= 0.8:
            performance_level = "très bonne"
            performance_color = "🟢"
        elif success_rate >= 0.7:
            performance_level = "bonne"
            performance_color = "🟡"
        elif success_rate >= 0.6:
            performance_level = "satisfaisante"
            performance_color = "🟡"
        else:
            performance_level = "préoccupante"
            performance_color = "🔴"
        
        # Évaluation du risque
        if emergency_rate > 0.3 or success_rate < 0.5:
            risk_level = "élevé"
            risk_color = "🔴"
        elif emergency_rate > 0.2 or success_rate < 0.7:
            risk_level = "modéré"
            risk_color = "🟡"
        else:
            risk_level = "faible"
            risk_color = "🟢"
        
        # Recommandation générale
        if success_rate >= 0.8 and emergency_rate < 0.1:
            recommendation = "Les opérations peuvent être menées en toute sécurité"
        elif success_rate >= 0.6:
            recommendation = "Des améliorations sont recommandées avant déploiement"
        else:
            recommendation = "Révision majeure des procédures nécessaire"
        
        return {
            "performance_level": performance_level,
            "performance_color": performance_color,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "overall_recommendation": recommendation,
            "confidence": "élevée" if metrics["nb_essais"] >= 20 else "modérée"
        }
    
    def _get_current_timestamp(self) -> str:
        """Retourne le timestamp actuel."""
        from datetime import datetime
        return datetime.now().isoformat()
