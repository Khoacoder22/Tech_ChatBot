import re

from src.models import (
    ExtractedInfo,
    ValidationResult,
)

class ErrorValidationService:
    STRONG_ERROR_PATTERN = re.compile(
        r"\b("
        r"failed|failure|"
        r"unauthorized|"
        r"forbidden|"
        r"timeout|timed out|"
        r"expired|"
        r"permission denied|"
        r"access denied|"
        r"connection refused|"
        r"connection reset|"
        r"cannot connect|"
        r"can't connect|"
        r"not responding|"
        r"service unavailable|"
        r"internal server error|"
        r"invalid token|"
        r"fatal|"
        r"crashed|crash|"
        r"segmentation fault"
        r")\b",
        re.IGNORECASE,
    )

    GENERIC_ERROR_PATTERN = re.compile(
        r"\b(error|exception)\b",
        re.IGNORECASE,
    )
    
    TECHNICAL_CONTEXT_PATTERN = re.compile(
        r"\b("
        r"server|api|database|db|"
        r"application|app|system|"
        r"login|authentication|"
        r"authorization|token|"
        r"request|response|"
        r"service|network|socket|"
        r"docker|kubernetes|pod|"
        r"container|azure|"
        r"http|https|endpoint|"
        r"connection|permission|"
        r"python|java|javascript|"
        r"client|daemon"
        r")\b",
        re.IGNORECASE,
    )
    
    STACK_TRACE_PATTERN = re.compile(
        r"("
        r"Traceback \(most recent call last\)|"
        r"\bat\s+[A-Za-z0-9_.$]+\([^)]*:\d+\)"
        r")",
        re.IGNORECASE,
    )

    def validate(self, text: str, extracted: ExtractedInfo) -> ValidationResult:
        clean = text.strip()
        
        if len(clean) < 5:
            return ValidationResult(is_valid=False, score=0, reasons=['Not found proper context'])
        
        score = 0
        reasons = []
        bad_statuses = []
        for status in extracted.http_statuses:
            try:
                status_number = int(status)
                if 400 <= status_number <= 599:
                    bad_statuses.append(status)
            except ValueError:
                continue

        if bad_statuses:
            score += 3

            reasons.append("Found HTTP error status.")
            
        if extracted.error_codes:
            score += 3

            reasons.append("Error code.")

        if extracted.exceptions:
            score += 3

            reasons.append("Found Exception.")

        if self.STACK_TRACE_PATTERN.search(clean):
            score += 3

            reasons.append("Stack trace.")

        if self.STRONG_ERROR_PATTERN.search(clean):
            score += 2

            reasons.append("Tech error.")

        generic_error = self.GENERIC_ERROR_PATTERN.search(clean)

        technical_context = (
            self.TECHNICAL_CONTEXT_PATTERN.search(clean)
        )

        if generic_error and technical_context:
            score += 2
            reasons.append("Error in system.")

        return ValidationResult(
            is_valid=score >= 2,
            score=score,
            reasons=reasons,
        )