import streamlit as st
import json
import os
import pandas as pd
import random
from datetime import datetime

FORM_STRUCTURE = {
    "📁 Métadonnées": {
        "session_keys": ["titre", "code_projet", "client"],
        "required_fields": ["titre", "code_projet", "client", "type", "numero", "annee"],
        "path": "metadonnees",
        "icon": "📁",
        "description": "Informations générales du projet"
    },
    "✍️ Introduction": {
        "session_keys": ["guidelines", "objectifs"],
        "required_fields": ["guidelines", "objectifs"],
        "path": "introduction",
        "icon": "✍️",
        "description": "Contexte et objectifs de l'étude"
    },
    "📊 Données d'entrée": {
        "session_keys": ["plan_de_masse", "balisage", "bathymetrie", "conditions_environnementales"],
        "required_fields": ["source", "date", "notes_profondeur"],
        "path": "donnees_entree",
        "icon": "📊",
        "description": "Les données d'entrée de l'étude de manœuvrabilité",
        "sub_sections": {
            "📍 Plan de masse": {"path": "donnees_entree.plan_de_masse"},
            "🚩 Balisage": {"path": "donnees_entree.balisage"},
            "🗺️ Bathymétrie": {"path": "donnees_entree.bathymetrie"},
            "🌊 Conditions env.": {"path": "donnees_entree.conditions_environnementales"}
        }
    },
    "🚢 Navires": {
        "session_keys": ["navires", "remorqueurs"],
        "required_fields": ["navires"],
        "path": "donnees_navires",
        "icon": "🚢",
        "description": "Données des navires projets et remorqueurs",
        "sub_sections": {
            "⚓ Navires": {"path": "donnees_navires.navires"},
            "🚤 Remorqueurs": {"path": "donnees_navires.remorqueurs"}
        }
    },
    "🌀 Simulations": {
        "session_keys": ["simulations_data"],
        "required_fields": ["simulations"],
        "path": "simulations",
        "icon": "🌀",
        "description": "Données de simulation et résultats"
    },
    "📈 Analyse": {
        "session_keys": ["recapitulatif_analyse"],
        "required_fields": ["recapitulatif_text"],
        "path": "analyse_synthese",
        "icon": "📈",
        "description": "Analyse des résultats et synthèse"
    },
    "📝 Conclusion": {
        "session_keys": ["conclusion"],
        "required_fields": ["conclusion"],
        "path": "conclusion",
        "icon": "📝",
        "description": "Conclusion générale du rapport"
    },
    "📎 Annexes": {
        "session_keys": ["annexes"],
        "required_fields": [],
        "path": "annexes",
        "icon": "📎",
        "description": "Figures et documents complémentaires"
    }
}

def get_section_status(section_name: str, section_config: dict) -> dict:
    """
    Évalue le statut de remplissage d'une section
    
    Returns:
        dict: {
            'status': 'complete'|'partial'|'empty',
            'icon': '✅'|'⚠️'|'❌',
            'filled_count': int,
            'total_count': int,
            'details': str
        }
    """
    rapport_data = st.session_state.get("rapport_data", {})
    
    # Récupérer les données de la section
    section_path = section_config["path"]
    section_data = rapport_data
    
    # Naviguer dans le chemin
    for part in section_path.split('.'):
        section_data = section_data.get(part, {}) if isinstance(section_data, dict) else {}
    
    # Compter les champs remplis
    filled_count = 0
    total_count = 0
    
    if section_name == "📊 Données d'entrée":
        # Logique spéciale pour les données d'entrée
        total_count = 4  # plan_masse, balisage, bathymetrie, conditions_env
        
        if section_data.get("plan_de_masse", {}).get("phases"):
            filled_count += 1
        if section_data.get("balisage", {}).get("actif"):
            filled_count += 1
        if section_data.get("bathymetrie", {}).get("source"):
            filled_count += 1
        if section_data.get("conditions_environnementales"):
            conditions = section_data["conditions_environnementales"]
            if any(conditions.get(cond, {}).get("valeurs_retenues") for cond in 
                   ["houle", "vent", "courant", "maree", "agitation"]):
                filled_count += 1
                
    elif section_name == "🚢 Navires":
        # Logique spéciale pour les navires
        total_count = 2  # navires + remorqueurs
        
        if section_data.get("navires", {}).get("navires"):
            filled_count += 1
        if section_data.get("remorqueurs", {}).get("remorqueurs"):
            filled_count += 1
            
    elif section_name == "🌀 Simulations":
        # Vérifier les simulations
        simulations = st.session_state.get("simulations_data", [])
        total_count = 1
        if simulations:
            filled_count = 1
    
    elif section_name == "📎 Annexes":
        # Spécifique annexes : considérer rempli si un type valide est présent
        total_count = 1
        annexes_type = section_data.get("type") if isinstance(section_data, dict) else ""
        if annexes_type and annexes_type.lower() != "none":
            filled_count = 1
            
    else:
        # Logique générale pour les autres sections
        required_fields = section_config.get("required_fields", [])
        total_count = len(required_fields) if required_fields else 1
        
        if isinstance(section_data, dict):
            if required_fields:
                for field in required_fields:
                    if section_data.get(field):
                        filled_count += 1
            else:
                # Pas de champs requis explicites : considérer rempli si la section existe et n'est pas vide
                filled_count = 1 if section_data else 0
        elif isinstance(section_data, str) and section_data.strip():
            filled_count = 1
        elif isinstance(section_data, list) and section_data:
            filled_count = 1
        elif section_data:  # Autres types non vides
            filled_count = 1
    
    # Déterminer le statut
    if filled_count == 0:
        status = 'empty'
        icon = '❌'
        details = "Non rempli"
    elif filled_count == total_count:
        status = 'complete'
        icon = '✅'
        details = "Complet"
    else:
        status = 'partial'
        icon = '⚠️'
        details = f"{filled_count}/{total_count}"
    
    return {
        'status': status,
        'icon': icon,
        'filled_count': filled_count,
        'total_count': total_count,
        'details': details
    }

def render_navigation_tree():
    """Affiche l'arborescence de navigation dans la sidebar"""
    st.sidebar.markdown("### 📋 Progression du rapport")
    
    total_sections = len(FORM_STRUCTURE)
    completed_sections = 0
    
    for section_name, section_config in FORM_STRUCTURE.items():
        status_info = get_section_status(section_name, section_config)
        
        if status_info['status'] == 'complete':
            completed_sections += 1
        
        # Affichage principal de la section
        with st.sidebar.expander(
            f"{status_info['icon']} {section_name} {status_info['details']}", 
            expanded=False
        ):
            st.write(f"**{section_config['description']}**")
            
            # Affichage des sous-sections si elles existent
            if "sub_sections" in section_config:
                for sub_name, sub_config in section_config["sub_sections"].items():
                    sub_status = get_subsection_status(sub_config["path"])
                    
                    # Affichage avec détails si disponibles
                    if sub_status.get('details'):
                        st.write(f"{sub_status['icon']} {sub_name} ({sub_status['details']})")
                    else:
                        st.write(f"{sub_status['icon']} {sub_name}")
    
    # Barre de progression globale
    progress = completed_sections / total_sections
    st.sidebar.progress(progress, text=f"Progression: {completed_sections}/{total_sections} sections")
    
    # Conseils selon la progression
    if progress == 0:
        st.sidebar.info("💡 Commencez par charger les données d'exemple")
    elif progress < 0.5:
        st.sidebar.info("💡 Continuez le remplissage des sections principales")
    elif progress < 1:
        st.sidebar.success("🎯 Presque terminé !")
    else:
        st.sidebar.success("🎉 Rapport complet ! Prêt pour l'export")

def get_subsection_status(path: str) -> dict:
    """Évalue le statut d'une sous-section avec plus de précision"""
    rapport_data = st.session_state.get("rapport_data", {})
    data = rapport_data
    
    # Naviguer dans le chemin
    for part in path.split('.'):
        data = data.get(part, {}) if isinstance(data, dict) else {}
    
    if "conditions_environnementales" in path:
        # Pour les conditions environnementales, compter les conditions remplies
        if not data or not isinstance(data, dict):
            return {'icon': '❌', 'status': 'empty'}
        
        # Compter combien de conditions (houle, vent, etc.) sont remplies
        conditions_remplies = 0
        conditions_obligatoires = ["houle", "vent", "courant", "maree"]  # 4 conditions principales obligatoires
        conditions_optionnelles = ["agitation"]  # Optionnelle selon le projet
        
        # Vérifier les conditions obligatoires
        for cond in conditions_obligatoires:
            cond_data = data.get(cond, {})
            if (cond_data.get("valeurs_retenues") or 
                cond_data.get("source") or 
                cond_data.get("conditions") or
                cond_data.get("analyse")):
                conditions_remplies += 1
        
        # Compter aussi les optionnelles remplies pour l'affichage
        conditions_optionnelles_remplies = 0
        for cond in conditions_optionnelles:
            cond_data = data.get(cond, {})
            if (cond_data.get("valeurs_retenues") or 
                cond_data.get("source") or 
                cond_data.get("conditions") or
                cond_data.get("analyse")):
                conditions_optionnelles_remplies += 1
        
        total_remplies = conditions_remplies + conditions_optionnelles_remplies
        total_conditions = len(conditions_obligatoires) + len(conditions_optionnelles)
        
        if conditions_remplies == 0:
            return {'icon': '❌', 'status': 'empty'}
        elif conditions_remplies == len(conditions_obligatoires):
            # Toutes les obligatoires + éventuellement des optionnelles
            if conditions_optionnelles_remplies > 0:
                return {'icon': '✅', 'status': 'complete', 'details': f'{total_remplies}/{total_conditions}'}
            else:
                return {'icon': '✅', 'status': 'complete', 'details': f'{conditions_remplies}/{len(conditions_obligatoires)} req.'}
        else:
            return {'icon': '⚠️', 'status': 'partial', 'details': f'{conditions_remplies}/{len(conditions_obligatoires)} req.'}
    
    if not data:
        return {'icon': '❌', 'status': 'empty'}
    elif isinstance(data, dict):
        # Pour un dict, vérifier s'il y a des valeurs non vides
        non_empty_values = sum(1 for v in data.values() if v)
        total_values = len(data)
        
        if non_empty_values == 0:
            return {'icon': '❌', 'status': 'empty'}
        elif non_empty_values == total_values:
            return {'icon': '✅', 'status': 'complete'}
        else:
            return {'icon': '⚠️', 'status': 'partial', 'details': f'{non_empty_values}/{total_values}'}
    elif isinstance(data, list) and data:
        return {'icon': '✅', 'status': 'filled'}
    elif isinstance(data, str) and data.strip():
        return {'icon': '✅', 'status': 'filled'}
    else:
        return {'icon': '❌', 'status': 'empty'}

def load_excel_simulations():
    """Charge les simulations depuis le fichier Excel et les convertit au format de l'application"""
    
    try:
        # Charger le fichier Excel
        df = pd.read_excel('uploads/newTable.xlsx', sheet_name='Sheet1')
        
        # Types de navires disponibles (comme dans l'ancienne version)
        navires_types = [
            {
                "nom": "Porte-conteneurs Type ULCV",
                "type": "Ultra Large Container Vessel",
                "longueur": 400.0,
                "largeur": 58.6,
                "deplacement_charge": 220000.0,
                "deplacement_lest": 180000.0
            },
            {
                "nom": "Porte-conteneurs Type Large", 
                "type": "Large Container Vessel",
                "longueur": 350.0,
                "largeur": 48.2,
                "deplacement_charge": 165000.0,
                "deplacement_lest": 135000.0
            },
            {
                "nom": "Porte-conteneurs Standard",
                "type": "Container Vessel", 
                "longueur": 300.0,
                "largeur": 42.8,
                "deplacement_charge": 95000.0,
                "deplacement_lest": 75000.0
            }
        ]
        
        simulations = []
        
        for index, row in df.iterrows():
            # Sélection aléatoire d'un navire
            navire_choisi = random.choice(navires_types)
            
            # État de charge aléatoire (70% chargé, 30% sur lest)
            est_charge = random.random() < 0.7
            etat_chargement = "Chargé" if est_charge else "Sur lest"
            
            # Calcul des tirants d'eau selon l'état de charge
            if est_charge:
                if navire_choisi["nom"] == "Porte-conteneurs Type ULCV":
                    tirant_eau_av, tirant_eau_ar = 16.0, 16.5
                elif navire_choisi["nom"] == "Porte-conteneurs Type Large":
                    tirant_eau_av, tirant_eau_ar = 14.5, 15.0
                else:  # Standard
                    tirant_eau_av, tirant_eau_ar = 12.0, 12.5
                deplacement = navire_choisi["deplacement_charge"]
            else:
                # Sur lest - tirants d'eau réduits
                if navire_choisi["nom"] == "Porte-conteneurs Type ULCV":
                    tirant_eau_av, tirant_eau_ar = 8.5, 9.0
                elif navire_choisi["nom"] == "Porte-conteneurs Type Large":
                    tirant_eau_av, tirant_eau_ar = 7.5, 8.0
                else:  # Standard
                    tirant_eau_av, tirant_eau_ar = 6.5, 7.0
                deplacement = navire_choisi["deplacement_lest"]
            
            # Conversion des données Excel vers le format application
            test_no = str(row.get('Test N°', '')).strip()
            
            # Déterminer le résultat basé sur les commentaires et le numéro de test
            commentaire = str(row.get('Comments', '')).lower()
            is_near_miss = 'near miss' in test_no.lower() or 'near miss' in commentaire
            is_emergency = any(word in commentaire for word in ['emergency', 'unavailable', 'failure', 'abort'])
            
            # Logique de détermination du résultat
            if is_near_miss:
                resultat = "Réussite conditionnelle"
            elif is_emergency or 'limit' in commentaire or 'excessive' in commentaire:
                resultat = "Échec"
            else:
                resultat = "Réussite"
            
            # Formatage des conditions environnementales
            wind = row.get('Wind', '')
            wave = row.get('Wave', '') 
            current = row.get('Current', '')
            tide = row.get('Tide', '')
            
            # Conversion du nombre de remorqueurs
            tugs_text = str(row.get('Tugs', '')).lower()
            if '5' in tugs_text:
                nb_remorqueurs = "5 Remorqueurs"
            elif '4' in tugs_text:
                nb_remorqueurs = "4 Remorqueurs" 
            elif '3' in tugs_text:
                nb_remorqueurs = "3 Remorqueurs"
            else:
                nb_remorqueurs = "4 Remorqueurs"  # Défaut
            
            # Conversion manœuvre
            manoeuvre_excel = str(row.get('Maneuver', '')).lower()
            if 'arrival' in manoeuvre_excel:
                manoeuvre = "Accostage"
            elif 'departure' in manoeuvre_excel:
                manoeuvre = "Appareillage"
            else:
                manoeuvre = "Accostage"
            
            # Conversion bord
            side = str(row.get('Side', '')).lower()
            if 'port' in side:
                bord = "Bâbord"
            elif 'starboard' in side:
                bord = "Tribord" 
            else:
                bord = "Tribord"  # Défaut
            
            # Création de la simulation
            simulation = {
                "id": index + 1,
                "numero_essai_original": test_no,
                "navire": navire_choisi["nom"],
                "type_navire": navire_choisi["type"],
                "longueur": navire_choisi["longueur"],
                "largeur": navire_choisi["largeur"],
                "tirant_eau_av": tirant_eau_av,
                "tirant_eau_ar": tirant_eau_ar,
                "deplacement": deplacement,
                "etat_chargement": etat_chargement,
                "manoeuvre": f"{manoeuvre} {row.get('Berth', 'P2')} {bord.lower()}",
                "conditions_env": {
                    "vent": wind,
                    "houle": wave,
                    "courant": current,
                    "maree": tide
                },
                "remorqueurs": nb_remorqueurs,
                "poste": row.get('Berth', 'P2'),
                "bord": bord,
                "entree": row.get('Entrance', 'TM3'),
                "pilote": row.get('Pilote', ''),
                "resultat": resultat,
                "commentaire_pilote": row.get('Comments', ''),
                "images": [],
                "is_emergency_scenario": is_emergency,
                "is_near_miss": is_near_miss,
                "condition": row.get('Condition', ''),
                "conditions_detaillees": {
                    "vent_detaille": wind,
                    "houle_detaillee": wave,
                    "courant_detaille": current,
                    "maree_detaillee": tide
                }
            }
            
            simulations.append(simulation)
        
        return simulations
        
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier Excel: {e}")
        return generate_fallback_simulations()

def generate_fallback_simulations():
    """Génère des simulations de secours en cas d'erreur avec Excel"""
    return [
        {
            "id": 1,
            "numero_essai_original": "1",
            "navire": "Porte-conteneurs Type ULCV",
            "etat_chargement": "Chargé",
            "manoeuvre": "Accostage P2 tribord",
            "conditions_env": {
                "vent": "NE 25 kts",
                "houle": "NE 2.5m T=12s",
                "courant": "3 kts 60°/N",
                "maree": "0.6m"
            },
            "remorqueurs": "4 Remorqueurs",
            "poste": "P2",
            "bord": "Tribord",
            "entree": "TM3",
            "pilote": "RAF/Berjal",
            "resultat": "Réussite",
            "commentaire_pilote": "Manœuvre réussie avec assistance de 4 remorqueurs",
            "images": [],
            "is_emergency_scenario": False,
            "condition": "E1"
        }
    ]

def create_complete_sample_data():
    """Crée des données de test complètes et réalistes avec simulations Excel"""
    
    sample_data = {
        "metadonnees": {
            "titre": "Extension Terminal à Conteneurs Port de Tanger Med",
            "code_projet": "TMD-2024-MAN-001", 
            "client": "Autorité Portuaire de Tanger Med",
            "type": "Rapport de manœuvrabilité",
            "numero": "RM-TMD-001",
            "annee": "2024",
            "type_etude": "initiale",
            "main_image": "uploads/vue_port.png",
            "client_logo": "uploads/cid.jpg",
            "historique_revisions": [
                {
                    "version": "A",
                    "date": "2024-01-15",
                    "description": "Version initiale pour revue client",
                    "auteur": "J. Benali",
                    "verificateur": "M. Alaoui", 
                    "approbateur": "Dr. K. Mansouri"
                },
                {
                    "version": "B",
                    "date": "2024-02-10",
                    "description": "Intégration des commentaires client",
                    "auteur": "J. Benali",
                    "verificateur": "M. Alaoui",
                    "approbateur": "Dr. K. Mansouri"
                }
            ]
        },
        
        "introduction": {
            "guidelines": "L'Autorité Portuaire de Tanger Med a confié à notre équipe l'élaboration d'une étude de manœuvrabilité portuaire dans le cadre de l'extension du terminal à conteneurs, situé dans la zone franche de Tanger Med. Ce projet vise à évaluer les capacités de manœuvre du nouveau quai Q4 destiné à accueillir des porte-conteneurs de nouvelle génération jusqu'à 24 000 EVP, dans un contexte de croissance prévue du trafic conteneurisé et d'optimisation des flux maritimes trans-méditerranéens.",
            "objectifs": "• Évaluer la faisabilité des manœuvres d'accostage et d'appareillage pour les porte-conteneurs de 300 à 400m\n• Analyser les interactions hydrodynamiques entre les navires et le nouveau quai Q4\n• Identifier les conditions météo-océaniques critiques et les zones à risque\n• Valider la compatibilité des dimensions du chenal d'accès avec les navires cibles\n• Proposer des recommandations pour l'optimisation des procédures de pilotage"
        },
        
        "donnees_entree": {
            "plan_de_masse": {
                "phases": [
                    {
                        "nom": "Phase 1 - Configuration actuelle",
                        "description": "Quais Q1, Q2, Q3 existants avec chenal principal 16m de tirant d'eau",
                        "figures": [
                            {
                                "chemin":"uploads/Plan de masse.png",
                                "legende":"Plan - Plan de masse",
                                "nom_fichier":"Plan de masse",
                                "taille":484146
                            }
                        ]
                    },
                    {
                        "nom": "Phase 2 - Extension Q4", 
                        "description": "Nouveau quai Q4 de 450m avec tirant d'eau 18m et aire d'évitage élargie",
                        "figures": []
                    }
                ],
                "commentaire": "L'extension Q4 nécessite un élargissement du chenal d'accès de 250m à 300m",
                "figures": [
                    {
                        "chemin": "uploads/Plan de masse.png",
                        "legende": "Plan de masse global",
                        "nom_fichier": "Plan_de_masse.png",
                        "taille": 484146
                    }
                ]
            },
            
            "balisage": {
                "actif": True,
                "figures": [
                    {
                        "chemin": "uploads/PlanBalisage.png",
                        "legende": "Plan - Planbalisage",
                        "nom_fichier": "Plan de balisage",
                        "taille": 112221
                    }
                ],
                "commentaire": "Balisage conforme aux recommandations IALA avec feux LED haute intensité"
            },
            
            "bathymetrie": {
                "source": "SHOM - Service Hydrographique et Océanographique de la Marine",
                "date": "Octobre 2023",
                "notes_profondeur": "Profondeurs suffisantes dans le chenal principal (16-18m). Fond stable composé de sable fin et vase. Zone d'évitage approfondie à 18m pour accueillir les plus gros navires.",
                "figures": [
                    {
                        "chemin": "uploads/vue_port.png",
                        "legende": "Carte bathymétrique - Zone portuaire et chenaux",
                        "nom_fichier": "vue_port.png",
                        "taille": 345678
                    }
                ],
                "commentaire": "Bathymétrie récente validée par levés multibeam haute résolution"
            },
            
            "conditions_environnementales": {
                "houle": {
                    "source": "Données houlographe SHOM station X, Modèle WAVEWATCH III, Mesures in-situ 2020-2024",
                    "conditions": [
                        "Houle dominante du NW, hauteur significative 1-3m",
                        "Période pic 8-12 secondes", 
                        "Houle secondaire du SW en hiver"
                    ],
                    "valeurs_retenues": "Houle critique: Hs=3m, Tp=10s, direction NW",
                    "analyse": "Analyse de la houle dominante du NW, périodes caractéristiques 8-12s, hauteurs significatives 1-3m selon les saisons. Houle secondaire du SW principalement en période hivernale.",
                    "figures": [
                        {
                            "chemin": "uploads/rose_houle.png",
                            "legende": "Rose de houle - Directions et hauteurs dominantes",
                            "nom_fichier": "rose_houle.png",
                            "taille": 156789
                        }
                    ],
                    "tableaux": [
                        {
                            "chemin": "uploads/donnees_houle.xlsx",
                            "legende": "Données statistiques houle par secteur",
                            "nom_fichier": "donnees_houle.xlsx", 
                            "taille": 45678
                        }
                    ],
                    "commentaire": "Données issues de 5 ans de mesures houlographe au large"
                },
                
                "vent": {
                    "source": "Station météorologique Tanger Med, Données Météo-France, Rose des vents 10 ans",
                    "conditions": [
                        "Vent dominant d'Est (Chergui) 15-25 kts",
                        "Vent d'Ouest en hiver 20-35 kts",
                        "Rafales exceptionnelles jusqu'à 45 kts"
                    ],
                    "valeurs_retenues": "Vent critique: 30 kts secteur Ouest avec rafales 40 kts",
                    "analyse": "Rose des vents montrant une dominante Est (Chergui) en été, vents d'Ouest en hiver, vitesses moyennes et extrêmes. Analyse des corrélations saisonnières.",
                    "figures": [
                        {
                            "chemin": "uploads/rose_vents.jpg",
                            "legende": "Rose des vents - Station Tanger Med 2014-2024",
                            "nom_fichier": "rose_vents.jpg",
                            "taille": 198765
                        }
                    ],
                    "tableaux": [
                    ],
                    "commentaire": "Rose des vents basée sur 10 ans de données météo-marine"
                },
                
                "courant": {
                    "source": "Mesures ADCP campagne 2023, Modèle hydrodynamique TELEMAC, Observations terrain",
                    "conditions": [
                        "Courant de marée faible 0.5-1 kt",
                        "Courant de dérive généralement < 0.3 kt",
                        "Courant renforcé en cas de vent fort"
                    ],
                    "valeurs_retenues": "Courant maximal: 1.2 kt direction variable selon marée",
                    "analyse": "Courants de marée faibles < 1 kt, courants de dérive liés au vent, variations saisonnières et influence de la bathymétrie sur les écoulements locaux.",
                    "figures": [],
                    "tableaux": [],
                    "commentaire": "Courants mesurés par ADCP sur 1 an complet"
                },
                
                "maree": {
                    "source": "SHOM - Annuaire des marées, Données marégraphiques Port Tanger Med, Prédictions harmoniques",
                    "conditions": [
                        "Marée semi-diurne, marnage 1.8m (VE) à 0.4m (ME)",
                        "Pleine mer: +1.1m à +2.4m/CM",
                        "Basse mer: -0.7m à +0.7m/CM"
                    ],
                    "valeurs_retenues": "Conditions extrêmes: PM +2.4m, BM -0.7m (coeff 95-120)",
                    "analyse": "Marnage semi-diurne 1.8m en VE à 0.4m en ME, hauteurs d'eau exploitables, coefficients critiques et optimisation des créneaux de manœuvre.",
                    "figures": [
                        {
                            "chemin": "uploads/courbe_maree.png",
                            "legende": "Courbes de marée type - VE et ME",
                            "nom_fichier": "courbe_maree.png",
                            "taille": 145678
                        }
                    ],
                    "tableaux": [],
                    "commentaire": "Référentiel Cote Marine (CM) Tanger Med"
                },
                
                "agitation": {
                    "source": "Modélisation numérique MIKE21, Mesures agitomètre bassin, Campagne de mesures 2023",
                    "conditions": [
                        "Agitation résiduelle faible dans le bassin",
                        "Critère d'exploitation < 0.5m",
                        "Agitation renforcée par houle diffractée"
                    ],
                    "valeurs_retenues": "Agitation maximale admissible: 0.5m au poste d'amarrage",
                    "analyse": "Agitation résiduelle faible dans le bassin protégé, critères d'exploitation < 0.5m, zones sensibles identifiées selon l'orientation des quais.",
                    "figures": [
                        {
                            "chemin": "uploads/carte_agitation.png",
                            "legende": "Carte d'agitation dans le bassin portuaire",
                            "nom_fichier": "carte_agitation.png",
                            "taille": 189456
                        }
                    ],
                    "tableaux": [],
                    "commentaire": "Modélisation numérique validée par mesures in-situ"
                }
            }
        },
        
        "donnees_navires": {
            "navires": {
                "navires": [
                    {
                        "nom": "Porte-conteneurs Type ULCV",
                        "type": "Ultra Large Container Vessel",
                        "etat_de_charge": "Chargé",
                        "longueur": 400.0,
                        "largeur": 58.6,
                        "tirant_eau_av": 16.0,
                        "tirant_eau_ar": 16.5,
                        "deplacement": 220000.0,
                        "propulsion": "Moteur diesel basse vitesse + hélice à pas variable",
                        "puissance_machine": "75 000 kW",
                        "remarques": "Navire représentatif de la nouvelle génération 24 000 EVP",
                        "figure": "uploads/navire1.png",
                        "est_actif": True
                    },
                    {
                        "nom": "Porte-conteneurs Type Large",
                        "type": "Large Container Vessel", 
                        "etat_de_charge": "Chargé",
                        "longueur": 350.0,
                        "largeur": 48.2,
                        "tirant_eau_av": 14.5,
                        "tirant_eau_ar": 15.0,
                        "deplacement": 165000.0,
                        "propulsion": "Moteur diesel + hélice à pas variable",
                        "puissance_machine": "55 000 kW",
                        "remarques": "Navire standard 18 000 EVP fréquent sur la ligne",
                        "figure": "uploads/navire2.png",
                        "est_actif": True
                    },
                    {
                        "nom": "Porte-conteneurs Standard",
                        "type": "Container Vessel",
                        "etat_de_charge": "sur lest",
                        "longueur": 300.0,
                        "largeur": 42.8,
                        "tirant_eau_av": 8.5,
                        "tirant_eau_ar": 9.0,
                        "deplacement": 95000.0,
                        "propulsion": "Moteur diesel + hélice fixe",
                        "puissance_machine": "35 000 kW",
                        "remarques": "Configuration lège pour étude des cas défavorables",
                        "figure": "uploads/navire3.png",
                        "est_actif": False
                    }
                ],
                "description": "Trois types de navires représentatifs du trafic attendu sur le terminal Q4",
                "commentaire": "Focus sur les porte-conteneurs ULCV qui représentent le défi principal"
            },
            
            "remorqueurs": {
                "remorqueurs": [
                    {
                        "nom": "Remorqueur ASD 70T",
                        "type": "Azimuth Stern Drive",
                        "longueur": 32.0,
                        "lbp": 28.5,
                        "largeur": 12.8,
                        "tirant_eau": 5.2,
                        "vitesse": 13.5,
                        "traction": 70.0,
                        "remarques": "Remorqueur principal haute performance",
                        "figure": "uploads/remorqueur1.png"
                    },
                    {
                        "nom": "Remorqueur ASD 50T", 
                        "type": "Azimuth Stern Drive",
                        "longueur": 28.0,
                        "lbp": 25.0,
                        "largeur": 11.0,
                        "tirant_eau": 4.8,
                        "vitesse": 12.0,
                        "traction": 50.0,
                        "remarques": "Remorqueur standard pour assistance",
                        "figure": "uploads/remorqueur2.png"
                    },
                    {
                        "nom": "Remorqueur Conventionnel 40T",
                        "type": "Tracteur conventionnel",
                        "longueur": 26.0,
                        "lbp": 23.0,
                        "largeur": 10.5,
                        "tirant_eau": 4.5,
                        "vitesse": 11.0,
                        "traction": 40.0,
                        "remarques": "Remorqueur de secours et manœuvres légères",
                        "figure": ""
                    }
                ],
                "commentaire": "Flotte mixte permettant différentes configurations selon les conditions"
            }
        },
        
        "simulations": {"simulations": load_excel_simulations()},
        
        "analyse_synthese": {
            "nombre_essais": 37,
            "taux_reussite": 0.73,
            "conditions_critiques": [
                "Vent Ouest > 25 kts avec rafales",
                "Houle NW > 2.5m en période de VE", 
                "Combinaison vent fort + courant de marée > 1 kt",
                "Visibilité < 500m par brouillard dense"
            ],
            "distances_trajectoires": "Distance parcourue moyenne: 2.8 milles du pilotage à l'accostage. Temps moyen de manœuvre: 45 minutes.",
            "commentaire": "L'analyse des simulations révèle une manœuvrabilité satisfaisante avec des conditions critiques bien identifiées.",
            "recapitulatif_text": "La présente étude de manœuvrabilité démontre la faisabilité des opérations portuaires pour les porte-conteneurs de nouvelle génération au terminal Q4 de Tanger Med. Le taux de réussite de 73% des simulations confirme que les dimensions du chenal et de la zone d'évitage sont adaptées aux navires cibles avec l'assistance appropriée de remorqueurs. Les conditions météo-océaniques critiques identifiées nécessitent la mise en place de procédures spécifiques et l'utilisation optimale des remorqueurs haute performance pour garantir la sécurité des manœuvres.",
            "metrics": {
                "caracteres": 820,
                "mots": 132,
                "temps_lecture": 1
            },
            "stats_text": "37 essais au total, 27 réussis (73%), 10 échecs. Réussite élevée sur appareillages, plus faible sur accostages par vent fort NW.",
            "recommandations_text": "• Limiter les manœuvres si vent > 25 kts NW\n• Utiliser 3 remorqueurs pour ULCV\n• Planifier marée haute pour houle > 2.5m",
            "objectifs_evaluations": {
                "objectif_1": {
                    "objectif_texte": "Évaluer la faisabilité des manœuvres d'accostage et d'appareillage pour les porte-conteneurs de 300 à 400m",
                    "degre_realisation": "✅ Objectif atteint",
                    "commentaire": "Les simulations montrent une faisabilité avec assistance adéquate.",
                    "metriques": "Taux de réussite 78%",
                    "ordre": 1
                },
                "objectif_2": {
                    "objectif_texte": "Analyser les interactions hydrodynamiques entre les navires et le nouveau quai Q4",
                    "degre_realisation": "🟡 Partiellement atteint",
                    "commentaire": "Interactions bien caractérisées pour vents < 25 kts, incertitudes au-delà.",
                    "metriques": "15 essais dédiés",
                    "ordre": 2
                },
                "objectif_3": {
                    "objectif_texte": "Identifier les conditions météo-océaniques critiques et les zones à risque",
                    "degre_realisation": "✅ Objectif atteint",
                    "commentaire": "Conditions critiques vent NW > 25 kts et houle > 2.5m identifiées.",
                    "metriques": "",
                    "ordre": 3
                }
            }
        },
        
        "conclusion": "L'étude de manœuvrabilité basée sur les simulations démontre la faisabilité des opérations portuaires pour les porte-conteneurs de nouvelle génération au terminal Q4. Les données collectées confirment que les dimensions du chenal et de la zone d'évitage sont adaptées aux navires cibles avec l'assistance appropriée de remorqueurs. Les conditions météo-océaniques critiques identifiées nécessitent la mise en place de procédures spécifiques et l'utilisation optimale des remorqueurs haute performance pour assurer la sécurité et l'efficacité des manœuvres portuaires.",
        
        "annexes": {
            "type": "automatic",
            "actif": True,
            "annexes": {
                "tableau_complet": {
                    "titre": "Tableau récapitulatif de tous les essais",
                    "simulations": load_excel_simulations(),
                    "actif": True
                },
                "essais_detailles": []
            }
        }
    }
    
    return sample_data

def load_complete_sample_data():
    """🔧 Chargeur complet avec navigation guidée"""
    
    st.write("🔧 **CHARGEMENT des données complètes...**")
    
    try:
        # Créer les données
        sample_data = create_complete_sample_data()
        st.write(f"✅ **Données créées:** {len(sample_data)} sections")
        
        # Vérifier les simulations Excel
        simulations = sample_data["simulations"]["simulations"]
        st.write(f"📊 **Simulations chargées:** {len(simulations)}")
        
        # Afficher quelques statistiques simplifiées
        reussites = sum(1 for s in simulations if s.get('resultat') == 'Réussite')
        echecs = sum(1 for s in simulations if s.get('resultat') == 'Échec')
        
        st.write(f"   ✅ Réussites: {reussites}")
        st.write(f"   ❌ Échecs: {echecs}")
        
        # Nettoyer le session state
        keys_to_clear = [
            "rapport_data", "revisions", "phases", "navires", "remorqueurs", 
            "simulations_data", "houle_conditions", "vent_conditions",
            "courant_conditions", "maree_conditions", "agitation_conditions"
        ]
        
        cleared_count = 0
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
                cleared_count += 1
        
        st.write(f"🧹 **Session nettoyée:** {cleared_count} clés supprimées")
        
        # CHARGER TOUTES LES DONNÉES dans rapport_data
        st.session_state.rapport_data = sample_data
        st.write("✅ **rapport_data chargé COMPLÈTEMENT**")
        
        # CHARGER AUSSI les données individuelles pour les formulaires
        st.session_state.revisions = sample_data["metadonnees"]["historique_revisions"]
        st.session_state.phases = sample_data["donnees_entree"]["plan_de_masse"]["phases"]
        # Figures de phases (clé partagée pour affichage existant)
        phase_figs = []
        for phase in sample_data["donnees_entree"]["plan_de_masse"]["phases"]:
            phase_figs.extend(phase.get("figures", []))
        st.session_state["phase_existing_figures"] = phase_figs
        
        # Conditions environnementales - TOUTES LES CONDITIONS + SESSION STATE
        conditions_env = sample_data["donnees_entree"]["conditions_environnementales"]
        
        # Charger les conditions ET les états de session pour chaque condition
        condition_types = ["houle", "vent", "courant", "maree", "agitation"]
        
        for condition_type in condition_types:
            condition_data = conditions_env.get(condition_type, {})
            
            # Charger les listes de conditions
            st.session_state[f"{condition_type}_conditions"] = condition_data.get("conditions", [])
            
            # Charger les valeurs retenues
            st.session_state[f"{condition_type}_retenues"] = condition_data.get("valeurs_retenues", "")
            
            # Charger les sources
            st.session_state[f"{condition_type}_source"] = condition_data.get("source", "")
            
            # Charger les analyses
            st.session_state[f"{condition_type}_analyse"] = condition_data.get("analyse", "")
            
            # Charger les commentaires et leurs états de checkbox
            commentaire = condition_data.get("commentaire", "")
            st.session_state[f"{condition_type}_commentaire"] = commentaire
            st.session_state[f"{condition_type}_comment_check"] = bool(commentaire)
            
            # Fichiers existants pour affichage (figures/tableaux)
            st.session_state[f"{condition_type}_existing_figures"] = condition_data.get("figures", [])
            st.session_state[f"{condition_type}_existing_tableaux"] = condition_data.get("tableaux", [])
            
            # États des inputs
            st.session_state[f"{condition_type}_retenues_input"] = condition_data.get("valeurs_retenues", "")
            st.session_state[f"{condition_type}_analyse_input"] = condition_data.get("analyse", "")
            st.session_state[f"{condition_type}_source_input"] = condition_data.get("source", "")
            
            # Gérer les tableaux de données si ils existent
            if condition_data.get("table_data"):
                table_data = condition_data["table_data"]
                st.session_state[f"{condition_type}_table_columns"] = table_data.get("columns", [])
                st.session_state[f"{condition_type}_table_data"] = table_data.get("data", [])
        
        st.write(f"✅ **Conditions environnementales chargées:** {len(condition_types)} types")
        
        # Navires et remorqueurs
        st.session_state.navires = sample_data["donnees_navires"]["navires"]["navires"]
        st.session_state.remorqueurs = sample_data["donnees_navires"]["remorqueurs"]["remorqueurs"]
        # Fichiers existants pour remorqueurs (figures)
        st.session_state["remorqueurs_existing_figures"] = [
            r for r in sample_data["donnees_navires"]["remorqueurs"]["remorqueurs"] if r.get("figure")
        ]
        # Figures existantes pour balisage et bathymétrie
        st.session_state["balisage_existing_figures"] = sample_data["donnees_entree"]["balisage"].get("figures", [])
        st.session_state["bathy_existing_figures"] = sample_data["donnees_entree"]["bathymetrie"].get("figures", [])
        # Figures du plan de masse (niveau racine)
        st.session_state["plan_de_masse_existing_figures"] = sample_data["donnees_entree"]["plan_de_masse"].get("figures", [])
        
        # Simulations - DONNÉES EXCEL
        st.session_state.simulations_data = sample_data["simulations"]["simulations"]
        
        # États des UI supplémentaires
        ui_defaults = {
            # Balisage
            "balisage_comment_check": bool(sample_data["donnees_entree"]["balisage"].get("commentaire")),
            # Bathymétrie  
            "bathy_comment_check": bool(sample_data["donnees_entree"]["bathymetrie"].get("commentaire")),
            # Plan de masse
            "plan_comment_check": bool(sample_data["donnees_entree"]["plan_de_masse"].get("commentaire")),
        }
        
        for key, default_value in ui_defaults.items():
            st.session_state[key] = default_value
        
        # Marquer comme chargé
        st.session_state._sample_data_loaded = True
        st.session_state._last_load_time = datetime.now().isoformat()
        
        st.write("🎉 **CHARGEMENT TERMINÉ AVEC SUCCÈS !**")
        st.write("💡 **Changez d'onglet pour voir les données**")
        return True
        
    except Exception as e:
        st.error(f"❌ **ERREUR lors du chargement:** {str(e)}")
        import traceback
        st.error(f"**Détails:** {traceback.format_exc()}")
        return False


def add_sample_data_ui():
    """Interface avec navigation guidée pour le chargement"""
    
    with st.sidebar:
        if st.session_state.get("_sample_data_loaded", False):
            render_navigation_tree()
                
        st.subheader("🧪 Données de test")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Charger exemple", help="Charge un rapport d'exemple COMPLET"):
                if load_complete_sample_data():
                    st.success("✅ Chargement réussi!")
                    st.rerun()
                else:
                    st.error("❌ Échec du chargement")
        
        with col2:
            if st.button("🗑️ Reset", help="Efface toutes les données"):
                # Clear session state
                keys_to_clear = [
                    "rapport_data", "revisions", "phases", "navires", "remorqueurs", 
                    "simulations_data", "_sample_data_loaded", "_last_load_time"
                ]
                
                # Ajouter toutes les clés de conditions
                condition_types = ["houle", "vent", "courant", "maree", "agitation"]
                for condition_type in condition_types:
                    keys_to_clear.extend([
                        f"{condition_type}_conditions",
                        f"{condition_type}_retenues", 
                        f"{condition_type}_source",
                        f"{condition_type}_analyse",
                        f"{condition_type}_commentaire",
                        f"{condition_type}_comment_check",
                        f"{condition_type}_retenues_input",
                        f"{condition_type}_analyse_input",
                        f"{condition_type}_source_input"
                    ])
                
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                
                st.success("✅ Données effacées!")
                st.rerun()
        
        if st.session_state.get("_sample_data_loaded", False):
            st.success("📊 Données d'exemple actives")
            
            # Résumé simplifié
            rapport_data = st.session_state.get("rapport_data", {})
            if rapport_data:
                # Compter les sections remplies
                sections_completes = 0
                total_sections = len(FORM_STRUCTURE)
                
                for section_name, section_config in FORM_STRUCTURE.items():
                    status = get_section_status(section_name, section_config)
                    if status['status'] == 'complete':
                        sections_completes += 1
                
                progression = sections_completes / total_sections
                st.progress(progression, text=f"Complétude: {sections_completes}/{total_sections}")
            
            # Temps de chargement
            last_load = st.session_state.get("_last_load_time")
            if last_load:
                st.caption(f"⏰ Chargé: {last_load[:16]}")
                
        else:
            st.info("⏳ Cliquez sur 'Charger exemple'")
            st.caption("📝 Aucune donnée d'exemple chargée")
    

def create_sample_data_file():
    """Crée un fichier JSON avec les données de test incluant Excel"""
    sample_data = create_complete_sample_data()
    
    # Créer le dossier static s'il n'existe pas
    os.makedirs("static", exist_ok=True)
    
    # Sauvegarder en JSON
    with open("static/sample_data_excel_improved.json", "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False, default=str)
    
    print("Données de test avec Excel sauvées dans static/sample_data_excel_improved.json")
    return "static/sample_data_excel_improved.json"


if __name__ == "__main__":
    print("🧪 GÉNÉRATION DE DONNÉES DE TEST AVEC NAVIGATION GUIDÉE")
    print("=" * 60)
    
    # Créer le fichier JSON
    filename = create_sample_data_file()
    
    # Afficher un résumé
    sample_data = create_complete_sample_data()
    
   # Statistiques des simulations
    simulations = sample_data['simulations']['simulations']
    print(f"   📊 Simulations: {len(simulations)}")
    
    if simulations:
        reussites = sum(1 for s in simulations if s.get('resultat') == 'Réussite')
        echecs = sum(1 for s in simulations if s.get('resultat') == 'Échec')
