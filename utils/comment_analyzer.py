#!/usr/bin/env python3
"""
Agent IA simplifié utilisant directement l'API HTTP OpenRouter
Sans dépendance au SDK OpenAI - Plus fiable pour les modèles gratuits
"""

import os
import json
import time
import random
import requests

class CommentAnalyzer:
    """Agent IA simple pour analyser les commentaires et retourner 1/0 avec gestion rate limit"""
    
    def __init__(self, model: str = None, max_retries: int = 3):
        # Modèles gratuits vérifiés et disponibles (janvier 2025)
        self.free_models = [
            "mistralai/mistral-nemo:free",
            "microsoft/mai-ds-r1:free", 
            "meta-llama/llama-4-maverick:free",
            "google/gemma-3-27b-it:free",
            "moonshotai/kimi-dev-72b:free",
            "qwen/qwen3-235b-a22b:free",
            "deepseek/deepseek-r1-distill-llama-70b:free"
        ]
        
        self.model = model if model else self.free_models[0]  # Premier modèle par défaut
        self.max_retries = max_retries
        self.base_delay = 1
        
        # Configuration API
        self.api_key = os.getenv("OPENROUTER_API_KEY", "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")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Headers pour les requêtes
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",  # Optionnel
            "X-Title": "Générateur de Rapports"  # Optionnel
        }
        
        # Prompt simple et direct
        self.prompt = """Tu es un expert en manœuvrabilité portuaire.
Analyse ce commentaire de simulation et détermine si la manœuvre a réussi ou échoué.

COMMENTAIRE À ANALYSER:
"{comment}"

RÈGLES:
- Si la manœuvre est réussie, accomplie, sans problème → réponds exactement "1"
- Si la manœuvre a échoué, été abandonnée, a eu des problèmes → réponds exactement "0"
- Ne réponds QUE par "1" ou "0", rien d'autre

RÉPONSE:"""
        
        print(f"🤖 CommentAnalyzer initialisé avec {self.model}")
    
    def _make_api_request(self, prompt: str) -> dict:
        """Fait une requête HTTP directe à OpenRouter"""
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un expert maritime. Tu réponds uniquement par 1 ou 0."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 5
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            # Vérifier le statut de la réponse
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {
                    "success": False, 
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout - requête trop lente"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Erreur réseau: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Erreur inattendue: {str(e)}"}
    
    def _analyze_single_attempt(self, comment: str) -> int:
        """Une seule tentative d'analyse"""
        
        # Vérifier que le commentaire n'est pas vide
        if not comment or len(comment.strip()) < 5:
            return -1  # Non défini si pas d'info
        
        # Préparer le prompt
        full_prompt = self.prompt.format(comment=comment.strip())
        
        # Faire la requête API
        result = self._make_api_request(full_prompt)
        
        if not result["success"]:
            error_msg = result["error"]
            status_code = result.get("status_code", 0)
            
            # Gestion spécifique des erreurs
            if status_code == 429 or "rate limit" in error_msg.lower():
                print(f"⏳ Rate limit atteint")
                return -1
            elif status_code == 404 or "not found" in error_msg.lower() or "no endpoints" in error_msg.lower():
                print(f"❌ Modèle {self.model} non disponible")
                return -1
            elif status_code == 401 or "unauthorized" in error_msg.lower():
                print(f"🔑 Erreur authentification")
                return -1
            else:
                print(f"❌ Erreur API: {error_msg}")
                return -1
        
        try:
            # Extraire la réponse
            response_data = result["data"]
            content = response_data["choices"][0]["message"]["content"].strip()
            
            # Parser la réponse
            if "1" in content:
                return 1
            elif "0" in content:
                return 0
            else:
                print(f"⚠️ Réponse IA inattendue: '{content}'")
                return -1
                
        except (KeyError, IndexError, TypeError) as e:
            print(f"❌ Erreur parsing réponse: {e}")
            return -1
    
    def analyze_comment(self, comment: str, use_retry: bool = True) -> int:
        """
        Analyse un commentaire et retourne 1 (réussite), 0 (échec), ou -1 (erreur/non défini)
        
        Args:
            comment: Commentaire du pilote à analyser
            use_retry: Utiliser le système de retry (True par défaut)
            
        Returns:
            int: 1 pour réussite, 0 pour échec, -1 pour erreur/non défini
        """
        if use_retry:
            return self._analyze_with_retry(comment)
        else:
            return self._analyze_single_attempt(comment)
    
    def _analyze_with_retry(self, comment: str) -> int:
        """Analyse avec retry automatique et changement de modèle"""
        
        for attempt in range(self.max_retries):
            try:
                result = self._analyze_single_attempt(comment)
                
                # Si succès, retourner le résultat
                if result != -1:
                    return result
                
                # Si erreur et encore des tentatives
                if attempt < self.max_retries - 1:
                    # Essayer un autre modèle si disponible
                    if attempt < len(self.free_models) - 1:
                        old_model = self.model
                        self.model = self.free_models[attempt + 1]
                        print(f"🔄 Changement de modèle: {old_model} → {self.model}")
                    
                    # Attendre avant retry
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"⏳ Attente {delay:.1f}s avant retry {attempt + 2}/{self.max_retries}...")
                    time.sleep(delay)
                
            except Exception as e:
                print(f"❌ Erreur tentative {attempt + 1}: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = 5 + random.uniform(0, 5)
                    print(f"⏳ Attente {delay:.1f}s...")
                    time.sleep(delay)
        
        # Toutes les tentatives ont échoué
        print(f"❌ Échec après {self.max_retries} tentatives avec {len(self.free_models)} modèles")
        return -1
    
    def analyze_batch_with_rate_limit(self, simulations: list, max_per_minute: int = 10) -> list:
        """
        Analyse un lot de simulations avec gestion intelligente du rate limit
        """
        updated_simulations = []
        
        print(f"🤖 Analyse IA de {len(simulations)} commentaires")
        print(f"📊 Limite conservative: {max_per_minute} requêtes/minute")
        print(f"🎯 Modèle principal: {self.model}")
        
        # Calculer le délai entre requêtes (plus conservateur)
        delay_between_requests = 60 / max_per_minute if max_per_minute > 0 else 6
        
        for i, sim in enumerate(simulations):
            updated_sim = sim.copy()
            comment = sim.get("commentaire_pilote", "")
            
            if comment and comment.strip():
                print(f"🔄 Analyse simulation {sim.get('id', i+1)}...")
                
                # Analyser avec retry automatique
                ai_result = self.analyze_comment(comment, use_retry=True)
                
                # Convertir les codes
                if ai_result == 1:
                    updated_sim["resultat"] = "Réussite"
                    updated_sim["resultat_source"] = "IA"
                    print(f"✅ Simulation {sim.get('id', i+1)}: Réussite")
                elif ai_result == 0:
                    updated_sim["resultat"] = "Échec"
                    updated_sim["resultat_source"] = "IA"
                    print(f"❌ Simulation {sim.get('id', i+1)}: Échec")
                else:  # -1 (erreur)
                    updated_sim["resultat"] = "Non défini"
                    updated_sim["resultat_source"] = "IA - Erreur"
                    print(f"⚠️ Simulation {sim.get('id', i+1)}: Non défini (Erreur)")
                
                # Attendre avant la prochaine requête
                if i < len(simulations) - 1:
                    print(f"⏱️ Attente {delay_between_requests:.1f}s...")
                    time.sleep(delay_between_requests)
                    
            else:
                updated_sim["resultat"] = "Non défini"
                updated_sim["resultat_source"] = "Aucun commentaire"
                print(f"📝 Simulation {sim.get('id', i+1)}: Pas de commentaire")
            
            updated_simulations.append(updated_sim)
        
        print(f"\n🎯 Analyse terminée: {len(updated_simulations)} simulations traitées")
        return updated_simulations
    
    def test_model_availability(self) -> dict:
        """Teste quels modèles gratuits sont disponibles"""
        print("🧪 Test de disponibilité des modèles gratuits...")
        
        available_models = []
        unavailable_models = []
        
        for model in self.free_models:
            print(f"🔍 Test {model}...")
            original_model = self.model
            self.model = model
            
            # Test simple
            result = self._analyze_single_attempt("Test de disponibilité")
            
            if result != -1:
                available_models.append(model)
                print(f"✅ {model} - DISPONIBLE")
            else:
                unavailable_models.append(model)
                print(f"❌ {model} - INDISPONIBLE")
            
            # Restaurer le modèle original
            self.model = original_model
            
            # Petite pause entre tests
            time.sleep(2)
        
        return {
            "available": available_models,
            "unavailable": unavailable_models,
            "total_tested": len(self.free_models)
        }

# Interfaces simplifiées
def ai_analyze_comment(comment: str, model: str = None) -> str:
    """Interface simple pour analyser un commentaire"""
    analyzer = CommentAnalyzer(model)
    result = analyzer.analyze_comment(comment)
    
    if result == 1:
        return "Réussite"
    elif result == 0:
        return "Échec"
    else:
        return "Non défini"

def analyze_simulation_comments(simulations: list, use_rate_limit: bool = True, model: str = None) -> list:
    """Analyse les commentaires avec le système robuste"""
    analyzer = CommentAnalyzer(model)
    
    if use_rate_limit:
        return analyzer.analyze_batch_with_rate_limit(simulations, max_per_minute=10)
    else:
        # Mode rapide (non recommandé)
        updated_simulations = []
        for sim in simulations:
            updated_sim = sim.copy()
            comment = sim.get("commentaire_pilote", "")
            
            if comment and comment.strip():
                ai_result = analyzer.analyze_comment(comment, use_retry=False)
                
                if ai_result == 1:
                    updated_sim["resultat"] = "Réussite"
                    updated_sim["resultat_source"] = "IA"
                elif ai_result == 0:
                    updated_sim["resultat"] = "Échec"
                    updated_sim["resultat_source"] = "IA"
                else:
                    updated_sim["resultat"] = "Non défini"
                    updated_sim["resultat_source"] = "IA - Erreur"
            else:
                updated_sim["resultat"] = "Non défini"
                updated_sim["resultat_source"] = "Aucun commentaire"
            
            updated_simulations.append(updated_sim)
        
        return updated_simulations

def test_comment_analyzer():
    """Test complet du système"""
    
    test_comments = [
        "Manœuvre réalisée sans difficulté, accostage parfait",
        "Impossible de contrôler le navire, manœuvre abandonnée", 
        "Bon déroulement de l'opération, objectifs atteints"
    ]
    
    analyzer = CommentAnalyzer()
    
    print("🧪 Test de l'analyseur de commentaires (API HTTP directe)")
    print("=" * 60)
    
    # Test de disponibilité des modèles
    availability = analyzer.test_model_availability()
    print(f"\n📊 Résultats disponibilité:")
    print(f"✅ Disponibles: {len(availability['available'])}")
    print(f"❌ Indisponibles: {len(availability['unavailable'])}")
    
    if availability['available']:
        print(f"\n🎯 Utilisation du premier modèle disponible: {availability['available'][0]}")
        analyzer.model = availability['available'][0]
        
        print(f"\n🔄 Tests d'analyse...")
        for i, comment in enumerate(test_comments, 1):
            print(f"\n--- Test {i} ---")
            print(f"Commentaire: {comment}")
            
            result = analyzer.analyze_comment(comment, use_retry=True)
            
            if result == 1:
                print("✅ RÉUSSITE")
            elif result == 0:
                print("❌ ÉCHEC")
            else:
                print("⚠️ NON DÉFINI")
    else:
        print("❌ Aucun modèle disponible")

if __name__ == "__main__":
    test_comment_analyzer()
