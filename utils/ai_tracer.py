import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class AIGenerationTracer:
    """Trace et log tout le contenu généré par l'IA"""
    
    def __init__(self, output_dir: str = "debug/ai_traces"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_trace = {
            "timestamp": None,
            "sections_generated": {},
            "sections_integrated": {},
            "sections_not_integrated": [],
            "template_variables_used": [],
            "warnings": []
        }
    
    def start_trace(self, rapport_title: str = ""):
        """Démarre une nouvelle trace"""
        self.current_trace = {
            "timestamp": datetime.now().isoformat(),
            "rapport_title": rapport_title,
            "sections_generated": {},
            "sections_integrated": {},
            "sections_not_integrated": [],
            "template_variables_used": [],
            "warnings": []
        }
        print(f"📝 Trace démarrée: {self.current_trace['timestamp']}")
    
    def log_generated(self, section_name: str, content: str, source: str = "ai"):
        """Log une section générée"""
        self.current_trace["sections_generated"][section_name] = {
            "content": content,
            "length": len(content) if content else 0,
            "source": source,  # "ai" ou "fallback"
            "preview": content[:200] + "..." if content and len(content) > 200 else content
        }
    
    def log_integrated(self, section_name: str, target_path: tuple, content: str):
        """Log une section intégrée dans rapport_data"""
        path_str = " → ".join(target_path)
        self.current_trace["sections_integrated"][section_name] = {
            "target_path": path_str,
            "target_variable": target_path[-1] if target_path else None,
            "length": len(content) if content else 0,
            "integrated": True
        }
    
    def log_template_variable(self, variable_name: str, has_content: bool, content_length: int = 0):
        """Log une variable utilisée dans le template"""
        self.current_trace["template_variables_used"].append({
            "variable": variable_name,
            "has_content": has_content,
            "content_length": content_length
        })
    
    def log_warning(self, message: str):
        """Log un avertissement"""
        self.current_trace["warnings"].append({
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
    
    def finish_trace(self) -> Dict[str, Any]:
        """Finalise la trace et génère le rapport"""
        
        # Identifier les sections générées mais non intégrées
        generated = set(self.current_trace["sections_generated"].keys())
        integrated = set(self.current_trace["sections_integrated"].keys())
        not_integrated = generated - integrated
        
        self.current_trace["sections_not_integrated"] = list(not_integrated)
        
        # Calculer les stats
        self.current_trace["stats"] = {
            "total_generated": len(generated),
            "total_integrated": len(integrated),
            "total_not_integrated": len(not_integrated),
            "integration_rate": f"{len(integrated)/len(generated)*100:.1f}%" if generated else "0%",
            "total_warnings": len(self.current_trace["warnings"])
        }
        
        # Sauvegarder
        self._save_trace()
        self._save_readable_report()
        
        return self.current_trace
    
    def _save_trace(self):
        """Sauvegarde la trace JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"trace_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.current_trace, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Trace JSON: {filename}")
    
    def _save_readable_report(self):
        """Sauvegarde un rapport lisible"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"report_{timestamp}.txt"
        
        lines = []
        lines.append("=" * 70)
        lines.append("RAPPORT DE GÉNÉRATION IA")
        lines.append("=" * 70)
        lines.append(f"Date: {self.current_trace['timestamp']}")
        lines.append(f"Rapport: {self.current_trace.get('rapport_title', 'N/A')}")
        lines.append("")
        
        # Stats
        stats = self.current_trace.get("stats", {})
        lines.append("-" * 70)
        lines.append("STATISTIQUES")
        lines.append("-" * 70)
        lines.append(f"Sections générées: {stats.get('total_generated', 0)}")
        lines.append(f"Sections intégrées: {stats.get('total_integrated', 0)}")
        lines.append(f"Sections NON intégrées: {stats.get('total_not_integrated', 0)}")
        lines.append(f"Taux d'intégration: {stats.get('integration_rate', '0%')}")
        lines.append("")
        
        # Sections générées
        lines.append("-" * 70)
        lines.append("SECTIONS GÉNÉRÉES")
        lines.append("-" * 70)
        for name, data in self.current_trace["sections_generated"].items():
            status = "✅" if name in self.current_trace["sections_integrated"] else "❌"
            lines.append(f"{status} {name}")
            lines.append(f"   Source: {data['source']}")
            lines.append(f"   Longueur: {data['length']} caractères")
            lines.append(f"   Aperçu: {data['preview'][:100]}...")
            lines.append("")
        
        # Sections non intégrées (IMPORTANT)
        if self.current_trace["sections_not_integrated"]:
            lines.append("-" * 70)
            lines.append("⚠️  SECTIONS NON INTÉGRÉES (CONTENU PERDU)")
            lines.append("-" * 70)
            for name in self.current_trace["sections_not_integrated"]:
                data = self.current_trace["sections_generated"].get(name, {})
                lines.append(f"❌ {name}")
                lines.append(f"   Contenu ({data.get('length', 0)} chars):")
                lines.append(f"   {data.get('content', 'N/A')[:500]}")
                lines.append("")
        
        # Intégrations
        lines.append("-" * 70)
        lines.append("MAPPINGS D'INTÉGRATION")
        lines.append("-" * 70)
        for name, data in self.current_trace["sections_integrated"].items():
            lines.append(f"✅ {name}")
            lines.append(f"   → {data['target_path']}")
            lines.append(f"   Variable finale: {data['target_variable']}")
            lines.append("")
        
        # Warnings
        if self.current_trace["warnings"]:
            lines.append("-" * 70)
            lines.append("⚠️  AVERTISSEMENTS")
            lines.append("-" * 70)
            for warning in self.current_trace["warnings"]:
                lines.append(f"- {warning['message']}")
            lines.append("")
        
        # Écrire le fichier
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        print(f"📄 Rapport lisible: {filename}")
        
        # Afficher un résumé si des sections sont perdues
        if self.current_trace["sections_not_integrated"]:
            print(f"\n⚠️  ATTENTION: {len(self.current_trace['sections_not_integrated'])} sections générées mais NON intégrées!")
            for name in self.current_trace["sections_not_integrated"]:
                print(f"   ❌ {name}")


# Instance globale pour faciliter l'usage
_tracer: Optional[AIGenerationTracer] = None


def get_tracer() -> AIGenerationTracer:
    """Retourne le tracer global"""
    global _tracer
    if _tracer is None:
        _tracer = AIGenerationTracer()
    return _tracer


def start_trace(rapport_title: str = ""):
    """Démarre une trace"""
    get_tracer().start_trace(rapport_title)


def log_generated(section_name: str, content: str, source: str = "ai"):
    """Log une section générée"""
    get_tracer().log_generated(section_name, content, source)


def log_integrated(section_name: str, target_path: tuple, content: str):
    """Log une intégration"""
    get_tracer().log_integrated(section_name, target_path, content)


def log_warning(message: str):
    """Log un warning"""
    get_tracer().log_warning(message)


def finish_trace() -> Dict[str, Any]:
    """Finalise et sauvegarde"""
    return get_tracer().finish_trace()
