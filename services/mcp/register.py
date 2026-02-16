"""Auto-register Vimix MCP server in all detected AI agent configurations.

Supports JSON and TOML config formats. Each agent provider is defined
declaratively — just add a new entry to PROVIDERS to support a new agent.

Usage:
    python register.py              # register in all detected agents
    python register.py --port 9999  # custom MCP port
    python register.py --remove     # unregister from all agents
"""

from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("vimix.mcp.register")

DEFAULT_MCP_PORT = 8788
MCP_SERVER_NAME = "vimix"


# ---------------------------------------------------------------------------
# Provider definitions
# ---------------------------------------------------------------------------


@dataclass
class AgentProvider:
    """Declarative definition for an AI agent that supports MCP.

    To add a new agent, append an AgentProvider to PROVIDERS below.

    Fields:
        name:         Human-readable agent name (for logs).
        config_path:  Path to the config file. Supports ~ for home dir.
                      Use a callable returning str for platform-specific paths.
        servers_key:  Top-level JSON key that holds MCP servers (e.g. "mcpServers").
        entry_builder: Callable that receives the MCP URL and returns the dict
                      to store under servers_key["vimix"].
        detect_hint:  Optional path (dir or file) that hints the agent is installed.
                      If the hint doesn't exist, registration is skipped.
        format:       Config file format: "json" or "toml".
    """

    name: str
    config_path: str | callable
    servers_key: str
    entry_builder: callable  # (url: str) -> dict
    detect_hint: str | None = None
    format: str = "json"

    def resolve_config_path(self) -> Path:
        raw = self.config_path() if callable(self.config_path) else self.config_path
        return Path(raw).expanduser()

    def resolve_detect_hint(self) -> Path | None:
        if self.detect_hint is None:
            return None
        return Path(self.detect_hint).expanduser()


# -- Entry builders (what goes into the config under "vimix") ---------------

def _entry_standard(url: str) -> dict:
    """Most agents: just a url field."""
    return {"url": url}


def _entry_claude_code(url: str) -> dict:
    """Claude Code: type=http for streamable HTTP."""
    return {"type": "http", "url": url}


def _entry_windsurf(url: str) -> dict:
    """Windsurf uses serverUrl instead of url."""
    return {"serverUrl": url}


def _entry_opencode(url: str) -> dict:
    """OpenCode uses type=remote + url."""
    return {"type": "remote", "url": url}


def _entry_vscode(url: str) -> dict:
    """VS Code: type=sse triggers streamable HTTP with SSE fallback."""
    return {"type": "sse", "url": url}


# -- Platform-specific config paths ----------------------------------------

def _vscode_config_path() -> str:
    if sys.platform == "darwin":
        return "~/Library/Application Support/Code/User/mcp.json"
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return str(Path(appdata) / "Code" / "User" / "mcp.json")
    else:
        return "~/.config/Code/User/mcp.json"


def _vscode_detect_hint() -> str:
    if sys.platform == "darwin":
        return "~/Library/Application Support/Code"
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return str(Path(appdata) / "Code")
    else:
        return "~/.config/Code"


# -- Provider registry ------------------------------------------------------
# Add new agents here. That's all you need to do to support a new agent.

PROVIDERS: list[AgentProvider] = [
    AgentProvider(
        name="Claude Code",
        config_path="~/.claude.json",
        servers_key="mcpServers",
        entry_builder=_entry_claude_code,
        detect_hint="~/.claude",
    ),
    AgentProvider(
        name="Cursor",
        config_path="~/.cursor/mcp.json",
        servers_key="mcpServers",
        entry_builder=_entry_standard,
    ),
    AgentProvider(
        name="Windsurf",
        config_path="~/.codeium/windsurf/mcp_config.json",
        servers_key="mcpServers",
        entry_builder=_entry_windsurf,
    ),
    AgentProvider(
        name="OpenCode",
        config_path="~/.config/opencode/opencode.json",
        servers_key="mcp",
        entry_builder=_entry_opencode,
    ),
    AgentProvider(
        name="Gemini CLI",
        config_path="~/.gemini/settings.json",
        servers_key="mcpServers",
        entry_builder=_entry_standard,
    ),
    AgentProvider(
        name="Kiro",
        config_path="~/.kiro/settings/mcp.json",
        servers_key="mcpServers",
        entry_builder=_entry_standard,
    ),
    AgentProvider(
        name="Copilot CLI",
        config_path="~/.copilot/mcp-config.json",
        servers_key="mcpServers",
        entry_builder=_entry_standard,
    ),
    AgentProvider(
        name="Antigravity",
        config_path="~/.gemini/antigravity/mcp_config.json",
        servers_key="mcpServers",
        entry_builder=_entry_standard,
    ),
    AgentProvider(
        name="VS Code",
        config_path=_vscode_config_path,
        servers_key="servers",
        entry_builder=_entry_vscode,
        detect_hint=_vscode_detect_hint(),
    ),
    AgentProvider(
        name="Codex CLI",
        config_path="~/.codex/config.toml",
        servers_key="mcp_servers",
        entry_builder=_entry_standard,
        format="toml",
    ),
]


# ---------------------------------------------------------------------------
# Registration logic
# ---------------------------------------------------------------------------


def _is_installed(provider: AgentProvider) -> bool:
    """Check if the agent appears to be installed on this machine."""
    config_path = provider.resolve_config_path()

    # Config file already exists → definitely installed
    if config_path.is_file():
        return True

    # Check the detect hint
    hint = provider.resolve_detect_hint()
    if hint is not None:
        return hint.exists()

    # Fallback: check if the config's parent dir exists (skip if it's home)
    parent = config_path.parent
    if parent == Path.home():
        return False
    return parent.is_dir()


def _register_json(provider: AgentProvider, mcp_url: str) -> bool:
    """Register Vimix in a JSON config file. Returns True if changed."""
    config_path = provider.resolve_config_path()

    if config_path.is_file():
        try:
            text = config_path.read_text(encoding="utf-8").strip()
            config = json.loads(text) if text else {}
        except (json.JSONDecodeError, OSError):
            logger.warning("Could not parse %s, skipping %s", config_path, provider.name)
            return False
    else:
        config = {}

    servers = config.setdefault(provider.servers_key, {})
    expected = provider.entry_builder(mcp_url)

    if servers.get(MCP_SERVER_NAME) == expected:
        return False  # already registered with correct config

    servers[MCP_SERVER_NAME] = expected

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return True


def _remove_json(provider: AgentProvider) -> bool:
    """Remove Vimix from a JSON config file. Returns True if changed."""
    config_path = provider.resolve_config_path()
    if not config_path.is_file():
        return False

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    servers = config.get(provider.servers_key, {})
    if MCP_SERVER_NAME not in servers:
        return False

    del servers[MCP_SERVER_NAME]
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return True


def _register_toml(provider: AgentProvider, mcp_url: str) -> bool:
    """Register Vimix in a TOML config file (Codex). Returns True if changed."""
    config_path = provider.resolve_config_path()
    if not config_path.parent.is_dir():
        return False

    content = ""
    if config_path.is_file():
        content = config_path.read_text(encoding="utf-8")

    toml_section = f"[{provider.servers_key}.{MCP_SERVER_NAME}]"
    expected_line = f'url = "{mcp_url}"'

    if toml_section in content:
        if expected_line in content:
            return False  # already registered with correct URL
        # URL changed — remove old entry first, then re-add
        _remove_toml(provider)
        content = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""

    entry = f'\n{toml_section}\n{expected_line}\n'
    config_path.write_text(content + entry, encoding="utf-8")
    return True


def _remove_toml(provider: AgentProvider) -> bool:
    """Remove Vimix from a TOML config file. Returns True if changed."""
    config_path = provider.resolve_config_path()
    if not config_path.is_file():
        return False

    content = config_path.read_text(encoding="utf-8")
    toml_section = f"[{provider.servers_key}.{MCP_SERVER_NAME}]"
    if toml_section not in content:
        return False

    # Remove the section and its key-value lines
    lines = content.split("\n")
    new_lines: list[str] = []
    skip = False
    for line in lines:
        if line.strip() == toml_section:
            skip = True
            continue
        if skip and (line.startswith("[") or line.strip() == ""):
            skip = False
            if line.strip() == "":
                continue
        if not skip:
            new_lines.append(line)

    config_path.write_text("\n".join(new_lines), encoding="utf-8")
    return True


def ensure_registered(port: int = DEFAULT_MCP_PORT) -> dict[str, str]:
    """Register Vimix MCP in all detected agent configurations.

    Returns a dict mapping agent name to status:
    "registered", "already_registered", "not_installed", or "error".
    """
    mcp_url = f"http://localhost:{port}/mcp"
    results: dict[str, str] = {}

    for provider in PROVIDERS:
        if not _is_installed(provider):
            results[provider.name] = "not_installed"
            continue

        try:
            if provider.format == "toml":
                changed = _register_toml(provider, mcp_url)
            else:
                changed = _register_json(provider, mcp_url)

            results[provider.name] = "registered" if changed else "already_registered"
            if changed:
                logger.info("Registered Vimix MCP in %s", provider.name)
        except OSError as exc:
            results[provider.name] = "error"
            logger.warning("Failed to register in %s: %s", provider.name, exc)

    return results


def ensure_removed() -> dict[str, str]:
    """Remove Vimix MCP from all agent configurations.

    Returns a dict mapping agent name to status:
    "removed", "not_present", or "error".
    """
    results: dict[str, str] = {}

    for provider in PROVIDERS:
        try:
            if provider.format == "toml":
                changed = _remove_toml(provider)
            else:
                changed = _remove_json(provider)

            results[provider.name] = "removed" if changed else "not_present"
            if changed:
                logger.info("Removed Vimix MCP from %s", provider.name)
        except OSError as exc:
            results[provider.name] = "error"
            logger.warning("Failed to remove from %s: %s", provider.name, exc)

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(description="Register/unregister Vimix MCP in AI agents")
    parser.add_argument("--port", type=int, default=DEFAULT_MCP_PORT, help="MCP server port")
    parser.add_argument("--remove", action="store_true", help="Remove Vimix from all agents")
    args = parser.parse_args()

    if args.remove:
        results = ensure_removed()
    else:
        results = ensure_registered(port=args.port)

    for name, status in results.items():
        icon = {"registered": "+", "removed": "-", "already_registered": "=",
                "not_present": "=", "not_installed": " ", "error": "!"}
        print(f"  [{icon.get(status, '?')}] {name}: {status}")
