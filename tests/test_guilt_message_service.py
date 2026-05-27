from app.services.guilt_message_service import pick


def test_streak_zero_returns_nonempty():
    msg = pick(0)
    assert isinstance(msg, str) and len(msg) > 0


def test_streak_zero_no_placeholder():
    # Zero tier has no {n} substitution
    msg = pick(0)
    assert "{n}" not in msg


def test_early_tier_streak_1():
    msg = pick(1)
    assert isinstance(msg, str) and len(msg) > 0
    assert "1" in msg


def test_early_tier_streak_6():
    msg = pick(6)
    assert isinstance(msg, str) and len(msg) > 0
    assert "6" in msg


def test_week_tier_streak_7():
    msg = pick(7)
    assert isinstance(msg, str) and len(msg) > 0
    assert "7" in msg


def test_week_tier_streak_29():
    msg = pick(29)
    assert isinstance(msg, str) and len(msg) > 0
    assert "29" in msg


def test_month_tier_streak_30():
    msg = pick(30)
    assert isinstance(msg, str) and len(msg) > 0
    assert "30" in msg


def test_month_tier_streak_99():
    msg = pick(99)
    assert isinstance(msg, str) and len(msg) > 0
    assert "99" in msg


def test_century_tier_streak_100():
    msg = pick(100)
    assert isinstance(msg, str) and len(msg) > 0
    assert "100" in msg


def test_century_tier_high_streak():
    msg = pick(365)
    assert isinstance(msg, str) and len(msg) > 0
    assert "365" in msg


def test_all_tiers_produce_varied_output():
    # Run each tier many times; we should get more than one unique message eventually
    results = {pick(0) for _ in range(30)}
    assert len(results) > 1, "Zero tier should produce varied messages"

    results = {pick(3) for _ in range(30)}
    assert len(results) > 1, "Early tier should produce varied messages"
