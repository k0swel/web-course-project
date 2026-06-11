import os
from dotenv import load_dotenv

load_dotenv()

_required = ['DB_USER', 'DB_PASSWORD', 'DB_NAME', 'OPENSTACK_TOKEN']
_missing = [k for k in _required if not os.getenv(k)]
if _missing:
    raise RuntimeError(f".env не загружен или отсутствуют переменные: {', '.join(_missing)}")

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST', 'localhost')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
