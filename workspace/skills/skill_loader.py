# skill_loader.py — Carrega skills e injeta em prompts LLM
# Skills são carregadas por condição de estado, não por role fixo.
# Cada skill é associada a uma condição que reflete quando ela é necessária.

import os
from typing import List, Optional

SKILLS_DIR = os.path.join(os.path.dirname(__file__))

# Mapeamento condição → skills
# Skills são carregadas quando o estado indica que a condição é relevante
CONDITION_SKILLS = {
    "content_generation": ["base_writing", "copy_prime", "humanizer"],
    "strategy_needed": ["content_strategy"],
    "deep_strategy": ["contextual_connection"],
    "trend_analysis": ["trend_detection"],
    "distribution_execution": ["distribution"],
}

# Skills que sempre são carregadas (fallback, comportamento base)
ALWAYS_SKILLS = ["client_fallback"]

_cache = {}


def load_skill(skill_name: str) -> Optional[str]:
    """Carrega conteúdo de uma skill do arquivo .md."""
    if skill_name in _cache:
        return _cache[skill_name]

    filepath = os.path.join(SKILLS_DIR, f"{skill_name}.md")
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        _cache[skill_name] = content
        return content
    except Exception:
        return None


def get_skills_for_condition(condition: str) -> List[str]:
    """Retorna nomes das skills associadas a uma condição de estado."""
    condition_skills = CONDITION_SKILLS.get(condition, [])
    return ALWAYS_SKILLS + condition_skills


def inject_skills_for_condition(prompt: str, condition: str, max_skills: int = 4) -> str:
    """Injeta skills relevantes no prompt baseado na condição de estado.

    Skills são adicionadas APÓS as instruções principais, nunca as substituindo.

    Args:
        prompt: Prompt original do LLM.
        condition: Condição de estado que determina quais skills carregar.
        max_skills: Máximo de skills a injetar (default 4).

    Returns:
        Prompt com skills injetadas, ou prompt original se condição não tem skills.
    """
    skill_names = get_skills_for_condition(condition)[:max_skills]
    if not skill_names:
        return prompt

    skill_parts = []
    for name in skill_names:
        content = load_skill(name)
        if content:
            lines = content.split("\n")
            relevant_lines = []
            in_frontmatter = False
            for line in lines:
                if line.strip() == "---":
                    in_frontmatter = not in_frontmatter
                    continue
                if not in_frontmatter:
                    relevant_lines.append(line)

            skill_text = "\n".join(relevant_lines).strip()
            if skill_text:
                skill_parts.append(f"### Skill: {name}\n{skill_text}")

    if not skill_parts:
        return prompt

    skills_block = "\n\n".join(skill_parts)
    return f"{prompt}\n\n---\n### Skills aplicáveis\n{skills_block}"


def clear_cache():
    """Limpa cache de skills."""
    global _cache
    _cache = {}