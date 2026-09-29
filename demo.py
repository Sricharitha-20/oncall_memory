"""Terminal demo: same alert, without vs with memory. Good for screen recording."""
import memory as mem
from agent import triage_with_memory, triage_without_memory

ALERT = (
    "checkout-api p99 latency 8.2s, error rate 14%. DB connection count at 100% of pool. "
    "Started ~10 minutes after deploy v2.31 of checkout-api."
)

if __name__ == "__main__":
    client = mem.get_client()
    print("=" * 70, "\nALERT:", ALERT, "\n" + "=" * 70)
    print("\n### WITHOUT MEMORY\n")
    print(triage_without_memory(ALERT))
    print("\n### WITH HINDSIGHT MEMORY\n")
    result = triage_with_memory(client, ALERT)
    print(result["answer"])
    print(f"\n({len(result['memories'])} memories recalled)")
