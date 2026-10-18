import os
import asyncio
import logging
import tempfile
from pathlib import Path
from config.settings import settings

logger = logging.getLogger("stt_service")

async def convert_to_wav(input_path: str, output_path: str) -> bool:
    """ffmpeg yordamida audio faylni 16kHz mono WAV formatiga o'tkazish"""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        output_path
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        return proc.returncode == 0
    except Exception as e:
        logger.error(f"ffmpeg konvertatsiyasida xatolik: {e}")
        return False

async def transcribe_with_groq(file_path: str, api_key: str) -> str | None:
    """Groq Whisper-large-v3 orqali o'zbek tilidagi ovozni matnga o'girish"""
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=api_key)
        
        with open(file_path, "rb") as audio_file:
            response = await client.audio.transcriptions.create(
                file=(Path(file_path).name, audio_file.read()),
                model="whisper-large-v3",
                language="uz",
                response_format="text"
            )
        text = str(response).strip()
        logger.info(f"Groq STT muvaffaqiyatli yakunlandi: {text[:50]}...")
        return text
    except Exception as e:
        logger.warning(f"Groq orqali ovozni aniqlashda xatolik: {e}. Google STT ga o'tilmoqda...")
        return None

async def transcribe_with_google(wav_path: str) -> str | None:
    """Google Speech Recognition (uz-UZ) orqali ovozni matnga o'girish"""
    import speech_recognition as sr
    recognizer = sr.Recognizer()

    def _recognize():
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            return recognizer.recognize_google(audio_data, language="uz-UZ")

    try:
        text = await asyncio.to_thread(_recognize)
        logger.info(f"Google STT muvaffaqiyatli yakunlandi: {text[:50]}...")
        return str(text).strip()
    except sr.UnknownValueError:
        logger.info("Google STT audio ichida nutqni aniqlay olmadi.")
        return None
    except sr.RequestError as e:
        logger.error(f"Google STT server xatosi: {e}")
        return None
    except Exception as e:
        logger.error(f"Google STT kutilmagan xato: {e}")
        return None

async def transcribe_voice(file_path: str) -> str | None:
    """
    Ovozli faylni qabul qilib, o'zbekcha matnga o'giradi.
    1. Agar GROQ_API_KEY bo'lsa, birinchi navbatda Groq Whisper-large-v3 ishlatiladi.
    2. Aks holda yoki xatolik yuz bersa, Google Speech Recognition (uz-UZ) ga o'tadi.
    """
    # 1. Groq tekshiruvi
    if settings.GROQ_API_KEY:
        groq_result = await transcribe_with_groq(file_path, settings.GROQ_API_KEY)
        if groq_result:
            return groq_result

    # 2. WAV ga o'girish va Google STT
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_wav_path = temp_wav.name

    try:
        converted = await convert_to_wav(file_path, temp_wav_path)
        if not converted:
            logger.error("Audio faylni WAV ga o'tkazib bo'lmadi.")
            return None

        google_result = await transcribe_with_google(temp_wav_path)
        return google_result
    finally:
        if os.path.exists(temp_wav_path):
            try:
                os.remove(temp_wav_path)
            except OSError:
                pass
