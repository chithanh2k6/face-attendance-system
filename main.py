from modules.database import create_tables
from ui.app import run_app


if __name__ == "__main__":
    create_tables()
    run_app()