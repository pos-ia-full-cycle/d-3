import re
import uuid
from datetime import datetime

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')

VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
VALID_ROLES = ['user', 'admin', 'manager']
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 8
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'


def validate_email(email):
    return bool(EMAIL_REGEX.match(email))


def is_valid_color(color):
    return bool(color and len(color) == 7 and color[0] == '#')


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def parse_date(date_string):
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    return None


def sanitize_string(s):
    return s.strip() if s else s


def generate_id():
    return str(uuid.uuid4())
