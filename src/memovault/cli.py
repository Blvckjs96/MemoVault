"""CLI entry point for MemoVault."""

import argparse
import json
import sys


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MemoVault - A personal memory system for AI assistants"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # MCP server command
    mcp_parser = subparsers.add_parser("mcp", help="Run MCP server for Claude Code")
    mcp_parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport method (default: stdio)",
    )
    mcp_parser.add_argument("--host", default="localhost", help="Host for HTTP/SSE")
    mcp_parser.add_argument("--port", type=int, default=8000, help="Port for HTTP/SSE")

    # REST API command
    api_parser = subparsers.add_parser("api", help="Run REST API server")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    api_parser.add_argument("--port", type=int, default=8080, help="Port to bind to")

    # Interactive shell command
    subparsers.add_parser("shell", help="Interactive shell")

    # Profile commands
    profile_parser = subparsers.add_parser("profile", help="Manage user profile")
    profile_sub = profile_parser.add_subparsers(dest="profile_command")
    profile_sub.add_parser("show", help="Show current profile")
    set_parser = profile_sub.add_parser("set", help="Set a profile field")
    set_parser.add_argument("field", help="Field name")
    set_parser.add_argument("value", help="Field value")

    # Session commands
    session_parser = subparsers.add_parser("session", help="Manage sessions")
    session_sub = session_parser.add_subparsers(dest="session_command")
    session_sub.add_parser("start", help="Start a new session")
    session_sub.add_parser("end", help="End current session")

    # Plugin commands
    plugin_parser = subparsers.add_parser("plugins", help="Manage IDE/CLI integrations")
    plugin_sub = plugin_parser.add_subparsers(dest="plugin_command")

    install_p = plugin_sub.add_parser("install", help="Install hooks for a platform")
    install_p.add_argument("platform", help="Platform name (claude-code, cursor, gemini, codex)")
    install_p.add_argument("--api", default="http://localhost:8080", help="MemoVault REST API URL")

    uninstall_p = plugin_sub.add_parser("uninstall", help="Remove hooks for a platform")
    uninstall_p.add_argument("platform", help="Platform name")

    plugin_sub.add_parser("list", help="List all platforms and their status")

    # Hook handler (called by installed hooks)
    hook_parser = subparsers.add_parser("hook", help="Internal hook handler (called by IDE hooks)")
    hook_sub = hook_parser.add_subparsers(dest="hook_event")

    ps_hook = hook_sub.add_parser("prompt-submit", help="UserPromptSubmit handler")
    ps_hook.add_argument("--api", default="http://localhost:8080", help="MemoVault REST API URL")
    ps_hook.add_argument("--top-k", type=int, default=5, help="Number of memories to inject")

    se_hook = hook_sub.add_parser("session-end", help="Stop/session-end handler")
    se_hook.add_argument("--api", default="http://localhost:8080", help="MemoVault REST API URL")

    # Service commands (background daemon for REST API)
    svc_parser = subparsers.add_parser("service", help="Manage the MemoVault background API service")
    svc_sub = svc_parser.add_subparsers(dest="service_command")
    svc_start = svc_sub.add_parser("start", help="Start REST API in background")
    svc_start.add_argument("--host", default="0.0.0.0")
    svc_start.add_argument("--port", type=int, default=8080)
    svc_sub.add_parser("stop", help="Stop the background service")
    svc_sub.add_parser("status", help="Show service status")

    args = parser.parse_args()

    if args.command == "mcp":
        from memovault.api.mcp import MemoVaultMCPServer

        server = MemoVaultMCPServer()
        server.run(transport=args.transport, host=args.host, port=args.port)

    elif args.command == "api":
        from memovault.api.rest import run_server

        run_server(host=args.host, port=args.port)

    elif args.command == "shell":
        run_interactive_shell()

    elif args.command == "profile":
        run_profile_command(args)

    elif args.command == "session":
        run_session_command(args)

    elif args.command == "plugins":
        run_plugin_command(args)

    elif args.command == "hook":
        run_hook_command(args)

    elif args.command == "service":
        run_service_command(args)

    else:
        parser.print_help()
        sys.exit(1)


def run_profile_command(args):
    """Handle profile subcommands."""
    from memovault import MemoVault

    vault = MemoVault()

    if args.profile_command == "show":
        profile = vault.get_profile()
        print(json.dumps(profile, indent=2))

    elif args.profile_command == "set":
        # Try to parse value as JSON for complex types (lists, dicts)
        try:
            value = json.loads(args.value)
        except (json.JSONDecodeError, TypeError):
            value = args.value

        vault.update_profile(args.field, value)
        print(f"Profile field '{args.field}' updated to: {value}")

    else:
        print("Usage: memovault profile {show|set}")
        sys.exit(1)


def run_session_command(args):
    """Handle session subcommands."""
    from memovault import MemoVault

    vault = MemoVault()

    if args.session_command == "start":
        context = vault.get_session_context()
        if context["profile"]:
            print(f"Profile: {context['profile']}")
        if context["recap"]:
            print("\nRecent sessions:")
            for s in context["recap"]:
                print(f"  - {s}")
        print("\nSession started.")

    elif args.session_command == "end":
        summary = vault.end_session()
        if summary:
            print(f"Session ended. Summary:\n{summary}")
        else:
            print("No chat history to summarize.")

    else:
        print("Usage: memovault session {start|end}")
        sys.exit(1)


def run_interactive_shell():
    """Run an interactive shell for MemoVault."""
    from memovault import MemoVault

    print("MemoVault Interactive Shell")
    print("Commands: add, search, chat, list, clear, profile, session, consolidate, quit")
    print("-" * 60)

    vault = MemoVault()

    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            parts = user_input.split(" ", 1)
            command = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if command in ("quit", "exit"):
                print("Goodbye!")
                break

            elif command == "add":
                if not arg:
                    print("Usage: add <memory text>")
                    continue
                ids = vault.add(arg)
                if ids:
                    print(f"Added memory: {ids[0]}")
                else:
                    print("Memory not stored (below importance threshold)")

            elif command == "search":
                if not arg:
                    print("Usage: search <query>")
                    continue
                results = vault.search(arg)
                if results:
                    print(f"Found {len(results)} memories:")
                    for mem in results:
                        print(f"  - {mem.memory}")
                else:
                    print("No memories found")

            elif command == "chat":
                if not arg:
                    print("Usage: chat <message>")
                    continue
                response = vault.chat(arg)
                print(f"\nAssistant: {response}")

            elif command == "list":
                memories = vault.get_all()
                if memories:
                    print(f"Total memories: {len(memories)}")
                    for mem in memories[:10]:
                        preview = mem.memory[:80] + "..." if len(mem.memory) > 80 else mem.memory
                        t = f" [{mem.metadata.type}]" if mem.metadata.type else ""
                        print(f"  - {preview}{t}")
                    if len(memories) > 10:
                        print(f"  ... and {len(memories) - 10} more")
                else:
                    print("No memories stored")

            elif command == "clear":
                count = vault.count()
                vault.delete_all()
                print(f"Cleared {count} memories")

            elif command == "profile":
                if arg.startswith("set "):
                    field_val = arg[4:].split(" ", 1)
                    if len(field_val) == 2:
                        vault.update_profile(field_val[0], field_val[1])
                        print(f"Profile '{field_val[0]}' updated")
                    else:
                        print("Usage: profile set <field> <value>")
                else:
                    profile = vault.get_profile()
                    print(json.dumps(profile, indent=2))

            elif command == "session":
                if arg == "end":
                    summary = vault.end_session()
                    if summary:
                        print(f"Session ended. Summary:\n{summary}")
                    else:
                        print("No chat history to summarize")
                elif arg == "start":
                    ctx = vault.get_session_context()
                    if ctx["profile"]:
                        print(f"Profile: {ctx['profile']}")
                    if ctx["recap"]:
                        print("Recent sessions:")
                        for s in ctx["recap"]:
                            print(f"  - {s}")
                    print("Session started.")
                else:
                    print("Usage: session {start|end}")

            elif command == "consolidate":
                result = vault.consolidate_memories()
                print(
                    f"Consolidated: {result['merged_groups']} groups merged, "
                    f"{result['total_removed']} duplicates removed"
                )

            elif command == "help":
                print("Commands:")
                print("  add <text>          - Add a memory")
                print("  search <query>      - Search memories")
                print("  chat <message>      - Chat with memory context")
                print("  list                - List recent memories")
                print("  clear               - Clear all memories")
                print("  profile             - Show user profile")
                print("  profile set <f> <v> - Set profile field")
                print("  session start       - Start session with context")
                print("  session end         - End session with summary")
                print("  consolidate         - Merge duplicate memories")
                print("  quit                - Exit")

            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def run_plugin_command(args):
    """Handle `memovault plugins` subcommands."""
    from memovault.plugins.installer import PluginInstaller, list_platforms

    if args.plugin_command == "list":
        api_url = getattr(args, "api", "http://localhost:8080")
        installer = PluginInstaller(api_url=api_url)
        rows = installer.status_all()
        print(f"{'Platform':<16} {'Detected':<10} {'Installed':<10} Description")
        print("─" * 72)
        for r in rows:
            detected = "yes" if r["detected"] else "no"
            installed = "yes" if r.get("installed") else "no"
            print(f"{r['platform']:<16} {detected:<10} {installed:<10} {r['description']}")

    elif args.plugin_command == "install":
        installer = PluginInstaller(api_url=args.api)
        installer.install(args.platform)
        print(f"\nDone. MemoVault hooks installed for {args.platform}.")
        print("Make sure the REST API is running:  memovault service start")

    elif args.plugin_command == "uninstall":
        installer = PluginInstaller()
        installer.uninstall(args.platform)

    else:
        print("Usage: memovault plugins {list|install <platform>|uninstall <platform>}")
        print(f"Available platforms: {', '.join(list_platforms())}")
        sys.exit(1)


def _assert_localhost_url(url: str) -> str:
    """Raise SystemExit if the URL is not a localhost address.

    Prevents SSRF — a modified settings file or malicious CLI argument
    could redirect hook traffic to an attacker-controlled server.
    """
    import os
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        print(f"[memovault] Blocked: api URL must use http or https ({url!r})", file=sys.stderr)
        sys.exit(1)
    allowed_hosts = {"localhost", "127.0.0.1", "::1"}
    if parsed.hostname not in allowed_hosts:
        # Allow override for intentional remote deployments
        if not os.environ.get("MEMOVAULT_ALLOW_REMOTE_API"):
            print(
                f"[memovault] Blocked: api URL must point to localhost, got {parsed.hostname!r}. "
                "Set MEMOVAULT_ALLOW_REMOTE_API=1 to allow remote URLs.",
                file=sys.stderr,
            )
            sys.exit(1)
    return url


def run_hook_command(args):
    """Handle `memovault hook` events dispatched by IDE hooks.

    prompt-submit: reads prompt from stdin (JSON or plain text),
    searches relevant memories, prints context block to stdout so
    the IDE prepends it to the user prompt.

    session-end: calls POST /session/end on the REST API.
    """
    import urllib.error
    import urllib.parse
    import urllib.request

    _assert_localhost_url(args.api)

    if args.hook_event == "prompt-submit":
        import sys as _sys

        raw = _sys.stdin.read().strip()
        # Claude Code sends JSON: {"prompt": "...", ...}
        try:
            payload = json.loads(raw)
            prompt = payload.get("prompt") or payload.get("content") or raw
        except (json.JSONDecodeError, AttributeError):
            prompt = raw

        if not prompt:
            return

        try:
            encoded_query = urllib.parse.quote(prompt[:512])
            url = f"{args.api}/session/context?query={encoded_query}&top_k={args.top_k}"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())

            sections = []
            recap = data.get("recap", [])
            if recap:
                lines = "\n".join(f"- {s}" for s in recap)
                sections.append(f"[Prior sessions]\n{lines}")

            facts = data.get("relevant_facts", [])
            if facts:
                lines = "\n".join(f"- {f}" for f in facts)
                sections.append(f"[Relevant memories]\n{lines}")

            if sections:
                print("[MemoVault context]\n" + "\n\n".join(sections) + "\n")
        except Exception:
            pass  # hooks must never block the IDE

    elif args.hook_event == "session-end":
        try:
            req = urllib.request.Request(
                f"{args.api}/session/end",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            if data.get("summary"):
                print(f"[MemoVault] Session saved: {data['summary'][:120]}")
        except Exception:
            pass

    else:
        print("Usage: memovault hook {prompt-submit|session-end}")
        sys.exit(1)


def run_service_command(args):
    """Manage the MemoVault REST API background daemon."""
    import os
    import signal
    import subprocess
    from pathlib import Path

    pid_file = Path.home() / ".memovault" / "api.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)

    if args.service_command == "start":
        if pid_file.exists():
            pid = int(pid_file.read_text().strip())
            try:
                os.kill(pid, 0)
                print(f"Service already running (PID {pid}). Use `memovault service stop` first.")
                return
            except ProcessLookupError:
                pid_file.unlink()

        proc = subprocess.Popen(
            ["memovault", "api", "--host", args.host, "--port", str(args.port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        pid_file.write_text(str(proc.pid))
        print(f"MemoVault API started (PID {proc.pid}) on http://{args.host}:{args.port}")
        print(f"Dashboard: http://localhost:{args.port}/ui")

    elif args.service_command == "stop":
        if not pid_file.exists():
            print("Service is not running.")
            return
        pid = int(pid_file.read_text().strip())
        try:
            os.kill(pid, signal.SIGTERM)
            pid_file.unlink()
            print(f"Service stopped (PID {pid})")
        except ProcessLookupError:
            pid_file.unlink()
            print("Service was not running (stale PID file removed)")

    elif args.service_command == "status":
        if not pid_file.exists():
            print("Service: stopped")
            return
        pid = int(pid_file.read_text().strip())
        try:
            os.kill(pid, 0)
            print(f"Service: running (PID {pid})")
        except ProcessLookupError:
            pid_file.unlink()
            print("Service: stopped (stale PID file removed)")

    else:
        print("Usage: memovault service {start|stop|status}")
        sys.exit(1)


if __name__ == "__main__":
    main()
