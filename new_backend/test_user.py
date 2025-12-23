from src import settings, Users

engine = settings.get_pg_engine()
from sqlalchemy.orm import Session
with Session(engine) as session:
    mokrota = Users(name="mokrota", permission_level=10)
    session.add(mokrota)
    session.commit()