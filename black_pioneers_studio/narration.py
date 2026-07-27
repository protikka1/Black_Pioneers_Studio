from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts


async def generate_narration_async(text: str, voice: str, output_path: Path, rate: str) -> None:
    communication = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communication.save(str(output_path))


def generate_narration(text: str, voice: str, output_path: Path, rate: str) -> None:
    asyncio.run(
        generate_narration_async(
            text=text,
            voice=voice,
            output_path=output_path,
            rate=rate,
        )
    )

