from collections import Counter
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models.assignment import DailyAssignment
from app.models.question import Question
from app.models.user import AppUser
from app.services.question_picker import pick_next


@pytest.fixture(scope="module")
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Seed user
    user = AppUser(email="test@example.com", current_streak=0, longest_streak=0,
                   total_solved=0, total_points=0)
    session.add(user)

    # 4 EASY, 6 MEDIUM, 2 HARD questions — distinct topics
    questions = [
        Question(leetcode_slug=f"easy-{i}", title=f"Easy {i}", difficulty="EASY",
                 url=f"https://lc.com/easy-{i}/", topics=f"array")
        for i in range(4)
    ] + [
        Question(leetcode_slug=f"medium-{i}", title=f"Medium {i}", difficulty="MEDIUM",
                 url=f"https://lc.com/medium-{i}/", topics=f"dynamic-programming")
        for i in range(6)
    ] + [
        Question(leetcode_slug=f"hard-{i}", title=f"Hard {i}", difficulty="HARD",
                 url=f"https://lc.com/hard-{i}/", topics=f"graph")
        for i in range(2)
    ]
    session.add_all(questions)
    session.commit()

    yield session
    session.close()


@pytest.fixture
def user(db):
    return db.query(AppUser).first()


def _mark_done(db: Session, user: AppUser, question: Question, day_offset: int = 0):
    d = date(2026, 1, 1 + day_offset)
    db.add(DailyAssignment(
        user_id=user.id, question_id=question.id,
        assigned_date=d, response="DONE",
    ))
    db.commit()


def _clear_assignments(db: Session):
    db.query(DailyAssignment).delete()
    db.commit()


# --- pool exclusion ---

def test_pick_returns_a_question(db, user):
    _clear_assignments(db)
    q = pick_next(user, db)
    assert q is not None


def test_done_question_excluded(db, user):
    _clear_assignments(db)
    easy_questions = db.query(Question).filter_by(difficulty="EASY").all()

    # Mark all but one EASY done, all MEDIUM and HARD done
    for q in easy_questions[1:]:
        _mark_done(db, user, q, day_offset=easy_questions.index(q))
    for i, q in enumerate(db.query(Question).filter(Question.difficulty != "EASY").all()):
        _mark_done(db, user, q, day_offset=10 + i)

    # Only one EASY remains; pick_next must always return it
    survivor = easy_questions[0]
    for _ in range(20):
        result = pick_next(user, db)
        assert result is not None
        assert result.id == survivor.id


def test_all_done_returns_none(db, user):
    _clear_assignments(db)
    all_q = db.query(Question).all()
    for i, q in enumerate(all_q):
        _mark_done(db, user, q, day_offset=i)

    assert pick_next(user, db) is None


# --- difficulty distribution ---

def test_difficulty_distribution_over_1000_trials(db, user):
    _clear_assignments(db)
    counts: Counter = Counter()
    trials = 1000

    for _ in range(trials):
        q = pick_next(user, db)
        counts[q.difficulty] += 1

    easy_pct = counts["EASY"] / trials
    medium_pct = counts["MEDIUM"] / trials
    hard_pct = counts["HARD"] / trials

    assert 0.15 <= easy_pct <= 0.35,   f"EASY {easy_pct:.2%} outside 25%±10%"
    assert 0.50 <= medium_pct <= 0.70, f"MEDIUM {medium_pct:.2%} outside 60%±10%"
    assert 0.05 <= hard_pct <= 0.25,   f"HARD {hard_pct:.2%} outside 15%±10%"


# --- topic rotation ---
# These tests use their own isolated DB with heterogeneous topics within MEDIUM
# so rotation can be verified without the fallback triggering.

@pytest.fixture
def topic_db():
    """In-memory DB with MEDIUM questions split across two topics."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker as SM
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    s = SM(bind=engine)()

    u = AppUser(email="topic@example.com", current_streak=0, longest_streak=0,
                total_solved=0, total_points=0)
    s.add(u)

    # 2 EASY (won't be DONE, just available), 3 MEDIUM with "dp", 3 MEDIUM with "tree"
    s.add_all([
        Question(leetcode_slug="e0", title="E0", difficulty="EASY",
                 url="https://lc.com/e0/", topics="array"),
        Question(leetcode_slug="e1", title="E1", difficulty="EASY",
                 url="https://lc.com/e1/", topics="array"),
        Question(leetcode_slug="m-dp-0", title="M-DP-0", difficulty="MEDIUM",
                 url="https://lc.com/m-dp-0/", topics="dynamic-programming"),
        Question(leetcode_slug="m-dp-1", title="M-DP-1", difficulty="MEDIUM",
                 url="https://lc.com/m-dp-1/", topics="dynamic-programming"),
        Question(leetcode_slug="m-dp-2", title="M-DP-2", difficulty="MEDIUM",
                 url="https://lc.com/m-dp-2/", topics="dynamic-programming"),
        Question(leetcode_slug="m-tree-0", title="M-Tree-0", difficulty="MEDIUM",
                 url="https://lc.com/m-tree-0/", topics="tree"),
        Question(leetcode_slug="m-tree-1", title="M-Tree-1", difficulty="MEDIUM",
                 url="https://lc.com/m-tree-1/", topics="tree"),
        Question(leetcode_slug="m-tree-2", title="M-Tree-2", difficulty="MEDIUM",
                 url="https://lc.com/m-tree-2/", topics="tree"),
    ])
    s.commit()
    yield s
    s.close()


def test_topic_rotation_excludes_banned_topics_when_alternatives_exist(topic_db):
    s = topic_db
    u = s.query(AppUser).first()

    # Mark EASY as done so only MEDIUM is available
    easy_qs = s.query(Question).filter_by(difficulty="EASY").all()
    for i, q in enumerate(easy_qs):
        s.add(DailyAssignment(user_id=u.id, question_id=q.id,
                              assigned_date=date(2026, 3, i + 1), response="DONE"))
    # Record recent assignments pointing at dp MEDIUM → bans "dynamic-programming"
    dp_qs = s.query(Question).filter_by(topics="dynamic-programming").all()
    for i, q in enumerate(dp_qs):
        s.add(DailyAssignment(user_id=u.id, question_id=q.id,
                              assigned_date=date(2026, 4, i + 1), response=None))
    s.commit()

    # With "dynamic-programming" banned and "tree" alternatives available,
    # every pick should come from the "tree" bucket
    results = [pick_next(u, s) for _ in range(60)]
    for q in results:
        assert q.topics == "tree", f"Expected tree topic, got {q.topics} ({q.title})"


def test_topic_rotation_falls_back_when_pool_empty(topic_db):
    s = topic_db
    u = s.query(AppUser).first()

    # Clear prior assignments from the exclusion test
    s.query(DailyAssignment).delete()
    s.commit()

    # Mark EASY and dp-MEDIUM as DONE — only tree-MEDIUM remain
    non_tree = s.query(Question).filter(Question.topics != "tree").all()
    for i, q in enumerate(non_tree):
        s.add(DailyAssignment(user_id=u.id, question_id=q.id,
                              assigned_date=date(2026, 5, i + 1), response="DONE"))
    # Recent assignments point at tree questions → bans "tree"
    tree_qs = s.query(Question).filter_by(topics="tree").all()
    for i, q in enumerate(tree_qs):
        s.add(DailyAssignment(user_id=u.id, question_id=q.id,
                              assigned_date=date(2026, 6, i + 1), response=None))
    s.commit()

    # Only tree-MEDIUM is available; rotation bans "tree" but fallback must kick in
    result = pick_next(u, s)
    assert result is not None
    assert result.topics == "tree"
