import os
import json
import docx
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class TrainingManager:
    """Gestionnaire d'entraînement granulaire pour TOUTES les sections"""
    
    def __init__(self, 
                 reports_directory: str = "examples",
                 cache_directory: str = "agents/training_cache",
                 prompts_directory: str = "prompts"):
        
        self.reports_directory = Path(reports_directory)
        self.cache_directory = Path(cache_directory)
        self.prompts_directory = Path(prompts_directory)
        
        # Créer les dossiers
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        self.reports_directory.mkdir(exist_ok=True)
        
        # Fichiers de cache
        self.extracted_cache = self.cache_directory / "extracted_examples_granular.json"
        self.training_cache = self.cache_directory / "training_data_granular.json"
        self.metadata_cache = self.cache_directory / "training_metadata_granular.json"
        self.prompts_cache = self.cache_directory / "prompts_mapping_granular.json"
         
        # Configuration Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.prompts_directory)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 🎯 MAPPING GRANULAIRE COMPLET - Toutes les sections/sous-sections
        self.granular_section_mapping = {
            # Sections principales
            "introduction": "introduction.txt",
            "analyse": "analyse.txt", 
            "conclusion": "conclusion.txt",
            
            # Données d'entrée - GRANULAIRE
            "donnees_entree_intro": "donnees_entree_intro.txt",
            "donnees_entree_plan_masse": "donnees_entree_plan_masse.txt",
            "donnees_entree_bathymetrie": "donnees_entree_bathymetrie.txt",
            "donnees_entree_balisage": "donnees_entree_balisage.txt",
            "donnees_entree_conditions_intro": "donnees_entree_conditions_intro.txt",
            "donnees_entree_houle": "donnees_entree_houle.txt",
            "donnees_entree_vent": "donnees_entree_vent.txt",
            "donnees_entree_courant": "donnees_entree_courant.txt",
            "donnees_entree_maree": "donnees_entree_maree.txt",
            "donnees_entree_agitation": "donnees_entree_agitation.txt",
            "donnees_entree_synthese": "donnees_entree_synthese.txt",
            
            # Navires - GRANULAIRE
            "navires": "navires.txt",
            "remorqueurs": "remorqueurs.txt",
            
            # Simulations - GRANULAIRE
            "simulations": "simulations.txt",
            "scenarios_urgence": "scenarios_urgence.txt"
        }
        
        # 🔍 PATTERNS D'EXTRACTION GRANULAIRES
        self.granular_extraction_patterns = {
            # Introduction
            "introduction": [
                r"(?i)(?:1\.?\s*)?introduction.*?(?=(?:\n\s*\d+\.|\n\s*[IVX]+\.|\Z))",
                r"(?i)(?:contexte|présentation|objectif).*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            
            # Données d'entrée - GRANULAIRE
            "donnees_entree_plan_masse": [
                r"(?i)plan\s+de\s+masse.*?(?=(?:\n\s*\d+\.|\n\s*[A-Z]\.|\Z))",
                r"(?i)aménagement.*?portuaire.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            "donnees_entree_bathymetrie": [
                r"(?i)bathym[éè]trie.*?(?=(?:\n\s*\d+\.|\n\s*[A-Z]\.|\Z))",
                r"(?i)profondeur.*?fond.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            "donnees_entree_balisage": [
                r"(?i)balisage.*?(?=(?:\n\s*\d+\.|\n\s*[A-Z]\.|\Z))",
                r"(?i)signalisation.*?maritime.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            "donnees_entree_houle": [
                r"(?i)houle.*?(?=(?:\n\s*\d+\.|\n\s*[A-Z]\.|\Z))",
                r"(?i)vagues.*?hauteur.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            "donnees_entree_vent": [
                r"(?i)vent.*?(?=(?:\n\s*\d+\.|\n\s*[A-Z]\.|\Z))",
                r"(?i)force.*?direction.*?vent.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            "donnees_entree_courant": [
                r"(?i)courant.*?(?=(?:\n\s*\d+\.|\n\s*[A-Z]\.|\Z))",
                r"(?i)vitesse.*?courant.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            "donnees_entree_maree": [
                r"(?i)mar[ée]e.*?(?=(?:\n\s*\d+\.|\n\s*[A-Z]\.|\Z))",
                r"(?i)niveau.*?eau.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            "donnees_entree_agitation": [
                r"(?i)agitation.*?(?=(?:\n\s*\d+\.|\n\s*[A-Z]\.|\Z))",
                r"(?i)oscillation.*?port.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            
            # Navires - GRANULAIRE
            "navires": [
                r"(?i)(?:navires?\s+[àa]\s+tester|s[ée]lection.*?navires?).*?(?=(?:\n\s*\d+\.|\Z))",
                r"(?i)caract[ée]ristiques.*?navires?.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            "remorqueurs": [
                r"(?i)remorqueurs?.*?(?=(?:\n\s*\d+\.|\n\s*[A-Z]\.|\Z))",
                r"(?i)assistance.*?pilotage.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            
            # Simulations - GRANULAIRE
            "simulations": [
                r"(?i)(?:essais\s+r[ée]alis[ée]s|simulations?).*?(?=(?:\n\s*\d+\.|\Z))",
                r"(?i)m[ée]thodologie.*?simulation.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            "scenarios_urgence": [
                r"(?i)(?:sc[ée]narios?\s+d['']urgence|situations?\s+d['']urgence).*?(?=(?:\n\s*\d+\.|\Z))",
                r"(?i)proc[ée]dures?\s+d['']urgence.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            
            # Analyse - GRANULAIRE
            "analyse": [
                r"(?i)(?:4\.?\s*)?analyse.*?r[ée]sultats.*?(?=(?:\n\s*\d+\.|\Z))",
                r"(?i)statistiques.*?g[ée]n[ée]rales.*?(?=(?:\n\s*\d+\.|\Z))"
            ],
            
            # Conclusion
            "conclusion": [
                r"(?i)(?:5\.?\s*)?conclusion.*?(?=(?:\n\s*\d+\.|\Z))",
                r"(?i)recommandations.*?(?=(?:\n\s*\d+\.|\Z))"
            ]
        }
        
        print(f"🎯 TrainingManager initialisé")
        print(f"🔍 Sections granulaires: {len(self.granular_section_mapping)}")
    
    def force_retrain_granular(self) -> Dict[str, Any]:
        """Force le ré-entraînement granulaire complet"""
        
        print("\n" + "="*70)
        print("🔥 FORÇAGE DU RÉ-ENTRAÎNEMENT GRANULAIRE")
        print("="*70)
        
        # 1. Analyser les prompts disponibles
        print("\n📝 PHASE 1: Analyse des prompts granulaires")
        prompts_analysis = self._analyze_granular_prompts()
        
        # 2. Supprimer le cache existant
        print("\n🧹 PHASE 2: Suppression du cache")
        self._clear_cache()
        
        # 3. Extraire TOUTES les sections granulaires
        print("\n📚 PHASE 3: Extraction granulaire complète")
        extracted_data = self._extract_granular_examples()
        
        if not extracted_data or not any(extracted_data.values()):
            print("❌ Aucun exemple extrait")
            return {"status": "failed", "reason": "no_examples"}
        
        # 4. Traiter avec intégration prompts granulaires
        print("\n🔧 PHASE 4: Traitement granulaire avec prompts")
        training_data = self._process_granular_training_data(extracted_data, prompts_analysis)
        
        # 5. Sauvegarder
        print("\n💾 PHASE 5: Sauvegarde granulaire")
        self._save_granular_cache(extracted_data, training_data, prompts_analysis)
        
        # 6. Générer métadonnées
        metadata = self._generate_granular_metadata(training_data, prompts_analysis)
        
        print("\n✅ RÉ-ENTRAÎNEMENT GRANULAIRE TERMINÉ")
        self._print_granular_summary(metadata)
        
        return metadata
    
    def _analyze_granular_prompts(self) -> Dict[str, Any]:
        """Analyse TOUS les prompts granulaires disponibles"""
        
        analysis = {
            "available_prompts": {},
            "missing_prompts": [],
            "total_prompts": 0,
            "sections_covered": [],
            "granular_coverage": {
                "donnees_entree": 0,
                "navires": 0,
                "simulations": 0,
                "analyse": 0,
                "general": 0
            }
        }
        
        print(f"🔍 Analyse granulaire du dossier: {self.prompts_directory}")
        
        if not self.prompts_directory.exists():
            print(f"❌ Dossier prompts non trouvé: {self.prompts_directory}")
            return analysis
        
        # Vérifier chaque mapping granulaire
        for section_name, prompt_file in self.granular_section_mapping.items():
            prompt_path = self.prompts_directory / prompt_file
            
            if prompt_path.exists():
                try:
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if content:
                        analysis["available_prompts"][section_name] = {
                            "file": prompt_file,
                            "path": str(prompt_path),
                            "content": content,
                            "length": len(content),
                            "variables": self._extract_jinja_variables(content),
                            "has_conditions": "{% if" in content,
                            "has_loops": "{% for" in content,
                            "category": self._categorize_section(section_name)
                        }
                        
                        # Compter par catégorie
                        category = self._categorize_section(section_name)
                        if category in analysis["granular_coverage"]:
                            analysis["granular_coverage"][category] += 1
                        
                        print(f"  ✅ {section_name}: {prompt_file} ({len(content)} chars)")
                        
                        # Analyser les sections principales
                        if section_name in ["introduction", "analyse", "conclusion"]:
                            analysis["sections_covered"].append(section_name)
                    else:
                        print(f"  ⚠️ {section_name}: {prompt_file} (vide)")
                        analysis["missing_prompts"].append(section_name)
                
                except Exception as e:
                    print(f"  ❌ {section_name}: {prompt_file} (erreur: {e})")
                    analysis["missing_prompts"].append(section_name)
            else:
                print(f"  ❌ {section_name}: {prompt_file} (non trouvé)")
                analysis["missing_prompts"].append(section_name)
        
        analysis["total_prompts"] = len(analysis["available_prompts"])
        
        print(f"\n📊 Résultats granulaires:")
        print(f"  ✅ Prompts trouvés: {analysis['total_prompts']}")
        print(f"  ❌ Prompts manquants: {len(analysis['missing_prompts'])}")
        print(f"  🎯 Sections principales: {len(analysis['sections_covered'])}/3")
        print(f"  📊 Données d'entrée: {analysis['granular_coverage']['donnees_entree']}")
        print(f"  🚢 Navires: {analysis['granular_coverage']['navires']}")
        print(f"  🌀 Simulations: {analysis['granular_coverage']['simulations']}")
        print(f"  📈 Analyse: {analysis['granular_coverage']['analyse']}")
        
        return analysis
    
    def _categorize_section(self, section_name: str) -> str:
        """Catégorise une section pour les statistiques"""
        if section_name.startswith("donnees_entree"):
            return "donnees_entree"
        elif section_name.startswith("navires") or section_name.startswith("remorqueurs"):
            return "navires"
        elif section_name.startswith("simulations") or section_name.startswith("scenarios"):
            return "simulations"
        elif section_name.startswith("analyse"):
            return "analyse"
        else:
            return "general"
    
    def _extract_granular_examples(self) -> Dict[str, List[Dict]]:
        """Extrait TOUS les exemples granulaires de tous les rapports"""
        
        if not self.reports_directory.exists():
            print(f"❌ Dossier {self.reports_directory} non trouvé")
            return {}
        
        all_files = []
        for ext in ['.docx', '.pdf']:
            all_files.extend(list(self.reports_directory.glob(f"*{ext}")))
        
        if not all_files:
            print(f"❌ Aucun fichier dans {self.reports_directory}")
            return {}
        
        print(f"📄 {len(all_files)} fichiers trouvés pour extraction granulaire")
        
        # Initialiser les conteneurs pour TOUTES les sections granulaires
        extracted_examples = {}
        for section_name in self.granular_section_mapping.keys():
            extracted_examples[section_name] = []
        
        processed_count = 0
        for file_path in all_files:
            try:
                print(f"🔄 Traitement granulaire: {file_path.name}")
                
                # Extraction selon le type de fichier
                if file_path.suffix.lower() == '.pdf':
                    sections = self._extract_granular_sections_from_pdf(file_path)
                else:
                    sections = self._extract_granular_sections_from_docx(file_path)
                
                # Traiter TOUTES les sections trouvées
                for section_name, content in sections.items():
                    if content and section_name in extracted_examples:
                        metadata = self._analyze_granular_content_metadata(content, section_name)
                        quality_score = self._calculate_granular_quality_score(content, section_name)
                        
                        if quality_score >= 0.2:  # Seuil plus bas pour sections granulaires
                            example = {
                                "source_file": file_path.name,
                                "content": content,
                                "metadata": metadata,
                                "quality_score": quality_score,
                                "word_count": len(content.split()),
                                "section_category": self._categorize_section(section_name),
                                "extraction_date": datetime.now().isoformat()
                            }
                            extracted_examples[section_name].append(example)
                            print(f"    ✅ {section_name}: {len(content)} chars (Q: {quality_score:.2f})")
                        else:
                            print(f"    ⚠️ {section_name}: qualité trop faible ({quality_score:.2f})")
                
                processed_count += 1
                
            except Exception as e:
                print(f"❌ Erreur granulaire: {e}")
        
        print(f"\n📊 Extraction granulaire terminée: {processed_count} rapports traités")
        
        # Afficher résumé granulaire
        total_examples = 0
        for section_name, examples in extracted_examples.items():
            count = len(examples)
            total_examples += count
            if count > 0:
                avg_quality = sum(ex["quality_score"] for ex in examples) / count
                category = self._categorize_section(section_name)
                print(f"  📋 {section_name} ({category}): {count} exemples (Q: {avg_quality:.2f})")
        
        print(f"\n🎯 Total granulaire: {total_examples} exemples dans {len([s for s in extracted_examples.values() if s])} sections")
        
        return extracted_examples
    
    def _extract_granular_sections_from_docx(self, docx_path: Path) -> Dict[str, str]:
        """Extrait TOUTES les sections granulaires d'un rapport Word"""
        try:
            doc = docx.Document(str(docx_path))
            full_text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
            
            sections = {}
            for section_name, patterns in self.granular_extraction_patterns.items():
                content = self._extract_section_content(full_text, patterns)
                if content:
                    sections[section_name] = content
            
            return sections
            
        except Exception as e:
            print(f"❌ Erreur lecture granulaire {docx_path}: {e}")
            return {}
    
    def _extract_granular_sections_from_pdf(self, pdf_path: Path) -> Dict[str, str]:
        """Extrait TOUTES les sections granulaires d'un PDF"""
        
        if not PDF_AVAILABLE:
            print(f"⚠️ PyPDF2 non installé - PDF ignoré: {pdf_path.name}")
            return {}
        
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if len(text.strip()) < 100:
                print(f"    ⚠️ PDF {pdf_path.name}: texte insuffisant")
                return {}
            
            # Nettoyer le texte PDF
            text = self._clean_pdf_text(text)
            
            # Extraire toutes les sections granulaires
            sections = {}
            for section_name, patterns in self.granular_extraction_patterns.items():
                content = self._extract_section_content(text, patterns)
                if content:
                    sections[section_name] = content
            
            return sections
            
        except Exception as e:
            print(f"❌ Erreur extraction PDF granulaire {pdf_path.name}: {e}")
            return {}
    
    def _analyze_granular_content_metadata(self, content: str, section_name: str) -> Dict[str, Any]:
        """Analyse les métadonnées granulaires du contenu"""
        
        metadata = {
            "length_words": len(content.split()),
            "length_chars": len(content),
            "section_category": self._categorize_section(section_name),
            "technical_density": 0,
            "has_quantitative_data": False,
            "specific_mentions": {}
        }
        
        content_lower = content.lower()
        
        # Mentions spécifiques selon la catégorie
        if section_name.startswith("donnees_entree"):
            metadata["specific_mentions"] = {
                "profondeur": content_lower.count("profondeur") + content_lower.count("fond"),
                "metres": len(re.findall(r'\d+[\s]*m(?:ètres?)?', content)),
                "conditions": content_lower.count("condition"),
                "donnees": content_lower.count("données") + content_lower.count("donnees")
            }
        elif section_name.startswith("navires"):
            metadata["specific_mentions"] = {
                "navires": content_lower.count("navire"),
                "longueur": content_lower.count("longueur"),
                "tirant_eau": content_lower.count("tirant"),
                "caracteristiques": content_lower.count("caractéristique")
            }
        elif section_name.startswith("simulations"):
            metadata["specific_mentions"] = {
                "simulations": content_lower.count("simulation"),
                "essais": content_lower.count("essai"),
                "scenarios": content_lower.count("scénario"),
                "tests": content_lower.count("test")
            }
        elif section_name.startswith("analyse"):
            metadata["specific_mentions"] = {
                "resultats": content_lower.count("résultat"),
                "performance": content_lower.count("performance"),
                "reussite": content_lower.count("réussite"),
                "echec": content_lower.count("échec")
            }
        
        # Densité technique générale
        total_mentions = sum(metadata["specific_mentions"].values())
        if len(content.split()) > 0:
            metadata["technical_density"] = total_mentions / len(content.split())
        
        # Données quantitatives
        metadata["has_quantitative_data"] = bool(re.search(r'\d+[%\s]*(?:kts?|m|km|°|nœuds|Hz|s)', content))
        
        return metadata
    
    def _calculate_granular_quality_score(self, content: str, section_name: str) -> float:
        """Calcule un score de qualité granulaire adapté à chaque type de section"""
        
        if not content:
            return 0.0
        
        score = 0.0
        word_count = len(content.split())
        metadata = self._analyze_granular_content_metadata(content, section_name)
        
        # Plages optimales adaptées par catégorie
        optimal_ranges = {
            "introduction": (200, 600),
            "analyse": (300, 1000),
            "conclusion": (150, 500),
            "donnees_entree_intro": (100, 300),
            "donnees_entree_plan_masse": (50, 200),
            "donnees_entree_bathymetrie": (50, 200),
            "donnees_entree_houle": (50, 150),
            "donnees_entree_vent": (50, 150),
            "donnees_entree_courant": (50, 150),
            "donnees_entree_maree": (50, 150),
            "navires": (100, 400),
            "remorqueurs": (50, 200),
            "simulations": (150, 500),
            "scenarios_urgence": (100, 300)
        }
        
        # Plage par défaut pour sections non spécifiées
        min_words, max_words = optimal_ranges.get(section_name, (50, 300))
        
        # Score basé sur la longueur
        if min_words <= word_count <= max_words:
            score += 0.4
        elif word_count >= min_words * 0.5:
            score += 0.2
        
        # Score basé sur la densité technique
        tech_density = metadata["technical_density"]
        if tech_density > 0.05:
            score += 0.3
        elif tech_density > 0.02:
            score += 0.2
        elif tech_density > 0.01:
            score += 0.1
        
        # Score basé sur la structure
        sentence_count = content.count('.')
        if sentence_count >= 2:
            score += 0.2
        elif sentence_count >= 1:
            score += 0.1
        
        # Bonus pour données quantitatives
        if metadata["has_quantitative_data"]:
            score += 0.1
        
        return min(score, 1.0)
    
    def _process_granular_training_data(self, extracted_data: Dict, prompts_analysis: Dict) -> Dict[str, List[Dict]]:
        """Traite les données granulaires avec intégration des prompts"""
        
        processed_data = {}
        
        for section_name, examples in extracted_data.items():
            if not examples:
                processed_data[section_name] = []
                continue
            
            print(f"🔧 Traitement granulaire {section_name}: {len(examples)} exemples")
            
            # Trier par qualité
            examples.sort(key=lambda x: x["quality_score"], reverse=True)
            
            # Sélectionner les meilleurs (max 3 par section granulaire)
            max_examples = 20 if self._categorize_section(section_name) != "general" else 30
            best_examples = examples[:max_examples]
            
            # Enrichir avec les prompts granulaires
            for example in best_examples:
                # Ajouter les informations de prompt
                if section_name in prompts_analysis["available_prompts"]:
                    prompt_info = prompts_analysis["available_prompts"][section_name]
                    example["prompt_template"] = prompt_info["content"]
                    example["prompt_variables"] = prompt_info["variables"]
                    example["prompt_file"] = prompt_info["file"]
                    example["has_custom_prompt"] = True
                else:
                    example["has_custom_prompt"] = False
                    example["prompt_template"] = self._generate_granular_fallback_prompt(section_name)
                
                # Générer des prompts d'entraînement contextualisés granulaires
                example["training_prompt"] = self._generate_granular_contextual_training_prompt(example, section_name)
                example["training_weight"] = self._calculate_granular_training_weight(example)
            
            processed_data[section_name] = best_examples
            print(f"  ✅ {len(best_examples)} exemples granulaires enrichis")
        
        return processed_data
    
    def _generate_granular_contextual_training_prompt(self, example: Dict, section_name: str) -> str:
        """Génère un prompt d'entraînement contextualisé granulaire"""
        
        if example.get("has_custom_prompt"):
            # Utiliser le vrai prompt avec des données mockées granulaires
            prompt_template = example["prompt_template"]
            
            # Créer un contexte mock granulaire
            mock_context = self._create_granular_mock_context(example, section_name)
            
            try:
                template = Template(prompt_template)
                rendered_prompt = template.render(**mock_context)
                return rendered_prompt
            except Exception as e:
                print(f"    ⚠️ Erreur rendu prompt granulaire {section_name}: {e}")
                return self._generate_granular_fallback_prompt(section_name)
        else:
            return self._generate_granular_fallback_prompt(section_name)
    
    def _create_granular_mock_context(self, example: Dict, section_name: str) -> Dict:
        """Crée un contexte mock granulaire adapté à chaque section"""
        
        metadata = example.get("metadata", {})
        category = self._categorize_section(section_name)
        
        # Contexte de base commun
        base_context = {
            "metadonnees": {
                "titre": "Étude de Manœuvrabilité - Terminal Conteneurs",
                "client": "Autorité Portuaire",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "port": "Port de Tanger Med"
            }
        }
        
        # Contexte spécifique par catégorie
        if category == "donnees_entree":
            base_context.update({
                "donnees_entree": {
                    "bathymetrie": {
                        "source": "Relevé bathymétrique 2024",
                        "profondeur_minimale": "12.5m",
                        "profondeur_maximale": "18.0m",
                        "commentaire": "Bathymétrie adaptée aux navires de grande taille"
                    },
                    "conditions_environnementales": {
                        "houle": {
                            "valeurs_retenues": "Hs = 2.5m, Tp = 8s",
                            "direction": "Nord-Ouest",
                            "commentaire": "Conditions de houle modérées"
                        },
                        "vent": {
                            "valeurs_retenues": "30 kts, rafales 40 kts",
                            "direction": "Ouest",
                            "commentaire": "Vent dominant d'ouest"
                        },
                        "courant": {
                            "valeurs_retenues": "1.5 kts",
                            "direction": "Est-Nord-Est",
                            "commentaire": "Courant de marée"
                        },
                        "maree": {
                            "valeurs_retenues": "Marnage 4.2m",
                            "type": "Semi-diurne",
                            "commentaire": "Marée atlantique"
                        },
                        "agitation": {
                            "valeurs_retenues": "0.5m à 0.8m",
                            "periode": "6-12s",
                            "commentaire": "Agitation résiduelle dans le port"
                        }
                    },
                    "plan_de_masse": {
                        "phases": [
                            {"nom": "Phase 1", "description": "Configuration actuelle"},
                            {"nom": "Phase 2", "description": "Extension terminale"}
                        ]
                    }
                }
            })
        
        elif category == "navires":
            base_context.update({
                "navires_liste": [
                    {
                        "nom": "Cargo 1200 EVP",
                        "type": "Porte-conteneurs",
                        "longueur": "210m",
                        "largeur": "32m",
                        "tirant_eau_av": "9.5m",
                        "tirant_eau_ar": "10.2m"
                    },
                    {
                        "nom": "Cargo 800 EVP",
                        "type": "Porte-conteneurs",
                        "longueur": "180m",
                        "largeur": "28m",
                        "tirant_eau_av": "8.5m",
                        "tirant_eau_ar": "9.0m"
                    }
                ],
                "remorqueurs_liste": [
                    {
                        "nom": "Remorqueur RT-01",
                        "type": "Azimuth",
                        "longueur": "28m",
                        "largeur": "12m",
                        "puissance": "3000 kW"
                    }
                ]
            })
        
        elif category == "simulations":
            base_context.update({
                "simulations": {
                    "simulations": [
                        {
                            "numero_essai_original": 1,
                            "navire": "Cargo 1200 EVP",
                            "condition": "Normale",
                            "resultat": "Réussite",
                            "manoeuvre": "Accostage",
                            "remorqueurs": "2 remorqueurs",
                            "commentaire_pilote": "Manœuvre réalisée sans difficulté"
                        },
                        {
                            "numero_essai_original": 2,
                            "navire": "Cargo 800 EVP",
                            "condition": "Vent fort",
                            "resultat": "Échec",
                            "manoeuvre": "Accostage",
                            "remorqueurs": "1 remorqueur",
                            "commentaire_pilote": "Assistance insuffisante par vent fort"
                        }
                    ]
                },
                "nb_simulations": 15,
                "simulations_description": "Méthodologie basée sur la simulation numérique temps réel"
            })
        
        elif category == "analyse":
            base_context.update({
                "analyse_synthese": {
                    "nombre_essais": 15,
                    "nombre_reussis": 12,
                    "nombre_echecs": 3,
                    "taux_reussite_pct": 80.0,
                    "nombre_scenarios_urgence": 3,
                    "conditions_critiques_liste": [
                        "Vent supérieur à 35 kts avec courant opposé",
                        "Combinaison houle + vent de travers",
                        "Visibilité réduite avec vent fort"
                    ],
                    "commentaire": "L'analyse révèle une bonne performance générale des manœuvres"
                }
            })
        
        # Enrichir selon les mentions spécifiques
        if section_name.endswith("_houle"):
            base_context["houle_conditions"] = True
        if section_name.endswith("_vent"):
            base_context["vent_conditions"] = True
        if section_name.endswith("_courant"):
            base_context["courant_conditions"] = True
        if section_name.endswith("_maree"):
            base_context["maree_conditions"] = True
        if section_name.endswith("_agitation"):
            base_context["agitation_conditions"] = True
        
        return base_context
    
    def _generate_granular_fallback_prompt(self, section_name: str) -> str:
        """Génère un prompt de fallback granulaire spécifique"""
        
        fallback_prompts = {
            # Sections principales
            "introduction": "Tu es un ingénieur maritime expert. Rédige l'introduction d'un rapport de manœuvrabilité professionnel.",
            "analyse": "Tu es un expert en simulations. Analyse les résultats des simulations de manœuvrabilité.",
            "conclusion": "Tu es un ingénieur maritime. Rédige la conclusion d'un rapport de manœuvrabilité.",
            
            # Données d'entrée granulaires
            "donnees_entree_intro": "Présente les données d'entrée d'une étude de manœuvrabilité.",
            "donnees_entree_plan_masse": "Décris le plan de masse et l'aménagement portuaire.",
            "donnees_entree_bathymetrie": "Présente les données bathymétriques du site d'étude.",
            "donnees_entree_balisage": "Décris le plan de balisage et la signalisation maritime.",
            "donnees_entree_houle": "Présente les conditions de houle retenues pour l'étude.",
            "donnees_entree_vent": "Décris les conditions de vent considérées.",
            "donnees_entree_courant": "Présente les données de courant utilisées.",
            "donnees_entree_maree": "Décris les conditions de marée retenues.",
            "donnees_entree_agitation": "Présente l'agitation portuaire considérée.",
            "donnees_entree_synthese": "Synthétise l'ensemble des données environnementales.",
            
            # Navires granulaires
            "navires": "Présente les navires sélectionnés pour l'étude de manœuvrabilité.",
            "remorqueurs": "Présente les remorqueurs et moyens d'assistance.",
            
            # Simulations granulaires
            "simulations": "Présente la méthodologie des simulations de manœuvrabilité.",
            "scenarios_urgence": "Décris les scénarios d'urgence étudiés."
        }
        
        return fallback_prompts.get(section_name, f"Rédige la section {section_name} d'un rapport technique de manœuvrabilité.")
    
    def _calculate_granular_training_weight(self, example: Dict) -> float:
        """Calcule un poids d'entraînement granulaire"""
        
        base_weight = example["quality_score"]
        
        # Bonus si prompt custom disponible
        if example.get("has_custom_prompt"):
            base_weight += 0.15
        
        # Bonus pour la spécificité de la section
        category = example.get("section_category", "general")
        category_bonus = {
            "donnees_entree": 0.1,
            "navires": 0.1,
            "simulations": 0.15,
            "analyse": 0.15,
            "general": 0.05
        }.get(category, 0)
        
        # Bonus pour la densité technique
        metadata = example.get("metadata", {})
        tech_bonus = min(metadata.get("technical_density", 0) * 2, 0.2)
        
        # Bonus quantitatif
        quantitative_bonus = 0.1 if metadata.get("has_quantitative_data") else 0
        
        return min(base_weight + category_bonus + tech_bonus + quantitative_bonus, 1.0)
    
    def _save_granular_cache(self, extracted_data: Dict, training_data: Dict, prompts_analysis: Dict):
        """Sauvegarde le cache granulaire enrichi"""
        
        # Cache des exemples extraits granulaires
        with open(self.extracted_cache, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        
        # Cache des données d'entraînement granulaires
        with open(self.training_cache, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)
        
        # Cache du mapping prompts granulaires
        with open(self.prompts_cache, 'w', encoding='utf-8') as f:
            json.dump(prompts_analysis, f, ensure_ascii=False, indent=2)
        
        print("✅ Cache granulaire enrichi sauvegardé")
    
    def _generate_granular_metadata(self, training_data: Dict, prompts_analysis: Dict) -> Dict[str, Any]:
        """Génère des métadonnées granulaires enrichies"""
        
        metadata = {
            "training_date": datetime.now().isoformat(),
            "training_type": "granular_v2",
            "forced_retrain": True,
            "prompts_integration": True,
            "reports_directory": str(self.reports_directory),
            "prompts_directory": str(self.prompts_directory),
            "total_examples": sum(len(examples) for examples in training_data.values()),
            "total_sections": len(self.granular_section_mapping),
            "prompts_analysis": prompts_analysis,
            "sections": {},
            "quality_stats": {},
            "granular_coverage": {
                "donnees_entree": 0,
                "navires": 0,
                "simulations": 0,
                "analyse": 0,
                "general": 0
            }
        }
        
        # Statistiques granulaires par section
        all_qualities = []
        for section_name, examples in training_data.items():
            category = self._categorize_section(section_name)
            
            if examples:
                qualities = [ex["quality_score"] for ex in examples]
                weights = [ex["training_weight"] for ex in examples]
                word_counts = [ex["word_count"] for ex in examples]
                custom_prompts = sum(1 for ex in examples if ex.get("has_custom_prompt"))
                
                metadata["sections"][section_name] = {
                    "count": len(examples),
                    "category": category,
                    "avg_quality": sum(qualities) / len(qualities),
                    "best_quality": max(qualities),
                    "avg_weight": sum(weights) / len(weights),
                    "avg_words": sum(word_counts) / len(word_counts),
                    "custom_prompts": custom_prompts,
                    "prompt_coverage": custom_prompts / len(examples),
                    "best_sources": [ex["source_file"] for ex in examples[:2]]
                }
                
                # Compter par catégorie
                if category in metadata["granular_coverage"]:
                    metadata["granular_coverage"][category] += len(examples)
                
                all_qualities.extend(qualities)
            else:
                metadata["sections"][section_name] = {
                    "count": 0,
                    "category": category,
                    "avg_quality": 0,
                    "best_quality": 0,
                    "avg_weight": 0,
                    "avg_words": 0,
                    "custom_prompts": 0,
                    "prompt_coverage": 0,
                    "best_sources": []
                }
        
        # Statistiques globales granulaires
        if all_qualities:
            metadata["quality_stats"] = {
                "overall_avg": sum(all_qualities) / len(all_qualities),
                "overall_best": max(all_qualities),
                "sections_with_data": len([s for s in metadata["sections"].values() if s["count"] > 0]),
                "sections_with_prompts": len([s for s in metadata["sections"].values() if s["custom_prompts"] > 0]),
                "granular_completeness": len([s for s in metadata["sections"].values() if s["count"] > 0]) / len(metadata["sections"])
            }
        
        # Sauvegarder
        with open(self.metadata_cache, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return metadata
    
    def _print_granular_summary(self, metadata: Dict[str, Any]):
        """Affiche un résumé granulaire enrichi"""
        
        print("\n" + "="*70)
        print("🎉 RÉSUMÉ DU RÉ-ENTRAÎNEMENT GRANULAIRE")
        print("="*70)
        
        prompts_analysis = metadata.get("prompts_analysis", {})
        quality_stats = metadata.get("quality_stats", {})
        sections_data = metadata.get("sections", {})
        granular_coverage = metadata.get("granular_coverage", {})
        
        print(f"🔥 Type: ENTRAÎNEMENT GRANULAIRE FORCÉ")
        print(f"📝 Prompts granulaires: {prompts_analysis.get('total_prompts', 0)}")
        print(f"📚 Total exemples: {metadata.get('total_examples', 0)}")
        print(f"🎯 Sections totales: {metadata.get('total_sections', 0)}")
        print(f"🏆 Qualité moyenne: {quality_stats.get('overall_avg', 0):.2f}")
        print(f"📊 Complétude granulaire: {quality_stats.get('granular_completeness', 0):.1%}")
        
        print(f"\n📝 Couverture Prompts Granulaires:")
        print(f"  ✅ Prompts trouvés: {prompts_analysis.get('total_prompts', 0)}/{metadata.get('total_sections', 0)}")
        print(f"  ❌ Prompts manquants: {len(prompts_analysis.get('missing_prompts', []))}")
        print(f"  🎯 Sections principales: {len(prompts_analysis.get('sections_covered', []))}/3")
        
        print(f"\n📊 Couverture par Catégorie:")
        for category, count in granular_coverage.items():
            if count > 0:
                print(f"  📋 {category.replace('_', ' ').title()}: {count} exemples")
        
        print(f"\n🔍 Top Sections par Qualité:")
        # Trier les sections par qualité moyenne
        sorted_sections = sorted(
            [(name, stats) for name, stats in sections_data.items() if stats["count"] > 0],
            key=lambda x: x[1]["avg_quality"],
            reverse=True
        )
        
        for i, (section_name, stats) in enumerate(sorted_sections[:10]):
            count = stats["count"]
            quality = stats["avg_quality"]
            prompts = stats["custom_prompts"]
            coverage = stats["prompt_coverage"]
            
            print(f"  {i+1:2d}. {section_name:25}: {count} ex. (Q:{quality:.2f}, P:{coverage:.1%})")
        
        if prompts_analysis.get("missing_prompts"):
            print(f"\n⚠️ Prompts granulaires manquants (premiers 10):")
            for missing in prompts_analysis["missing_prompts"][:10]:
                print(f"  • {missing}")
        
        print(f"\n💾 Cache granulaire: {self.cache_directory}")
        print(f"📅 Date: {metadata.get('training_date', 'N/A')}")
    
    # Méthodes utilitaires héritées et adaptées
    def _extract_jinja_variables(self, content: str) -> List[str]:
        """Extrait les variables Jinja2 d'un prompt"""
        variables = re.findall(r'\{\{\s*([^}]+)\s*\}\}', content)
        clean_vars = []
        for var in variables:
            clean_var = var.split('|')[0].split('.')[0].strip()
            if clean_var and clean_var not in clean_vars:
                clean_vars.append(clean_var)
        return clean_vars
    
    def _clear_cache(self):
        """Supprime tout le cache granulaire existant"""
        cache_files = [
            self.extracted_cache,
            self.training_cache, 
            self.metadata_cache,
            self.prompts_cache
        ]
        
        for cache_file in cache_files:
            if cache_file.exists():
                cache_file.unlink()
                print(f"🗑️ Supprimé: {cache_file.name}")
        
        print("✅ Cache granulaire nettoyé")
    
    def _extract_section_content(self, full_text: str, patterns: List[str]) -> str:
        """Extrait le contenu d'une section avec plusieurs patterns"""
        for pattern in patterns:
            match = re.search(pattern, full_text, re.DOTALL)
            if match:
                content = match.group(0).strip()
                content = self._clean_extracted_content(content)
                
                if len(content) > 50 and len(content.split()) > 10:  # Seuil plus bas pour granulaire
                    return content
        
        return ""
    
    def _clean_extracted_content(self, content: str) -> str:
        """Nettoie le contenu extrait"""
        content = re.sub(r'^\d+\.?\s*[A-Za-z\s]*\n?', '', content).strip()
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r'[^\w\s\.\,\;\:\!\?\(\)\-\'\"\n]', ' ', content)
        return content.strip()
    
    def _clean_pdf_text(self, text: str) -> str:
        """Nettoie le texte extrait d'un PDF"""
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        return text.strip()
    
    # Interfaces publiques
    def get_training_status(self) -> Dict[str, Any]:
        """Retourne le statut de l'entraînement granulaire"""
        if not self._is_training_valid():
            return {
                "status": "not_trained",
                "message": "Aucun entraînement granulaire trouvé",
                "ready": False,
                "type": "granular_v2"
            }
        
        metadata = self._load_training_metadata()
        return {
            "status": "trained",
            "message": "Agents granulaires pré-entraînés disponibles",
            "ready": True,
            "type": "granular_v2",
            "metadata": metadata
        }
    
    def _is_training_valid(self) -> bool:
        """Vérifie si l'entraînement granulaire en cache est valide"""
        cache_files = [self.extracted_cache, self.training_cache, self.metadata_cache]
        if not all(f.exists() for f in cache_files):
            return False
        
        try:
            metadata = self._load_training_metadata()
            return metadata.get("training_type") == "granular_v2"
        except Exception:
            return False
    
    def _load_training_metadata(self) -> Dict[str, Any]:
        """Charge les métadonnées d'entraînement granulaire"""
        try:
            with open(self.metadata_cache, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def load_granular_training_data(self) -> Optional[Dict[str, List[Dict]]]:
        """Charge les données d'entraînement granulaires depuis le cache"""
        if not self.training_cache.exists():
            return None
        
        try:
            with open(self.training_cache, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur chargement cache granulaire: {e}")
            return None


# ============================================================================
# INTERFACES SIMPLIFIÉES POUR INTÉGRATION
# ============================================================================

def setup_granular_training(reports_directory="examples") -> TrainingManager:
    """Configure et lance l'entraînement granulaire si nécessaire"""
    manager = TrainingManager(reports_directory)
    
    status = manager.get_training_status()
    if not status["ready"]:
        print("🎓 Lancement de l'entraînement granulaire initial...")
        manager.force_retrain_granular()
    else:
        print("✅ Agents granulaires déjà entraînés et prêts")
    
    return manager


def get_granular_pretrained_data() -> Optional[Dict[str, List[Dict]]]:
    """Interface rapide pour charger les données granulaires pré-entraînées"""
    manager = TrainingManager()
    return manager.load_granular_training_data()


def force_granular_retrain(reports_dir: str = "examples", 
                          prompts_dir: str = "prompts") -> bool:
    """Interface simple pour forcer le ré-entraînement granulaire"""
    
    try:
        manager = TrainingManager(
            reports_directory=reports_dir,
            prompts_directory=prompts_dir
        )
        
        result = manager.force_retrain_granular()
        return result.get("status") != "failed"
        
    except Exception as e:
        print(f"❌ Erreur ré-entraînement granulaire: {e}")
        return False


def check_granular_prompts_integration() -> Dict[str, Any]:
    """Vérifie l'état de l'intégration granulaire avec les prompts"""
    
    try:
        manager = TrainingManager()
        prompts_analysis = manager._analyze_granular_prompts()
        
        return {
            "prompts_found": prompts_analysis["total_prompts"],
            "prompts_missing": len(prompts_analysis["missing_prompts"]),
            "sections_covered": len(prompts_analysis["sections_covered"]),
            "granular_coverage": prompts_analysis["granular_coverage"],
            "available_prompts": list(prompts_analysis["available_prompts"].keys()),
            "missing_prompts": prompts_analysis["missing_prompts"],
            "ready_for_training": prompts_analysis["total_prompts"] > 0,
            "completeness": prompts_analysis["total_prompts"] / len(manager.granular_section_mapping)
        }
        
    except Exception as e:
        return {"error": str(e), "ready_for_training": False}


# ============================================================================
# CLI ÉTENDUE POUR L'ENTRAÎNEMENT GRANULAIRE
# ============================================================================

def cli_force_granular_retrain():
    """Commande CLI pour forcer le ré-entraînement granulaire"""
    
    print("🔥 FORÇAGE DU RÉ-ENTRAÎNEMENT GRANULAIRE")
    print("="*50)
    
    # Vérifier les prompts d'abord
    print("🔍 Vérification des prompts granulaires...")
    prompts_status = check_granular_prompts_integration()
    
    if prompts_status.get("error"):
        print(f"❌ Erreur prompts: {prompts_status['error']}")
        return False
    
    print(f"✅ Prompts trouvés: {prompts_status['prompts_found']}")
    print(f"⚠️ Prompts manquants: {prompts_status['prompts_missing']}")
    print(f"📊 Complétude: {prompts_status.get('completeness', 0):.1%}")
    
    for category, count in prompts_status.get('granular_coverage', {}).items():
        if count > 0:
            print(f"  📋 {category}: {count} prompts")
    
    if prompts_status["prompts_found"] == 0:
        print("❌ Aucun prompt trouvé - Vérifiez le dossier prompts/")
        return False
    
    # Confirmation
    response = input(f"\n❓ Forcer le ré-entraînement granulaire avec {prompts_status['prompts_found']} prompts? (y/N): ")
    if response.lower() != 'y':
        print("⚠️ Ré-entraînement granulaire annulé")
        return False
    
    # Lancer le ré-entraînement granulaire
    success = force_granular_retrain()
    
    if success:
        print("\n🎉 Ré-entraînement granulaire terminé avec succès!")
        print("💡 Système prêt pour génération granulaire IA")
        return True
    else:
        print("\n❌ Ré-entraînement granulaire échoué")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "force-granular":
            success = cli_force_granular_retrain()
            sys.exit(0 if success else 1)
            
        elif command == "check-granular":
            status = check_granular_prompts_integration()
            print(f"🎯 Statut granulaire: {status}")
            sys.exit(0)
            
        elif command == "quick-granular":
            print("🚀 Ré-entraînement granulaire rapide...")
            success = force_granular_retrain()
            print("✅ Terminé!" if success else "❌ Échec")
            sys.exit(0 if success else 1)
    
    # Usage par défaut
    print("🌊 Enhanced Training Manager")
    print("="*60)
    print("Commandes disponibles:")
    print("  python enhanced_training_v2.py force-granular")
    print("  python enhanced_training_v2.py check-granular") 
    print("  python enhanced_training_v2.py quick-granular")
    print()
    print("Intégration dans votre code:")
    print("  from enhanced_training_v2 import force_granular_retrain")
    print("  success = force_granular_retrain()")
