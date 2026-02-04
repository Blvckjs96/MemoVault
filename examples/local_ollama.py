"""Example using MemoVault with local Ollama backend."""

import os

# Set environment variables for Ollama
os.environ["MEMOVAULT_LLM_BACKEND"] = "ollama"
os.environ["MEMOVAULT_OLLAMA_MODEL"] = "llama3.1:latest"
os.environ["MEMOVAULT_EMBEDDER_BACKEND"] = "ollama"
os.environ["MEMOVAULT_EMBEDDER_OLLAMA_MODEL"] = "nomic-embed-text:latest"

from memovault import MemoVault


def main():
    """Demonstrate MemoVault with local Ollama."""
    print("MemoVault with Local Ollama")
    print("=" * 50)
    print("\nNote: Make sure Ollama is running locally!")
    print("      ollama serve\n")

    # Initialize MemoVault with Ollama
    mem = MemoVault()

    # Add memories
    print("Adding memories...")
    mem.add("I prefer dark mode in all my applications")
    mem.add("I usually code in VS Code")
    mem.add("I'm working on a machine learning project")

    print(f"Total memories: {mem.count()}")

    # Search
    print("\nSearching for 'coding setup'...")
    results = mem.search("coding setup")
    for r in results:
        print(f"  - {r.memory}")

    # Chat
    print("\nAsking about preferred settings...")
    response = mem.chat("What IDE and theme should I use?")
    print(f"Response: {response}")

    # Clean up
    mem.delete_all()
    print("\nCleaned up memories.")


if __name__ == "__main__":
    main()
