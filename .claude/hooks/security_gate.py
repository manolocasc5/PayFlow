#!/usr/bin/env python3
"""
PreToolUse hook: Security gate para PayFlow API.
Bloquea comandos peligrosos y acceso a archivos sensibles.
Usa JSON decision control (permissionDecision) para dar razones claras.

Cross-platform: cubre tanto la herramienta Bash (Git Bash en Windows, o
Unix/macOS) como la herramienta PowerShell (Windows nativo sin Git for Windows,
o con la herramienta PowerShell habilitada) y comandos CMD.
"""
import sys
import json
import re


def check_shell_command(cmd: str) -> tuple[bool, str]:
    """Verifica si un comando de shell es seguro. Retorna (bloqueado, razón)."""
    dangerous_patterns = [
        # --- Borrado destructivo ---
        (r"rm\s+(-[rf]+\s+|.*--no-preserve-root)", "Borrado recursivo/forzado (Unix)"),
        (r"\b(Remove-Item|rm|del|erase|rd|rmdir)\b.*(-Recurse|-Force|/s\b|/q\b)",
         "Borrado recursivo/forzado (PowerShell/CMD)"),
        # --- Git destructivo (cross-platform) ---
        (r"git\s+(reset\s+--hard|push\s+(-f|--force))", "Operación git destructiva"),
        # --- Elevación de privilegios ---
        (r"\bsudo\s+", "Ejecución con privilegios elevados (Unix)"),
        (r"Start-Process\b.*-Verb\s+RunAs", "Elevación de privilegios (PowerShell)"),
        # --- Permisos excesivos ---
        (r"chmod\s+777", "Permisos excesivamente permisivos (Unix)"),
        (r"icacls\b.*/grant\b.*(Everyone|Todos).*(:F|FullControl)",
         "Permisos totales a Everyone (Windows)"),
        # --- Descarga + ejecución remota ---
        (r"(curl|wget)\b.*\|\s*(ba)?sh", "Ejecución de script remoto por pipe (Unix)"),
        (r"\b(irm|iwr|Invoke-RestMethod|Invoke-WebRequest|curl|wget)\b.*\|\s*(iex|Invoke-Expression)\b",
         "Descarga y ejecución remota (PowerShell)"),
        # --- SQL destructivo (cross-platform) ---
        (r"DROP\s+(TABLE|DATABASE)", "Borrado de estructura de BD"),
        (r"DELETE\s+FROM\s+\w+\s*;?\s*$", "DELETE sin WHERE"),
    ]
    for pattern, reason in dangerous_patterns:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True, reason

    sensitive_files = [
        ".env", ".env.local", ".env.production",
        "id_rsa", "id_ed25519", ".pem", ".key",
    ]
    for f in sensitive_files:
        if f in cmd:
            return True, f"Acceso a archivo sensible: {f}"

    prod_patterns = [
        (r"(psql|mysql|mongo).*prod", "Cliente de BD apuntando a producción"),
        (r"ssh.*prod", "SSH a servidor de producción"),
    ]
    for pattern, reason in prod_patterns:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True, reason

    return False, ""


def check_file_write(file_path: str) -> tuple[bool, str]:
    """Verifica si la escritura a un archivo es segura. Acepta separadores / y \\."""
    protected = [
        (r"\.env($|\.)", "Archivo de variables de entorno"),
        (r"(id_rsa|id_ed25519|\.pem|\.key)$", "Archivo de claves privadas"),
        (r"alembic[\\/]versions[\\/].*\.py$", "Migración de BD (requiere revisión manual)"),
    ]
    for pattern, reason in protected:
        if re.search(pattern, file_path, re.IGNORECASE):
            return True, reason
    return False, ""


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Payload ilegible: no bloqueamos para no romper la sesión.
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    blocked = False
    reason = ""

    # Tanto la herramienta Bash (Git Bash) como la herramienta PowerShell
    # entregan el comando en el campo "command".
    if tool_name in ("Bash", "PowerShell"):
        blocked, reason = check_shell_command(tool_input.get("command", ""))
    elif tool_name in ("Write", "Edit", "MultiEdit"):
        blocked, reason = check_file_write(tool_input.get("file_path", ""))

    if blocked:
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Bloqueado por política de seguridad: {reason}"
            }
        }, sys.stdout)

    sys.exit(0)


if __name__ == "__main__":
    main()
