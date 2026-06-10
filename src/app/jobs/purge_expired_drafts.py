import argparse
import json

from app.db.session import SessionLocal
from app.services.document_service import DocumentService


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete expired draft documents and their files.")
    parser.add_argument("--retention-days", type=int, default=30, dest="retention_days")
    parser.add_argument("--batch-size", type=int, default=100, dest="batch_size")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = DocumentService(db).purge_expired_drafts(
            retention_days=args.retention_days,
            batch_size=args.batch_size,
        )
    finally:
        db.close()

    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
