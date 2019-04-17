import datetime as dt

from flask_login import current_user
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy import func, and_

from server.api.database import db
from server.api.database.mixins import (
    Column,
    Model,
    SurrogatePK,
    reference_col,
    relationship,
)
from server.api.database.models import Topic
from server.api.database.utils import QueryWithSoftDelete


class Lesson(SurrogatePK, Model):
    """A driving lesson"""

    __tablename__ = "lessons"
    query_class = QueryWithSoftDelete
    teacher_id = reference_col("teachers", nullable=False)
    teacher = relationship("Teacher", backref=backref("lessons", lazy="dynamic"))
    student_id = reference_col("students", nullable=True)
    student = relationship("Student", backref=backref("lessons", lazy="dynamic"))
    topics = relationship("LessonTopic", lazy="dynamic")
    duration = Column(db.Integer, nullable=False)
    date = Column(db.DateTime, nullable=False)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    meetup_place_id = reference_col("places", nullable=True)
    meetup_place = relationship("Place", foreign_keys=[meetup_place_id])
    dropoff_place_id = reference_col("places", nullable=True)
    dropoff_place = relationship("Place", foreign_keys=[dropoff_place_id])
    is_approved = Column(db.Boolean, nullable=False, default=True)
    comments = Column(db.Text, nullable=True)
    deleted = Column(db.Boolean, nullable=False, default=False)
    creator_id = reference_col("users", nullable=False)
    creator = relationship("User")

    ALLOWED_FILTERS = [
        "deleted",
        "is_approved",
        "date",
        "student_id",
        "created_at",
        "creator_id",
    ]
    default_sort_column = "date"

    def __init__(self, **kwargs):
        """Create instance."""
        if current_user and not kwargs.get("creator") and current_user.is_authenticated:
            self.creator = current_user
        db.Model.__init__(self, **kwargs)

    def update_only_changed_fields(self, **kwargs):
        args = {k: v for k, v in kwargs.items() if v or isinstance(v, bool)}
        self.update(**args)

    @hybrid_property
    def lesson_number(self):
        return (
            db.session.query(func.count(Lesson.id))
            .select_from(Lesson)
            .filter(and_(Lesson.date < self.date, Lesson.student == self.student))
            .scalar()
        ) + 1

    def to_dict(self):
        return {
            "id": self.id,
            "student": self.student.to_dict() if self.student else None,
            "date": self.date,
            "meetup_place": self.meetup_place.to_dict() if self.meetup_place else None,
            "dropoff_place": self.dropoff_place.to_dict()
            if self.dropoff_place
            else None,
            "is_approved": self.is_approved,
            "comments": self.comments,
            "topics": [topic.to_dict() for topic in self.topics.all()],
            "lesson_number": self.lesson_number,
            "created_at": self.created_at,
            "duration": self.duration,
        }

    def __repr__(self):
        return (
            f"<Lesson date={self.date}, created_at={self.created_at},"
            f"student={self.student}, teacher={self.teacher}"
            f",approved={self.is_approved}, number={self.lesson_number}, duration={self.duration}>"
        )
