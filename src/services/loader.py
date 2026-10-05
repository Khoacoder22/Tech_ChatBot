from pathlib import Path


class DocumentLoader:
    def load_file(self, file_path: Path) -> dict:
        text = file_path.read_text(encoding="utf-8")

        return {
            "text": text,
            "metadata": {
                "title": file_path.stem,
                "source_url": str(file_path),
                "category": file_path.parent.name,
                "path": str(file_path)
            }
        }

    def load_folder(self, folder: str) -> list[dict]:
        documents = []

        for file_path in Path(folder).rglob("*.md"):
            documents.append(self.load_file(file_path))

        return documents