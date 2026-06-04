"""Flask extensions — initialized once, bound to app in factory."""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_apscheduler import APScheduler

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
scheduler = APScheduler()
