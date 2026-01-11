from datetime import datetime
from typing import Any, Dict, List

CONDITION_TYPES: tuple[str, ...] = ("houle", "vent", "courant", "maree", "agitation")

class ContextBuilder:
    """Classe responsable de la construction du contexte pour les templates Word"""
    
    def __init__(self):
        pass
    
    def prepare_context_for_template(self, rapport_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prépare le contexte pour le template Word"""
        context = self._map_template_structure(rapport_data)        
        self._add_generation_metadata(context)
        return context
    
    def _map_template_structure(self, rapport_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mappe les données exactement selon la structure attendue par le template - ORDRE CORRIGÉ"""
        context = {}
        
        # 1. MÉTADONNÉES
        metadonnees = rapport_data.get("metadonnees", {})
        context["metadonnees"] = {
            "titre": metadonnees.get("titre", ""),
            "code_projet": metadonnees.get("code_projet", ""),
            "client": metadonnees.get("client", ""),
            "type": metadonnees.get("type", ""),
            "numero": metadonnees.get("numero", ""),
            "annee": metadonnees.get("annee", ""),
            "type_etude": metadonnees.get("type_etude", ""),
            "main_image": metadonnees.get("main_image", ""),
            "client_logo": metadonnees.get("client_logo", ""),
            "historique_revisions": metadonnees.get("historique_revisions", [])
        }
        
        # 2. INTRODUCTION
        introduction = rapport_data.get("introduction", {})
        context["introduction"] = introduction.get("guidelines", "")
        context["objectifs_text"] = introduction.get("objectifs", "")
        
        # 3. DONNÉES D'ENTRÉE
        donnees_entree = rapport_data.get("donnees_entree", {})

        # Variables plates pour le template
        donnees_entree_introduction = donnees_entree.get("introduction", {})
        
        plan_masse = donnees_entree.get("plan_de_masse", {})
        context["donnees_entree_plan_masse"] = plan_masse.get("commentaire", "")
        
        balisage = donnees_entree.get("balisage", {})
        context["donnees_entree_balisage"] = balisage.get("commentaire", "")
        
        bathymetrie = donnees_entree.get("bathymetrie", {})
        context["donnees_entree_bathymetrie"] = bathymetrie.get("commentaire", "")
        context["bathymetrie_source"] = bathymetrie.get("source", "")
        context["bathymetrie_date"] = bathymetrie.get("date", "")
        context["bathymetrie_notes"] = bathymetrie.get("notes_profondeur", "")
        
        # Structure hiérarchique pour le template
        context["donnees_entree"] = {
            "introduction": donnees_entree_introduction,
            "plan_de_masse": self._process_plan_masse(plan_masse),
            "balisage": self._process_balisage(balisage),
            "bathymetrie": self._process_bathymetrie(bathymetrie),
            "conditions_environnementales": self._process_conditions_env(donnees_entree.get("conditions_environnementales", {}))
        }
        
        # Variables de conditions
        self._add_conditions_variables(context, donnees_entree.get("conditions_environnementales", {}))
        
        # 4. NAVIRES
        donnees_navires = rapport_data.get("donnees_navires", {})
        # Texte d'introduction généré par IA (si disponible)
        context["navires_intro"] = donnees_navires.get("introduction", "")
        context["remorqueurs_intro"] = donnees_navires.get("remorqueurs_intro", "")
        context["navires_liste"] = donnees_navires.get("navires", {}).get("navires", [])
        context["remorqueurs_liste"] = donnees_navires.get("remorqueurs", {}).get("remorqueurs", [])
        
        # 5. SIMULATIONS
        simulations_data = rapport_data.get("simulations", {})
        context["simulations"] = {
            "simulations": simulations_data.get("simulations", []),
            # Description globale (générée par IA si disponible)
            "description": simulations_data.get("description", "")
        }
        
        # 6. ANALYSE - CRÉER D'ABORD LA STRUCTURE VIDE
        analyse_data = rapport_data.get("analyse_synthese", {})
        context["analyse_synthese"] = {
            "nombre_essais": analyse_data.get("nombre_essais", 0),
            "nombre_reussis": analyse_data.get("nombre_reussis", 0),
            "nombre_echecs": analyse_data.get("nombre_echecs", 0),
            "taux_reussite_pct": analyse_data.get("taux_reussite_pct", 0),
            "nombre_scenarios_urgence": analyse_data.get("nombre_scenarios_urgence", 0),
            "commentaire": analyse_data.get("commentaire", ""),
            "conditions_critiques_liste": analyse_data.get("conditions_critiques", []),
            "distances_trajectoires": analyse_data.get("distances_trajectoires", ""),
            "stats_text": analyse_data.get("stats_text", ""),
            "recommandations_text": analyse_data.get("recommandations_text", ""),
            "recapitulatif_text": analyse_data.get("recapitulatif_text", ""),
            "recapitulatif_metrics": analyse_data.get("metrics", {}),
            "objectifs_evaluations": analyse_data.get("objectifs_evaluations", {})
        }
        
        # Alias pour compatibilité template plus ancien : recapitulatif_analyse
        recap_text = context["analyse_synthese"].get("recapitulatif_text", "")
        context["analyse_synthese"]["recapitulatif_analyse"] = recap_text
        
        # 7. MAINTENANT calculer et mettre à jour les stats (analyse_synthese existe déjà)
        self._add_simulations_stats(context, simulations_data.get("simulations", []))
        
        # 8. CONCLUSION
        context["conclusion_text"] = rapport_data.get("conclusion", "")
        
        # 9. ANNEXES
        context["annexes"] = self._process_annexes(
            rapport_data.get("annexes", {}), 
            context["simulations"]["simulations"]
        )
        
        return context

    def _process_plan_masse(self, plan_masse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les données du plan de masse"""
        return {
            "phases": plan_masse_data.get("phases", []),
            "commentaire": plan_masse_data.get("commentaire", ""),
            "figures": plan_masse_data.get("figures", [])
        }
    
    def _process_balisage(self, balisage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les données de balisage"""
        return {
            "figures": balisage_data.get("figures", []),
            "commentaire": balisage_data.get("commentaire", "")
        }
    
    def _process_bathymetrie(self, bathymetrie_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les données de bathymétrie"""
        return {
            "source": bathymetrie_data.get("source", ""),
            "date": bathymetrie_data.get("date", ""),
            "notes_profondeur": bathymetrie_data.get("notes_profondeur", ""),
            "figures": bathymetrie_data.get("figures", [])
        }
    
    def _process_conditions_env(self, conditions_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les conditions environnementales"""
        processed = {}
        
        for condition_type in CONDITION_TYPES:
            condition_info = conditions_data.get(condition_type, {})
            processed[condition_type] = {
                "conditions": condition_info.get("conditions", []),
                "valeurs_retenues": condition_info.get("valeurs_retenues", ""),
                "commentaire": condition_info.get("commentaire", ""),
                "figures": condition_info.get("figures", []),
                "tableaux": condition_info.get("tableaux", [])
            }
        
        return processed
    
    def _add_conditions_variables(self, context: Dict[str, Any], conditions_data: Dict[str, Any]):
        """Ajoute les variables de conditions pour le template"""
        # Introduction des conditions
        context["donnees_entree_conditions_intro"] = self._get_ai_text_or_default(
            conditions_data, "introduction",
            "Les conditions environnementales influencent directement la manœuvrabilité des navires."
        )
        
        # Variables pour chaque condition
        for condition_type in CONDITION_TYPES:
            condition_info = conditions_data.get(condition_type, {})
            
            # Texte principal généré par IA
            context[f"donnees_entree_{condition_type}"] = self._get_ai_text_or_default(
                condition_info, "commentaire", "TODO: Rédiger cette section"
            )
            
            # Variables spécifiques pour le template
            context[f"{condition_type}_conditions"] = condition_info.get("conditions", [])
            context[f"{condition_type}_retenues"] = condition_info.get("valeurs_retenues", "")
            context[f"{condition_type}_commentaire"] = condition_info.get("commentaire", "")
            context[f"{condition_type}_figures"] = condition_info.get("figures", [])
            context[f"{condition_type}_tableaux"] = condition_info.get("tableaux", [])
        
        # Synthèse
        context["donnees_entree_synthese"] = self._get_ai_text_or_default(
            conditions_data, "synthese",
            "La synthèse des données environnementales permet d'identifier les conditions critiques."
        )
    
    def _add_simulations_stats(self, context: dict, simulations: list):
        """Ajoute les statistiques de simulations"""
        if not simulations:
            return
        
        nb_total = len(simulations)
        nb_reussis = sum(1 for s in simulations if s.get("resultat") == "Réussite")
        nb_echecs = sum(1 for s in simulations if s.get("resultat") == "Échec")
        nb_urgence = sum(1 for s in simulations if s.get("is_emergency_scenario", False))
        
        if "analyse_synthese" not in context:
            context["analyse_synthese"] = {}

        # Mettre à jour analyse_synthese avec les stats calculées
        context["analyse_synthese"].update({
            "nombre_essais": nb_total,
            "nombre_reussis": nb_reussis,
            "nombre_echecs": nb_echecs,
            "taux_reussite_pct": round((nb_reussis / nb_total) * 100, 1) if nb_total > 0 else 0,
            "nombre_scenarios_urgence": nb_urgence
        })
    
    def _process_annexes(self, annexes_data: Dict[str, Any], simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Traite les annexes selon la structure exacte du template"""
        if not annexes_data or annexes_data.get("type") == "none":
            return {
                "actif": False,
                "type": "none",
                "tableau_complet": {"actif": False}
            }
        
        # Structure pour annexes automatiques
        if simulations:
            return {
                "actif": True,
                "type": "automatic",
                "tableau_complet": {
                    "actif": True,
                    "titre": "Tableau récapitulatif de tous les essais",
                    "simulations": simulations,
                    "total_essais": len(simulations)
                }
            }
        
        return {"actif": False, "type": "none", "tableau_complet": {"actif": False}}
    
    def _get_ai_text_or_default(self, data: Dict[str, Any], key: str, default: str) -> str:
        """Récupère le texte généré par IA ou une valeur par défaut"""
        if isinstance(data, dict) and key in data and data[key]:
            return data[key]
        return default
    
    def _add_generation_metadata(self, context: Dict[str, Any]):
        """Ajoute les métadonnées de génération"""
        now = datetime.now()
        context["date_generation"] = now.strftime("%d/%m/%Y")
        context["heure_generation"] = now.strftime("%H:%M")
