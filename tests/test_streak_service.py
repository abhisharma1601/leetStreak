from datetime import date

import pytest

from app.models.assignment import DailyAssignment
from app.models.question import Question
from app.models.user import AppUser
from app.services.streak_service import apply_done, apply_skip


def _user(current_streak=0, longest_streak=0, total_solved=0, total_points=0):
    u = AppUser(
        email="test@example.com",
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_solved=total_solved,
        total_points=total_points,
    )
    return u


def _question(difficulty="MEDIUM"):
    return Question(
        leetcode_slug=f"test-{difficulty.lower()}",
        title=f"Test {difficulty}",
        difficulty=difficulty,
        url="https://leetcode.com/problems/test/",
        topics="array",
    )


def _assignment():
    a = DailyAssignment(user_id=1, question_id=1, assigned_date=date.today())
    return a


# --- apply_done: base points (no multiplier, streak < 7) ---

def test_done_easy_base_points():
    u, q, a = _user(), _question("EASY"), _assignment()
    earned = apply_done(u, q, a)
    assert earned == 1
    assert u.total_points == 1


def test_done_medium_base_points():
    u, q, a = _user(), _question("MEDIUM"), _assignment()
    earned = apply_done(u, q, a)
    assert earned == 3
    assert u.total_points == 3


def test_done_hard_base_points():
    u, q, a = _user(), _question("HARD"), _assignment()
    earned = apply_done(u, q, a)
    assert earned == 6
    assert u.total_points == 6


# --- apply_done: multipliers ---

def test_done_multiplier_1x_below_7():
    u = _user(current_streak=5)   # new_streak=6, still <7 → x1.0
    earned = apply_done(u, _question("HARD"), _assignment())
    assert earned == 6


def test_done_multiplier_1_2x_at_streak_7():
    u = _user(current_streak=6)   # new_streak=7 → x1.2
    earned = apply_done(u, _question("MEDIUM"), _assignment())
    assert earned == round(3 * 1.2)   # 4


def test_done_multiplier_1_2x_at_streak_29():
    u = _user(current_streak=28)  # new_streak=29, still <30 → x1.2
    earned = apply_done(u, _question("HARD"), _assignment())
    assert earned == round(6 * 1.2)   # 7


def test_done_multiplier_1_5x_at_streak_30():
    u = _user(current_streak=29)  # new_streak=30 → x1.5
    earned = apply_done(u, _question("MEDIUM"), _assignment())
    assert earned == round(3 * 1.5)   # 4 (banker's rounding)


def test_done_multiplier_2x_at_streak_100():
    u = _user(current_streak=99)  # new_streak=100 → x2.0
    earned = apply_done(u, _question("HARD"), _assignment())
    assert earned == round(6 * 2.0)   # 12


# --- apply_done: streak and counters ---

def test_done_increments_streak():
    u = _user(current_streak=4)
    apply_done(u, _question(), _assignment())
    assert u.current_streak == 5


def test_done_increments_total_solved():
    u = _user(total_solved=10)
    apply_done(u, _question(), _assignment())
    assert u.total_solved == 11


def test_done_updates_longest_streak_when_higher():
    u = _user(current_streak=9, longest_streak=9)
    apply_done(u, _question(), _assignment())
    assert u.longest_streak == 10


def test_done_does_not_lower_longest_streak():
    u = _user(current_streak=2, longest_streak=50)
    apply_done(u, _question(), _assignment())
    assert u.longest_streak == 50


def test_done_sets_assignment_response():
    a = _assignment()
    apply_done(_user(), _question(), a)
    assert a.response == "DONE"
    assert a.responded_at is not None


# --- apply_skip ---

def test_skip_resets_streak_to_zero():
    u = _user(current_streak=15)
    apply_skip(u, _assignment())
    assert u.current_streak == 0


def test_skip_does_not_touch_longest_streak():
    u = _user(current_streak=15, longest_streak=30)
    apply_skip(u, _assignment())
    assert u.longest_streak == 30


def test_skip_does_not_touch_total_solved():
    u = _user(total_solved=7)
    apply_skip(u, _assignment())
    assert u.total_solved == 7


def test_skip_does_not_touch_total_points():
    u = _user(total_points=42)
    apply_skip(u, _assignment())
    assert u.total_points == 42


def test_skip_sets_assignment_response():
    a = _assignment()
    apply_skip(_user(), a)
    assert a.response == "SKIP"
    assert a.responded_at is not None
