from p0_tag_acquisition import classify_channel, tag_for_channel, safe_campaign, internal_landing

def test_search_and_social_tags():
    assert tag_for_channel("google") == "TAG_01"
    assert tag_for_channel("chatgpt") == "TAG_01"
    assert tag_for_channel("tiktok") == "TAG_02"
    assert tag_for_channel("creator") == "TAG_02"
    assert tag_for_channel("unknown") == "DIRECT"

def test_unknown_source_does_not_claim_referral():
    assert classify_channel("google.evil.example") == "direct"
    assert internal_landing(116, "google.evil.example") == "/go/116?channel=direct"

def test_safe_internal_landing_only():
    assert internal_landing(116, "google", "busca_2026") == "/go/116?channel=google&campaign=busca_2026"
    assert safe_campaign("https://example.com/?token=secret") == ""
    assert "token" not in internal_landing(116, "creator", "https://example.com/?token=secret")

def test_invalid_offer_id():
    import pytest
    for bad in (0, -1, True):
        with pytest.raises(ValueError):
            internal_landing(bad, "google")
