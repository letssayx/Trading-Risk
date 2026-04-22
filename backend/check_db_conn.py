from infrastructure.db import SessionLocal

def main():
    db = SessionLocal()
    print("DB connection successful.")

if __name__ == "__main__":
    main()
