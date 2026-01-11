import streamlit as st
import os
import zipfile
from typing import Dict, Any, List
from config import validate_image_format, validate_document_format, validate_excel_format


def clear_session_key(key: str):
    """
    Supprime une clé de session si elle existe.
    
    Args:
        key: Clé de session à supprimer
    """
    if key in st.session_state:
        del st.session_state[key]

def update_session_from_form_data(form_data: Dict[str, Any], mappings: Dict[str, str]):
    """
    Met à jour plusieurs clés de session depuis les données de formulaire.
    
    Args:
        form_data: Données du formulaire
        mappings: Dict {session_key: form_key}
    """
    for session_key, form_key in mappings.items():
        if form_key in form_data:
            st.session_state[session_key] = form_data[form_key]

def handle_file_upload_with_legend(label: str, file_types: List[str], key: str) -> List[Dict]:
    """
    Gère l'upload de fichiers avec légendes + affichage des fichiers existants.
    
    Args:
        label: Label du widget d'upload
        file_types: Types de fichiers acceptés
        key: Clé unique pour le widget
        
    Returns:
        Liste des fichiers avec métadonnées (existants + nouveaux)
    """
    from utils.data import save_uploaded_file
    
    # Récupérer les fichiers existants depuis sample_data_generator
    # Déduire le type de fichier et la condition depuis la clé
    if '_fig' in key:
        condition_key = key.replace('_fig', '')
        file_type = 'figures'
    elif '_tab' in key:
        condition_key = key.replace('_tab', '')
        file_type = 'tableaux'
    else:
        condition_key = key
        file_type = 'figures'  # Par défaut
    
    existing_files_key = f"{condition_key}_existing_{file_type}"
    existing_files = st.session_state.get(existing_files_key, [])
    
    # AFFICHAGE DES FICHIERS EXISTANTS
    if existing_files:
        st.write(f"**📁 {label} existant(s) ({len(existing_files)}):**")
        
        files_to_remove = []
        for i, file_info in enumerate(existing_files):
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                # Nom et légende
                nom_fichier = file_info.get('nom_fichier', f'Fichier {i+1}')
                legende = file_info.get('legende', 'Sans légende')
                st.write(f"📄 **{nom_fichier}**")
                st.caption(f"💬 {legende}")
            
            with col2:
                # Taille du fichier
                taille = file_info.get('taille', 0)
                if taille > 0:
                    if taille > 1024*1024:
                        st.caption(f"📏 {taille/(1024*1024):.1f} MB")
                    elif taille > 1024:
                        st.caption(f"📏 {taille/1024:.1f} KB")
                    else:
                        st.caption(f"📏 {taille} B")
                else:
                    st.caption("📏 Taille inconnue")
            
            with col3:
                # Bouton de suppression
                if st.button("🗑️", key=f"remove_existing_{key}_{i}", help="Supprimer ce fichier"):
                    files_to_remove.append(i)
        
        # Traiter les suppressions
        if files_to_remove:
            for idx in sorted(files_to_remove, reverse=True):
                existing_files.pop(idx)
            st.session_state[existing_files_key] = existing_files
            st.rerun()
        
        # Séparateur visuel
        st.write("---")
    
    # WIDGET D'UPLOAD POUR NOUVEAUX FICHIERS
    if existing_files:
        st.write(f"**📤 Ajouter de nouveaux {label.lower()} :**")
    
    uploaded_files = st.file_uploader(
        label if not existing_files else f"Sélectionnez des fichiers", 
        type=file_types, 
        accept_multiple_files=True, 
        key=f"{key}_upload_new",
        help=f"Vous pouvez ajouter des fichiers aux {len(existing_files)} déjà présents" if existing_files else None
    )
    
    # TRAITEMENT DES NOUVEAUX FICHIERS
    new_files = []
    if uploaded_files:
        st.write(f"**🏷️ Légendes pour les nouveaux fichiers :**")
        
        for i, file in enumerate(uploaded_files):
            path = save_uploaded_file(file)
            
            # Interface pour la légende
            col1, col2 = st.columns([3, 1])
            with col1:
                legend = st.text_input(
                    f"Légende pour {file.name}", 
                    key=f"{key}_new_legend_{i}",
                    value=generate_auto_legend(file.name),
                    help="Description de ce fichier"
                )
            
            with col2:
                # Afficher la taille du nouveau fichier
                file_size = len(file.getvalue()) if hasattr(file, 'getvalue') else 0
                if file_size > 1024*1024:
                    st.caption(f"📏 {file_size/(1024*1024):.1f} MB")
                elif file_size > 1024:
                    st.caption(f"📏 {file_size/1024:.1f} KB")
                else:
                    st.caption(f"📏 {file_size} B")
            
            # Aperçu si c'est une image
            if path and os.path.exists(path) and _is_image_file(file.name):
                st.image(path, caption=f"Aperçu: {legend}", width=300)
            
            # Ajouter à la liste des nouveaux fichiers
            new_files.append({
                "chemin": path,
                "legende": legend,
                "nom_fichier": file.name,
                "taille": file_size
            })
    
    # COMBINAISON ET SAUVEGARDE
    all_files = existing_files + new_files
    
    # Mettre à jour le session state avec tous les fichiers
    if new_files:  # Seulement si on a ajouté de nouveaux fichiers
        st.session_state[existing_files_key] = all_files
        st.success(f"{len(new_files)} nouveau(x) fichier(s) ajouté(s). Total: {len(all_files)}")
    
    # AFFICHAGE DU RÉSUMÉ
    if all_files:
        st.info(f"📊 **Total: {len(all_files)} fichier(s)** ({len(existing_files)} existants + {len(new_files)} nouveaux)")
    
    return all_files

def _is_image_file(filename: str) -> bool:
    """Vérifie si un fichier est une image."""
    return validate_image_format(filename)

def create_dynamic_list_manager(session_key: str, item_renderer_func, 
                               default_items: List[Any] = None,
                               add_button_label: str = "Ajouter",
                               section_label: str = "éléments") -> List[Any]:
    """
    Crée un gestionnaire de liste dynamique avec fonctions add/remove.
    
    Args:
        session_key: Clé de session pour stocker la liste
        item_renderer_func: Fonction pour rendre chaque élément (index, existing_item) -> new_item
        default_items: Éléments par défaut
        add_button_label: Label du bouton d'ajout
        section_label: Label pour la section
        
    Returns:
        Liste des éléments
    """
    # Initialiser si nécessaire
    if session_key not in st.session_state:
        st.session_state[session_key] = default_items or []
    
    # En-tête avec bouton d'ajout
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**{section_label.title()}**")
    with col2:
        if st.button(f"➕ {add_button_label}", key=f"add_{session_key}"):
            st.session_state[session_key].append({})
            st.rerun()
    
    # Rendre chaque élément
    items = []
    for i in range(len(st.session_state[session_key])):
        with st.expander(f"{section_label.capitalize()} {i+1}", expanded=True):
            existing_item = st.session_state[session_key][i] if i < len(st.session_state[session_key]) else {}
            
            # Rendre l'élément avec la fonction fournie
            item = item_renderer_func(i, existing_item)
            
            # Bouton de suppression
            if st.button(f"🗑️ Supprimer {section_label} {i+1}", key=f"del_{session_key}_{i}"):
                st.session_state[session_key].pop(i)
                st.rerun()
            
            items.append(item)
    
    return items

def create_tabbed_condition_editor(condition_types: List[tuple], defaults: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crée un éditeur de conditions avec onglets.
    
    Args:
        condition_types: Liste de tuples (key, title, placeholder)
        defaults: Valeurs par défaut
        
    Returns:
        Dict des conditions par type
    """
    if not condition_types:
        return {}
    
    # Créer les onglets
    tab_labels = [title for _, title, _ in condition_types]
    tabs = st.tabs(tab_labels)
    
    conditions_data = {}
    
    for i, (condition_key, condition_title, placeholder) in enumerate(condition_types):
        with tabs[i]:
            conditions_data[condition_key] = create_single_condition_editor(
                condition_key, condition_title, placeholder, defaults
            )
    
    return conditions_data

def create_single_condition_editor(condition_key: str, title: str, 
                                 placeholder: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crée un éditeur pour une condition environnementale.
    
    Args:
        condition_key: Clé de la condition (ex: "houle")
        title: Titre affiché
        placeholder: Placeholder pour les champs
        defaults: Valeurs par défaut
        
    Returns:
        Dict avec les données de la condition
    """
    st.write(f"**{title}**")
    
    # Initialiser les conditions depuis session state
    session_key = f"{condition_key}_conditions"
    if session_key not in st.session_state:
        st.session_state[session_key] = get_existing_conditions(condition_key)
    
    # Interface de gestion des conditions
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Conditions observées")
    with col2:
        if st.button("➕ Ajouter", key=f"add_{condition_key}_condition"):
            st.session_state[session_key].append("")
            st.rerun()
    
    # Liste des conditions
    conditions_list = []
    for i in range(len(st.session_state[session_key])):
        current_value = (st.session_state[session_key][i] 
                        if i < len(st.session_state[session_key]) else "")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            condition_value = st.text_input(
                f"Condition {i+1}", 
                value=current_value,
                key=f"{condition_key}_cond_{i}",
                placeholder=placeholder
            )
            conditions_list.append(condition_value)
        
        with col2:
            if st.button("🗑️", key=f"del_{condition_key}_cond_{i}", help="Supprimer"):
                st.session_state[session_key].pop(i)
                st.rerun()
    
    # Mettre à jour la session
    st.session_state[session_key] = conditions_list
    
    # Valeurs retenues
    retenues_key = f"{condition_key}_retenues"
    valeurs_retenues = st.text_area(
        f"Valeurs de {condition_key} retenues pour l'étude",
        value=defaults.get(retenues_key, ""),
        key=f"{condition_key}_retenues_input",
        placeholder=f"Ex: {placeholder}"
    )
    
    # Upload de figures et tableaux
    figures = handle_file_upload_with_legend(
        f"Figures {condition_key}", 
        ["png", "jpg", "jpeg"], 
        f"{condition_key}_fig"
    )
    
    tableaux = handle_file_upload_with_legend(
        f"Tableaux {condition_key}", 
        ["xlsx", "csv", "pdf"], 
        f"{condition_key}_tab"
    )
    
    # Commentaire optionnel
    comment_key = f"{condition_key}_commentaire"
    commentaire = create_optional_comment_field(
        f"Ajouter un commentaire sur {condition_key}",
        f"Commentaire {condition_key}",
        defaults.get(comment_key, ""),
        key=f"{condition_key}_comment_check"
    )
    
    return {
        "conditions": [c for c in conditions_list if c.strip()],
        "valeurs_retenues": valeurs_retenues,
        "figures": figures,
        "tableaux": tableaux,
        "commentaire": commentaire
    }

def create_optional_comment_field(checkbox_label: str, textarea_label: str, 
                                default_value: str, key: str = None) -> str:
    """
    Crée un champ de commentaire optionnel avec checkbox.
    
    Args:
        checkbox_label: Label de la checkbox
        textarea_label: Label du textarea
        default_value: Valeur par défaut
        key: Clé unique (optionnel)
        
    Returns:
        Commentaire saisi ou chaîne vide
    """
    comment_exists = bool(default_value)
    checkbox_key = key if key else f"comment_check_{hash(textarea_label)}"
    
    if st.checkbox(f"➕ {checkbox_label}", value=comment_exists, key=checkbox_key):
        return st.text_area(textarea_label, value=default_value)
    
    return ""

def create_file_upload_with_preview(label: str, file_types: List[str], 
                                   key: str, current_path: str = "", 
                                   help_text: str = "") -> str:
    """
    Crée un upload de fichier avec aperçu.
    
    Args:
        label: Label du widget
        file_types: Types de fichiers acceptés
        key: Clé unique
        current_path: Chemin du fichier existant
        help_text: Texte d'aide
        
    Returns:
        Chemin du fichier (nouveau ou existant)
    """
    from utils.data import save_uploaded_file
    
    uploaded_file = st.file_uploader(
        label,
        type=file_types,
        help=help_text,
        key=key
    )
    
    # Utiliser le nouveau fichier ou garder l'existant
    file_path = save_uploaded_file(uploaded_file) if uploaded_file else current_path
    
    # Afficher l'aperçu si c'est une image
    if file_path and os.path.exists(file_path) and _is_image_file(file_path):
        st.image(file_path, caption=label, width=200)
    
    return file_path

def format_file_size_human(size_bytes: int) -> str:
    """Formate une taille de fichier pour affichage humain."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

# =============================================================================
# FONCTIONS SPÉCIALISÉES POUR LES TYPES DE FORMULAIRES
# =============================================================================

def validate_ship_dimensions(longueur: float, largeur: float, 
                           ship_name: str = "", show_warnings: bool = True) -> List[str]:
    """
    Valide les dimensions d'un navire.
    
    Args:
        longueur: Longueur du navire
        largeur: Largeur du navire
        ship_name: Nom du navire (pour les messages)
        show_warnings: Afficher les avertissements
        
    Returns:
        Liste des messages de validation
    """
    warnings = []
    
    if longueur > 0 and largeur > 0:
        ratio = longueur / largeur
        
        if ratio < 3:
            msg = f"{ship_name}: Ratio L/B = {ratio:.1f} (faible pour un navire)"
            warnings.append(msg)
            if show_warnings:
                st.warning(f"⚠️ {msg}")
        elif ratio > 15:
            msg = f"{ship_name}: Ratio L/B = {ratio:.1f} (très élancé)"
            warnings.append(msg)
            if show_warnings:
                st.warning(f"⚠️ {msg}")
        
        if longueur < largeur:
            msg = f"{ship_name}: Longueur < largeur (incohérent)"
            warnings.append(msg)
            if show_warnings:
                st.error(f"❌ {msg}")
    
    return warnings

# =============================================================================
# EXPORTS ET COMPATIBILITÉ
# =============================================================================
# Fonctions exportées pour maintenir la compatibilité
__all__ = [
    # Fonctions principales
    'get_form_defaults',
    'safe_get_value', 
    'get_existing_conditions',
    'sort_all_simulations',
    'handle_file_upload_with_legend',
    
    # Gestion de fichiers
    'categorize_file_type',
    'generate_auto_legend',
    'organize_zip_contents',
    'process_zip_file',
    
    # Interfaces UI
    'create_dynamic_list_manager',
    'create_tabbed_condition_editor',
    'create_optional_comment_field',
    'create_file_upload_with_preview',
    
    # Validation
    'validate_form_data',
    'validate_ship_dimensions',
    
    # Utilitaires
    'format_file_size_human',
    
    # Session state
    'initialize_session_key',
    'clear_session_key',
    'update_session_from_form_data'
] 
def get_form_defaults() -> Dict[str, Any]:
    """
    Récupère les valeurs par défaut depuis rapport_data pour tous les formulaires.
    
    Version sécurisée qui retourne toujours des valeurs par défaut même si 
    rapport_data est vide.
    
    Returns:
        Dict des valeurs par défaut pour tous les formulaires
    """
    rapport_data = st.session_state.get("rapport_data", {})
    
    # Extraire les sections principales
    metadonnees = rapport_data.get("metadonnees", {})
    introduction = rapport_data.get("introduction", {})
    donnees_entree = rapport_data.get("donnees_entree", {})
    bathymetrie = donnees_entree.get("bathymetrie", {})
    conditions_env = donnees_entree.get("conditions_environnementales", {})
    
    return {
        # Métadonnées
        "titre": metadonnees.get("titre", ""),
        "code_projet": metadonnees.get("code_projet", ""),
        "client": metadonnees.get("client", ""),
        "type": metadonnees.get("type", ""),
        "numero": metadonnees.get("numero", ""),
        "annee": metadonnees.get("annee", ""),
        "type_etude": metadonnees.get("type_etude", "initiale"),
        "main_image": metadonnees.get("main_image", ""),
        "client_logo": metadonnees.get("client_logo", ""),
        
        # Introduction
        "guidelines": introduction.get("guidelines", ""),
        "objectifs": introduction.get("objectifs", ""),
        
        # Plan de masse
        "plan_commentaire": donnees_entree.get("plan_de_masse", {}).get("commentaire", ""),
        
        # Balisage
        "balisage_commentaire": donnees_entree.get("balisage", {}).get("commentaire", ""),
        
        # Bathymétrie
        "source_bathy": bathymetrie.get("source", ""),
        "date_bathy": bathymetrie.get("date", ""),
        "notes_profondeur": bathymetrie.get("notes_profondeur", ""),
        "bathy_commentaire": bathymetrie.get("commentaire", ""),
        
        # Conditions environnementales
        "houle_retenues": conditions_env.get("houle", {}).get("valeurs_retenues", ""),
        "vent_retenues": conditions_env.get("vent", {}).get("valeurs_retenues", ""),
        "courant_retenues": conditions_env.get("courant", {}).get("valeurs_retenues", ""),
        "maree_retenues": conditions_env.get("maree", {}).get("valeurs_retenues", ""),
        "agitation_retenues": conditions_env.get("agitation", {}).get("valeurs_retenues", ""),

        # Source conditions
        "houle_source": conditions_env.get("houle", {}).get("source", ""),
        "vent_source": conditions_env.get("vent", {}).get("source", ""),
        "courant_source": conditions_env.get("courant", {}).get("source", ""),
        "maree_source": conditions_env.get("maree", {}).get("source", ""),
        "agitation_source": conditions_env.get("agitation", {}).get("source", ""),

        # Analyse conditions
        "houle_analyse": conditions_env.get("houle", {}).get("analyse", ""),
        "vent_analyse": conditions_env.get("vent", {}).get("analyse", ""),
        "courant_analyse": conditions_env.get("courant", {}).get("analyse", ""),
        "maree_analyse": conditions_env.get("maree", {}).get("analyse", ""),
        "agitation_analyse": conditions_env.get("agitation", {}).get("analyse", ""),
        
        # Commentaires conditions
        "houle_commentaire": conditions_env.get("houle", {}).get("commentaire", ""),
        "vent_commentaire": conditions_env.get("vent", {}).get("commentaire", ""),
        "courant_commentaire": conditions_env.get("courant", {}).get("commentaire", ""),
        "maree_commentaire": conditions_env.get("maree", {}).get("commentaire", ""),
        "agitation_commentaire": conditions_env.get("agitation", {}).get("commentaire", ""),
        
        # Navires
        "navires_description": rapport_data.get("donnees_navires", {}).get("navires", {}).get("description", ""),
        "navires_commentaire": rapport_data.get("donnees_navires", {}).get("navires", {}).get("commentaire", ""),
        "remorqueurs_commentaire": rapport_data.get("donnees_navires", {}).get("remorqueurs", {}).get("commentaire", ""),
        
        # Analyse
        "distances_trajectoires": rapport_data.get("analyse_synthese", {}).get("distances_trajectoires", ""),
        "analyse_commentaire": rapport_data.get("analyse_synthese", {}).get("commentaire", ""),
        
        # Conclusion
        "conclusion": rapport_data.get("conclusion", "")
    }

def safe_get_value(data_dict: Dict[str, Any], key: str, default: Any = "") -> Any:
    """
    Récupère une valeur en sécurité depuis un dictionnaire.
    
    Args:
        data_dict: Dictionnaire source
        key: Clé à récupérer
        default: Valeur par défaut
        
    Returns:
        Valeur récupérée ou valeur par défaut
    """
    if not isinstance(data_dict, dict):
        return default
    return data_dict.get(key, default)

def get_existing_conditions(condition_type: str) -> List[str]:
    """
    Récupère les conditions existantes pour un type donné.
    
    Args:
        condition_type: Type de condition (houle, vent, courant, maree, agitation)
        
    Returns:
        Liste des conditions existantes
    """
    rapport_data = st.session_state.get("rapport_data", {})
    conditions_env = rapport_data.get("donnees_entree", {}).get("conditions_environnementales", {})
    return conditions_env.get(condition_type, {}).get("conditions", [])

# =============================================================================
# FONCTIONS DE TRI ET ORGANISATION
# =============================================================================

def sort_all_simulations(simulations: List[Dict]) -> List[Dict]:
    """
    Trie toutes les simulations par numéro d'essai.
    
    Args:
        simulations: Liste des simulations à trier
        
    Returns:
        Liste triée des simulations
    """
    if not simulations:
        return []
    
    def extract_sort_key(numero_essai):
        """Extrait une clé de tri depuis le numéro d'essai."""
        import re
        
        if not numero_essai:
            return (9999, 0)
        
        # Extraire le numéro principal
        match = re.match(r'^(\d+)', str(numero_essai))
        if match:
            num = int(match.group(1))
            
            # Gérer bis, ter, etc.
            numero_str = str(numero_essai).lower()
            if 'bis' in numero_str:
                suffixe = 1
            elif 'ter' in numero_str:
                suffixe = 2
            elif 'quater' in numero_str:
                suffixe = 3
            else:
                suffixe = 0
            
            return (num, suffixe)
        else:
            try:
                return (int(float(str(numero_essai))), 0)
            except:
                return (9999, 0)
    
    return sorted(simulations, key=lambda s: extract_sort_key(s.get("numero_essai_original", "")))

# =============================================================================
# FONCTIONS DE GESTION DE FICHIERS
# =============================================================================

def categorize_file_type(filename: str) -> str:
    """
    Catégorise un fichier selon son extension.
    
    Args:
        filename: Nom du fichier
        
    Returns:
        Type de fichier ('image', 'pdf', 'tableau', 'document', 'autre')
    """
    if validate_image_format(filename):
        return "image"
    elif filename.lower().endswith('.pdf'):
        return "pdf"
    elif validate_excel_format(filename):
        return "tableau"
    elif validate_document_format(filename):
        return "document"
    else:
        return "autre"

def generate_auto_legend(filename: str) -> str:
    """
    Génère une légende automatique basée sur le nom du fichier.
    
    Args:
        filename: Nom du fichier
        
    Returns:
        Légende générée automatiquement
    """
    # Nettoyer le nom de fichier
    name_without_ext = os.path.splitext(filename)[0]
    
    # Remplacer les underscores et tirets par des espaces
    cleaned_name = name_without_ext.replace('_', ' ').replace('-', ' ')
    
    # Capitaliser la première lettre
    legend = cleaned_name.capitalize()
    
    # Quelques améliorations heuristiques
    if 'plan' in legend.lower():
        legend = f"Plan - {legend}"
    elif 'graph' in legend.lower() or 'chart' in legend.lower():
        legend = f"Graphique - {legend}"
    elif 'table' in legend.lower():
        legend = f"Tableau - {legend}"
    elif 'photo' in legend.lower() or 'image' in legend.lower():
        legend = f"Photo - {legend}"
    
    return legend

def organize_zip_contents(zip_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Organise le contenu du ZIP pour le rapport.
    
    Args:
        zip_info: Informations sur le contenu du ZIP
        
    Returns:
        Contenu organisé par type
    """
    contents = zip_info["contents"]
    
    organized = {
        "figures": [],
        "tableaux": [],
        "documents": [],
        "autres": []
    }
    
    # Organiser par type avec métadonnées
    for file_info in contents:
        file_type = categorize_file_type(file_info["name"])
        
        organized_item = {
            "nom": file_info["name"],
            "chemin": file_info["path"],
            "taille": file_info["size"],
            "legende": generate_auto_legend(file_info["name"])
        }
        
        if file_type == "image":
            organized["figures"].append(organized_item)
        elif file_type == "tableau":
            organized["tableaux"].append(organized_item)
        elif file_type == "document":
            organized["documents"].append(organized_item)
        else:
            organized["autres"].append(organized_item)
    
    return organized

def process_zip_file(zip_file) -> Dict[str, Any]:
    """
    Traite un fichier ZIP uploadé.
    
    Args:
        zip_file: Fichier ZIP uploadé via Streamlit
        
    Returns:
        Dict avec les informations sur le traitement
    """
    try:
        from utils.data import save_uploaded_file
        from config import Config
        
        # Sauvegarder le ZIP temporairement
        zip_path = save_uploaded_file(zip_file)
        
        # Analyser le contenu
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            # Filtrer les fichiers valides
            valid_files = []
            for file_name in file_list:
                if not file_name.startswith('__MACOSX/') and not file_name.endswith('/'):
                    file_ext = os.path.splitext(file_name)[1].lower()
                    
                    valid_extensions = []
                    valid_extensions.extend(Config.SUPPORTED_FORMATS[Config.FileType.IMAGE]["extensions"])
                    valid_extensions.extend(Config.SUPPORTED_FORMATS[Config.FileType.DOCUMENT]["extensions"])
                    valid_extensions.extend(Config.SUPPORTED_FORMATS[Config.FileType.SPREADSHEET]["extensions"])

                    if file_ext.replace('.', '') in valid_extensions:
                        valid_files.append(file_name)
            
            # Extraire les fichiers valides
            extract_dir = os.path.join(Config.UPLOAD_DIR, f"extracted_{zip_file.name.split('.')[0]}")
            os.makedirs(extract_dir, exist_ok=True)
            
            extracted_files = []
            for file_name in valid_files:
                try:
                    zip_ref.extract(file_name, extract_dir)
                    extracted_files.append({
                        "name": file_name,
                        "path": os.path.join(extract_dir, file_name),
                        "size": zip_ref.getinfo(file_name).file_size,
                        "type": categorize_file_type(file_name)
                    })
                except Exception as e:
                    st.warning(f"Erreur extraction {file_name}: {e}")
        
        return {
            "valid": True,
            "zip_path": zip_path,
            "extract_dir": extract_dir,
            "contents": extracted_files,
            "total_files": len(extracted_files),
            "original_files": len(file_list)
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }

# =============================================================================
# FONCTIONS DE VALIDATION
# =============================================================================

def validate_form_data(data: Dict[str, Any], required_fields: List[str] = None) -> Dict[str, List[str]]:
    """
    Valide les données d'un formulaire.
    
    Args:
        data: Données à valider
        required_fields: Liste des champs requis
        
    Returns:
        Dict avec 'errors' et 'warnings'
    """
    result = {
        "errors": [],
        "warnings": []
    }
    
    if not data:
        result["errors"].append("Aucune donnée fournie")
        return result
    
    # Validation des champs requis
    if required_fields:
        for field in required_fields:
            if field not in data or not _is_filled(data[field]):
                result["errors"].append(f"Champ requis manquant : {field}")
    
    return result

def _is_filled(value: Any) -> bool:
    """
    Vérifie si une valeur n'est pas vide.
    
    Args:
        value: Valeur à tester
        
    Returns:
        True si la valeur n'est pas vide
    """
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return bool(value)

# =============================================================================
# FONCTIONS DE SESSION STATE
# =============================================================================

def initialize_session_key(key: str, default_value: Any, source_path: str = None):
    """
    Initialise une clé de session avec une valeur par défaut ou depuis rapport_data.
    
    Args:
        key: Clé de session
        default_value: Valeur par défaut
        source_path: Chemin dans rapport_data (ex: "metadonnees.historique_revisions")
    """
    if key not in st.session_state:
        if source_path:
            # Extraire depuis rapport_data
            rapport_data = st.session_state.get("rapport_data", {})
            value = rapport_data
            
            # Naviguer dans le chemin
            for path_part in source_path.split('.'):
                value = value.get(path_part, {}) if isinstance(value, dict) else {}
            
            # Si on a trouvé quelque chose, l'utiliser, sinon utiliser la valeur par défaut
            st.session_state[key] = value if value else default_value
        else:
            st.session_state[key] = default_value
