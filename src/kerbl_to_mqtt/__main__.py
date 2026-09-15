from dotenv import load_dotenv

from .service import run


def main() -> None:
    load_dotenv()
    run()


if __name__ == "__main__":
    main()
