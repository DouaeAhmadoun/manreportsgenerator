# =============================================================================
# forms/ships_form.py - Formulaire des navires et remorqueurs
# =============================================================================

import streamlit as st
import os
from typing import Dict, Any, List
from .base_form import BaseForm
from .form_utils import initialize_session_key


class ShipsForm(BaseForm):
    """
    Formulaire pour la gestion des navires et remorqueurs.
    
    Gère :
    - Liste des navires avec caractéristiques techniques
    - Liste des remorqueurs avec capacités
    - Upload d'images pour chaque unité
    - Validation des données techniques
    - Commentaires et descriptions
    """
    
    def __init__(self):
        super().__init__("ships")
        self.required_ship_fields = ["nom", "type", "longueur", "largeur"]
        self.required_tugboat_fields = ["nom", "type", "traction"]
    
    def render(self) -> Dict[str, Any]:
        """Rend le formulaire des navires et remorqueurs."""
        try:
            self.render_section_header(
                "🚢 Navires et remorqueurs", 
                divider=True,
                help_text="💡 Définissez les navires et remorqueurs pour l'étude"
            )
            
            # Récupérer les valeurs par défaut
            defaults = self.get_defaults()
            
            # Section navires
            navires_data = self._render_ships_section(defaults)
            
            # Section remorqueurs
            remorqueurs_data = self._render_tugboats_section(defaults)
            
            # Données complètes
            ships_data = {
                "navires": navires_data,
                "remorqueurs": remorqueurs_data
            }
            
            # Validation
            if self.validate_data(ships_data):
                self.display_validation_messages()
            
            # Affichage du résumé
            self._render_summary(ships_data)
            
            return ships_data
            
        except Exception as e:
            st.error(f"❌ Erreur dans le formulaire navires : {str(e)}")
            return self._get_default_ships_data()
    
    def _render_ships_section(self, defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Rend la section des navires."""
        st.subheader("🚢 Navires projets", divider=True)
        
        # Initialiser les navires depuis rapport_data
        initialize_session_key(
            "navires",
            [],
            "donnees_navires.navires.navires"
        )
        
        # Interface de gestion des navires
        navires = self.create_dynamic_list_widget(
            "Navire",
            "navires",
            [],
            self._render_single_ship
        )
        
        commentaire_navires = self._render_optional_comment(
            "Ajouter un commentaire sur les navires",
            "Commentaire navires",
            defaults["navires_commentaire"]
        )
        
        return {
            "navires": navires,
            "commentaire": commentaire_navires
        }
    
    def _render_single_ship(self, index: int, existing_ship: Dict[str, Any]) -> Dict[str, Any]:
        """Rend le formulaire pour un navire individuel."""
        col1, col2 = st.columns(2)
        
        with col1:
            # Informations de base
            nom = st.text_input(
                "Nom du navire *",
                value=existing_ship.get("nom", ""),
                key=f"nav_nom_{index}"
            )
            
            type_nav = st.text_input(
                "Type *",
                value=existing_ship.get("type", ""),
                key=f"nav_type_{index}",
                help="Ex: Porte-conteneurs, Pétrolier, Vraquier..."
            )
            
            # Dimensions principales
            longueur = st.number_input(
                "Longueur (m) *",
                value=float(existing_ship.get("longueur", 0.0)), 
                min_value=0.0, 
                step=0.5, 
                key=f"nav_longueur_{index}"
            )
            
            largeur = st.number_input(
                "Largeur (m) *", 
                value=float(existing_ship.get("largeur", 0.0)), 
                min_value=0.0, 
                step=0.5, 
                key=f"nav_largeur_{index}"
            )
            
            # Tirants d'eau
            tirant_av = st.number_input(
                "Tirant d'eau avant (m)", 
                value=float(existing_ship.get("tirant_eau_av", 0.0)), 
                min_value=0.0, 
                step=0.1, 
                key=f"nav_tir_av_{index}"
            )
            
            tirant_ar = st.number_input(
                "Tirant d'eau arrière (m)", 
                value=float(existing_ship.get("tirant_eau_ar", 0.0)), 
                min_value=0.0, 
                step=0.1, 
                key=f"nav_tir_ar_{index}"
            )

            deplacement = st.number_input(
                "Déplacement (tonnes)", 
                value=float(existing_ship.get("deplacement", 0.0)), 
                min_value=0.0, 
                step=100.0, 
                key=f"nav_deplacement_{index}"
            )
        
        with col2:
            # Caractéristiques techniques
            propulsion = st.text_input(
                "Type de propulsion", 
                value=existing_ship.get("propulsion", ""), 
                key=f"nav_propulsion_{index}",
                help="Ex: Moteur diesel, Turbine à gaz..."
            )
            
            puissance = st.text_input(
                "Puissance machine", 
                value=existing_ship.get("puissance_machine", ""), 
                key=f"nav_puissance_{index}",
                help="Ex: 15 000 kW, 20 000 HP..."
            )
            
            # Rôle dans l'étude
            role_options = ["actif", "passif"]
            current_role = "actif" if existing_ship.get("est_actif", True) else "passif"
            role_index = role_options.index(current_role)
            est_actif = st.selectbox(
                "Rôle dans l'étude", 
                role_options, 
                index=role_index, 
                key=f"nav_role_{index}",
                help="Actif: navire principal étudié, Passif: navire de référence"
            )
            
            # Remarques
            remarque = st.text_input(
                "Remarques", 
                value=existing_ship.get("remarques", ""), 
                key=f"nav_remarque_{index}",
            )
        
            # Image du navire (sur toute la largeur)
            image_path = self._render_ship_image_upload(index, existing_ship)
            
            # Validation des dimensions
            self._validate_ship_dimensions(longueur, largeur, tirant_av, tirant_ar, index)
        
        return {
            "nom": nom,
            "type": type_nav,
            "longueur": longueur,
            "largeur": largeur,
            "tirant_eau_av": tirant_av,
            "tirant_eau_ar": tirant_ar,
            "deplacement": deplacement,
            "propulsion": propulsion,
            "puissance_machine": puissance,
            "remarques": remarque,
            "figure": image_path,
            "est_actif": est_actif == "actif"
        }
    
    def _render_tugboats_section(self, defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Rend la section des remorqueurs."""
        st.subheader("🚤 Remorqueurs", divider=True)
        
        # Initialiser les remorqueurs depuis rapport_data
        initialize_session_key(
            "remorqueurs", 
            [], 
            "donnees_navires.remorqueurs.remorqueurs"
        )
        
        # Interface de gestion des remorqueurs
        remorqueurs = self.create_dynamic_list_widget(
            "Remorqueur",
            "remorqueurs",
            [],
            self._render_single_tugboat
        )
        
        # Commentaire sur les remorqueurs
        commentaire_remorqueurs = self._render_optional_comment(
            "Ajouter un commentaire sur les remorqueurs",
            "Commentaire remorqueurs",
            defaults["remorqueurs_commentaire"]
        )
        
        return {
            "remorqueurs": remorqueurs,
            "commentaire": commentaire_remorqueurs
        }
    
    def _render_single_tugboat(self, index: int, existing_tugboat: Dict[str, Any]) -> Dict[str, Any]:
        """Rend le formulaire pour un remorqueur individuel."""
        col1, col2 = st.columns(2)
        
        with col1:
            # Informations de base
            nom = st.text_input(
                "Nom *", 
                value=existing_tugboat.get("nom", ""), 
                key=f"rem_nom_{index}"
            )
            
            type_rem = st.text_input(
                "Type *", 
                value=existing_tugboat.get("type", ""), 
                key=f"rem_type_{index}",
                help="Ex: ASD, Tracteur conventionnel, VSP..."
            )
            
            # Dimensions
            longueur = st.number_input(
                "Longueur (m)", 
                value=float(existing_tugboat.get("longueur", 0.0)), 
                min_value=0.0, 
                step=0.5, 
                key=f"rem_longueur_{index}"
            )
            
            lbp = st.number_input(
                "LBP (m)", 
                value=float(existing_tugboat.get("lbp", 0.0)), 
                min_value=0.0, 
                step=0.5, 
                key=f"rem_lbp_{index}",
                help="Longueur entre perpendiculaires"
            )
            
            largeur = st.number_input(
                "Largeur (m)", 
                value=float(existing_tugboat.get("largeur", 0.0)), 
                min_value=0.0, 
                step=0.5, 
                key=f"rem_largeur_{index}"
            )
            
            tirant_eau = st.number_input(
                "Tirant d'eau (m)", 
                value=float(existing_tugboat.get("tirant_eau", 0.0)), 
                min_value=0.0, 
                step=0.1, 
                key=f"rem_tirant_{index}"
            )
        
        with col2:
            # Performances
            vitesse = st.number_input(
                "Vitesse max (nœuds)", 
                value=float(existing_tugboat.get("vitesse", 0.0)), 
                min_value=0.0, 
                step=0.5, 
                key=f"rem_vitesse_{index}"
            )
            
            traction = st.number_input(
                "Capacité de traction (tonnes) *", 
                value=float(existing_tugboat.get("traction", 0.0)), 
                min_value=0.0, 
                step=0.5, 
                key=f"rem_traction_{index}"
            )
            
            # Remarques
            remarque = st.text_input(
                "Remarques", 
                value=existing_tugboat.get("remarques", ""), 
                key=f"rem_remarque_{index}",
            )
        
            # Image du remorqueur (sur toute la largeur)
            image_path = self._render_tugboat_image_upload(index, existing_tugboat)
            
            # Validation des performances
            self._validate_tugboat_performance(traction, vitesse, index)
        
        return {
            "nom": nom,
            "type": type_rem,
            "longueur": longueur,
            "lbp": lbp,
            "largeur": largeur,
            "tirant_eau": tirant_eau,
            "vitesse": vitesse,
            "traction": traction,
            "remarques": remarque,
            "figure": image_path
        }
    
    def _render_ship_image_upload(self, index: int, existing_ship: Dict[str, Any]) -> str:
        """Rend l'upload d'image pour un navire."""        
        image = st.file_uploader(
            "Image du navire", 
            type=["png", "jpg", "jpeg"], 
            key=f"nav_img_{index}",
            help="Profil ou photo du navire"
        )
        
        # Utiliser le nouveau fichier ou garder l'existant
        img_path = self.save_uploaded_file(image) if image else existing_ship.get("figure", "")
        
        # Afficher l'aperçu
        if img_path and os.path.exists(img_path):
            st.image(img_path, caption="Profil navire", width=220)
        
        return img_path
    
    def _render_tugboat_image_upload(self, index: int, existing_tugboat: Dict[str, Any]) -> str:
        """Rend l'upload d'image pour un remorqueur."""
        #st.write("**📷 Image du remorqueur**")
        
        image = st.file_uploader(
            "Image du remorqueur (facultative)", 
            type=["png", "jpg", "jpeg"], 
            key=f"rem_img_{index}",
            help="Profil ou photo du remorqueur"
        )
        
        # Utiliser le nouveau fichier ou garder l'existant
        img_path = self.save_uploaded_file(image) if image else existing_tugboat.get("figure", "")
        
        # Afficher l'aperçu
        if img_path and os.path.exists(img_path):
            st.image(img_path, caption="Profil remorqueur", width=220)
        
        return img_path
    
    def _render_optional_comment(self, checkbox_label: str, textarea_label: str, default_value: str) -> str:
        """Rend un commentaire optionnel avec checkbox."""
        comment_exists = bool(default_value)
        
        if st.checkbox(f"➕ {checkbox_label}", value=comment_exists):
            return st.text_area(textarea_label, value=default_value)
        
        return ""
    
    def _validate_ship_dimensions(self, longueur: float, largeur: float, 
                                tirant_av: float, tirant_ar: float, index: int):
        """Valide les dimensions d'un navire."""
        if longueur > 0 and largeur > 0:
            # Vérifier les proportions
            ratio = longueur / largeur
            if ratio < 3:
                st.warning(f"⚠️ Navire {index+1}: Ratio L/B = {ratio:.1f} (faible pour un navire)")
            elif ratio > 15:
                st.warning(f"⚠️ Navire {index+1}: Ratio L/B = {ratio:.1f} (très élancé)")
            
            # Vérifier la cohérence longueur/largeur
            if longueur < largeur:
                st.error(f"❌ Navire {index+1}: Longueur < largeur (incohérent)")
        
        # Vérifier les tirants d'eau
        if tirant_av > 0 and tirant_ar > 0:
            diff_tirant = abs(tirant_ar - tirant_av)
            if diff_tirant > 5:
                st.warning(f"⚠️ Navire {index+1}: Grande différence de tirant d'eau ({diff_tirant:.1f}m)")
    
    def _validate_tugboat_performance(self, traction: float, vitesse: float, index: int):
        """Valide les performances d'un remorqueur."""
        if traction > 0:
            # Catégoriser le remorqueur selon sa traction
            if traction < 20:
                category = "Léger"
            elif traction < 50:
                category = "Moyen"
            elif traction < 80:
                category = "Lourd"
            else:
                category = "Très lourd"
            
            st.info(f"📊 Remorqueur {index+1}: Catégorie {category} ({traction}T)")
            
            # Vérifier la cohérence traction/vitesse
            if vitesse > 0:
                if traction > 60 and vitesse > 15:
                    st.warning(f"⚠️ Remorqueur {index+1}: Traction élevée + vitesse élevée (inhabituel)")
                elif traction < 30 and vitesse < 10:
                    st.warning(f"⚠️ Remorqueur {index+1}: Performances faibles")
    
    def _render_summary(self, ships_data: Dict[str, Any]):
        """Affiche un résumé des navires et remorqueurs."""
        with st.expander("📋 Résumé des unités", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🚢 Navires**")
                navires = ships_data["navires"]["navires"]
                if navires:
                    for i, navire in enumerate(navires):
                        status = "🟢 Actif" if navire.get("est_actif") else "⚪ Passif"
                        st.write(f"• {navire.get('nom', f'Navire {i+1}')} - {status}")
                        if navire.get("longueur") and navire.get("largeur"):
                            st.write(f"  📏 {navire['longueur']}m × {navire['largeur']}m")
                        if navire.get("type"):
                            st.write(f"  🔧 Type: {navire['type']}")
                else:
                    st.write("Aucun navire défini")
            
            with col2:
                st.write("**🚤 Remorqueurs**")
                remorqueurs = ships_data["remorqueurs"]["remorqueurs"]
                if remorqueurs:
                    for i, remorqueur in enumerate(remorqueurs):
                        st.write(f"• {remorqueur.get('nom', f'Remorqueur {i+1}')}")
                        if remorqueur.get("traction"):
                            st.write(f"  💪 {remorqueur['traction']}T de traction")
                        if remorqueur.get("type"):
                            st.write(f"  🔧 Type: {remorqueur['type']}")
                else:
                    st.write("Aucun remorqueur défini")
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Valide les données des navires et remorqueurs."""
        self.errors.clear()
        self.warnings.clear()
        
        # Validation des navires
        navires = data.get("navires", {}).get("navires", [])
        if not navires:
            self.errors.append("Au moins un navire doit être défini")
        else:
            for i, navire in enumerate(navires):
                self._validate_single_ship_data(navire, i+1)
        
        # Validation des remorqueurs
        remorqueurs = data.get("remorqueurs", {}).get("remorqueurs", [])
        if not remorqueurs:
            self.warnings.append("Aucun remorqueur défini")
        else:
            for i, remorqueur in enumerate(remorqueurs):
                self._validate_single_tugboat_data(remorqueur, i+1)
        
        # Validation de cohérence
        self._validate_fleet_coherence(navires, remorqueurs)
        
        return len(self.errors) == 0
    
    def _validate_single_ship_data(self, navire: Dict[str, Any], index: int):
        """Valide les données d'un navire individuel."""
        # Champs requis
        for field in self.required_ship_fields:
            if not navire.get(field):
                self.warnings.append(f"Navire {index}: {field} manquant")
        
        # Validation des dimensions numériques
        numeric_fields = ["longueur", "largeur", "tirant_eau_av", "tirant_eau_ar", "deplacement"]
        for field in numeric_fields:
            value = navire.get(field)
            if value is not None:
                try:
                    num_value = float(value)
                    if num_value < 0:
                        self.errors.append(f"Navire {index}: {field} ne peut pas être négatif")
                    elif field in ["longueur", "largeur"] and num_value == 0:
                        self.warnings.append(f"Navire {index}: {field} non défini")
                except (ValueError, TypeError):
                    self.errors.append(f"Navire {index}: {field} doit être numérique")
    
    def _validate_single_tugboat_data(self, remorqueur: Dict[str, Any], index: int):
        """Valide les données d'un remorqueur individuel."""
        # Champs requis
        for field in self.required_tugboat_fields:
            if not remorqueur.get(field):
                self.warnings.append(f"Remorqueur {index}: {field} manquant")
        
        # Validation de la traction
        traction = remorqueur.get("traction")
        if traction is not None:
            try:
                traction_value = float(traction)
                if traction_value <= 0:
                    self.errors.append(f"Remorqueur {index}: traction doit être positive")
                elif traction_value > 200:
                    self.warnings.append(f"Remorqueur {index}: traction très élevée ({traction_value}T)")
            except (ValueError, TypeError):
                self.errors.append(f"Remorqueur {index}: traction doit être numérique")
    
    def _validate_fleet_coherence(self, navires: List[Dict], remorqueurs: List[Dict]):
        """Valide la cohérence de la flotte."""
        if navires and remorqueurs:
            # Vérifier l'adéquation taille navires / puissance remorqueurs
            max_navire_longueur = max(
                (float(n.get("longueur", 0)) for n in navires if n.get("longueur")), 
                default=0
            )
            max_traction_remorqueur = max(
                (float(r.get("traction", 0)) for r in remorqueurs if r.get("traction")), 
                default=0
            )
            
            if max_navire_longueur > 300 and max_traction_remorqueur < 50:
                self.warnings.append(
                    "Grands navires (>300m) avec remorqueurs de faible puissance (<50T)"
                )
    
    def _get_default_ships_data(self) -> Dict[str, Any]:
        """Retourne des données par défaut en cas d'erreur."""
        return {
            "navires": {
                "navires": [],
                "description": "",
                "commentaire": ""
            },
            "remorqueurs": {
                "remorqueurs": [],
                "commentaire": ""
            }
        }


# Fonction de compatibilité pour l'ancien code
def render() -> Dict[str, Any]:
    """Fonction de compatibilité avec l'ancien code."""
    st.divider()
    form = ShipsForm()
    return form.render()
