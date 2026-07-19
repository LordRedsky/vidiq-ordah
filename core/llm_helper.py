"""
core/llm_helper.py
==================
Helper tangguh untuk pemanggilan LLM dengan fitur:
1. Auto Retry & Exponential Backoff jika terkena HTTP 429 (Rate Limit).
2. Fallback Model Cascade (gemini-2.0-flash -> gemini-2.0-flash-lite -> gemini-1.5-flash -> gemini-1.5-pro).
3. API Key Rotation (memutar multiple keys: GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3).
4. Dukungan Provider Gratis Tambahan: Groq API (llama-3.3-70b-versatile) jika GROQ_API_KEY tersedia.
"""

import os
import time
import re
from dotenv import load_dotenv

load_dotenv(override=True)


def get_gemini_api_keys() -> list[str]:
    """Mendapatkan daftar API key Gemini dari os.getenv atau streamlit secrets."""
    keys = []
    # 1. Main key
    k1 = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
    if k1 and k1.strip():
        keys.append(k1.strip())

    # 2. Key tambahan (GEMINI_API_KEY_2, GEMINI_API_KEY_3, dst)
    for i in range(2, 10):
        k = os.getenv(f"GEMINI_API_KEY_{i}")
        if k and k.strip() and k.strip() not in keys:
            keys.append(k.strip())

    # 3. Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets") and st.secrets:
            s_key = st.secrets.get("GEMINI_API_KEY")
            if s_key and str(s_key).strip() not in keys:
                keys.append(str(s_key).strip())
    except Exception:
        pass

    return keys


def get_groq_api_key() -> str:
    """Mendapatkan API key Groq dari os.getenv atau streamlit secrets."""
    key = os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY") or ""
    if key and key.strip():
        return key.strip()
    try:
        import streamlit as st
        if hasattr(st, "secrets") and st.secrets:
            gk = st.secrets.get("GROQ_API_KEY") or st.secrets.get("GROK_API_KEY")
            if gk and str(gk).strip():
                return str(gk).strip()
    except Exception:
        pass
    return ""


def call_llm_with_resilience(
    prompt: str,
    system_instruction: str = "",
    temperature: float = 0.7,
    max_output_tokens: int = 8192,
    prefer_groq: bool = False
) -> str:
    """
    Memanggil LLM secara resilien terhadap Rate Limit (429):
    - Jika Groq API tersedia & diprioritaskan atau Gemini rate-limited, langsung gunakan Groq!
    - Coba Gemini dengan model fallback & key rotation + delay otomatis saat 429
    """
    groq_key = get_groq_api_key()
    gemini_keys = get_gemini_api_keys()

    # 1. Jika prefer Groq dan GROQ_API_KEY tersedia
    if prefer_groq and groq_key:
        try:
            return _call_groq(prompt, system_instruction, temperature, max_output_tokens, groq_key)
        except Exception as e:
            print(f"[LLM Helper] Groq gagal: {e}, beralih ke Gemini...")

    if not gemini_keys and not groq_key:
        raise ValueError("GEMINI_API_KEY atau GROQ_API_KEY belum dikonfigurasi di .env")

    # Models cascade untuk Gemini (setiap model punya kuota rate limit terpisah di Free Tier!)
    models_cascade = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro-latest",
    ]

    last_error = None

    for key_idx, api_key in enumerate(gemini_keys):
        for model_name in models_cascade:
            for attempt in range(2): # 2 kali coba per model
                try:
                    return _call_gemini_single(
                        prompt=prompt,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                        api_key=api_key,
                        model_name=model_name
                    )
                except Exception as e:
                    err_msg = str(e)
                    last_error = e
                    # Cek apakah 429 / Resource Exhausted
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "Quota" in err_msg:
                        # JIKA GROQ KEY ADA: LANGSUNG SWAP KE GROQ TANPA MENUNGGU!
                        if groq_key:
                            try:
                                print(f"[LLM Helper] 429 di Gemini ({model_name}). Langsung beralih ke Groq API (Llama 3.3 70B)...")
                                return _call_groq(prompt, system_instruction, temperature, max_output_tokens, groq_key)
                            except Exception as groq_err:
                                print(f"[LLM Helper] Groq API gagal: {groq_err}. Melanjutkan retry Gemini...")

                        # Cari waktu retryDelay jika ada di error
                        match = re.search(r"retryDelay[':]\s*['\"]?(\d+(?:\.\d+)?)s?", err_msg)
                        wait_seconds = float(match.group(1)) if match else (attempt + 1) * 5

                        if wait_seconds > 15:
                            print(f"[LLM Helper] 429 pada {model_name} (wait {wait_seconds}s). Ganti model...")
                            break

                        print(f"[LLM Helper] 429 Rate Limit pada {model_name}. Menunggu {wait_seconds:.1f}s...")
                        time.sleep(min(wait_seconds, 15))
                    else:
                        print(f"[LLM Helper] Non-429 Error pada {model_name}: {err_msg[:100]}")
                        break

    # 2. Jika semua Gemini key/model gagal, coba Groq sebagai fallback terakhir jika ada
    if groq_key:
        try:
            print("[LLM Helper] Semua Gemini rate limited. Menggunakan Groq API sebagai fallback...")
            return _call_groq(prompt, system_instruction, temperature, max_output_tokens, groq_key)
        except Exception as groq_err:
            last_error = groq_err

    raise RuntimeError(
        f"Gagal generate LLM setelah mencoba beberapa model/key & retry. Detail error terakhir: {last_error}"
    )


def _call_gemini_single(
    prompt: str,
    system_instruction: str,
    temperature: float,
    max_output_tokens: int,
    api_key: str,
    model_name: str
) -> str:
    """Pemanggilan single Gemini request."""
    # Opsi 1: google.genai SDK
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        config_args = {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        }
        if system_instruction:
            config_args["system_instruction"] = system_instruction

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(**config_args)
        )
        if response and response.text:
            return response.text.strip()
    except ImportError:
        pass

    # Opsi 2: legacy google.generativeai SDK
    import google.generativeai as legacy_genai
    legacy_genai.configure(api_key=api_key)
    kwargs = {}
    if system_instruction:
        kwargs["system_instruction"] = system_instruction
    model = legacy_genai.GenerativeModel(
        model_name=model_name,
        generation_config={
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
        },
        **kwargs
    )
    response = model.generate_content(prompt)
    if response and response.text:
        return response.text.strip()

    raise ValueError("Respons Gemini kosong")


def _call_groq(
    prompt: str,
    system_instruction: str,
    temperature: float,
    max_output_tokens: int,
    api_key: str
) -> str:
    """Pemanggilan Groq API (Llama 3.3 70B Versatile)."""
    import json

    url = "https://api.groq.com/openai/v1/chat/completions"
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": min(max_output_tokens, 8192)
    }

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Coba via requests (lebih robust) atau fallback ke urllib
    try:
        import requests
        res = requests.post(url, json=payload, headers=headers, timeout=120)
        if res.status_code == 200:
            data = res.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0]["message"]["content"].strip()
        else:
            raise RuntimeError(f"HTTP Error {res.status_code}: {res.text[:200]}")
    except ImportError:
        import urllib.request
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            choices = res_data.get("choices", [])
            if choices:
                return choices[0]["message"]["content"].strip()

    raise ValueError("Respons Groq API kosong")
