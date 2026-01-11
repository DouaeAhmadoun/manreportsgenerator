"""
AIGenerator - Interface simplifiée pour l'export Word
Avec traçage du contenu généré
"""

import copy
from typing import Dict, Any


class AIGenerator:
    """Générateur IA - Wrapper pour les agents pré-entraînés"""
    
    def __init__(self, model):
        self.model = model
        # Mapping des sections vers leur chemin dans rapport_data
        self.SECTIONS_MAPPING = {
            "introduction": ("introduction", "guidelines"),
            "analyse": ("analyse_synthese", "commentaire"), 
            "analyse_stats": ("analyse_synthese", "stats_text"),
            "analyse_recommandations": ("analyse_synthese", "recommandations_text"),
            "conclusion": ("conclusion",),
            "simulations": ("simulations", "description"),
            "navires": ("donnees_navires", "introduction"),
            "remorqueurs": ("donnees_navires", "remorqueurs_intro"),
            "scenarios_urgence": ("simulations", "scenarios_urgence_description"),
            "donnees_entree_intro": ("donnees_entree", "introduction"),
            "donnees_entree_plan_masse": ("donnees_entree", "plan_de_masse", "commentaire"),
            "donnees_entree_bathymetrie": ("donnees_entree", "bathymetrie", "commentaire"),
            "donnees_entree_balisage": ("donnees_entree", "balisage", "commentaire"),
            "donnees_entree_houle": ("donnees_entree", "conditions_environnementales", "houle", "commentaire"),
            "donnees_entree_vent": ("donnees_entree", "conditions_environnementales", "vent", "commentaire"),
            "donnees_entree_courant": ("donnees_entree", "conditions_environnementales", "courant", "commentaire"),
            "donnees_entree_maree": ("donnees_entree", "conditions_environnementales", "maree", "commentaire"),
            "donnees_entree_agitation": ("donnees_entree", "conditions_environnementales", "agitation", "commentaire"),
            "donnees_entree_conditions_intro": ("donnees_entree", "conditions_environnementales", "introduction"),
            # La synthèse doit aller sous conditions_environnementales.synthese pour que le context_builder la reprenne
            "donnees_entree_synthese": ("donnees_entree", "conditions_environnementales", "synthese"),
        }
        
        # Tracer (optionnel)
        self.tracer = None
        self._init_tracer()
    
    def _init_tracer(self):
        """Initialise le tracer si disponible"""
        try:
            from utils.ai_tracer import get_tracer
            self.tracer = get_tracer()
        except ImportError:
            # Tracer non disponible, continuer sans
            pass
    
    def generate_ai_sections_for_report(self, rapport_data: dict, progress_mgr=None, progress_range=None) -> dict:
        """
        Point d'entrée principal - Génère le contenu IA et l'intègre aux données
        
        Args:
            rapport_data: Données du rapport à enrichir
            progress_mgr: ProgressManager pour log/update en direct (optionnel)
            progress_range: tuple(start, end) pour les updates de progression IA
            
        Returns:
            rapport_data enrichi avec le contenu généré par IA
        """
        print("🤖 Génération IA avec agents pré-entraînés")
        
        # Démarrer la trace
        rapport_title = rapport_data.get("metadonnees", {}).get("titre", "Sans titre")
        if self.tracer:
            self.tracer.start_trace(rapport_title)
        
        try:
            from agents.pretrained_agents import generate_granular_sections_for_report
            
            # Générer toutes les sections
            generated_sections = generate_granular_sections_for_report(
                rapport_data=rapport_data,
                sections_requested=None,
                progress_mgr=progress_mgr,
                progress_range=progress_range
            )
            
            # Logger les sections générées
            if self.tracer and generated_sections:
                for section_name, content in generated_sections.items():
                    source = "ai" if content and len(str(content)) > 20 else "fallback"
                    self.tracer.log_generated(section_name, content, source)
            
            if generated_sections:
                enriched = self._integrate_content(rapport_data, generated_sections)
                
                # Finaliser la trace
                if self.tracer:
                    trace_result = self.tracer.finish_trace()
                
                return enriched
            else:
                if self.tracer:
                    self.tracer.log_warning("Aucune section générée")
                    self.tracer.finish_trace()
                print("⚠️ Aucune section générée - données originales retournées")
                return rapport_data
        
        except ImportError as e:
            if self.tracer:
                self.tracer.log_warning(f"Agents non disponibles: {e}")
                self.tracer.finish_trace()
            print(f"⚠️ Agents non disponibles: {e}")
            return rapport_data
            
        except Exception as e:
            if self.tracer:
                self.tracer.log_warning(f"Erreur génération: {e}")
                self.tracer.finish_trace()
            print(f"⚠️ Erreur génération: {e}")
            return rapport_data
    
    def _integrate_content(self, rapport_data: dict, generated_content: dict) -> dict:
        """Intègre le contenu généré dans rapport_data"""
        enriched = copy.deepcopy(rapport_data)
        
        for section_name, content in generated_content.items():
            # Accepter les contenus courts (certaines sections IA peuvent être concises)
            if not content or len(str(content).strip()) < 2:
                if self.tracer:
                    self.tracer.log_warning(f"Section {section_name} ignorée (contenu trop court)")
                continue
                
            path = self.SECTIONS_MAPPING.get(section_name)
            if not path:
                if self.tracer:
                    self.tracer.log_warning(f"Section {section_name} générée mais pas de mapping défini!")
                continue
            
            try:
                # Naviguer et créer la structure si nécessaire
                current = enriched
                for key in path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Assigner le contenu
                current[path[-1]] = content
                print(f"  📝 {section_name}: {len(content)} caractères → {' → '.join(path)}")
                
                # Logger l'intégration
                if self.tracer:
                    self.tracer.log_integrated(section_name, path, content)
                
            except Exception as e:
                if self.tracer:
                    self.tracer.log_warning(f"Erreur intégration {section_name}: {e}")
                print(f"  ⚠️ Erreur intégration {section_name}: {e}")
        
        return enriched
