import asyncio
import httpx
import json
from adapters.factory import get_adapter_for_company

async def test_all():
    with open("companies.json", "r", encoding="utf-8") as f:
        comps = json.load(f)

    async with httpx.AsyncClient(timeout=12.0) as client:
        for c in comps:
            ad = get_adapter_for_company(c)
            if not ad:
                continue
            try:
                jobs = await ad.fetch_jobs(client)
                if jobs:
                    print(f"[{c['name']}] Found {len(jobs)} recent openings:")
                    for j in jobs[:3]:
                        print(f"   -> {j.title} | {j.location} | {j.age_category} ({j.age_text})")
                else:
                    print(f"[{c['name']}] 0 recent openings")
            except Exception as e:
                print(f"[{c['name']}] Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_all())
