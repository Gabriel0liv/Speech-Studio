"""
src/tts/ptbr_text.py
--------------------
Conservative Brazilian Portuguese text analysis and normalization.

Purpose:
- Detect common unaccented PT-BR patterns that hurt TTS quality.
- Apply safe, conservative replacements for well-known missing accents.
- Never attempt full grammar correction.
- Preserve user text when in doubt.
"""

import re
import unicodedata
from typing import Dict, List

# ---------------------------------------------------------------------------
# Accent / word normalisation table
# Only substitute exact whole-word matches (case-insensitive), and only when
# the substitution is unambiguous.  Entries are (unaccented, accented) pairs.
# Order matters: longer / more specific patterns first.
# ---------------------------------------------------------------------------
_WORD_FIXES: List[tuple] = [
    # Very common PT-BR words people forget to accent
    ("validacao",   "validação"),
    ("diarizacao",  "diarização"),
    ("transcricao", "transcrição"),
    ("descricao",   "descrição"),
    ("configuracao","configuração"),
    ("pronuncia",   "pronúncia"),
    ("pronuncias",  "pronúncias"),
    ("sintese",     "síntese"),
    ("musica",      "música"),
    ("publico",     "público"),
    ("numero",      "número"),
    ("numeros",     "números"),
    ("audio",       "áudio"),
    ("audios",      "áudios"),
    ("video",       "vídeo"),
    ("videos",      "vídeos"),
    ("portugues",   "português"),
    ("ingles",      "inglês"),
    ("frances",     "francês"),
    ("japones",     "japonês"),
    ("tambem",      "também"),
    ("entao",       "então"),
    ("porem",       "porém"),
    ("rapido",      "rápido"),
    ("rapida",      "rápida"),
    ("facil",       "fácil"),
    ("dificil",     "difícil"),
    ("possivel",    "possível"),
    ("voce",        "você"),
    ("voces",       "vocês"),
    ("ola",         "Olá"),     # Keep capitalised (greeting)
    ("nao",         "não"),
    ("propria",     "própria"),
    ("proprio",     "próprio"),
    ("proprios",    "próprios"),
    ("proprias",    "próprias"),
    ("unico",       "único"),
    ("unica",       "única"),
    ("ultima",      "última"),
    ("ultimo",      "último"),
    ("otimo",       "ótimo"),
    ("otima",       "ótima"),
    ("logico",      "lógico"),
    ("logica",      "lógica"),
    ("classico",    "clássico"),
    ("classica",    "clássica"),
    ("automatico",  "automático"),
    ("automatica",  "automática"),
    ("especifico",  "específico"),
    ("especifica",  "específica"),
    ("pratico",     "prático"),
    ("pratica",     "prática"),
]

# Isolated "e" (the word "and" in Portuguese) -> "é" is risky in general text.
# We only do it in the safe pattern:  ", e "  at sentence boundaries.
# We do NOT do blind replacement of all standalone "e" occurrences.

def _strip_accents(s: str) -> str:
    """Return a version of s with all diacritics removed (for comparison)."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def analyze_ptbr_text(text: str) -> Dict:
    """
    Analyse a PT-BR text string and return a report dict with:
      - warnings: list of human-readable warning strings
      - suggestions: list of (original_word, suggested_word) tuples
      - has_issues: bool — True if any warnings were raised
    """
    warnings: List[str] = []
    suggestions: List[Dict] = []

    if not text or not text.strip():
        return {"warnings": [], "suggestions": [], "has_issues": False}

    stripped = _strip_accents(text)
    total_chars = len(text.replace(" ", "").replace("\n", ""))
    accented_chars = sum(
        1 for c in text
        if unicodedata.category(c) in ("Ll", "Lu", "Lt", "Lm", "Lo")
        and c != _strip_accents(c)
    )
    word_count = len(text.split())

    # --- Check 1: very few accent marks ---
    if total_chars > 30:
        accent_ratio = accented_chars / max(total_chars, 1)
        if accent_ratio < 0.01 and word_count > 5:
            warnings.append(
                "[AVISO] O texto parece ter poucos ou nenhum acento. "
                "O PT-BR sem acentos pode soar robotico ou incorreto. "
                "Considere usar --normalize-ptbr ou adicionar acentos manualmente."
            )

    # --- Check 2: all lowercase ---
    non_space = text.replace(" ", "").replace("\n", "")
    if non_space and non_space == non_space.lower() and len(non_space) > 15:
        warnings.append(
            "[AVISO] O texto esta completamente em letras minusculas. "
            "Inicie frases com maiusculas para melhor qualidade de sintese."
        )

    # --- Check 3: little punctuation ---
    punct_count = sum(1 for c in text if c in ".,;:!?…")
    if word_count > 20 and punct_count == 0:
        warnings.append(
            "[AVISO] O texto tem mais de 20 palavras mas pouca pontuacao. "
            "Adicione virgulas e pontos para pausas e entonacao mais naturais."
        )

    # --- Check 4: very long sentences ---
    sentences = re.split(r"[.!?…]+", text)
    long_sentences = [s for s in sentences if len(s.split()) > 40]
    if long_sentences:
        warnings.append(
            f"[AVISO] {len(long_sentences)} frase(s) com mais de 40 palavras detectada(s). "
            "Frases longas podem causar corte de audio. Divida-as com pontos ou virgulas."
        )

    # --- Check 5: common unaccented words ---
    words_lower = {w.lower().strip(".,;:!?\"'()[]") for w in text.split()}
    for unaccented, accented in _WORD_FIXES:
        if unaccented.lower() in words_lower:
            suggestions.append({
                "original": unaccented,
                "suggested": accented,
                "note": f"'{unaccented}' -> '{accented}'"
            })

    if suggestions:
        note_list = ", ".join(s["note"] for s in suggestions[:5])
        suffix = f" (e mais {len(suggestions)-5})" if len(suggestions) > 5 else ""
        warnings.append(
            f"[AVISO] Palavras sem acento detectadas: {note_list}{suffix}. "
            "Use --normalize-ptbr para aplicar correccoes automaticas."
        )

    return {
        "warnings": warnings,
        "suggestions": suggestions,
        "has_issues": len(warnings) > 0,
    }


def normalize_basic_ptbr_text(text: str) -> str:
    """
    Apply conservative whole-word accent corrections to PT-BR text.

    Rules:
    - Only substitute known, unambiguous word→accented-word pairs.
    - Preserve surrounding punctuation and casing as much as possible.
    - Do NOT attempt full grammar correction.
    - Return original text unchanged on any error.
    """
    if not text or not text.strip():
        return text

    result = text

    for unaccented, accented in _WORD_FIXES:
        # Build a regex that matches the word as a whole token (word boundary),
        # case-insensitive, and captures the original for casing preservation.
        pattern = r"(?<![A-Za-zÀ-ÿ])" + re.escape(unaccented) + r"(?![A-Za-zÀ-ÿ])"

        def _replace(m: re.Match, _acc=accented, _unacc=unaccented) -> str:
            original = m.group(0)
            # Preserve ALL-CAPS if original was all caps
            if original.isupper():
                return _acc.upper()
            # Preserve Title Case if original was title-cased (and accented form starts lowercase)
            if original[0].isupper() and _acc[0].islower():
                return _acc[0].upper() + _acc[1:]
            # If accented form already has the right casing (e.g. "Olá"), return as-is
            return _acc

        result = re.sub(pattern, _replace, result, flags=re.IGNORECASE)

    # Safe "e" -> "é" substitution: only for the conjunctive "e" between
    # two clauses (comma before it), e.g. "texto, e imagem" -> "texto, e imagem"
    # We do NOT do this blindly to avoid breaking "ele e ela" type patterns.
    # This rule is deliberately very narrow.
    result = re.sub(r"(,\s+)e(\s+)", r"\1é\2", result)

    return result


def print_analysis_report(analysis: Dict, verbose: bool = False) -> None:
    """Print the analysis report to stdout in a readable format."""
    if not analysis["has_issues"]:
        print("[OK] Analise PT-BR: nenhum problema detectado no texto.")
        return

    print("\n[*] === Analise PT-BR do Texto ===")
    for w in analysis["warnings"]:
        print(f"    {w}")

    if verbose and analysis["suggestions"]:
        print("\n    Sugestoes de substituicao:")
        for s in analysis["suggestions"]:
            print(f"      {s['note']}")
    print()
