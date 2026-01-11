import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Template
import streamlit as st

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Règles de formatage communes injectées dans les prompts
COMMON_FORMAT_RULES = (
    "- Pas de titres ni de HMTL ni de Markdown\n"
    "- Pas de mise en forme (gras, listes longues)\n"
    "- Style professionnel, phrases courtes\n"
    "- N'invente pas de données absentes du contexte\n"
    "- Écris en français professionnel, phrases fluides\n"
    "- Commence directement par le contenu (pas de titre)\n"
    "- Utilise un vocabulaire technique maritime précis\n"
)


class PretrainedManager:
    """Gestionnaire d'agents pré-entraînés granulaires avec few-shot examples"""
    
    def __init__(self, cache_directory: str = "agents/training_cache", verbose: bool = True):
        self.cache_directory = Path(cache_directory)
        self.verbose = verbose
        self.debug_run_dir: Optional[Path] = None
        
        # Fichiers de cache
        self.training_cache = self.cache_directory / "training_data_granular.json"
        self.metadata_cache = self.cache_directory / "training_metadata_granular.json"
        
        # Données chargées
        self.training_data = None
        self.metadata = None
        
        # Configuration
        self.default_model = "mistralai/mistral-small-3.1-24b-instruct:free"
        self.timeout = 30
        
        # Nombre d'exemples few-shot à utiliser par section
        self.few_shot_count = 2
        
        # Mapping des sections vers les générateurs
        self.section_generators = {
            "introduction": self._generate_introduction,
            "analyse": self._generate_analyse,
            "analyse_stats": self._generate_analyse_stats,
            "analyse_recommandations": self._generate_analyse_recommandations,
            "donnees_entree_intro": self._generate_donnees_entree_intro,
            "donnees_entree_plan_masse": self._generate_donnees_entree_plan_masse,
            "donnees_entree_bathymetrie": self._generate_donnees_entree_bathymetrie,
            "donnees_entree_balisage": self._generate_donnees_entree_balisage,
            "donnees_entree_conditions_intro": self._generate_donnees_entree_conditions_intro,
            "donnees_entree_houle": self._generate_donnees_entree_houle,
            "donnees_entree_vent": self._generate_donnees_entree_vent,
            "donnees_entree_courant": self._generate_donnees_entree_courant,
            "donnees_entree_maree": self._generate_donnees_entree_maree,
            "donnees_entree_agitation": self._generate_donnees_entree_agitation,
            "donnees_entree_synthese": self._generate_donnees_entree_synthese,
            "navires": self._generate_navires,
            "remorqueurs": self._generate_remorqueurs,
            "simulations": self._generate_simulations,
            "scenarios_urgence": self._generate_scenarios_urgence,
            "conclusion": self._generate_conclusion,
        }
        
        self._log(f"🤖 PretrainedManager initialisé ({len(self.section_generators)} générateurs)")
    
    def load_training_data(self) -> bool:
        """Charge les données d'entraînement"""
        try:
            if self.training_cache.exists():
                with open(self.training_cache, 'r', encoding='utf-8') as f:
                    self.training_data = json.load(f)
            
            if self.metadata_cache.exists():
                with open(self.metadata_cache, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            
            # Vérifier le type
            if self.metadata and self.metadata.get("training_type") != "granular_v2":
                self._log("⚠️ Données non granulaires - Ré-entraînement recommandé")
                return False
            
            if not self.training_data:
                self._log("❌ Aucune donnée d'entraînement")
                return False
            
            # Compter les exemples
            total_examples = sum(len(examples) for examples in self.training_data.values() if isinstance(examples, list))
            self._log(f"✅ Données chargées: {len(self.training_data)} sections, {total_examples} exemples")
            return True
            
        except Exception as e:
            self._log(f"❌ Erreur chargement: {e}")
            return False
    
    # =========================================================================
    # FEW-SHOT EXAMPLES - NOUVEAU
    # =========================================================================
    
    def _get_few_shot_examples(self, section_name: str, n: int = None) -> List[Dict[str, Any]]:
        """
        Récupère les meilleurs exemples few-shot pour une section
        
        Args:
            section_name: Nom de la section
            n: Nombre d'exemples (défaut: self.few_shot_count)
            
        Returns:
            Liste d'exemples avec 'content' et 'score'
        """
        if n is None:
            n = self.few_shot_count
        
        if not self.training_data:
            self._log(f"    ⚠️ training_data non chargé pour {section_name}")
            return []
        
        # Récupérer les exemples pour cette section
        examples = self.training_data.get(section_name, [])
        
        if not examples:
            # Essayer des variantes du nom de section
            alternative_names = [
                section_name.replace("_", "-"),
                section_name.replace("-", "_"),
                section_name.lower(),
            ]
            for alt_name in alternative_names:
                examples = self.training_data.get(alt_name, [])
                if examples:
                    break
        
        if not examples:
            self._log(f"    ⚠️ Aucun exemple pour {section_name} (sections dispo: {list(self.training_data.keys())[:5]}...)")
            return []
        
        # Trier par score (si disponible) et prendre les n meilleurs
        if isinstance(examples, list) and len(examples) > 0:
            # Vérifier si les exemples ont un score
            if isinstance(examples[0], dict) and "quality_score" in examples[0]:
                sorted_examples = sorted(examples, key=lambda x: x.get("quality_score", 0), reverse=True)
            elif isinstance(examples[0], dict) and "score" in examples[0]:
                sorted_examples = sorted(examples, key=lambda x: x.get("score", 0), reverse=True)
            else:
                sorted_examples = examples
            
            # Prendre les n meilleurs
            best_examples = sorted_examples[:n]
            
            self._log(f"    📚 {len(best_examples)} exemple(s) few-shot pour {section_name}")
            return best_examples
        
        return []
    
    def _format_few_shot_examples(self, examples: List[Dict[str, Any]]) -> str:
        """
        Formate les exemples few-shot pour injection dans le prompt
        
        Args:
            examples: Liste d'exemples
            
        Returns:
            Texte formaté des exemples
        """
        if not examples:
            return ""
        
        formatted_parts = []
        
        for i, example in enumerate(examples, 1):
            # Extraire le contenu - plusieurs clés possibles
            if isinstance(example, dict):
                content = (
                    example.get("content") or 
                    example.get("text") or 
                    example.get("extract") or 
                    ""
                )
                # Extraire la source
                source_file = example.get("source_file", "")
                if source_file:
                    # Nettoyer le nom du fichier
                    source = source_file.replace(".docx", "").replace(".pdf", "")
                    # Raccourcir si trop long
                    if len(source) > 40:
                        source = source[:37] + "..."
                else:
                    source = f"Rapport {i}"
            else:
                content = str(example)
                source = f"Exemple {i}"
            
            # Nettoyer le contenu
            content = content.strip()
            
            # Supprimer les retours à la ligne excessifs
            import re
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            # Limiter la taille (max 600 caractères par exemple pour garder le contexte)
            if len(content) > 600:
                # Couper à la fin d'une phrase si possible
                cut_point = content[:600].rfind('.')
                if cut_point > 400:
                    content = content[:cut_point + 1]
                else:
                    content = content[:600] + "..."
            
            if content and len(content) > 50:  # Ignorer les contenus trop courts
                formatted_parts.append(f"--- Exemple {i} ({source}) ---\n{content}")
        
        if formatted_parts:
            return "\n\n".join(formatted_parts)
        
        return ""
    
    # =========================================================================
    # CONSTRUCTION DES PROMPTS - MODIFIÉ
    # =========================================================================
    
    def _build_prompt(self, section_name: str, rapport_data: dict) -> str:
        """Construit le prompt pour une section AVEC few-shot examples"""
        
        # S'assurer que les données d'entraînement sont chargées
        if self.training_data is None:
            self.load_training_data()
        
        # Essayer de charger depuis fichier
        prompt_file = Path("prompts") / f"{section_name}.txt"

        # Préparer un contexte enrichi avec les alias attendus par certains prompts
        prompt_context = dict(rapport_data)
        prompt_context["analyse_synthese"] = rapport_data.get("analyse_synthese", {})
        donnees_navires = rapport_data.get("donnees_navires", {})
        prompt_context["navires_liste"] = donnees_navires.get("navires", {}).get("navires", [])
        prompt_context["remorqueurs_liste"] = donnees_navires.get("remorqueurs", {}).get("remorqueurs", [])
        
        # ✨ NOUVEAU: Récupérer et formater les few-shot examples
        few_shot_examples = self._get_few_shot_examples(section_name)
        formatted_examples = self._format_few_shot_examples(few_shot_examples)
        print("\n" + "="*60)
        print(f"🔥 DEBUG {section_name}: {len(few_shot_examples)} exemples few-shot")
        print("="*60 + "\n")
        prompt_context["examples"] = formatted_examples
        prompt_context["has_examples"] = bool(formatted_examples)
        
        if prompt_file.exists():
            try:
                content = prompt_file.read_text(encoding='utf-8')
                
                # ✨ NOUVEAU: Ajouter la section examples au prompt si pas déjà présente
                if formatted_examples and "{{ examples }}" not in content and "{% if examples %}" not in content:
                    # Injecter les examples avant les règles de rédaction
                    examples_section = self._create_examples_section(formatted_examples)
                    
                    # Chercher où insérer (avant RÈGLES ou à la fin)
                    insertion_markers = ["RÈGLES DE RÉDACTION", "RÈGLES STRICTES", "Style:", "Rédige maintenant"]
                    inserted = False
                    
                    for marker in insertion_markers:
                        if marker in content:
                            content = content.replace(marker, f"{examples_section}\n\n{marker}")
                            inserted = True
                            break
                    
                    if not inserted:
                        content = content + f"\n\n{examples_section}"
                
                template = Template(content)
                rendered = template.render(**prompt_context, regles_formatage=COMMON_FORMAT_RULES)
                
                # Dump du prompt rendu pour inspection
                self._dump_prompt(section_name, rendered)
                
                return rendered
                
            except Exception as e:
                print(f"    ⚠️ Erreur prompt {section_name}: {e}")
        else:
            print(f"    ⚠️ Prompt {section_name} doesn't exist")
        
        return self._get_fallback_prompt(section_name, rapport_data)
    
    def _create_examples_section(self, formatted_examples: str) -> str:
        """Crée la section des exemples à injecter dans le prompt"""
        return f"""EXEMPLES DE RÉFÉRENCE (style à suivre):
Les exemples ci-dessous proviennent de rapports TME validés. Inspire-toi de leur style et structure, mais adapte le contenu aux données fournies.

{formatted_examples}

FIN DES EXEMPLES - Maintenant rédige en utilisant les données ci-dessus."""
    
    def _dump_prompt(self, section_name: str, rendered: str):
        """Sauvegarde le prompt rendu pour debug"""
        try:
            out_dir = self.debug_run_dir if self.debug_run_dir else Path("debug/prompt_renders")
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = out_dir / f"{section_name}_{ts}.txt"
            out_path.write_text(rendered, encoding="utf-8")
        except Exception:
            pass
    
    def _get_fallback_prompt(self, section_name: str, rapport_data: dict) -> str:
        """Prompt de fallback simple basé sur le titre du rapport"""
        meta = rapport_data.get("metadonnees", {})
        titre = meta.get("titre", "Étude de manœuvrabilité")
        
        prompts = {
            "introduction": f"Rédige l'introduction pour un rapport de manœuvrabilité intitulé \"{titre}\". Inclus: contexte, objectifs, méthodologie.",
            "donnees_entree_bathymetrie": f"Présente les données bathymétriques pour l'étude \"{titre}\". Inclus: source, profondeurs, caractéristiques.",
            "donnees_entree_conditions_intro": f"Rédige l'introduction des conditions environnementales pour l'étude \"{titre}\".",
            "donnees_entree_houle": f"Décris les conditions de houle pour l'étude \"{titre}\".",
            "navires": f"Présente les navires sélectionnés pour l'étude \"{titre}\".",
            "simulations": f"Décris la méthodologie des simulations pour l'étude \"{titre}\".",
            "analyse": f"Analyse les résultats de l'étude \"{titre}\".",
            "conclusion": f"Rédige la conclusion de l'étude \"{titre}\" avec recommandations.",
        }
        
        return prompts.get(section_name, f"Rédige la section {section_name} pour l'étude {titre}.")
    
    # =========================================================================
    # GÉNÉRATION PRINCIPALE
    # =========================================================================
    
    def generate_granular_sections_for_report(self, 
                                              rapport_data: dict, 
                                              sections_requested: List[str] = None,
                                              progress_mgr=None,
                                              progress_range=None) -> dict:
        """
        Génère les sections avec les agents pré-entraînés + few-shot examples
        """
        if not self.load_training_data():
            self._log("⚠️ Mode fallback activé (pas d'exemples)")
        else:
            self._log(f"✅ Few-shot examples disponibles")
        
        # Préparer un dossier de debug par génération
        run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.debug_run_dir = Path("debug/prompt_renders") / run_ts
        try:
            self.debug_run_dir.mkdir(parents=True, exist_ok=True)
            self._log(f"[debug] prompts → {self.debug_run_dir}")
        except Exception as e:
            self._log(f"[debug] impossible de créer le dossier: {e}")
            self.debug_run_dir = None
        
        # Sections à générer
        if sections_requested is None:
            sections = list(self.section_generators.keys())
        else:
            sections = [s for s in sections_requested if s in self.section_generators]
        
        self._log(f"🚀 Génération de {len(sections)} sections...")
        if progress_mgr:
            progress_mgr.log_detail(f"Génération IA: {len(sections)} sections à traiter")
        
        start_p, end_p = progress_range if progress_range else (20, 65)
        steps_count = max(1, len(sections))
        step_increment = max(1, int((end_p - start_p) / steps_count))
        current_step = start_p
        
        generated = {}
        stats = {"success": 0, "fallback": 0, "failed": 0, "with_examples": 0}
        
        for section_name in sections:
            try:
                self._log(f"  🔄 {section_name}...")
                if progress_mgr:
                    progress_mgr.log_detail(f"Génération de la section {section_name} en cours...")
                    progress_mgr.update(current_step, "Génération IA", f"✏️ {section_name} en cours...")
                
                generator = self.section_generators[section_name]
                content = generator(rapport_data)
                
                if content and len(content.strip()) > 20:
                    generated[section_name] = content
                    stats["success"] += 1
                    
                    # Vérifier si des examples ont été utilisés
                    if self.training_data and section_name in self.training_data:
                        stats["with_examples"] += 1
                    
                    self._log(f"  ✅ {section_name}: {len(content)} chars")
                    if progress_mgr:
                        progress_mgr.log_detail(f"Section {section_name} générée ({len(content)} caractères)")
                    
                    # Dump du texte généré
                    self._dump_generated(section_name, content)
                else:
                    # Fallback
                    fallback = self._get_fallback_for_section(section_name, rapport_data)
                    generated[section_name] = fallback
                    stats["fallback"] += 1
                    self._log(f"  ⚠️ {section_name}: fallback")
                    if progress_mgr:
                        progress_mgr.log_detail(f"Section {section_name} en fallback")
                    self._dump_generated(section_name, fallback)
                    
            except Exception as e:
                self._log(f"  ❌ {section_name}: {e}")
                stats["failed"] += 1
                
                try:
                    generated[section_name] = self._get_fallback_for_section(section_name, rapport_data)
                    stats["fallback"] += 1
                except:
                    pass
            finally:
                if progress_mgr:
                    current_step = min(end_p, current_step + step_increment)
        
        if progress_mgr:
            progress_mgr.update(end_p, "Génération IA", "✅ Sections IA traitées")
        
        self._print_stats(stats, len(sections))
        self.debug_run_dir = None
        return generated
    
    def _dump_generated(self, section_name: str, content: str):
        """Sauvegarde le texte généré pour debug"""
        try:
            if self.debug_run_dir:
                gen_path = self.debug_run_dir / f"{section_name}_generated.txt"
                gen_path.write_text(content, encoding="utf-8")
        except Exception:
            pass
    
    # =========================================================================
    # APPEL API
    # =========================================================================
    
    def _generate_with_ai(self, section_name: str, prompt: str) -> Optional[str]:
        """Appelle l'API OpenRouter"""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            key = self._get_api_key()
            if os.getenv("STREAMLIT_SERVER_RUN_ON_SAVE"):
                key = st.secrets["OPENROUTER_API_KEY"].strip()
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.default_model,
                    "messages": [
                        {
                            "role": "system", 
                            "content": "Tu es un expert en ingénierie maritime et rédaction de rapports techniques pour TME (Tanger Med Engineering). Réponds uniquement avec le contenu demandé, sans préambule. Inspire-toi des exemples fournis pour le style."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.3
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content and len(content.strip()) > 20:
                    return content.strip()
            elif response.status_code == 429:
                print(f"    ⚠️ Rate limit pour {section_name}")
                time.sleep(2)
            else:
                print(f"    ⚠️ API Error {response.status_code}")
                
        except Exception as e:
            print(f"    ⚠️ Erreur API: {e}")
        
        return None
    
    def _get_api_key(self) -> str:
        """Récupère la clé API"""
        key = os.getenv("OPENROUTER_API_KEY")
        if key:
            return key
        
        try:
            from config import get_openrouter_key
            return get_openrouter_key()
        except ImportError:
            return ""
    
    # =========================================================================
    # GÉNÉRATEURS PAR SECTION
    # =========================================================================
    
    def _generate_introduction(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("introduction", rapport_data)
        return self._generate_with_ai("introduction", prompt) or self._fallback_introduction(rapport_data)
    
    def _generate_analyse(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("analyse", rapport_data)
        return self._generate_with_ai("analyse", prompt) or self._fallback_analyse(rapport_data)

    def _generate_analyse_stats(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("analyse_stats", rapport_data)
        return self._generate_with_ai("analyse_stats", prompt) or \
            "Statistiques clés des simulations : taux de réussite global, répartition par manœuvre et par navire."

    def _generate_analyse_recommandations(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("analyse_recommandations", rapport_data)
        return self._generate_with_ai("analyse_recommandations", prompt) or \
            "Recommandations principales : adapter les seuils météo, configurer l'assistance remorqueurs selon le navire."
    
    def _generate_donnees_entree_intro(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("donnees_entree_intro", rapport_data)
        return self._generate_with_ai("donnees_entree_intro", prompt) or \
            "Cette section présente l'ensemble des données d'entrée utilisées pour l'étude."
    
    def _generate_donnees_entree_plan_masse(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("donnees_entree_plan_masse", rapport_data)
        return self._generate_with_ai("donnees_entree_plan_masse", prompt) or \
            "Le plan de masse présente l'aménagement portuaire étudié."
    
    def _generate_donnees_entree_bathymetrie(self, rapport_data: dict) -> str:
        donnees = rapport_data.get("donnees_entree", {}).get("bathymetrie", {})
        prompt = self._build_prompt("donnees_entree_bathymetrie", rapport_data)
        result = self._generate_with_ai("donnees_entree_bathymetrie", prompt)
        return result or f"La bathymétrie du site a été établie à partir de {donnees.get('source', 'relevés récents')}."
    
    def _generate_donnees_entree_balisage(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("donnees_entree_balisage", rapport_data)
        return self._generate_with_ai("donnees_entree_balisage", prompt) or \
            "Le plan de balisage définit la signalisation maritime."
    
    def _generate_donnees_entree_conditions_intro(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("donnees_entree_conditions_intro", rapport_data)
        return self._generate_with_ai("donnees_entree_conditions_intro", prompt) or \
            "Les conditions environnementales influencent directement la manœuvrabilité."
    
    def _generate_donnees_entree_houle(self, rapport_data: dict) -> str:
        conditions = rapport_data.get("donnees_entree", {}).get("conditions_environnementales", {})
        houle = conditions.get("houle", {})
        prompt = self._build_prompt("donnees_entree_houle", rapport_data)
        result = self._generate_with_ai("donnees_entree_houle", prompt)
        return result or f"Les conditions de houle retenues sont: {houle.get('valeurs_retenues', 'Hs = 2.5m')}."
    
    def _generate_donnees_entree_vent(self, rapport_data: dict) -> str:
        conditions = rapport_data.get("donnees_entree", {}).get("conditions_environnementales", {})
        vent = conditions.get("vent", {})
        prompt = self._build_prompt("donnees_entree_vent", rapport_data)
        result = self._generate_with_ai("donnees_entree_vent", prompt)
        return result or f"Les conditions de vent considérées sont: {vent.get('valeurs_retenues', '30 kts')}."
    
    def _generate_donnees_entree_courant(self, rapport_data: dict) -> str:
        conditions = rapport_data.get("donnees_entree", {}).get("conditions_environnementales", {})
        courant = conditions.get("courant", {})
        prompt = self._build_prompt("donnees_entree_courant", rapport_data)
        result = self._generate_with_ai("donnees_entree_courant", prompt)
        return result or f"Les conditions de courant retenues sont: {courant.get('valeurs_retenues', '1.5 kts')}."
    
    def _generate_donnees_entree_maree(self, rapport_data: dict) -> str:
        conditions = rapport_data.get("donnees_entree", {}).get("conditions_environnementales", {})
        maree = conditions.get("maree", {})
        prompt = self._build_prompt("donnees_entree_maree", rapport_data)
        result = self._generate_with_ai("donnees_entree_maree", prompt)
        return result or f"Les conditions de marée considérées sont: {maree.get('valeurs_retenues', 'Marnage 4.2m')}."
    
    def _generate_donnees_entree_agitation(self, rapport_data: dict) -> str:
        conditions = rapport_data.get("donnees_entree", {}).get("conditions_environnementales", {})
        agitation = conditions.get("agitation", {})
        prompt = self._build_prompt("donnees_entree_agitation", rapport_data)
        result = self._generate_with_ai("donnees_entree_agitation", prompt)
        return result or f"L'agitation résiduelle est estimée à: {agitation.get('valeurs_retenues', '0.5m')}."
    
    def _generate_donnees_entree_synthese(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("donnees_entree_synthese", rapport_data)
        return self._generate_with_ai("donnees_entree_synthese", prompt) or \
            "La synthèse des données environnementales permet de définir les conditions représentatives."
    
    def _generate_navires(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("navires", rapport_data)
        ai_result = self._generate_with_ai("navires", prompt)
        
        if ai_result:
            ai_lower = ai_result.lower()
            blockers = ["aucune donnée", "aucune information", "je ne dispose pas", "je ne peux pas"]
            if not any(b in ai_lower for b in blockers):
                return ai_result
    
        # Fallback enrichi
        navires = rapport_data.get("donnees_navires", {}).get("navires", {}).get("navires", [])
        if navires:
            lignes = []
            for nav in navires[:5]:
                nom = nav.get("nom", "Navire")
                type_nav = nav.get("type", "Type")
                parts = [f"{nom} ({type_nav})"]
                if nav.get("longueur"):
                    parts.append(f"{nav['longueur']} m")
                if nav.get("tirant_eau_av"):
                    parts.append(f"TE {nav['tirant_eau_av']} m")
                lignes.append(" - " + ", ".join(parts))
            intro = "La sélection des navires types couvre les unités attendues au port."
            return "\n".join([intro] + lignes)

        return "La sélection des navires types représente les différentes catégories appelées à fréquenter le port."
    
    def _generate_remorqueurs(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("remorqueurs", rapport_data)
        return self._generate_with_ai("remorqueurs", prompt) or \
            "Les moyens d'assistance comprennent des remorqueurs adaptés aux navires étudiés."
    
    def _generate_simulations(self, rapport_data: dict) -> str:
        simulations = rapport_data.get("simulations", {})
        nb = len(simulations.get("simulations", []))
        prompt = self._build_prompt("simulations", rapport_data)
        result = self._generate_with_ai("simulations", prompt)
        return result or f"La méthodologie repose sur {nb} simulations numériques représentatives."
    
    def _generate_scenarios_urgence(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("scenarios_urgence", rapport_data)
        return self._generate_with_ai("scenarios_urgence", prompt) or \
            "Les scénarios d'urgence testent la réaction en cas de défaillance des équipements."
    
    def _generate_conclusion(self, rapport_data: dict) -> str:
        prompt = self._build_prompt("conclusion", rapport_data)
        return self._generate_with_ai("conclusion", prompt) or self._fallback_conclusion(rapport_data)
    
    # =========================================================================
    # FALLBACKS
    # =========================================================================
    
    def _generate_fallback_sections(self, rapport_data: dict) -> dict:
        """Génère toutes les sections en mode fallback"""
        print("⚠️ Mode fallback complet")
        
        sections = {}
        for section_name in self.section_generators.keys():
            try:
                sections[section_name] = self._get_fallback_for_section(section_name, rapport_data)
            except:
                pass
        
        return sections
    
    def _get_fallback_for_section(self, section_name: str, rapport_data: dict) -> str:
        """Retourne le fallback pour une section"""
        fallbacks = {
            "introduction": self._fallback_introduction(rapport_data),
            "analyse": self._fallback_analyse(rapport_data),
            "conclusion": self._fallback_conclusion(rapport_data),
            "donnees_entree_intro": "Cette section présente les données d'entrée de l'étude.",
            "donnees_entree_conditions_intro": "Les conditions environnementales influencent la manœuvrabilité.",
            "donnees_entree_bathymetrie": "La bathymétrie a été établie à partir de relevés récents.",
            "donnees_entree_houle": "Les conditions de houle correspondent aux états de mer caractéristiques.",
            "donnees_entree_vent": "Les données de vent représentent les conditions météorologiques locales.",
            "donnees_entree_courant": "Les conditions de courant intègrent les effets de marée.",
            "donnees_entree_maree": "Le régime de marée définit les variations du niveau d'eau.",
            "donnees_entree_agitation": "L'agitation résiduelle influence les conditions de manœuvre.",
            "donnees_entree_synthese": "La synthèse des données permet de définir les conditions représentatives.",
            "analyse_stats": "Statistiques des simulations : taux de réussite, répartition par manœuvre.",
            "analyse_recommandations": "Recommandations : seuils météo, configuration remorqueurs.",
            "navires": "La sélection des navires représente les catégories appelées à fréquenter le port.",
            "remorqueurs": "Les moyens d'assistance comprennent des remorqueurs adaptés.",
            "simulations": "La méthodologie repose sur une approche numérique temps réel.",
            "scenarios_urgence": "Les scénarios d'urgence évaluent la réaction en cas de défaillance.",
        }
        
        meta = rapport_data.get("metadonnees", {})
        titre = meta.get("titre", "Étude")
        
        return fallbacks.get(section_name, f"Section {section_name} de l'étude {titre}.")
    
    def _fallback_introduction(self, rapport_data: dict) -> str:
        meta = rapport_data.get("metadonnees", {})
        titre = meta.get("titre", "Étude de manœuvrabilité")
        client = meta.get("client", "l'Autorité Portuaire")
        
        return f"""L'étude de manœuvrabilité intitulée "{titre}" a été réalisée pour {client}. Cette étude vise à évaluer les capacités de manœuvre des navires dans les configurations portuaires étudiées.

Les objectifs principaux comprennent l'évaluation de la faisabilité des manœuvres d'accostage et d'appareillage, l'identification des conditions environnementales critiques, et la définition des procédures d'assistance optimales.

La méthodologie employée s'appuie sur la modélisation numérique et la simulation de manœuvres représentatives des conditions d'exploitation futures."""
    
    def _fallback_analyse(self, rapport_data: dict) -> str:
        simulations = rapport_data.get("simulations", {}).get("simulations", [])
        nb = len(simulations)
        
        if simulations:
            nb_ok = sum(1 for s in simulations if s.get("resultat") == "Réussite")
            taux = round((nb_ok / nb) * 100, 1) if nb > 0 else 0
            
            return f"""L'analyse des {nb} simulations révèle un taux de réussite de {taux}%. Les configurations testées permettent d'évaluer la faisabilité des manœuvres dans diverses conditions.

Les résultats montrent l'importance de l'assistance par remorqueurs pour garantir la sécurité des opérations."""
        
        return "L'analyse des simulations révèle les performances générales du système portuaire étudié."
    
    def _fallback_conclusion(self, rapport_data: dict) -> str:
        meta = rapport_data.get("metadonnees", {})
        titre = meta.get("titre", "Étude de manœuvrabilité")
        simulations = rapport_data.get("simulations", {}).get("simulations", [])
        
        if simulations:
            nb = len(simulations)
            nb_ok = sum(1 for s in simulations if s.get("resultat") == "Réussite")
            taux = round((nb_ok / nb) * 100, 1) if nb > 0 else 0
            
            return f"""L'étude de manœuvrabilité "{titre}" a permis d'évaluer {nb} configurations de manœuvre avec un taux de réussite de {taux}%.

Les résultats confirment la faisabilité des opérations dans les conditions nominales définies. Les recommandations formulées permettront d'optimiser la sécurité et l'efficacité des manœuvres."""
        
        return f"L'étude \"{titre}\" a permis d'évaluer les conditions de manœuvrabilité et de formuler des recommandations opérationnelles."
    
    def _print_stats(self, stats: dict, total: int):
        """Affiche les statistiques"""
        self._log(f"\n📊 Statistiques:")
        self._log(f"  ✅ Succès: {stats['success']}/{total}")
        self._log(f"  📚 Avec examples: {stats.get('with_examples', 0)}/{total}")
        self._log(f"  ⚠️ Fallback: {stats['fallback']}/{total}")
        self._log(f"  ❌ Échecs: {stats['failed']}/{total}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retourne le statut du système"""
        status = {
            "overall_readiness": 0,
            "training_available": False,
            "examples_count": 0,
            "api_available": REQUESTS_AVAILABLE,
            "sections_count": len(self.section_generators),
            "model": self.default_model,
            "few_shot_enabled": False,
            "recommendation": "",
        }
        
        if self.load_training_data():
            status["training_available"] = True
            status["few_shot_enabled"] = True
            status["examples_count"] = sum(len(ex) for ex in self.training_data.values() if isinstance(ex, list))
            status["overall_readiness"] = 70
            
            if REQUESTS_AVAILABLE:
                status["overall_readiness"] = 95
                status["recommendation"] = "✅ Système opérationnel avec few-shot examples"
            else:
                status["recommendation"] = "⚠️ API non disponible - Mode fallback"
        else:
            status["recommendation"] = "❌ Entraînement requis - Exécuter: python training_manager.py force-granular"
        
        return status

    def _log(self, message: str):
        if self.verbose:
            print(message)


# =============================================================================
# INTERFACES PUBLIQUES
# =============================================================================

def create_pretrained_manager() -> PretrainedManager:
    """Crée un gestionnaire"""
    return PretrainedManager()


def generate_granular_sections_for_report(rapport_data: dict, 
                                          sections_requested: List[str] = None,
                                          progress_mgr=None,
                                          progress_range=None) -> dict:
    """Interface principale - Génère les sections avec agents pré-entraînés + few-shot"""
    try:
        manager = create_pretrained_manager()
        if progress_mgr:
            progress_mgr.log_detail("Démarrage de la génération IA (agents pré-entraînés + few-shot)")
        
        try:
            result = manager.generate_granular_sections_for_report(
                rapport_data, sections_requested,
                progress_mgr=progress_mgr,
                progress_range=progress_range
            )
        except TypeError:
            result = manager.generate_granular_sections_for_report(rapport_data, sections_requested)
        
        if progress_mgr:
            progress_mgr.log_detail("Sections IA générées")
        return result
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return {}


def get_granular_system_status() -> Dict[str, Any]:
    """Retourne le statut du système"""
    try:
        manager = create_pretrained_manager()
        return manager.get_system_status()
    except Exception as e:
        return {"error": str(e), "overall_readiness": 0}
