from app import workflow as workflow_module
from app.workflow import assess_risk, run_damage_workflow


def make_metrics(**overrides):
    metrics = {
        "detection_count": 0,
        "total_area_ratio": 0.0,
        "crack_count": 0,
        "spalling_count": 0,
        "stain_count": 0,
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


def test_assess_risk_returns_medium_for_single_candidate():
    level, reason = assess_risk(make_metrics(detection_count=1, crack_count=1, avg_confidence=0.7), {"readable": True})

    assert level == "中"
    assert "结合现场情况" in reason


def test_assess_risk_returns_high_for_multi_type_damage():
    level, reason = assess_risk(
        make_metrics(
            detection_count=3,
            crack_count=1,
            spalling_count=1,
            stain_count=1,
            total_area_ratio=0.03,
            avg_confidence=0.7,
        ),
        {"readable": True},
    )

    assert level == "高"
    assert "优先复核" in reason


def test_assess_risk_returns_low_for_clean_readable_images():
    level, reason = assess_risk(make_metrics(), {"readable": True})

    assert level == "低"
    assert "常规巡检" in reason


def test_run_damage_workflow_routes_low_risk_results_to_auto_pass(monkeypatch, tmp_path):
    def fake_analyze_image(image_path, annotated_path):
        return {
            "quality": {"readable": True},
            "detections": [],
            "metrics": make_metrics(),
        }

    monkeypatch.setattr(workflow_module, "analyze_image", fake_analyze_image)

    result = run_damage_workflow(tmp_path / "source.png", tmp_path / "annotated.png")

    assert result["risk_level"] == "低"
    assert result["review_status"] == "自动通过"
    assert result["confidence"] == 0.0
    assert len(result["workflow"]) == 6
    assert result["workflow"][-1]["agent"] == "ReportArchiveAgent"


def test_run_damage_workflow_routes_high_risk_results_to_manual_review(monkeypatch, tmp_path):
    def fake_analyze_image(image_path, annotated_path):
        return {
            "quality": {
                "readable": True,
                "width": 480,
                "height": 320,
                "brightness": 180,
                "contrast": 20,
                "blur_score": 100,
            },
            "detections": [
                {"kind": "crack", "label": "裂缝疑似", "confidence": 0.8},
                {"kind": "crack", "label": "裂缝疑似", "confidence": 0.75},
            ],
            "metrics": make_metrics(detection_count=8, crack_count=8, avg_confidence=0.8),
        }

    monkeypatch.setattr(workflow_module, "analyze_image", fake_analyze_image)

    result = run_damage_workflow(tmp_path / "source.png", tmp_path / "annotated.png")

    assert result["risk_level"] == "高"
    assert result["review_status"] == "待复核"
    assert result["confidence"] == 0.8
    assert "优先复核" in result["risk_reason"]
    assert "风险=高" in result["workflow"][3]["summary"]
    assert "裂缝" in result["workflow"][2]["summary"]
    assert "可识别" in result["workflow"][0]["summary"]
