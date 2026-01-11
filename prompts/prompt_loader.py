import os
from pathlib import Path
from typing import Optional
from jinja2 import Template

class PromptLoader:
    """Gestionnaire pour charger et gérer les prompts depuis des fichiers"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._prompts_cache = {}
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """Charge tous les prompts au démarrage"""
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Dossier prompts non trouvé: {self.prompts_dir}")
        
        for prompt_file in self.prompts_dir.glob("*.txt"):
            section_name = prompt_file.stem
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    self._prompts_cache[section_name] = content
            except Exception as e:
                print(f"❌ Erreur chargement {prompt_file}: {e}")
    
    def get_prompt(self, section_name: str) -> Optional[str]:
        """Récupère un prompt par nom de section"""
        return self._prompts_cache.get(section_name)
    
    def list_available_prompts(self) -> list:
        """Liste tous les prompts disponibles"""
        return list(self._prompts_cache.keys())
    
    def render_prompt(self, section_name: str, data: dict) -> str:
        """Rend un prompt avec les données (Jinja2)"""
        prompt_template = self.get_prompt(section_name)
        if not prompt_template:
            raise ValueError(f"Prompt '{section_name}' non trouvé")
        
        template = Template(prompt_template)
        return template.render(**data)
    
    def update_prompt(self, section_name: str, new_content: str, save_to_file: bool = True):
        """Met à jour un prompt existant"""
        if section_name not in self._prompts_cache:
            raise ValueError(f"Prompt '{section_name}' n'existe pas")
        
        self._prompts_cache[section_name] = new_content
        
        if save_to_file:
            prompt_file = self.prompts_dir / f"{section_name}.txt"
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"🔄 Prompt mis à jour: {prompt_file}")
