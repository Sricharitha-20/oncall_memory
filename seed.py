"""Load past incidents + team conventions into Hindsight. Run once."""
import json
from pathlib import Path

import memory as mem


def main() -> None:
    data = json.loads((Path(__file__).parent / "data" / "incidents.json").read_text())
    client = mem.get_client()
    mem.ensure_bank(client)

    for i, note in enumerate(data["team_notes"]):
        mem.retain_team_note(client, note, i)
        print(f"retained team note {i}")

    for inc in data["incidents"]:
        mem.retain_incident(client, inc)
        print(f"retained {inc['id']} ({inc['service']})")

    print(f"\nDone. {len(data['incidents'])} incidents + {len(data['team_notes'])} team notes in bank '{mem.BANK_ID}'.")


if __name__ == "__main__":
    main()
