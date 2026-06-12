"""YouTube audio download and transcription pipeline."""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import ffmpeg
import pytubefix

from src.core.transcriber import transcribe, transcribe_async
from src.core.cloudflare import Cloudflare


def extract_audio(url: str, output_dir: str | Path) -> str:
    yt = pytubefix.YouTube(url)
    stream = yt.streams.filter(only_audio=True).first()
    if not stream:
        raise ValueError(f"No audio stream found for {url}")

    temp_dir = tempfile.mkdtemp()
    out_path = os.path.join(str(output_dir), f"{yt.video_id}.wav")
    try:
        downloaded = stream.download(output_path=temp_dir)
        ffmpeg.input(downloaded).output(
            out_path,
            format="wav",
            acodec="pcm_s16le",
            ar="16000",
            ac=1,
            loglevel="error",
        ).run(overwrite_output=True)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return out_path


def transcribe_youtube(url: str, cf: Optional[Cloudflare] = None) -> str:
    temp_dir = tempfile.mkdtemp()
    try:
        wav = extract_audio(url, temp_dir)
        return transcribe(wav, cf)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def transcribe_youtube_async(url: str, cf: Optional[Cloudflare] = None) -> str:
    """Async variant — runs the full download+transcribe pipeline in a thread pool."""
    return await asyncio.to_thread(transcribe_youtube, url, cf)
