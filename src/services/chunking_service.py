import re

import tiktoken


class ChunkingService:
    def __init__(
        self,
        chunk_size: int = 450,
        overlap: int = 80,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap

        self.encoder = tiktoken.get_encoding(
"cl100k_base")

    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(
            r"\A---\s*\n.*?\n---\s*\n",
            "",
            text,
            flags=re.DOTALL,
        )

        text = re.sub(
            r"<!--.*?-->",
            "",
            text,
            flags=re.DOTALL,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    def chunk_document(self, text: str, metadata: dict) -> list[dict]:
        clean_text = self.clean_text(text)

        tokens = self.encoder.encode(clean_text)

        chunks = []

        start = 0
        chunk_index = 0

        while start < len(tokens):
            end = min(
                start + self.chunk_size,
                len(tokens),
            )

            chunk_tokens = tokens[
                start:end
            ]

            chunk_text = self.encoder.decode(
                chunk_tokens
            ).strip()

            if chunk_text:
                chunks.append(
                    {
                        **metadata,
                        "text": chunk_text,
                        "chunk_index": chunk_index,
                    }
                )

                chunk_index += 1

            if end >= len(tokens):
                break

            start = (end - self.overlap)

        return chunks