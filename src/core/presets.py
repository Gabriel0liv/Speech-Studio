import json
import sqlite3
import unicodedata
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from src.core.database import get_connection

# =====================================================================
# Preset Alias Resolution
# =====================================================================
# Maps short/friendly aliases -> canonical preset names stored in the DB.
# Lookup is case-insensitive and accent-insensitive.
_PRESET_ALIASES: Dict[str, str] = {
    # Kokoro PT-BR
    "dora":              "Narradora Kokoro Dora (Padrao)",
    "kokoro dora":       "Narradora Kokoro Dora (Padrao)",
    "kokoro_dora":       "Narradora Kokoro Dora (Padrao)",
    "kokoro-dora":       "Narradora Kokoro Dora (Padrao)",
    "alex":              "Narrador Kokoro Alex",
    "kokoro alex":       "Narrador Kokoro Alex",
    "kokoro_alex":       "Narrador Kokoro Alex",
    "kokoro-alex":       "Narrador Kokoro Alex",
    "santa":             "Narrador Kokoro Santa",
    "kokoro santa":      "Narrador Kokoro Santa",
    "kokoro_santa":      "Narrador Kokoro Santa",
    "kokoro-santa":      "Narrador Kokoro Santa",
    # Piper PT-BR
    "faber":             "Piper Voz Faber (Narrador)",
    "piper faber":       "Piper Voz Faber (Narrador)",
    "piper_faber":       "Piper Voz Faber (Narrador)",
    "piper-faber":       "Piper Voz Faber (Narrador)",
    "edresson":          "Piper Voz Edresson",
    "piper edresson":    "Piper Voz Edresson",
    "piper_edresson":    "Piper Voz Edresson",
    "piper-edresson":    "Piper Voz Edresson",
}

def _normalize_alias(s: str) -> str:
    """Lowercase + strip accents for comparison."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

def resolve_preset_alias(name_or_id: Union[int, str]) -> Union[int, str]:
    """
    Resolve a short preset alias to the canonical DB name.
    Falls back to name_or_id unchanged if no alias matches.
    """
    if isinstance(name_or_id, int):
        return name_or_id
    normalized = _normalize_alias(str(name_or_id))
    # Direct alias table lookup
    if normalized in _PRESET_ALIASES:
        return _PRESET_ALIASES[normalized]
    # Also try without accent normalization
    for alias_key, canonical in _PRESET_ALIASES.items():
        if _normalize_alias(alias_key) == normalized:
            return canonical
    return name_or_id


# =====================================================================
# App Settings Persistence APIs
# =====================================================================

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve setting value by key."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default
    except Exception as e:
        print(f"[WARN] Nao foi possivel ler configuracao '{key}': {e}")
        return default

def set_setting(key: str, value: str) -> None:
    """Save or update a setting value."""
    try:
        now_str = datetime.now().isoformat()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO app_settings (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, str(value), now_str))
            conn.commit()
    except Exception as e:
        print(f"[WARN] Nao foi possivel salvar configuracao '{key}': {e}")


# =====================================================================
# TTS Presets Persistence APIs
# =====================================================================

def create_tts_preset(
    name: str,
    engine: str,
    voice: Optional[str] = None,
    output_format: str = "wav",
    speed: float = 1.0,
    preview_chars: int = 300,
    chunk_chars: int = 400,
    language: Optional[str] = None,
    metadata_json: str = "{}",
    is_default: int = 0
) -> Optional[int]:
    """Create a new TTS parameter preset."""
    try:
        now_str = datetime.now().isoformat()
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # If is_default=1, reset previous default
            if is_default == 1:
                cursor.execute("UPDATE tts_presets SET is_default = 0")
                
            cursor.execute("""
                INSERT INTO tts_presets (
                    name, engine, voice, output_format, speed, preview_chars,
                    chunk_chars, language, metadata_json, is_default, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, engine, voice, output_format, speed, preview_chars,
                chunk_chars, language, metadata_json, is_default, now_str, now_str
            ))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"[WARN] Nao foi possivel criar preset '{name}': {e}")
        return None

def update_tts_preset(
    preset_id_or_name: Union[int, str],
    engine: Optional[str] = None,
    voice: Optional[str] = None,
    output_format: Optional[str] = None,
    speed: Optional[float] = None,
    preview_chars: Optional[int] = None,
    chunk_chars: Optional[int] = None,
    language: Optional[str] = None,
    metadata_json: Optional[str] = None,
    is_default: Optional[int] = None
) -> None:
    """Update preset values by ID or UNIQUE name."""
    try:
        now_str = datetime.now().isoformat()
        
        # Build dynamic SQL query
        updates = ["updated_at = ?"]
        params = [now_str]
        
        if engine is not None:
            updates.append("engine = ?")
            params.append(engine)
        if voice is not None:
            updates.append("voice = ?")
            params.append(voice)
        if output_format is not None:
            updates.append("output_format = ?")
            params.append(output_format)
        if speed is not None:
            updates.append("speed = ?")
            params.append(speed)
        if preview_chars is not None:
            updates.append("preview_chars = ?")
            params.append(preview_chars)
        if chunk_chars is not None:
            updates.append("chunk_chars = ?")
            params.append(chunk_chars)
        if language is not None:
            updates.append("language = ?")
            params.append(language)
        if metadata_json is not None:
            updates.append("metadata_json = ?")
            params.append(metadata_json)
        if is_default is not None:
            updates.append("is_default = ?")
            params.append(is_default)
            
        # Determine column condition
        if isinstance(preset_id_or_name, int) or (isinstance(preset_id_or_name, str) and preset_id_or_name.isdigit()):
            condition = "WHERE id = ?"
            params.append(int(preset_id_or_name))
        else:
            condition = "WHERE name = ?"
            params.append(preset_id_or_name)
            
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # If default is being set, reset others first
            if is_default == 1:
                cursor.execute("UPDATE tts_presets SET is_default = 0")
                
            cursor.execute(f"UPDATE tts_presets SET {', '.join(updates)} {condition}", tuple(params))
            conn.commit()
    except Exception as e:
        print(f"[WARN] Nao foi possivel atualizar preset '{preset_id_or_name}': {e}")

def delete_tts_preset(preset_id_or_name: Union[int, str]) -> None:
    """Delete a preset by ID or UNIQUE name."""
    try:
        if isinstance(preset_id_or_name, int) or (isinstance(preset_id_or_name, str) and preset_id_or_name.isdigit()):
            condition = "WHERE id = ?"
            param = int(preset_id_or_name)
        else:
            condition = "WHERE name = ?"
            param = preset_id_or_name
            
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM tts_presets {condition}", (param,))
            conn.commit()
    except Exception as e:
        print(f"[WARN] Nao foi possivel remover preset '{preset_id_or_name}': {e}")

def list_tts_presets() -> List[Dict[str, Any]]:
    """Retrieve all saved presets."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tts_presets ORDER BY name ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"[WARN] Nao foi possivel listar presets: {e}")
        return []

def get_tts_preset(name_or_id: Union[int, str]) -> Optional[Dict[str, Any]]:
    """Retrieve a single preset by ID, exact name, or registered alias."""
    try:
        # Resolve alias first (e.g. "Dora" -> "Narradora Kokoro Dora (Padrao)")
        resolved = resolve_preset_alias(name_or_id)

        if isinstance(resolved, int) or (isinstance(resolved, str) and resolved.isdigit()):
            condition = "WHERE id = ?"
            param = int(resolved)
        else:
            condition = "WHERE name = ?"
            param = resolved

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM tts_presets {condition}", (param,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[WARN] Nao foi possivel obter preset '{name_or_id}': {e}")
        return None


def set_default_tts_preset(preset_id_or_name: Union[int, str]) -> None:
    """Set the specified preset as default."""
    try:
        if isinstance(preset_id_or_name, int) or (isinstance(preset_id_or_name, str) and preset_id_or_name.isdigit()):
            condition = "WHERE id = ?"
            param = int(preset_id_or_name)
        else:
            condition = "WHERE name = ?"
            param = preset_id_or_name
            
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tts_presets SET is_default = 0")
            cursor.execute(f"UPDATE tts_presets SET is_default = 1 {condition}", (param,))
            conn.commit()
    except Exception as e:
        print(f"[WARN] Nao foi possivel configurar preset default: {e}")


# =====================================================================
# Speaker Profiles Persistence APIs
# =====================================================================

def create_speaker_profile(
    name: str,
    mapping: Dict[str, str],
    notes: Optional[str] = None
) -> Optional[int]:
    """Create a new Speaker Profile dictionary mapping."""
    try:
        now_str = datetime.now().isoformat()
        mapping_str = json.dumps(mapping)
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO speaker_profiles (name, mapping_json, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, mapping_str, notes, now_str, now_str))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"[WARN] Nao foi possivel criar perfil '{name}': {e}")
        return None

def update_speaker_profile(
    profile_id_or_name: Union[int, str],
    mapping: Optional[Dict[str, str]] = None,
    notes: Optional[str] = None
) -> None:
    """Update speaker profile mapping or notes."""
    try:
        now_str = datetime.now().isoformat()
        
        updates = ["updated_at = ?"]
        params = [now_str]
        
        if mapping is not None:
            updates.append("mapping_json = ?")
            params.append(json.dumps(mapping))
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
            
        # Determine column condition
        if isinstance(profile_id_or_name, int) or (isinstance(profile_id_or_name, str) and profile_id_or_name.isdigit()):
            condition = "WHERE id = ?"
            params.append(int(profile_id_or_name))
        else:
            condition = "WHERE name = ?"
            params.append(profile_id_or_name)
            
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE speaker_profiles SET {', '.join(updates)} {condition}", tuple(params))
            conn.commit()
    except Exception as e:
        print(f"[WARN] Nao foi possivel atualizar perfil '{profile_id_or_name}': {e}")

def delete_speaker_profile(profile_id_or_name: Union[int, str]) -> None:
    """Delete a speaker profile by ID or UNIQUE name."""
    try:
        if isinstance(profile_id_or_name, int) or (isinstance(profile_id_or_name, str) and profile_id_or_name.isdigit()):
            condition = "WHERE id = ?"
            param = int(profile_id_or_name)
        else:
            condition = "WHERE name = ?"
            param = profile_id_or_name
            
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM speaker_profiles {condition}", (param,))
            conn.commit()
    except Exception as e:
        print(f"[WARN] Nao foi possivel remover perfil '{profile_id_or_name}': {e}")

def list_speaker_profiles() -> List[Dict[str, Any]]:
    """Retrieve all speaker profiles."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM speaker_profiles ORDER BY name ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"[WARN] Nao foi possivel listar perfis: {e}")
        return []

def get_speaker_profile(name_or_id: Union[int, str]) -> Optional[Dict[str, Any]]:
    """Retrieve a single speaker profile by ID or name."""
    try:
        if isinstance(name_or_id, int) or (isinstance(name_or_id, str) and name_or_id.isdigit()):
            condition = "WHERE id = ?"
            param = int(name_or_id)
        else:
            condition = "WHERE name = ?"
            param = name_or_id
            
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM speaker_profiles {condition}", (param,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[WARN] Nao foi possivel obter perfil '{name_or_id}': {e}")
        return None
