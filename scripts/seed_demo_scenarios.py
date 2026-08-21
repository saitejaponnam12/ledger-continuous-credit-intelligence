"""
LEDGER — Seed 5 Demo Scenarios
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.database import AsyncSessionLocal
from app.api.demo import _load_demo_personas, _seed_demo_persona


async def seed_scenarios():
    async with AsyncSessionLocal() as session:
        personas = _load_demo_personas()
        print(f"Seeding {len(personas)} demo personas...")
        for persona in personas:
            app_id = await _seed_demo_persona(session, persona)
            print(f"  [SEEDED] {persona['display_name']} ({persona['persona_tag']}) -> App ID: {app_id}")
        await session.commit()
        print("\n[SUCCESS] All 5 demo scenarios seeded and scored!")


if __name__ == "__main__":
    asyncio.run(seed_scenarios())
