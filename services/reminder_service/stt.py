import os
import asyncio
import logging
import tempfile
from pathlib import Path
from config.settings import settings

logger = logging.getLogger("stt_service")

# Whisper uchun o'zbek tili lug'ati va kontekst prompti
WHISPER_UZBEK_PROMPT = (
    "O'zbekcha nutq: 35000 so'm, 50k, 100 ming, 1.5 mln so'm, "
    "tushlik, taxi, bozor, go'sht, supermarket, kommunal, oylik maosh, avans, "
    "ertaga soat 15:00 da, eslatma, uchrashuv, xarajat, kirim, chiqim, "
    "karta, naqd pul, dori, do'kon, kiyim, kafe, oshxona."
)

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
    """
    Groq Whisper orqali o'zbek tilidagi ovozni matnga o'girish.
    Birinchi navbatda eng yuqori sifatli 'whisper-large-v3',
    muammo bo'lsa 'whisper-large-v3-turbo' modeliga murojaat qiladi.
    """
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=api_key)

        with open(file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()

        filename = Path(file_path).name

        try:
            response = await client.audio.transcriptions.create(
                file=(filename, audio_bytes),
                model="whisper-large-v3",
                prompt=WHISPER_UZBEK_PROMPT,
                language="uz",
                temperature=0.0,
                response_format="text"
            )
            text = str(response).strip()
            logger.info(f"Groq Whisper-large-v3 muvaffaqiyatli yakunlandi: {text[:60]}...")
            return text
        except Exception as e:
            logger.warning(f"Groq whisper-large-v3 xatosi: {e}. Turbo modelga urinib ko'rilmoqda...")
            response = await client.audio.transcriptions.create(
                file=(filename, audio_bytes),
                model="whisper-large-v3-turbo",
                prompt=WHISPER_UZBEK_PROMPT,
                language="uz",
                temperature=0.0,
                response_format="text"
            )
            text = str(response).strip()
            logger.info(f"Groq Whisper-turbo muvaffaqiyatli yakunlandi: {text[:60]}...")
            return text

    except Exception as e:
        logger.warning(f"Groq orqali ovozni aniqlashda xatolik: {e}. Google STT ga o'tilmoqda...")
        return None

async def transcribe_with_google(wav_path: str) -> str | None:
    """Google Speech Recognition (uz-UZ) orqali ovozni matnga o'girish (zaxira)"""
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
    Ovozli faylni qabul qilib, o'zbekcha matnga o'giradi:
    1. Groq Whisper Large v3 (yuqori sifatli va tezkor)
    2. Groq Whisper Turbo (zaxira)
    3. Google Speech Recognition uz-UZ (offline/fallback)
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
