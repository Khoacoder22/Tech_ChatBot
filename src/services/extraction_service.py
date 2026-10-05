import re

from src.models import ExtractedInfo


class ExtractionService:
    
    # Matches HTTP status codes
    HTTP_PATTERN = re.compile(r"\b(?:HTTP(?:/\d(?:\.\d)?)?|status(?:\s+code)?|error)?\s*[:=-]?\s*([45]\d{2})\b", re.IGNORECASE)

    # Matches various error code formats
    ERROR_CODE_PATTERNS = [
        re.compile(
            r"\b(AADSTS\d{4,10})\b",
            re.IGNORECASE
        ),
        re.compile(
            r"\b(ERR_[A-Z0-9_]{3,})\b",
            re.IGNORECASE
        ),
        re.compile(
            r"\b(0x[0-9A-Fa-f]{4,16})\b"
        ),
        re.compile(
            r"\b(?:error\s*code|code)"
            r"\s*[:=#-]?\s*"
            r"([A-Z0-9][A-Z0-9_.:-]{2,40})",
            re.IGNORECASE
        ),
    ]

    # Matches Exception 
    EXCEPTION_PATTERN = re.compile(
        r"\b("
        r"[A-Za-z_][A-Za-z0-9_.]*"
        r"(?:Exception|Error|Failure)"
        r")\b"
    )

    # Matches lines containing common error keywords
    ERROR_LINE_PATTERN = re.compile(
        r"\b("
        r"error|exception|failed|failure|"
        r"unauthorized|forbidden|"
        r"timeout|timed out|expired|"
        r"permission denied|"
        r"connection refused|"
        r"connection reset|"
        r"cannot connect|can't connect|"
        r"not responding|"
        r"service unavailable|"
        r"internal server error|"
        r"fatal|crashed|crash|"
        r"invalid token|"
        r"access denied"
        r")\b",
        re.IGNORECASE
    )

    @staticmethod
    def unique(values: list[str]) -> list[str]:
        result = []
        seen = set()

        for value in values:
            value = str(value).strip()

            key = value.lower()

            if value and key not in seen:
                seen.add(key)
                result.append(value)

        return result

    def extract(self, text: str) -> ExtractedInfo:
        statuses = self.HTTP_PATTERN.findall(text)

        error_codes = []

        for pattern in self.ERROR_CODE_PATTERNS:
            error_codes.extend(
                pattern.findall(text)
            )

        exceptions = self.EXCEPTION_PATTERN.findall(
            text
        )
        # Collect lines containing error keywords
        error_lines = []
        for line in text.splitlines():
            clean_line = " ".join(
                line.split()
            )

            if (
                clean_line
                and self.ERROR_LINE_PATTERN.search(
                    clean_line
                )
            ):
                error_lines.append(
                    clean_line[:500]
                )

        return ExtractedInfo(
            http_statuses=self.unique(
                statuses
            ),
            error_codes=self.unique(
                error_codes
            ),
            exceptions=self.unique(
                exceptions
            ),
            key_error_lines=self.unique(
                error_lines
            ),
        )

    def build_search_query(
        self,
        original_text: str,
        extracted: ExtractedInfo,
        user_note: str = "",
    ) -> str:
        parts = []

        if extracted.http_statuses:
            parts.append(
                "HTTP status: "
                + ", ".join(
                    extracted.http_statuses
                )
            )

        if extracted.error_codes:
            parts.append(
                "Error codes: "
                + ", ".join(
                    extracted.error_codes
                )
            )

        if extracted.exceptions:
            parts.append(
                "Exceptions: "
                + ", ".join(
                    extracted.exceptions
                )
            )

        parts.extend(
            extracted.key_error_lines[:8]
        )

        cleaned_text = " ".join(
            original_text.split()
        )

        if cleaned_text:
            parts.append(
                cleaned_text[:1500]
            )

        if user_note.strip():
            parts.append(
                user_note.strip()[:500]
            )

        return "\n".join(
            dict.fromkeys(parts)
        )