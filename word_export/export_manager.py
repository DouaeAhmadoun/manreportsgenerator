import streamlit as st
import os
from datetime import datetime
import time
import base64
from config import get_template_path, get_default_ai_model


class ProgressManager:
    """Gestionnaire avec spinner et téléchargement automatique"""
    
    def __init__(self, total_steps=100):
        self.main_container = st.container()
        
        with self.main_container:
            # Spinner principal
            self.spinner_container = st.container()
            with self.spinner_container:
                self.spinner_placeholder = st.empty()
                
            # Header avec statut et bouton d'arrêt
            self.status_cols = st.columns([2, 1, 1])
            with self.status_cols[0]:
                self.status_text = st.empty()
            with self.status_cols[1]:
                self.time_display = st.empty()
            with self.status_cols[2]:
                self.stop_button_container = st.empty()
            
            # Barre de progression
            self.progress_bar = st.progress(0)
            
            # Zone de détails
            self.details_expander = st.expander("📋 Détails de génération", expanded=True)
            with self.details_expander:
                self.details_container = st.empty()
        
        self.start_time = time.time()
        self.current_step = 0
        self.total_steps = total_steps
        self.phase = "Initialisation"
        self.messages_history = []
        self.generation_stopped = False
        
        self._update_visual_indicator("📄 Initialisation en cours...")
        
    def _update_visual_indicator(self, message: str):
        """Indicateur visuel simple"""
        with self.spinner_placeholder:
            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: center; 
                        padding: 8px; background-color: #e8f4f8; border-radius: 5px; 
                        border-left: 4px solid #1f77b4; margin: 5px 0;">
                <div style="margin-right: 10px; font-size: 18px;">⚙️</div>
                <div style="font-weight: 500; color: #1f77b4;">{message}</div>
            </div>
            """, unsafe_allow_html=True)
    
    def update(self, step: int, phase: str, detail: str = ""):
        """Met à jour la progression"""
        if self._check_stop_requested():
            self.generation_stopped = True
            self.error("Génération arrêtée par l'utilisateur")
            return False
        
        self.current_step = step
        self.phase = phase
        
        progress = min(step / self.total_steps, 1.0)
        
        indicator_message = f"{progress:.0%} - {phase}"
        if detail:
            indicator_message += f" | {detail}"
        
        self._update_visual_indicator(indicator_message)
        self.progress_bar.progress(progress)
        
        elapsed = time.time() - self.start_time
        with self.status_text:
            st.write(f"Phase: **{phase}**")
        
        with self.time_display:
            st.write(f"⏱️ {elapsed:.1f}s")
        
        with self.stop_button_container:
            unique_key = f"stop_btn_{int(time.time() * 1000)}_{step}"
            if st.button("🛑 Arrêter", key=unique_key, help="Arrêter la génération"):
                st.session_state.stop_generation = True
                #st.rerun()
        
        if detail:
            timestamp = f"[{elapsed:.1f}s]"
            message = f"{timestamp} {detail}"
            self.messages_history.append(message)
            
            if len(self.messages_history) > 10:
                self.messages_history = self.messages_history[-10:]
            
            self._render_details_block()
        
        return True
    
    def log_detail(self, detail: str):
        """Ajoute une ligne de détail sans modifier la progression."""
        elapsed = time.time() - self.start_time
        message = f"[{elapsed:.1f}s] {detail}"
        self.messages_history.append(message)
        if len(self.messages_history) > 10:
            self.messages_history = self.messages_history[-10:]
        self._render_details_block()
    
    def _check_stop_requested(self) -> bool:
        """Vérifie si l'arrêt a été demandé"""
        return st.session_state.get("stop_generation", False)
    
    def complete(self, success_message: str, output_path: str = None, filename: str = None):
        """Finalise avec notifications et téléchargement auto"""
        
        # Arrêter le spinner
        self.spinner_placeholder.empty()
        self.progress_bar.progress(1.0)
        
        # Notification de succès
        with self.status_text:
            st.success(f"✅ **{success_message}**")
        
        total_time = time.time() - self.start_time
        with self.time_display:
            st.write(f"⏱️ {total_time:.1f}s")
        
        # Masquer le bouton d'arrêt
        self.stop_button_container.empty()
        
        # Message final dans l'historique
        final_message = f"[{total_time:.1f}s] 🎉 **{success_message}**"
        self.messages_history.append(final_message)
        
        with self.details_container.container():
            for msg in reversed(self.messages_history):
                st.write(msg)
        
        # Sauvegarder les résultats
        if output_path and filename:
            file_size = os.path.getsize(output_path) / (1024 * 1024) if os.path.exists(output_path) else 0.0
            
            st.session_state.last_generation_result = {
                "output_path": output_path,
                "filename": filename,
                "total_time": total_time,
                "timestamp": datetime.now(),
                "messages_history": self.messages_history.copy(),
                "file_size_mb": file_size
            }
            
            # Préparer le téléchargement
            st.session_state.auto_download_ready = {
                "path": output_path,
                "filename": filename,
                "timestamp": datetime.now(),
                "ready": True
            }
        
        # Toast
        st.toast("🎉 " + success_message, icon="✅")
        st.balloons()
        
        # Rafraîchir
       # st.rerun()
    
    def error(self, error_message: str):
        """Affiche une erreur"""
        self.spinner_placeholder.empty()
        
        with self.status_text:
            st.error(f"❌ **{error_message}**")
        
        self.stop_button_container.empty()
        
        elapsed = time.time() - self.start_time
        error_msg = f"[{elapsed:.1f}s] ❌ **{error_message}**"
        self.messages_history.append(error_msg)
        
        self._render_details_block()

    def _render_details_block(self):
        """Affiche l'historique dans un bloc style terminal."""
        with self.details_container.container():
            st.code("\n".join(reversed(self.messages_history)), language="text")


class WordExportManager:
    """Gestionnaire d'export Word avec Ok, téléchargement automatique"""
    
    def __init__(self, ai_model: str = None):
        if ai_model is None:
            ai_model = get_default_ai_model()
        
        self.ai_model = ai_model
        self.default_template = str(get_template_path())
        
        # Lazy loading
        self._context_builder = None
        self._image_processor = None
        
        self._init_default_options()
    
    @property
    def context_builder(self):
        if self._context_builder is None:
            from .context_builder import ContextBuilder
            self._context_builder = ContextBuilder()
        return self._context_builder
    
    @property
    def image_processor(self):
        if self._image_processor is None:
            from .image_processor import ImageProcessor
            self._image_processor = ImageProcessor()
        return self._image_processor
    
    def _init_default_options(self):
        """Initialise les options par défaut"""
        if "word_export_options" not in st.session_state:
            st.session_state.word_export_options = {
                "include_images": True,
                "generate_ai": True,
                "ai_model": self.ai_model,
                "template_path": self.default_template
            }
    
    def generate_with_progress(self, rapport_data: dict) -> tuple:
        """Génération avec gestion de progression"""
        # Sauvegarder la référence à ce manager
        st.session_state.current_export_manager = self
        
        # Gestion du progress manager
        if ('current_progress_manager' not in st.session_state or 
            st.session_state.current_progress_manager is None):
            progress_mgr = ProgressManager(total_steps=100)
            st.session_state.current_progress_manager = progress_mgr
        else:
            progress_mgr = st.session_state.current_progress_manager
            
            # Réinitialiser pour la nouvelle génération
            progress_mgr.start_time = time.time()
            progress_mgr.current_step = 0
            progress_mgr.messages_history = []
            progress_mgr.generation_stopped = False
            
            # Nettoyer les containers
            progress_mgr.spinner_placeholder.empty()
            progress_mgr.details_container.empty()
            
            # Redémarrer l'indicateur
            progress_mgr._update_visual_indicator("📄 Initialisation en cours...")
        
        try:
            # Phase 1: Préparation (0-10%)
            if not progress_mgr.update(5, "Préparation", "🔧 Initialisation des modules..."):
                return None, None, rapport_data
            progress_mgr.log_detail("Initialisation des modules en cours...")
            
            # Charger les modules nécessaires
            _ = self.context_builder
            
            options = st.session_state.word_export_options
            if options["include_images"]:
                _ = self.image_processor
            
            if not progress_mgr.update(10, "Préparation", "✅ Modules chargés"):
                return None, None, rapport_data
            progress_mgr.log_detail("Modules chargés, préparation de la génération...")
            
            # Phase 2: Génération IA (10-70%)
            if options.get("generate_ai", True):
                if not progress_mgr.update(15, "Génération IA", "🤖 Démarrage des agents pré-entraînés..."):
                    return None, None, rapport_data
                progress_mgr.log_detail("Agents IA démarrés, génération des sections...")
                
                from agents.ai_generator import AIGenerator
                ai_gen = AIGenerator(model=self.ai_model)
                enriched_data = ai_gen.generate_ai_sections_for_report(
                    rapport_data, progress_mgr=progress_mgr, progress_range=(20, 65)
                )
                
                # Journaliser quelques longueurs de sections pour la barre de détail (global, après IA)
                self._log_section_lengths(progress_mgr, enriched_data)
                
                if progress_mgr.generation_stopped:
                    return None, None, rapport_data
                    
                if not progress_mgr.update(70, "Génération IA", "✅ Contenu IA généré"):
                    return None, None, rapport_data
            else:
                progress_mgr.log_detail("IA désactivée : utilisation des données existantes")
                # Simuler des jalons pour montrer l'avancement même sans IA
                if not progress_mgr.update(30, "Génération IA", "⭐ IA désactivée : préparation des données..."):
                    return None, None, rapport_data
                progress_mgr.log_detail("Données existantes prêtes (sans enrichissement IA)")
                if not progress_mgr.update(50, "Génération IA", "⭐ IA désactivée : consolidation..."):
                    return None, None, rapport_data
                enriched_data = rapport_data
                if not progress_mgr.update(70, "Génération IA", "⭐ Génération IA désactivée"):
                    return None, None, rapport_data
            
            # Phase 3: Génération Word (70-95%)
            if not progress_mgr.update(75, "Génération Word", "📄 Préparation du template..."):
                return None, None, rapport_data
            progress_mgr.log_detail("Phase Word démarrée (préparation du template)")
            
            output_path, filename = self._generate_word(
                enriched_data, progress_mgr, start_step=75, end_step=95
            )
            
            if progress_mgr.generation_stopped:
                return None, None, rapport_data
            
            # Phase 5: Finalisation (95-100%)
            if not progress_mgr.update(98, "Finalisation", "🎯 Vérification du fichier..."):
                return None, None, rapport_data
            progress_mgr.log_detail("Vérification finale du fichier en cours...")
            
            if output_path and os.path.exists(output_path):
                progress_mgr.complete("Rapport généré avec succès", output_path, filename)
                return output_path, filename, enriched_data
            else:
                progress_mgr.error("Échec de la génération")
                return None, None, rapport_data
                
        except Exception as e:
            progress_mgr.error(f"Erreur: {str(e)}")
            return None, None, rapport_data
        
        finally:
            # Nettoyer à la fin
            st.session_state.current_progress_manager = None
    
    def _log_section_lengths(self, progress_mgr, data: dict):
        """Ajoute dans les détails des infos sur les sections générées et leur taille."""
        try:
            sections = []
            
            intro = data.get("introduction", {}) if isinstance(data, dict) else {}
            if isinstance(intro, dict):
                if intro.get("guidelines"):
                    sections.append(("Introduction / guidelines", intro["guidelines"]))
                if intro.get("objectifs"):
                    sections.append(("Introduction / objectifs", intro["objectifs"]))
            
            analyse = data.get("analyse_synthese", {}) if isinstance(data, dict) else {}
            if isinstance(analyse, dict):
                if analyse.get("recapitulatif_text"):
                    sections.append(("Analyse / recapitulatif", analyse["recapitulatif_text"]))
                if analyse.get("stats_text"):
                    sections.append(("Analyse / stats", analyse["stats_text"]))
                if analyse.get("recommandations_text"):
                    sections.append(("Analyse / recommandations", analyse["recommandations_text"]))
            
            conclusion = data.get("conclusion")
            if isinstance(conclusion, str) and conclusion.strip():
                sections.append(("Conclusion", conclusion))
            
            for name, content in sections:
                if isinstance(content, str):
                    length = len(content)
                    progress_mgr.log_detail(f"Génération section {name}… {length} chars")
        except Exception:
            # On ignore les erreurs de log pour ne pas interrompre la génération
            pass
    
    def _generate_word(self, rapport_data: dict, progress_mgr, start_step: int, end_step: int) -> tuple:
        """Génération Word avec vérification d'arrêt"""
        
        options = st.session_state.word_export_options
        
        def count_inline_images(payload):
            """Compte grossièrement les InlineImage ou chemins images."""
            count = 0
            from docxtpl import InlineImage
            if isinstance(payload, dict):
                for _, v in payload.items():
                    count += count_inline_images(v)
            elif isinstance(payload, list):
                for item in payload:
                    count += count_inline_images(item)
            else:
                if isinstance(payload, InlineImage):
                    count += 1
                elif isinstance(payload, str):
                    if payload.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp")):
                        count += 1
            return count
        
        try:
            if not progress_mgr.update(start_step + 2, "Génération Word", "📋 Préparation du contexte..."):
                return None, None
            progress_mgr.log_detail("Préparation du contexte pour le template")
            
            # Préparer le contexte
            context = self.context_builder.prepare_context_for_template(rapport_data)
            try:
                sims_count = len(context.get("simulations", {}).get("simulations", []))
                conds = context.get("donnees_entree", {}).get("conditions_environnementales", {})
                houle_figs = len(conds.get("houle", {}).get("figures", []))
                vent_figs = len(conds.get("vent", {}).get("figures", []))
                navires_figs = sum(1 for n in context.get("navires_liste", []) if n.get("figure"))
                remorqueurs_figs = sum(1 for r in context.get("remorqueurs_liste", []) if r.get("figure"))
                progress_mgr.log_detail(
                    f"Contexte: {sims_count} simulations, houle_figures={houle_figs}, vent_figures={vent_figs}, "
                    f"navires_figures={navires_figs}, remorqueurs_figures={remorqueurs_figs}"
                )
            except Exception:
                pass
            
            if not progress_mgr.update(start_step + 5, "Génération Word", "📄 Chargement du template..."):
                return None, None
            progress_mgr.log_detail("Template chargé, ready pour injection du contexte")
            
            # Charger et traiter le template
            from docxtpl import DocxTemplate
            doc = DocxTemplate(options["template_path"])
            
            if not progress_mgr.update(start_step + 8, "Génération Word", "📑 Analyse du contenu..."):
                return None, None
            progress_mgr.log_detail("Template chargé, préparation du rendu...")
            
            if not progress_mgr.update(start_step + 12, "Génération Word", "🖼️ Traitement des images..."):
                return None, None
            
            # Traitement des images si nécessaire
            if options["include_images"]:
                try:
                    context = self.image_processor.replace_images_in_data(context, doc)
                    try:
                        img_count = count_inline_images(context)
                        progress_mgr.log_detail(f"Images intégrées: {img_count} éléments")
                    except Exception:
                        pass
                except Exception as e:
                    progress_mgr.update(start_step + 14, "Génération Word", f"⚠️ Images ignorées: {str(e)}")
                    progress_mgr.log_detail(f"Images ignorées: {e}")
            else:
                progress_mgr.log_detail("Images ignorées (option désactivée)")
            
            if not progress_mgr.update(start_step + 16, "Génération Word", "🔧 Application du contexte..."):
                return None, None
            progress_mgr.log_detail("Application des filtres utilitaires (formatage dates, nombres, pourcentages)")
            
            # Ajouter les fonctions utilitaires
            from .word_utils import WordUtils
            word_utils = WordUtils()
            context["format_success_rate"] = word_utils.format_success_rate
            context["format_date"] = word_utils.format_date
            context["format_number"] = word_utils.format_number
            context["format_percentage"] = word_utils.format_percentage
            
            if not progress_mgr.update(start_step + 18, "Génération Word", "⚙️ Rendu du document..."):
                return None, None
            progress_mgr.log_detail("Rendu du document en cours...")
            
            # Rendre le document
            doc.render(context)
            progress_mgr.log_detail("Rendu terminé")
            
            if not progress_mgr.update(start_step + 20, "Génération Word", "💾 Sauvegarde..."):
                return None, None
            progress_mgr.log_detail("Sauvegarde du fichier DOCX...")
            
            # Générer nom de fichier et sauvegarder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            projet_name = rapport_data.get("metadonnees", {}).get("titre", "rapport")
            projet_clean = "".join(c for c in projet_name if c.isalnum() or c in ('-', '_')).rstrip()[:50]
            filename = f"{timestamp}_rapport_manoeuvrabilite_{projet_clean}.docx"
            
            from config import Config
            output_dir = Config.OUTPUT_DIR
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)
            
            doc.save(output_path)
            
            progress_mgr.update(end_step, "Génération Word", f"✅ Fichier sauvegardé: {filename}")
            
            return output_path, filename
            
        except Exception as e:
            progress_mgr.update(end_step, "Génération Word", f"❌ Erreur: {str(e)}")
            return None, None
    
    def export_word_ui(self, rapport_data: dict):
        """Interface utilisateur pour l'export"""
        st.subheader("📄 Export Word avec Template")
        
        if not rapport_data:
            st.warning("⚠️ Aucune donnée de rapport disponible")
            return
        
        # Interface normale
        self._render_quick_interface(rapport_data)
        
        # Options avancées
        show_advanced = st.toggle(
            "⚙️ Options avancées",
            value=st.session_state.get("show_advanced_export_options", False),
            help="Affiche toutes les options de personnalisation avancées"
        )
        st.session_state.show_advanced_export_options = show_advanced
        if show_advanced:
            with st.expander("⚙️ Options avancées", expanded=False):
                self._render_advanced_options()
        else:
            st.info("📄 **Mode simple :** DOCX, qualité standard, enrichissement IA automatique")
        
        # Bouton principal de génération
        if st.button("🚀 Générer le rapport Word", type="primary", width='stretch'):
            st.session_state.stop_generation = False
            self._execute_generation(rapport_data)
        
        # Gestion du téléchargement automatique
        self._handle_auto_download()
        
        # Afficher les résultats de la dernière génération
        self._show_previous_results()
    
    def _render_quick_interface(self, rapport_data: dict):
        """Interface rapide et claire"""
        options = st.session_state.word_export_options
        template_path = options["template_path"]
        
        if os.path.exists(template_path):
            st.success(f"✅ Template Word chargé: {os.path.basename(template_path)}")
        else:
            st.error(f"❌ Template manquant: {template_path}")
            return
        
        # Statistiques en colonnes compactes
        stats = self._get_quick_stats(rapport_data)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Sections", stats["sections"])
        with col2:
            st.metric("Simulations", stats["simulations"])
        with col3:
            st.metric("Pages est.", stats["pages"])
        with col4:
            st.metric("Agents IA", "Prêts", help="Agents disponibles")
    
    def _render_advanced_options(self):
        """Options avancées simplifiées"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Options IA
            enable_ai = st.checkbox(
                "Enrichissement IA automatique",
                value=st.session_state.word_export_options.get("generate_ai", True),
                key="enable_ai_checkbox",
                help="Génère automatiquement du contenu avec les agents pré-entraînés"
            )
            st.session_state.word_export_options["generate_ai"] = enable_ai
            
            if enable_ai:
                st.success("🤖 **Agents IA disponibles**")
            else:
                st.info("ℹ️ **Génération IA désactivée**")
        
        with col2:
            # Options de format
            include_images = st.checkbox(
                "Inclure les images",
                value=st.session_state.word_export_options.get("include_images", True),
                key="include_images_checkbox",
                help="Intègre les images de navires et diagrammes"
            )
            st.session_state.word_export_options["include_images"] = include_images
    
    def _handle_auto_download(self):
        """Gère le téléchargement automatique"""
        if st.session_state.get("auto_download_ready", {}).get("ready", False):
            auto_download = st.session_state.auto_download_ready
            if os.path.exists(auto_download["path"]):
                st.success("🎉 **Rapport généré avec succès !**")
                
                # Informations sur le fichier
                file_size = os.path.getsize(auto_download["path"]) / (1024 * 1024)
                st.info(f"📄 {auto_download['filename']} • {file_size:.1f} MB • {auto_download.get('timestamp', datetime.now()).strftime('%H:%M')}")
                
                # Container stable pour le téléchargement
                download_container = st.container()
                with download_container:
                    with open(auto_download["path"], "rb") as file:
                        file_data = file.read()  # Lire une seule fois
                        
                    download_success = st.download_button(
                        label="Télécharger le rapport",
                        data=file_data,
                        file_name=auto_download["filename"],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        width='stretch',
                        key=f"download_btn_{auto_download['filename']}"  # ← Clé unique basée sur le fichier
                    )
                    
                    # Nettoyer SEULEMENT si téléchargement réussi
                    if download_success:
                        st.success("Téléchargement lancé !")
                        # Marquer comme utilisé au lieu de supprimer complètement
                        st.session_state.auto_download_ready["ready"] = False
            else:
                st.error("❌ Fichier non trouvé pour le téléchargement")
                st.session_state.auto_download_ready = {"ready": False}
    
    def _show_previous_results(self):
        """Affiche les résultats de la dernière génération si disponibles"""
        if "last_generation_result" in st.session_state:
            result = st.session_state.last_generation_result
            
            if os.path.exists(result["output_path"]):
                with st.expander("📁 Dernière génération disponible"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Généré le", result["timestamp"].strftime("%H:%M"))
                    with col2:
                        st.metric("Durée", f"{result['total_time']:.1f}s")
                    with col3:
                        st.metric("Taille", f"{result['file_size_mb']:.1f} MB")
                    
                    # Bouton de téléchargement persistant
                    with open(result["output_path"], "rb") as file:
                        st.download_button(
                            label="📥 Télécharger le dernier rapport",
                            data=file.read(),
                            file_name=result["filename"],
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="secondary",
                            width='stretch'
                        )
            else:
                # Fichier n'existe plus, nettoyer
                del st.session_state.last_generation_result
    
    def _execute_generation(self, rapport_data: dict):
        """Exécute la génération avec spinner"""
        with st.spinner("📄 Génération du rapport en cours... Veuillez patienter"):
            progress_zone = st.container()
            with progress_zone:
                _, _, _ = self.generate_with_progress(rapport_data)
    
    def _get_quick_stats(self, rapport_data: dict) -> dict:
        """Statistiques rapides pour l'interface"""
        try:
            simulations = rapport_data.get("simulations", {}).get("simulations", [])
            sections = len([k for k in ["metadonnees", "introduction", "donnees_entree", "simulations", "analyse_synthese", "conclusion"] if rapport_data.get(k)])
            pages = 6 + len(simulations) // 10
            
            return {
                "sections": sections,
                "simulations": len(simulations),
                "pages": pages
            }
        except:
            return {"sections": 0, "simulations": 0, "pages": 5}


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def export_word_ui(rapport_data: dict):
    """Point d'entrée principal"""
    manager = WordExportManager()
    return manager.export_word_ui(rapport_data)
