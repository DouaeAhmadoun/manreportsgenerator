import streamlit as st
import os
import zipfile
from typing import Dict, Any, List, Tuple, Set
from .base_form import BaseForm
from .form_utils import process_zip_file, organize_zip_contents


class AnnexesForm(BaseForm):
    """Formulaire pour la gestion des annexes du rapport."""
    
    def __init__(self):
        super().__init__("annexes")
    
    def render(self) -> Dict[str, Any]:
        """Rend le formulaire des annexes."""
        try:
            self.render_section_header("📎 Annexes", divider=True)
            
            st.info("Mode automatique : génère les annexes à partir des simulations Excel et d'un ZIP de figures")
            return self._render_automatic_annexes()
                
        except Exception as e:
            st.error(f"Erreur dans le formulaire annexes : {str(e)}")
            return {"type": "none", "actif": False}
    
    def _render_automatic_annexes(self) -> Dict[str, Any]:
        """Interface pour génération automatique des annexes."""
        self.render_section_header(
            "🔄 Génération automatique", 
            divider=False,
        )
        
        # Vérifier que nous avons des simulations
        simulations_data = st.session_state.get("simulations_data", [])
        
        if not simulations_data:
            st.warning("Aucune simulation disponible. Importez d'abord un fichier Excel dans l'onglet Simulations.")
            st.info("💡 Vous pouvez tout de même uploader un ZIP pour préparer les annexes")
        else:
            st.success(f"{len(simulations_data)} simulations disponibles pour les annexes")
        
        # Upload du ZIP
        zip_file = st.file_uploader(
            "📁 Fichier ZIP des figures par essai",
            type=["zip"],
            help="ZIP contenant des dossiers nommés avec le N° d'essai (ex: '1- E1 - Accostage...')"
        )
        
        if not zip_file:
            st.info("💡 Uploadez un ZIP pour générer les annexes automatiquement")
            return {"type": "none", "actif": False}
        
        # Traitement du ZIP
        if not simulations_data:
            # Analyse du ZIP sans simulations
            with st.spinner("Analyse du ZIP..."):
                zip_analysis = self._analyze_zip_structure(zip_file)
            
            if zip_analysis["success"]:
                st.success(f"ZIP analysé : {len(zip_analysis['folders'])} dossiers trouvés")
                
                with st.expander("📁 Structure du ZIP", expanded=True):
                    for folder_name, trial_number in zip_analysis['folders'].items():
                        st.write(f"• `{folder_name}` → Essai `{trial_number}`")
                
                st.info("🔄 Retournez à l'onglet Simulations pour importer les données Excel, puis revenez ici.")
            else:
                st.error(f"Erreur ZIP : {zip_analysis['error']}")
            
            return {"type": "zip_only", "zip_analysis": zip_analysis}
        
        # Traitement complet avec simulations
        with st.spinner("Analyse du ZIP et création des annexes..."):
            annexes_result = self._process_zip_and_create_annexes(zip_file, simulations_data)
        
        if annexes_result["success"]:
            st.success(f"Annexes générées : {annexes_result['stats']['total_essais']} essais traités")
            
            # Afficher les statistiques
            self._display_annexes_stats(annexes_result["stats"])

            # Aperçu des annexes générées
            with st.expander("👁️ Aperçu des annexes générées", expanded=True):
                self._display_annexes_preview(annexes_result["annexes"])
            
            
            
            # Gestion des problèmes de correspondance
            manual_pairs = []
            selected_folders = set()
            if annexes_result["issues"]:
                matches_state_key = f"manual_annexes_matches_{zip_file.name}"
                manual_pairs, selected_folders = self._handle_correspondence_issues(
                    annexes_result["issues"],
                    annexes_result.get("unmatched_context", {}),
                    matches_state_key
                )
            
            if manual_pairs:
                combined_pairs = annexes_result.get("matched_pairs", []) + manual_pairs
                annexes_result["annexes"] = self._create_annexes_structure(combined_pairs, simulations_data)
                annexes_result["stats"]["matched_pairs"] = len(combined_pairs)
                annexes_result["stats"]["total_essais"] = len(combined_pairs)
                
                resolved_sims = {p[0] for p in manual_pairs}
                annexes_result["issues"] = {
                    "unmatched_simulations": [
                        sim for sim in annexes_result["issues"].get("unmatched_simulations", [])
                        if sim not in resolved_sims
                    ],
                    "unmatched_folders": [
                        folder for folder in annexes_result["issues"].get("unmatched_folders", [])
                        if folder not in selected_folders
                    ]
                }
                
                st.info(f"{len(manual_pairs)} correspondance(s) manuelle(s) ajoutée(s)")
            
            return {
                "type": "automatic",
                "actif": True,
                "annexes": {
                    "tableau_complet": {
                        "titre": "Tableau récapitulatif de tous les essais",
                        "simulations": simulations_data,
                        "actif": bool(simulations_data)
                    },
                    "essais_detailles": annexes_result["annexes"].get("essais_detailles", [])
                },
                "stats": annexes_result.get("stats", {}),
                "issues": annexes_result.get("issues", {})
            }
        else:
            st.error(f"Erreur lors de la génération : {annexes_result['error']}")
            return {"type": "none", "actif": False}
    
    def _render_manual_annexes(self) -> Dict[str, Any]:
        """Interface pour annexes manuelles."""
        self.render_section_header(
            "📦 Annexes manuelles", 
            divider=False,
            help_text="Uploadez un fichier ZIP contenant toutes vos annexes (figures, tableaux, documents)"
        )
        
        zip_file = st.file_uploader(
            "Fichier ZIP des annexes",
            type=["zip"],
            help="Fichier ZIP contenant toutes les annexes du rapport"
        )
        
        zip_info = {}
        organized_files = {}
        
        if zip_file:
            # Traiter le fichier ZIP
            zip_info = process_zip_file(zip_file)
            
            if zip_info.get("valid"):
                st.success(f"ZIP traité avec succès : {zip_info['total_files']} fichiers")
                
                # Organiser les fichiers
                organized_files = organize_zip_contents(zip_info)
                
                # Afficher l'organisation
                self._display_manual_organization(organized_files)
                
            else:
                st.error(f"Erreur lors du traitement du ZIP : {zip_info.get('error', 'Erreur inconnue')}")
        
        # Commentaires
        commentaire_annexes = st.text_area(
            "Commentaires généraux sur les annexes",
            help="Instructions spéciales, organisation particulière, etc."
        )
        
        # Retourner les données selon l'état
        if zip_file and zip_info.get("valid"):
            return {
                "type": "manual",
                "actif": True,
                "zip_file": zip_file.name,
                "zip_path": zip_info["zip_path"],
                "organized_files": organized_files,
                "total_files": zip_info["total_files"],
                "commentaire": commentaire_annexes
            }
        else:
            return {
                "type": "none",
                "actif": False,
                "commentaire": commentaire_annexes
            }
    
    def _analyze_zip_structure(self, zip_file) -> Dict[str, Any]:
        """Analyse la structure du ZIP sans simulations."""
        try:
            # Sauvegarder le ZIP
            zip_path = self.save_uploaded_file(zip_file)
            
            folders = {}  # {folder_name: trial_number}
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Lister tous les dossiers dans le ZIP
                all_paths = zip_ref.namelist()
                folder_names = set()
                
                for path in all_paths:
                    path_parts = path.split('/')
                    # Chercher au niveau 2
                    if len(path_parts) >= 2 and path_parts[1] and not path_parts[1].startswith('.'):
                        folder_name = path_parts[1]  # Niveau 2
                        folder_names.add(folder_name)
                
                # Analyser chaque dossier
                for folder_name in folder_names:
                    trial_number = self._extract_trial_number(folder_name)
                    if trial_number:
                        folders[folder_name] = trial_number
            
            return {
                "success": True,
                "folders": folders,
                "total_folders": len(folders)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_trial_number(self, folder_name: str) -> str:
        """Extrait le numéro d'essai depuis le nom du dossier."""
        try:
            import re
            
            if not folder_name:
                return None
            
            # Pattern pour dossiers: "NUMERO SUFFIXE-"
            pattern = r'^(\d+(?:\s*(?:bis|ter|BIS|TER))?)\s*-'
            
            match = re.match(pattern, folder_name, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                return extracted
            
            # Pattern alternatif sans tiret
            pattern_alt = r'^(\d+(?:\s*(?:bis|ter|BIS|TER))?)'
            match_alt = re.match(pattern_alt, folder_name, re.IGNORECASE)
            if match_alt:
                extracted = match_alt.group(1).strip()
                return extracted
            
            return None
            
        except Exception as e:
            return None
    
    def _process_zip_and_create_annexes(self, zip_file, simulations: List[Dict]) -> Dict[str, Any]:
        """Traite le ZIP et crée les annexes automatiquement."""
        try:
            import os
            import tempfile
            from collections import defaultdict
            
            # Sauvegarder et analyser le ZIP
            zip_path = self.save_uploaded_file(zip_file)
            
            # Extraire le contenu du ZIP
            extract_dir = os.path.join("uploads", f"extracted_annexes_{zip_file.name.split('.')[0]}")
            os.makedirs(extract_dir, exist_ok=True)
            
            zip_folders = {}  # {numero_essai: dossier_path}
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                all_paths = zip_ref.namelist()
                folders = set()
                
                # Chercher les dossiers au niveau 2
                for path in all_paths:
                    path_parts = path.split('/')
                    if len(path_parts) >= 2 and path_parts[1] and not path_parts[1].startswith('.'):
                        folder_name = path_parts[1]
                        folders.add(folder_name)
                
                # Analyser chaque dossier trouvé
                for folder_name in sorted(folders):
                    numero_essai = self._extract_trial_number(folder_name)
                    
                    if numero_essai:
                        # Normaliser le numéro d'essai
                        from utils.excel import normalize_trial_number
                        numero_normalized = normalize_trial_number(numero_essai)
                        
                        # Créer le dossier d'extraction
                        folder_path = os.path.join(extract_dir, folder_name)
                        os.makedirs(folder_path, exist_ok=True)
                        
                        # Extraire tous les fichiers de ce dossier
                        files_extracted = 0
                        for file_path in all_paths:
                            path_parts = file_path.split('/')
                            
                            if (len(path_parts) >= 3 and 
                                path_parts[1] == folder_name and 
                                not file_path.endswith('/')):
                                
                                try:
                                    target_path = os.path.join(folder_path, os.path.basename(file_path))
                                    with zip_ref.open(file_path) as source, open(target_path, 'wb') as target:
                                        target.write(source.read())
                                    files_extracted += 1
                                except Exception as e:
                                    st.warning(f"Erreur extraction {file_path}: {e}")
                        
                        # Stocker le mapping
                        zip_folders[numero_normalized] = folder_path
            
            # Créer le mapping simulations ↔ dossiers
            simulation_map = {}
            sim_label_map = {}
            for sim in simulations:
                from utils.excel import normalize_trial_number
                
                raw_num = sim.get("numero_essai_original", "")
                numero_normalized = normalize_trial_number(raw_num)
                
                if numero_normalized:
                    simulation_map[numero_normalized] = sim
                    sim_label_map[numero_normalized] = raw_num or numero_normalized
            
            # Trouver les correspondances
            matched_pairs = []
            unmatched_simulations = []
            unmatched_folders = []
            
            for numero_sim in simulation_map.keys():
                if numero_sim in zip_folders:
                    matched_pairs.append((numero_sim, simulation_map[numero_sim], zip_folders[numero_sim]))
                else:
                    unmatched_simulations.append(numero_sim)
            
            for numero_zip in zip_folders.keys():
                if numero_zip not in simulation_map:
                    unmatched_folders.append(numero_zip)
            
            # Ajouter les images aux simulations
            for numero_essai, simulation, folder_path in matched_pairs:
                images = self._get_images_from_folder(folder_path)
                simulation["images"] = images
            
            # Créer les annexes
            annexes = self._create_annexes_structure(matched_pairs, simulations)
            
            # Statistiques
            stats = {
                "total_essais": len(matched_pairs),
                "total_simulations": len(simulations),
                "total_folders": len(zip_folders),
                "matched_pairs": len(matched_pairs),
                "unmatched_simulations": len(unmatched_simulations),
                "unmatched_folders": len(unmatched_folders)
            }
            
            # Issues de correspondance
            issues = {
                "unmatched_simulations": unmatched_simulations,
                "unmatched_folders": unmatched_folders
            }
            
            unmatched_context = {
                "unmatched_simulations": {num: simulation_map[num] for num in unmatched_simulations if num in simulation_map},
                "unmatched_simulation_labels": {num: sim_label_map.get(num, num) for num in unmatched_simulations},
                "unmatched_folders": {num: zip_folders[num] for num in unmatched_folders if num in zip_folders}
            }
            
            return {
                "success": True,
                "annexes": annexes,
                "stats": stats,
                "issues": issues,
                "matched_pairs": matched_pairs,
                "unmatched_context": unmatched_context
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_images_from_folder(self, folder_path: str) -> List[Dict[str, str]]:
        """Récupère et trie les images PNG d'un dossier."""
        try:
            import re
            from PIL import Image
            
            if not os.path.exists(folder_path):
                return []
            
            png_files = []
            corrupted_files = []

            for file_name in os.listdir(folder_path):
                if file_name.lower().endswith('.png'):
                    file_path = os.path.join(folder_path, file_name)

                    # Tester l'image
                    try:
                        with Image.open(file_path) as img:
                            img.verify()
                        png_files.append((file_name, file_path))
                        
                    except Exception as e:
                        corrupted_files.append(file_name)

            # Afficher warning s'il y a des images corrompues
            if corrupted_files:
                st.warning(f"⚠️ {len(corrupted_files)} image(s) corrompue(s) ignorée(s) dans {os.path.basename(folder_path)}")
            
            # Trier par numéro
            def extract_number(filename):
                numbers = re.findall(r'\d+', filename)
                return int(numbers[0]) if numbers else 9999
            
            png_files.sort(key=lambda x: extract_number(x[0]))
            
            return [{"nom": name, "chemin": path} for name, path in png_files]
            
        except Exception as e:
            st.warning(f"Erreur lors de la lecture du dossier {folder_path}: {e}")
            return []
    
    def _create_annexes_structure(self, matched_pairs: List, all_simulations: List[Dict]) -> Dict[str, Any]:
        """Crée la structure des annexes."""
        annexes = {
            "tableau_complet": {
                "titre": "Tableau récapitulatif de tous les essais",
                "simulations": all_simulations
            },
            "essais_detailles": []
        }
        
        # Trier les essais par numéro
        def sort_key_for_trial(numero_essai):
            try:
                import re
                match = re.match(r'^(\d+)', str(numero_essai))
                if match:
                    num = int(match.group(1))
                    if 'bis' in str(numero_essai).lower():
                        return (num, 1)
                    elif 'ter' in str(numero_essai).lower():
                        return (num, 2)
                    else:
                        return (num, 0)
                else:
                    return (9999, 0)
            except Exception:
                return (9999, 0)
        
        sorted_pairs = sorted(matched_pairs, key=lambda x: sort_key_for_trial(x[0]))
        
        for numero_essai, simulation, folder_path in sorted_pairs:
            images = self._get_images_from_folder(folder_path)
            
            essai_detail = {
                "numero_essai": numero_essai,
                "simulation": simulation,
                "images": images,
                "folder_path": folder_path
            }
            
            annexes["essais_detailles"].append(essai_detail)
        
        return annexes
    
    def _display_annexes_stats(self, stats: Dict[str, Any]):
        """Affiche les statistiques des annexes."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Essais traités", stats["matched_pairs"])
        with col2:
            st.metric("📋 Total simulations", stats["total_simulations"])
        with col3:
            st.metric("📁 Total dossiers ZIP", stats["total_folders"])
        with col4:
            taux_match = stats["matched_pairs"] / max(stats["total_simulations"], 1) * 100
            st.metric("🎯 Taux de correspondance", f"{taux_match:.1f}%")
    
    def _handle_correspondence_issues(
        self, 
        issues: Dict[str, List], 
        unmatched_context: Dict[str, Dict], 
        matches_state_key: str
    ) -> Tuple[List, Set[str]]:
        """Gère les problèmes de correspondance et permet des associations manuelles."""
        manual_pairs = []
        selected_folders = set()
        
        # Stocker l'état des correspondances dans la session (sélections précédentes)
        st.session_state.setdefault(matches_state_key, {})
        
        unmatched_simulations = issues.get("unmatched_simulations", [])
        unmatched_folders = issues.get("unmatched_folders", [])
        
        if not unmatched_simulations and not unmatched_folders:
            return manual_pairs, selected_folders
        
        st.warning("⚠️ Problèmes de correspondance détectés")
        
        if unmatched_simulations:
            with st.expander("❌ Simulations sans dossier ZIP correspondant"):
                labels = unmatched_context.get("unmatched_simulation_labels", {})
                for sim_num in unmatched_simulations:
                    label = labels.get(sim_num, sim_num)
                    st.write(f"• Simulation `{label}` - Aucun dossier trouvé")
        
        if unmatched_folders:
            with st.expander("❌ Dossiers ZIP sans simulation correspondante"):
                for folder_num in unmatched_folders:
                    st.write(f"• Dossier `{folder_num}` - Aucune simulation trouvée")
        
        # Interface de correspondance manuelle
        with st.expander("🔗 Associer manuellement les dossiers ZIP aux simulations", expanded=True):
            st.info("Sélectionnez un dossier ZIP pour chaque simulation sans correspondance, puis validez.")
            
            folder_options = ["— Aucune association —"] + unmatched_folders
            
            # Utiliser une form pour capter les choix et conserver l'état
            with st.form(f"manual_match_form_{matches_state_key}"):
                for sim_num in unmatched_simulations:
                    widget_key = f"{matches_state_key}_widget_{sim_num}"
                    
                    stored_choice = st.session_state[matches_state_key].get(sim_num, folder_options[0])
                    if stored_choice not in folder_options:
                        stored_choice = folder_options[0]
                    
                    if widget_key not in st.session_state:
                        st.session_state[widget_key] = stored_choice
                    
                    current_choice = st.session_state.get(widget_key, stored_choice)
                    if current_choice not in folder_options:
                        current_choice = folder_options[0]
                    
                    choice = st.selectbox(
                        f"Simulation {sim_num}",
                        folder_options,
                        index=folder_options.index(current_choice),
                        key=widget_key
                    )
                
                submitted = st.form_submit_button("Appliquer les correspondances")
            
            if submitted:
                for sim_num in unmatched_simulations:
                    widget_key = f"{matches_state_key}_widget_{sim_num}"
                    selected_value = st.session_state.get(widget_key, folder_options[0])
                    st.session_state[matches_state_key][sim_num] = selected_value
                st.success("Correspondances sauvegardées")
            
            # Construire les paires manuelles à partir de l'état courant
            stored_map = st.session_state[matches_state_key]
            selection_map = {
                sim_num: stored_map.get(sim_num, folder_options[0])
                for sim_num in unmatched_simulations
            }
            
            for sim_num, folder_id in selection_map.items():
                if folder_id and folder_id != folder_options[0]:
                    simulation_obj = unmatched_context.get("unmatched_simulations", {}).get(sim_num)
                    folder_path = unmatched_context.get("unmatched_folders", {}).get(folder_id)
                    
                    if simulation_obj and folder_path:
                        manual_pairs.append((sim_num, simulation_obj, folder_path))
                        selected_folders.add(folder_id)
        
        return manual_pairs, selected_folders
    
    def _display_annexes_preview(self, annexes: Dict[str, Any]):
        """Affiche un aperçu des annexes générées."""
        st.write("### 📊 Tableau complet")
        nb_simulations = len(annexes['tableau_complet']['simulations'])
        st.write(f"**{nb_simulations} simulations** seront incluses dans le tableau récapitulatif")
        
        if annexes.get('essais_detailles'):
            st.write("### 📷 Essais détaillés")
            nb_essais = len(annexes['essais_detailles'])
            st.write(f"**{nb_essais} essais** avec images détaillées")
            
            # Aperçu de quelques essais
            for i, essai in enumerate(annexes['essais_detailles'][:3]):
                nb_images = len(essai.get('images', []))
                st.write(f"• Essai {essai['numero_essai']}: {nb_images} image(s)")
            
            if len(annexes['essais_detailles']) > 3:
                st.write(f"• ... et {len(annexes['essais_detailles']) - 3} autres essais")
    
    def _display_manual_organization(self, organized_files: Dict[str, List]):
        """Affiche l'organisation des fichiers manuels."""
        with st.expander("📁 Organisation des fichiers", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📷 Figures**")
                figures = organized_files.get("figures", [])
                if figures:
                    for fig in figures[:5]:  # Montrer les 5 premiers
                        st.write(f"• {fig['nom']}")
                    if len(figures) > 5:
                        st.write(f"• ... et {len(figures) - 5} autres")
                else:
                    st.write("Aucune figure")
                
                st.write("**📊 Tableaux**")
                tableaux = organized_files.get("tableaux", [])
                if tableaux:
                    for tab in tableaux[:5]:
                        st.write(f"• {tab['nom']}")
                    if len(tableaux) > 5:
                        st.write(f"• ... et {len(tableaux) - 5} autres")
                else:
                    st.write("Aucun tableau")
            
            with col2:
                st.write("**📄 Documents**")
                documents = organized_files.get("documents", [])
                if documents:
                    for doc in documents[:5]:
                        st.write(f"• {doc['nom']}")
                    if len(documents) > 5:
                        st.write(f"• ... et {len(documents) - 5} autres")
                else:
                    st.write("Aucun document")
                
                st.write("**📦 Autres**")
                autres = organized_files.get("autres", [])
                if autres:
                    for autre in autres[:5]:
                        st.write(f"• {autre['nom']}")
                    if len(autres) > 5:
                        st.write(f"• ... et {len(autres) - 5} autres")
                else:
                    st.write("Aucun autre fichier")


# Fonction de compatibilité pour l'ancien code
def render() -> Dict[str, Any]:
    """Fonction de compatibilité avec l'ancien code."""
    form = AnnexesForm()
    return form.render()
