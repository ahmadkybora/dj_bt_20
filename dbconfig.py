import os
from orator import DatabaseManager

# from dotenv import load_dotenv

# load_dotenv(verbose=True)

# DB_HOST = os.getenv("DB_HOST") if os.getenv("DB_HOST") else 'localhost'
# DB_PORT = int(os.getenv("DB_PORT")) if int(os.getenv("DB_PORT")) else 3306
# DB_USERNAME = os.getenv("DB_USERNAME") if os.getenv("DB_USERNAME") else 'ahmadkyb_root'
# DB_PASSWORD = os.getenv("DB_PASSWORD") if os.getenv("DB_PASSWORD") else 'EsX-BD@^5WjG'
# DB_NAME = os.getenv("DB_NAME") if os.getenv("DB_NAME") else 'ahmadkyb_django'

DATABASES = {
    'default': 'mysql',
    'mysql': {
        'driver': 'mysql',
        'host': 'localhost',
        'port': 3306,
        'user': '',
        'password': '',
        'database': '',
        'prefix': ''
    }
}

db = DatabaseManager(DATABASES)
