"""Quickstart example for MemoVault."""

from memovault import MemoVault


def main():
    """Demonstrate basic MemoVault usage."""
    print("MemoVault Quickstart Example")
    print("=" * 50)

    # Initialize MemoVault (uses environment variables or defaults)
    mem = MemoVault()

    # Add some memories
    print("\n1. Adding memories...")
    mem.add("I prefer Python for backend development")
    mem.add("My favorite color is blue")
    mem.add("I have a project deadline on March 15th")
    mem.add("I'm learning about machine learning")
    print(f"   Added 4 memories. Total: {mem.count()}")

    # Search for memories
    print("\n2. Searching for 'programming preferences'...")
    results = mem.search("programming preferences")
    for result in results:
        print(f"   - {result.memory}")

    # Chat with memory context
    print("\n3. Chatting with memory context...")
    response = mem.chat("What programming language should I use for my backend?")
    print(f"   Response: {response[:200]}...")

    # Get all memories
    print("\n4. Listing all memories...")
    all_memories = mem.get_all()
    for m in all_memories:
        print(f"   [{m.id[:8]}...] {m.memory}")

    # Save memories to disk
    print("\n5. Saving memories to ./my_memories...")
    mem.dump("./my_memories")
    print("   Done!")

    # Clean up
    print("\n6. Clearing memories...")
    mem.delete_all()
    print(f"   Memories remaining: {mem.count()}")

    print("\n" + "=" * 50)
    print("Quickstart complete!")


if __name__ == "__main__":
    main()
