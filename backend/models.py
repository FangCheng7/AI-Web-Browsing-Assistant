from sqlalchemy import Column, Integer, String, Text

from database import Base


class BrowseRecord(Base):
    __tablename__ = "browse_records"

    id = Column(Integer, primary_key=True, index=True)

    tab_id = Column(Integer)

    url = Column(String(2000))

    title = Column(Text)

    start_time = Column(Integer)

    end_time = Column(Integer)

    duration = Column(Integer)


class PageAnalysis(Base):
    __tablename__ = "page_analyses"

    id = Column(Integer, primary_key=True, index=True)

    # 对应哪一次浏览记录
    browse_record_id = Column(Integer, nullable=True, index=True)

    url = Column(String(2000))

    title = Column(Text)

    category = Column(String(100))

    subcategory = Column(String(100))

    topics = Column(Text)

    summary = Column(Text)

    interest = Column(Integer)

    importance = Column(Integer)

    created_at = Column(Integer)