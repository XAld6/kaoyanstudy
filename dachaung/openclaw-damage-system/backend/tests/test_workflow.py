from app.workflow import assess_risk


def make_metrics(**overrides):
    metrics = {
        "detection_count": 0,
        "total_area_ratio": 0.0,
        "crack_count": 0,
        "avg_confidence": 0.0,
    }
    metrics.update(overrides)
    return metrics


def test_assess_risk_routes_unreadable_images_to_manual_review():
    level, reason = assess_risk(make_metrics(), {"readable": False})

    assert level == "中"
    assert "图像质量偏低" in reason


def test_assess_risk_returns_high_for_large_damage_area():
    level, reason = assess_risk(make_metrics(total_area_ratio=0.06), {"readable": True})

    assert level == "高"
    assert "优先复核" in reason


def test_assess_risk_returns_medium_for_multiple_candidates():
    level, reason = assess_risk(make_metrics(detection_count=2), {"readable": True})

    assert level == "中"
    assert "结合现场情况" in reason


def test_assess_risk_returns_low_for_clean_readable_images():
    level, reason = assess_risk(make_metrics(), {"readable": True})

    assert level == "低"
    assert "常规巡检" in reason
