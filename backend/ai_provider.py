# ============================================================
# TRIPGENIE AI - AI PROVIDER MANAGER
# ============================================================

import json
import time
from typing import Optional

from google import genai
from groq import Groq

from config import (
    GEMINI_API_KEY,
    GROQ_API_KEY,
    GEMINI_MODEL,
    GROQ_MODEL,
    MAX_RETRIES,
    RETRY_DELAYS,
)

# ============================================================
# CLIENTS
# ============================================================

gemini_client: Optional[genai.Client] = None
groq_client: Optional[Groq] = None

if GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )

if GROQ_API_KEY:
    groq_client = Groq(
        api_key=GROQ_API_KEY
    )

# ============================================================
# ERROR CLASSIFICATION
# ============================================================

def is_permanent_error(error: Exception) -> bool:
    """
    Errors that should NOT be retried.

    Examples:
    - 400 invalid request
    - 401 authentication failure
    - 403 permission failure
    - 404 model not found
    - invalid model
    - unsupported model
    """

    message = str(error).lower()

    permanent_errors = [
        "400",
        "401",
        "403",
        "404",
        "not_found",
        "not found",
        "model not found",
        "model is unavailable",
        "invalid model",
        "unsupported model",
        "permission denied",
        "unauthorized",
        "api key",
    ]

    return any(
        item in message
        for item in permanent_errors
    )

def is_temporary_error(error: Exception) -> bool:
    """
    Errors that may succeed after a short retry.
    """

    message = str(error).lower()

    temporary_errors = [
        "408",
        "409",
        "425",
        "429",
        "500",
        "502",
        "503",
        "504",
        "unavailable",
        "overloaded",
        "rate limit",
        "rate_limit",
        "temporarily",
        "timeout",
        "timed out",
        "service unavailable",
    ]

    return any(
        item in message
        for item in temporary_errors
    )


def summarize_provider_error(error: Exception) -> str:
    message = " ".join(str(error).split())
    normalized = message.lower()

    if any(
        marker in normalized
        for marker in ("429", "rate limit", "rate_limit", "quota")
    ):
        return "quota/rate limit"

    if any(
        marker in normalized
        for marker in ("503", "unavailable", "overloaded", "service unavailable")
    ):
        return "service temporarily unavailable"

    if any(
        marker in normalized
        for marker in ("timeout", "timed out", "408")
    ):
        return "request timed out"

    if is_permanent_error(error):
        return "authentication, permission, or model configuration error"

    return message[:200] or type(error).__name__

# ============================================================
# GEMINI
# ============================================================

def generate_with_gemini(
    prompt: str,
    system_instruction: str = "",
    json_mode: bool = False,
) -> str:

    if not gemini_client:

        raise RuntimeError(
            "Gemini API key is not configured."
        )

    last_error = None

    for attempt in range(MAX_RETRIES):

        try:

            config = {
                "system_instruction": system_instruction,
                "temperature": 0.7,
            }

            if json_mode:

                config[
                    "response_mime_type"
                ] = "application/json"

            response = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=config,
            )

            if response.text:

                return response.text

            raise RuntimeError(
                "Gemini returned an empty response."
            )

        except Exception as error:

            last_error = error

            print(
                f"[Gemini] Attempt "
                f"{attempt + 1}/{MAX_RETRIES} failed: "
                f"{error}"
            )

            # ------------------------------------------------
            # Permanent error
            # ------------------------------------------------

            if is_permanent_error(error):

                print(
                    "[Gemini] Permanent error detected. "
                    "Skipping remaining retries."
                )

                raise RuntimeError(
                    f"Gemini permanent error: {error}"
                )

            # ------------------------------------------------
            # Retry only temporary errors
            # ------------------------------------------------

            if (
                is_temporary_error(error)
                and attempt < MAX_RETRIES - 1
            ):

                delay = RETRY_DELAYS[
                    min(
                        attempt,
                        len(RETRY_DELAYS) - 1
                    )
                ]

                print(
                    f"[Gemini] Temporary error. "
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)

                continue

            # ------------------------------------------------
            # Unknown error
            # ------------------------------------------------

            raise RuntimeError(
                f"Gemini request failed: {error}"
            )

    raise RuntimeError(
        f"Gemini unavailable: {last_error}"
    )

# ============================================================
# GROQ
# ============================================================

def generate_with_groq(
    prompt: str,
    system_instruction: str = "",
    json_mode: bool = False,
) -> str:

    if not groq_client:

        raise RuntimeError(
            "Groq API key is not configured."
        )

    last_error = None

    for attempt in range(MAX_RETRIES):

        try:

            messages = []

            if system_instruction:

                messages.append(
                    {
                        "role": "system",
                        "content": system_instruction,
                    }
                )

            messages.append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )

            kwargs = {
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": 0.7,
            }

            if json_mode:

                kwargs[
                    "response_format"
                ] = {
                    "type": "json_object"
                }

            response = groq_client.chat.completions.create(
                **kwargs
            )

            content = (
                response
                .choices[0]
                .message
                .content
            )

            if content:

                return content

            raise RuntimeError(
                "Groq returned an empty response."
            )

        except Exception as error:

            last_error = error

            print(
                f"[Groq] Attempt "
                f"{attempt + 1}/{MAX_RETRIES} failed: "
                f"{error}"
            )

            # ------------------------------------------------
            # Permanent error
            # ------------------------------------------------

            if is_permanent_error(error):

                print(
                    "[Groq] Permanent error detected. "
                    "Skipping remaining retries."
                )

                raise RuntimeError(
                    f"Groq permanent error: {error}"
                )

            # ------------------------------------------------
            # Retry temporary errors
            # ------------------------------------------------

            if (
                is_temporary_error(error)
                and attempt < MAX_RETRIES - 1
            ):

                delay = RETRY_DELAYS[
                    min(
                        attempt,
                        len(RETRY_DELAYS) - 1
                    )
                ]

                print(
                    f"[Groq] Temporary error. "
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)

                continue

            raise RuntimeError(
                f"Groq request failed: {error}"
            )

    raise RuntimeError(
        f"Groq unavailable: {last_error}"
    )

# ============================================================
# JSON CLEANING
# ============================================================

def clean_json_response(text: str) -> str:

    text = text.strip()

    if text.startswith("```json"):

        text = text[7:]

    elif text.startswith("```"):

        text = text[3:]

    if text.endswith("```"):

        text = text[:-3]

    return text.strip()

def parse_json_response(text: str) -> dict:

    cleaned = clean_json_response(text)

    try:

        return json.loads(cleaned)

    except json.JSONDecodeError:

        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1 and end > start:

            possible_json = cleaned[
                start:end + 1
            ]

            return json.loads(
                possible_json
            )

        raise

# ============================================================
# MAIN PROVIDER
# ============================================================

def generate_ai_response(
    prompt: str,
    system_instruction: str = "",
    json_mode: bool = False,
) -> str:
    """
    Provider priority:

        Gemini
           ↓
        Groq
           ↓
        controlled failure

    Gemini permanent errors immediately trigger
    Groq fallback.

    Gemini temporary errors are retried first.
    """

    provider_errors = []

    if gemini_client:

        try:

            print(
                f"[AI Provider] Trying Gemini "
                f"({GEMINI_MODEL})..."
            )

            response = generate_with_gemini(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=json_mode,
            )

            print(
                "[AI Provider] Gemini response received."
            )

            return response

        except Exception as error:

            provider_errors.append(
                f"Gemini unavailable: {summarize_provider_error(error)}"
            )

            print(
                "[AI Provider] Gemini failed. "
                "Switching to Groq..."
            )

            print(
                f"[AI Provider] Gemini error: {error}"
            )

    else:

        provider_errors.append(
            "Gemini unavailable: API key is not configured."
        )

        print(
            "[AI Provider] Gemini is not configured."
        )

    # ========================================================
    # BACKUP: GROQ
    # ========================================================

    if groq_client:

        try:

            print(
                f"[AI Provider] Trying Groq backup "
                f"({GROQ_MODEL})..."
            )

            response = generate_with_groq(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=json_mode,
            )

            print(
                "[AI Provider] Groq response received."
            )

            return response

        except Exception as error:

            provider_errors.append(
                f"Groq unavailable: {summarize_provider_error(error)}"
            )

            print(
                "[AI Provider] Groq backup failed."
            )

            print(
                f"[AI Provider] Groq error: {error}"
            )

    else:

        provider_errors.append(
            "Groq unavailable: API key is not configured."
        )

        print(
            "[AI Provider] Groq is not configured."
        )

    raise RuntimeError(
        "; ".join(provider_errors)
    )

# ============================================================
# JSON PROVIDER
# ============================================================

def generate_ai_json(
    prompt: str,
    system_instruction: str = "",
) -> dict:
    """
    Generate structured JSON using:

        Gemini → Groq
    """

    response = generate_ai_response(
        prompt=prompt,
        system_instruction=system_instruction,
        json_mode=True,
    )

    return parse_json_response(response)