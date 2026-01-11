import streamlit as st
import os
from docxtpl import InlineImage
from docx.shared import Mm
from PIL import Image
from typing import Dict, Any, List, Tuple, Union
import tempfile
import pandas as pd
import matplotlib.pyplot as plt


class ImageProcessor:
    """Classe responsable du traitement des images pour les documents Word"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        self.temp_files = []
        
        self.image_rules = {
            "logo": (70, 30),
            # Augmenté pour améliorer la lisibilité du logo client
            "client_logo": (140, 100),
            "main": (160, 120),
            "main_image": (160, 120),
            "gallery": (50, 40), 
            "simulation": (70, 55),
            "figure": (130, 98),
            "planche": (90, 70),
            "navire": (130, 98),
            "remorqueur": (120, 90),
            "bathymetrie": (140, 105),
            "balisage": (140, 105),
            "plan_masse": (160, 120),
            "essai": (150, 120), 
            "annexe": (200, 150),
            "default": (120, 100)
        }
        
        self.quality_settings = {
            "logo": 98,
            "client_logo": 98,
            "main_image": 95,
            "main": 95,
            "simulation": 92,
            "figure": 95,
            "navire": 100,
            "remorqueur": 93,
            "plan_masse": 93,
            "default": 99 
        }
        
        self.target_dpi = 200
        # Autorise un DPI plus élevé pour les exports de tableaux afin d'améliorer la lisibilité
        self.max_dpi = 400

    def excel_to_png(self, excel_path: str, max_rows: int = 20, max_cols: int = 10) -> str:
        """Convertit un fichier Excel en image PNG (aperçu tableau)."""
        try:
            df = pd.read_excel(excel_path, nrows=max_rows)
            df = df.iloc[:, :max_cols]
            
            # Taille fig ajustée pour limiter les marges et améliorer la lisibilité
            fig_w = min(14, max(6, df.shape[1] * 1.4))
            fig_h = min(14, max(4.5, df.shape[0] * 0.5))
            fig, ax = plt.subplots(figsize=(fig_w, fig_h))
            ax.axis('off')
            ax.set_frame_on(False)

            tbl = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(10)
            tbl.scale(1.15, 1.25)

            # Uniformise la hauteur des cellules pour réduire l'espace vertical
            for (_, _), cell in tbl.get_celld().items():
                cell.set_height(0.24)

            tmp_png = tempfile.mktemp(suffix=".png")
            plt.tight_layout(pad=0.05)

            # Sauvegarde en minimisant les marges autour du tableau
            fig.canvas.draw()
            bbox = tbl.get_window_extent(fig.canvas.get_renderer())
            fig.savefig(
                tmp_png,
                bbox_inches=bbox.transformed(fig.dpi_scale_trans.inverted()),
                pad_inches=0.02,
                dpi=min(self.max_dpi, 400),
            )
            plt.close(fig)
            return tmp_png
        except Exception as e:
            st.warning(f"⚠️ Tableau Excel non converti ({os.path.basename(excel_path)}): {e}")
            return excel_path
    
    def is_image_path(self, value: Any) -> bool:
        """Vérifie si une valeur est un chemin d'image valide"""
        if not isinstance(value, str) or not value.strip():
            return False
        
        try:
            ext = os.path.splitext(value.lower())[1]
            is_image_ext = ext in self.supported_formats
            
            if is_image_ext and '/' not in value and '\\' not in value:
                return False
            
            return is_image_ext
        except:
            return False

    def validate_image(self, image_path: str) -> Dict[str, Any]:
        """Valide qu'une image existe et est utilisable"""
        validation = {
            "valid": False,
            "exists": False,
            "readable": False,
            "format_supported": False,
            "error": None,
            "info": {}
        }
        
        if not image_path or not isinstance(image_path, str):
            validation["error"] = "Chemin d'image invalide"
            return validation
    
        if not os.path.exists(image_path):
            validation["error"] = f"Fichier non trouvé: {image_path}"
            return validation
        
        validation["exists"] = True
        
        ext = os.path.splitext(image_path.lower())[1]
        if ext not in self.supported_formats:
            validation["error"] = f"Format non supporté: {ext}"
            return validation
        
        validation["format_supported"] = True
        
        try:
            with Image.open(image_path) as img:
                img.verify()
                validation["readable"] = True
                validation["valid"] = True
                
                with Image.open(image_path) as img_info:
                    validation["info"] = {
                        "width": img_info.width,
                        "height": img_info.height,
                        "format": img_info.format,
                        "mode": img_info.mode,
                        "size_bytes": os.path.getsize(image_path),
                        "size_mb": os.path.getsize(image_path) / (1024 * 1024)
                    }
                    
        except Exception as e:
            validation["error"] = f"Image corrompue: {str(e)}"
        
        return validation
    
    def get_image_size_for_context(self, key_context: str = None) -> Tuple[int, int]:
        """Détermine la taille d'image appropriée selon le contexte - AVEC DEBUG NAVIRES"""
        if not key_context:
            return self.image_rules["default"]
        
        key_lower = key_context.lower()
        
        # Recherche par correspondance partielle avec priorité navires
        for keyword, (max_w, max_h) in self.image_rules.items():
            if keyword in key_lower:
                return max_w, max_h
        
        return self.image_rules["default"]
    
    def get_quality_for_context(self, key_context: str = None) -> int:
        """Détermine la qualité JPEG selon le contexte"""
        if not key_context:
            return self.quality_settings["default"]
        
        key_lower = key_context.lower()
        
        for keyword, quality in self.quality_settings.items():
            if keyword in key_lower:
                return quality
        
        return self.quality_settings["default"]
    
    def get_dpi_for_context(self, key_context: str = None) -> int:
        """Détermine le DPI selon le contexte"""
        if not key_context:
            return self.target_dpi
        
        key_lower = key_context.lower()
        
        # Contextes nécessitant DPI maximum
        high_dpi_contexts = ["logo", "client_logo", "plan_masse", "navire", "figure", "remorqueur"]
        
        for context in high_dpi_contexts:
            if context in key_lower:
                return self.max_dpi
        
        return self.target_dpi
    
    def optimize_image_for_word(self, image_path: str, max_width: int = None, max_height: int = None, 
                               quality: int = None, target_dpi: int = None) -> str:
        """Optimise une image pour l'inclusion dans Word"""
        validation = self.validate_image(image_path)
        
        if not validation["valid"]:
            st.warning(f"⚠️ Image non valide: {validation['error']}")
            return image_path
        
        if max_width is None:
            max_width = 2000
        if max_height is None:
            max_height = 1500
        if quality is None:
            quality = 85
        if target_dpi is None:
            target_dpi = self.target_dpi
        
        try:
            with Image.open(image_path) as img:
                original_size = img.size
                
                # Convertir en RGB si nécessaire
                if img.mode in ('RGBA', 'LA', 'P'):
                    if img.mode == 'P' and 'transparency' in img.info:
                        img = img.convert('RGBA')
                    
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'RGBA':
                            background.paste(img, mask=img.split()[3])
                        else:
                            background.paste(img, mask=img.split()[1])
                        img = background
                    else:
                        img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # REDIMENSIONNEMENT PLUS INTELLIGENT
                needs_resize = img.width > max_width or img.height > max_height
                
                # NE REDIMENSIONNER QUE SI VRAIMENT NÉCESSAIRE
                resize_threshold = 1.2  # Seuil plus élevé
                if img.width > max_width * resize_threshold or img.height > max_height * resize_threshold:
                    # Calculer les nouvelles dimensions en gardant le ratio
                    ratio = min(max_width / img.width, max_height / img.height)
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    
                    # ALGORITHME DE REDIMENSIONNEMENT DE MEILLEURE QUALITÉ
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    needs_optimization = True
                else:
                    needs_optimization = False
                
                # CRITÈRES D'OPTIMISATION PLUS STRICTS
                file_size_mb = validation["info"]["size_mb"]
                needs_format_conversion = img.format != 'JPEG'
                needs_compression = file_size_mb > 5  # Seuil plus élevé
                
                if needs_optimization or needs_format_conversion or needs_compression:
                    base_name = os.path.splitext(os.path.basename(image_path))[0]
                    temp_dir = tempfile.gettempdir()
                    optimized_path = os.path.join(temp_dir, f"{base_name}_hq_{id(img)}.jpg")
                    
                    # SAUVEGARDE HAUTE QUALITÉ
                    save_kwargs = {
                        'format': 'JPEG',
                        'quality': quality,
                        'optimize': True,
                        'progressive': True,  # JPEG progressif pour meilleur rendu
                        'dpi': (target_dpi, target_dpi)  # DPI élevé
                    }
                    
                    img.save(optimized_path, **save_kwargs)
                    self.temp_files.append(optimized_path)
                    
                    # Log des informations
                    new_size = os.path.getsize(optimized_path) / (1024 * 1024)
                    
                    return optimized_path
                else:
                    return image_path
                    
        except Exception as e:
            st.warning(f"Impossible d'optimiser l'image {image_path}: {e}")
            return image_path
    
    def create_inline_image(self, doc, image_path: str, key_context: str = None) -> Union[InlineImage, str]:
        """Crée une InlineImage HAUTE QUALITÉ"""
        validation = self.validate_image(image_path)
        
        if not validation["valid"]:
            error_msg = f"[Image non disponible: {os.path.basename(image_path) if image_path else 'N/A'}]"
            if validation["error"]:
                st.warning(f"⚠️ {validation['error']}")
            return error_msg
        
        try:
            # PARAMÈTRES ADAPTÉS AU CONTEXTE
            max_width, max_height = self.get_image_size_for_context(key_context)
            quality = self.get_quality_for_context(key_context)
            target_dpi = self.get_dpi_for_context(key_context)
            
            # LIMITES PLUS GÉNÉREUSES pour l'optimisation
            opt_max_width = max_width * 3   # 3x plus grand pour la résolution
            opt_max_height = max_height * 3
            
            # Optimiser l'image
            optimized_path = self.optimize_image_for_word(
                image_path, opt_max_width, opt_max_height, quality, target_dpi
            )
            
            # DIMENSIONS FINALES PRÉCISES AVEC AGRANDISSEMENT
            with Image.open(optimized_path) as img:
                width_px, height_px = img.size
                
                # CALCUL DPI INTELLIGENT
                actual_dpi = target_dpi
                if hasattr(img, 'info') and 'dpi' in img.info:
                    try:
                        actual_dpi = img.info['dpi'][0] if isinstance(img.info['dpi'], tuple) else img.info['dpi']
                    except:
                        actual_dpi = target_dpi
                
                # Convertir en mm avec DPI correct
                width_mm = width_px * 25.4 / actual_dpi
                height_mm = height_px * 25.4 / actual_dpi
                
                # AGRANDIR LES PETITES IMAGES
                if width_mm < max_width and height_mm < max_height:
                    # L'image est plus petite que la cible -> l'agrandir modérément
                    scale_width = max_width / width_mm
                    scale_height = max_height / height_mm
                    
                    target_scale = min(scale_width, scale_height) * 0.85
                    
                    if target_scale > 1.5:
                        target_scale = 1.5
                    
                    if key_context and any(ship in key_context.lower() for ship in ['navire', 'figure', 'remorqueur']):
                        final_width = width_mm * target_scale
                        
                        if final_width < 100:  # Minimum 10cm
                            target_scale = 100 / width_mm
                        elif final_width > 120:  # Maximum 12cm
                            target_scale = 120 / width_mm
                    
                    width_mm *= target_scale
                    height_mm *= target_scale

                elif width_mm > max_width or height_mm > max_height:
                    scale = min(max_width / width_mm, max_height / height_mm)
                    width_mm *= scale
                    height_mm *= scale
                
                # CRÉATION avec dimensions optimales
                return InlineImage(doc, optimized_path, width=Mm(width_mm), height=Mm(height_mm))
        
        except Exception as e:
            error_msg = f"[⚠️ Erreur image: {os.path.basename(image_path)}]"
            st.warning(f"⚠️ Erreur traitement image {os.path.basename(image_path)}: {e}")
            print(f"❌ ERREUR: {e}")
            return error_msg
    
    def replace_images_in_data(self, data: Any, doc, key_context: str = None) -> Any:
        """Remplace récursivement tous les chemins d'images par des InlineImage - AVEC DEBUG COMPLET"""
        if isinstance(data, dict):
            result = {}
            for k, v in data.items():                
                # DEBUG SPÉCIAL POUR NAVIRES
                if k == "annexes" and isinstance(v, dict):
                    result[k] = self.process_annexes_images(v, doc)
                elif k.lower() == "tableaux" and isinstance(v, list):
                    tableaux_converted = []
                    for tab in v:
                        tab_copy = dict(tab) if isinstance(tab, dict) else {"chemin": tab}
                        chemin = tab_copy.get("chemin", "")
                        if isinstance(chemin, str):
                            ext = os.path.splitext(chemin.lower())[1]
                            if ext in [".xlsx", ".xls"]:
                                tab_copy["chemin"] = self.excel_to_png(chemin)
                            # Ajouter une légende auto si absente
                            if not tab_copy.get("legende"):
                                tab_copy["legende"] = os.path.splitext(os.path.basename(chemin))[0]
                        tableaux_converted.append(tab_copy)
                    result[k] = [self.replace_images_in_data(t, doc, "tableau") for t in tableaux_converted]
                else:
                    # Ne traiter que les champs qui DOIVENT contenir des chemins d'images
                    if self._should_process_as_image(k, v):
                        # Légende auto si absente sur un dict porteur d'image
                        if isinstance(v, dict) and v.get("chemin") and not v.get("legende"):
                            v = dict(v)
                            v["legende"] = os.path.splitext(os.path.basename(v["chemin"]))[0]
                        # Passer la clé comme contexte pour les images
                        context = k if self.is_image_path(v) else key_context
                        result[k] = self.create_inline_image(doc, v, context)
                    else:
                        # Continuer la récursion pour les autres champs
                        context = k if self.is_image_path(v) else key_context
                        result[k] = self.replace_images_in_data(v, doc, context)
            return result
            
        elif isinstance(data, list):
            items = []
            for item in data:
                if isinstance(item, dict):
                    tab_copy = dict(item)
                    chemin = tab_copy.get("chemin", "")
                    if isinstance(chemin, str):
                        ext = os.path.splitext(chemin.lower())[1]
                        if ext in [".xlsx", ".xls"]:
                            tab_copy["chemin"] = self.excel_to_png(chemin)
                        if not tab_copy.get("legende"):
                            tab_copy["legende"] = os.path.splitext(os.path.basename(chemin))[0]
                    items.append(self.replace_images_in_data(tab_copy, doc, key_context))
                else:
                    items.append(self.replace_images_in_data(item, doc, key_context))
            return items
            
        elif self.is_image_path(data):
            # SÉCURITÉ : Double vérification
            return self.create_inline_image(doc, data, key_context)
            
        else:
            return data

    def _should_process_as_image(self, key: str, value: Any) -> bool:
        """Détermine si un champ doit être traité comme un chemin d'image"""
        
        image_field_names = {
            "chemin", "figure", "main_image", "path", "client_logo",
            "image_path", "inline_image"
        }
        
        non_image_fields = {
            "nom_fichier", "nom", "name", "filename", "title", "legende", 
            "legend", "description", "taille", "size", "width", "height", 
            "format", "extension"
        }
        
        key_lower = key.lower()
        if key_lower in non_image_fields:
            return False
        if key_lower in image_field_names:
            return self.is_image_path(value)
        
        return self.is_image_path(value)

    def process_annexes_images(self, annexes_data: dict, doc) -> dict:
        """Traite spécifiquement les images dans les annexes"""
        if not isinstance(annexes_data, dict):
            return annexes_data
        
        result = {}
        
        for key, value in annexes_data.items():
            if key == "tableau_complet" and isinstance(value, dict):
                result[key] = self.process_tableau_images(value, doc)
            elif key == "essais_detailles" and isinstance(value, list):
                result[key] = self.process_essais_images(value, doc)
            else:
                result[key] = self.replace_images_in_data(value, doc, "annexe")
        
        return result
    
    def process_tableau_images(self, tableau_data: dict, doc) -> dict:
        """Traite les images dans le tableau des simulations avec HAUTE QUALITÉ"""
        result = {}
        
        for key, value in tableau_data.items():
            if key == "simulations" and isinstance(value, list):
                simulations_with_images = []
                
                for i, sim in enumerate(value):
                    sim_copy = dict(sim)
                    
                    if "images" in sim_copy and isinstance(sim_copy["images"], list):
                        images_processed = []
                        
                        for img in sim_copy["images"]:
                            img_copy = dict(img)
                            image_path = img_copy.get("chemin")
                            
                            if image_path:
                                try:
                                    # CONTEXTE SPÉCIFIQUE pour simulations
                                    inline_image = self.create_inline_image(doc, image_path, "annexe")
                                    img_copy["inline_image"] = inline_image
                                    
                                except Exception as e:
                                    st.error(f"❌ Erreur image simulation {i+1}: {e}")
                                    img_copy["inline_image"] = f"[Erreur: {img_copy.get('nom', 'N/A')}]"
                            else:
                                img_copy["inline_image"] = f"[Pas de chemin: {img_copy.get('nom', 'N/A')}]"
                            
                            images_processed.append(img_copy)
                        
                        sim_copy["images"] = images_processed
                    
                    simulations_with_images.append(sim_copy)
                
                result[key] = simulations_with_images
            else:
                result[key] = value
        
        return result
    
    def process_essais_images(self, essais_list: list, doc) -> list:
        """Traite les images dans les essais détaillés avec HAUTE QUALITÉ"""
        processed_essais = []
        
        for i, essai in enumerate(essais_list):
            essai_copy = dict(essai)
            
            if "images" in essai_copy and isinstance(essai_copy["images"], list):
                images_processed = []
                
                for img in essai_copy["images"]:
                    img_copy = dict(img)
                    image_path = img_copy.get("chemin")
                    
                    if image_path:
                        try:
                            # CONTEXTE SPÉCIFIQUE pour essais
                            inline_image = self.create_inline_image(doc, image_path, "essai")
                            img_copy["inline_image"] = inline_image
                        except Exception as e:
                            st.warning(f"⚠️ Erreur image essai {i+1}: {e}")
                            img_copy["inline_image"] = f"[Erreur: {img_copy.get('nom', 'N/A')}]"
                    else:
                        img_copy["inline_image"] = f"[Pas de chemin: {img_copy.get('nom', 'N/A')}]"
                    
                    images_processed.append(img_copy)
                
                essai_copy["images"] = images_processed
            
            processed_essais.append(essai_copy)
        
        return processed_essais
