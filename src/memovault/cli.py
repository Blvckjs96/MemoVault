"""CLI entry point for MemoVault."""

import argparse
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
    shell_parser = subparsers.add_parser("shell", help="Interactive shell")

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

    else:
        parser.print_help()
        sys.exit(1)


def run_interactive_shell():
    """Run an interactive shell for MemoVault."""
    from memovault import MemoVault

    print("MemoVault Interactive Shell")
    print("Commands: add <text>, search <query>, chat <message>, list, clear, quit")
    print("-" * 50)

    vault = MemoVault()

    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            parts = user_input.split(" ", 1)
            command = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if command == "quit" or command == "exit":
                print("Goodbye!")
                break

            elif command == "add":
                if not arg:
                    print("Usage: add <memory text>")
                    continue
                ids = vault.add(arg)
                print(f"Added memory: {ids[0]}")

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
                        print(f"  - {preview}")
                    if len(memories) > 10:
                        print(f"  ... and {len(memories) - 10} more")
                else:
                    print("No memories stored")

            elif command == "clear":
                count = vault.count()
                vault.delete_all()
                print(f"Cleared {count} memories")

            elif command == "help":
                print("Commands:")
                print("  add <text>     - Add a memory")
                print("  search <query> - Search memories")
                print("  chat <message> - Chat with memory context")
                print("  list           - List recent memories")
                print("  clear          - Clear all memories")
                print("  quit           - Exit")

            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
