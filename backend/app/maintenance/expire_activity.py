from app.db.session import SessionLocal
from app.services.activity import expire_activity


def main() -> None:
    total = 0
    with SessionLocal() as db:
        while count := expire_activity(db):
            total += count
    print(f"Expired {total} retained records or pending requests")


if __name__ == "__main__":
    main()
