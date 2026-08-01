from app import build_payload

def test_truncates_text():
    assert len(build_payload({"to": "a", "text": "x" * 500})["text"]) == 280
