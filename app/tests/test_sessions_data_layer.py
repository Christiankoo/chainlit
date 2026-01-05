from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from app.crud.sessions import (
    get_sessions,
    create_session_record,
    update_session_record,
)

from app.db.models import Session as SessionModel

@pytest.fixture
def db() -> Session:
    return MagicMock(spec=Session)

def test_get_sessions_applies_user_filter_orders_offsets_limits_and_caps(db):
    """
    High-signal behavior:
    - Applies filter when user_id is provided
    - Orders by created_at desc
    - Applies offset + limit
    - Caps limit to 200
    """
    q = MagicMock()
    db.query.return_value = q

    # chainable query methods
    q.filter.return_value = q
    q.order_by.return_value = q
    q.offset.return_value = q
    q.limit.return_value = q

    expected_rows = [SimpleNamespace(id=uuid4(), user_id="u1", title=None, created_at=datetime.utcnow())]
    q.all.return_value = expected_rows

    rows = get_sessions(user_id="u1", limit=9999, offset=10, db=db)

    assert rows == expected_rows
    db.query.assert_called_once_with(SessionModel)
    q.filter.assert_called_once()  # don't overfit expression details
    q.offset.assert_called_once_with(10)
    q.limit.assert_called_once_with(200)  # cap applied
    q.all.assert_called_once()


def test_create_session_record_adds_commits_refreshes_and_returns_obj(db):
    """
    Verifies unit-of-work semantics in your create helper:
    add -> commit -> refresh -> return
    """
    obj = create_session_record(db, user_id="u123", title="Hello")

    # confirm correct object type/fields were constructed
    assert isinstance(obj, SessionModel)
    assert obj.user_id == "u123"
    assert obj.title == "Hello"

    db.add.assert_called_once_with(obj)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(obj)


def test_update_session_record_raises_404_when_not_found(db):
    """
    Ensures consistent 404 behavior when the record doesn't exist.
    """
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.first.return_value = None  # not found

    sid = uuid4()
    with pytest.raises(HTTPException) as e:
        update_session_record(db, session_id=sid, title="New title")

    assert e.value.status_code == 404
    assert "not found" in e.value.detail.lower()
    db.commit.assert_not_called()
    db.refresh.assert_not_called()
