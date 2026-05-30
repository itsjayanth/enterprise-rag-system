"""Phase 2 smoke test: checks DB session + insert for Document model.

Run after migrations:
    python scripts/phase2_smoke_test.py
"""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal
from app.models.document import Document


def main() -> None:
    db = SessionLocal()
    try:
        doc = Document(
            filename="phase2-smoke.pdf",
            file_size=12345,
            file_type="pdf",
            storage_path="/data/uploads/phase2-smoke.pdf",
            status="uploaded",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        print(f"inserted document id={doc.id} status={doc.status}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

