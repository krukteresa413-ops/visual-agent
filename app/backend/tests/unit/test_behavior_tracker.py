"""
TDD Step 1 (RED): Behavior Tracker tests.
Event recording, querying, and calibration analysis.
"""
import json
import pytest
from unittest.mock import patch, MagicMock


# ── Helpers ────────────────────────────────────────────────────

def make_mock_event(**overrides):
    """Create a mock BehaviorEvent."""
    import datetime
    mock = MagicMock()
    mock.id = 1
    mock.project_id = 2
    mock.generation_id = 10
    mock.event_type = "viewed"
    mock.image_path = "/static/canvas/test.png"
    mock.ai_score = 75.5
    mock.metadata_json = '{"quality_check": {"passed": true}}'
    mock.created_at = datetime.datetime(2026, 6, 15, 12, 0, 0)
    for k, v in overrides.items():
        setattr(mock, k, v)
    return mock


# ── Event Recording Tests ──────────────────────────────────────

def test_record_event_persists_to_db():
    """记录事件后可以从数据库查询到。"""
    from app.services.behavior_tracker import BehaviorTracker

    tracker = BehaviorTracker()

    with patch("app.services.behavior_tracker.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        tracker.record_event(
            project_id=2,
            generation_id=10,
            event_type="exported",
            image_path="/static/canvas/test.png",
            ai_score=75.5,
            metadata={"quality_check": {"passed": True}},
        )

    # Verify db.add + db.commit were called
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_record_event_with_minimal_fields():
    """最少字段也能记录。"""
    from app.services.behavior_tracker import BehaviorTracker

    tracker = BehaviorTracker()

    with patch("app.services.behavior_tracker.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        tracker.record_event(
            project_id=2,
            event_type="viewed",
        )

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


# ── Event Query Tests ──────────────────────────────────────────

def test_get_project_events_returns_filtered():
    """按 project_id 查询事件列表。"""
    from app.services.behavior_tracker import BehaviorTracker

    tracker = BehaviorTracker()
    events = [make_mock_event(id=i, event_type="exported") for i in range(1, 4)]

    with patch("app.services.behavior_tracker.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = events
        mock_session.return_value = mock_db

        result = tracker.get_project_events(project_id=2)

    assert len(result) == 3
    assert all(e["event_type"] == "exported" for e in result)


def test_get_project_events_filters_by_type():
    """按 event_type 过滤。"""
    from app.services.behavior_tracker import BehaviorTracker

    tracker = BehaviorTracker()
    events = [make_mock_event(id=1, event_type="finalized")]

    with patch("app.services.behavior_tracker.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = events
        mock_session.return_value = mock_db

        result = tracker.get_project_events(project_id=2, event_type="finalized")

    assert len(result) == 1


# ── Calibration Tests ──────────────────────────────────────────

def test_calibrate_returns_accuracy_metrics():
    """校准分析返回 AI 预测 vs 用户选择的准确率。"""
    from app.services.behavior_tracker import BehaviorTracker

    tracker = BehaviorTracker()

    # Mock get_project_events to return known data
    finalized_events = [
        {"image_path": "/static/a.png", "ai_score": 85.0, "event_type": "finalized"},
        {"image_path": "/static/b.png", "ai_score": 72.0, "event_type": "finalized"},
        {"image_path": "/static/c.png", "ai_score": 90.0, "event_type": "finalized"},
    ]
    exported_events = [
        {"image_path": "/static/a.png", "ai_score": 85.0, "event_type": "exported"},
        {"image_path": "/static/b.png", "ai_score": 72.0, "event_type": "exported"},
    ]

    with patch.object(tracker, "get_project_events") as mock_query:
        mock_query.side_effect = [finalized_events, exported_events]
        report = tracker.calibrate(project_id=2)

    assert report["total_finalized"] == 3
    assert report["matched_exports"] == 2
    assert report["calibration_score"] > 0


def test_calibrate_empty_project():
    """无数据时返回空报告。"""
    from app.services.behavior_tracker import BehaviorTracker

    tracker = BehaviorTracker()

    with patch("app.services.behavior_tracker.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_session.return_value = mock_db

        report = tracker.calibrate(project_id=999)

    assert report["total_finalized"] == 0
    assert report["calibration_score"] == 0
    assert report["status"] == "insufficient_data"
