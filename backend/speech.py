import ctypes
import os
import time

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from faster_whisper import WhisperModel

load_dotenv()

whisper_model = WhisperModel(
    model_size_or_path="base",
    device="auto",
    compute_type="default",
    use_auth_token=os.getenv("HF_TOKEN") or None,
)

SAMPLE_RATE = 16_000
VK_SPACE = 0x20


def space_held() -> bool:
    return bool(ctypes.windll.user32.GetAsyncKeyState(VK_SPACE) & 0x8000)


def record_while_space_held() -> np.ndarray:
    while space_held():
        time.sleep(0.02)
    print("Hold Space and speak. Release Space to write the query.")

    chunks: list[np.ndarray] = []
    recording = False

    def on_audio(indata: np.ndarray, _frames: int, _time_info, _status) -> None:
        if recording:
            chunks.append(indata.copy())

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        callback=on_audio,
    ):
        while not space_held():
            time.sleep(0.02)
        recording = True
        print("Listening...")
        while space_held():
            time.sleep(0.02)
        recording = False

    if not chunks:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(chunks).reshape(-1)


def transcribe_audio(audio: str | np.ndarray, *, vad_filter: bool = False) -> str:
    segments, _info = whisper_model.transcribe(audio, vad_filter=vad_filter)
    return "".join(segment.text for segment in segments).strip()


def listen_for_query() -> str:
    audio = record_while_space_held()
    if audio.size == 0:
        return ""
    return transcribe_audio(audio, vad_filter=True)
