from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class QueryRecord(Base):
    __tablename__ = "query_records"
    id = Column(Integer, primary_key=True)
    case_type = Column(String(50))
    case_number = Column(String(50))
    year = Column(String(10))
    court = Column(String(200), nullable=True)
    raw_response = Column(Text)   # raw HTML / JSON
    parsed_json = Column(Text)    # JSON string of parsed fields
    created_at = Column(DateTime, default=datetime.utcnow)