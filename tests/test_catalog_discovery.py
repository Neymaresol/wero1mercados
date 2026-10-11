from catalog_discovery import discover

def test_pagination_dedup_and_rejection():
    pages = {
        None: {"items": [
            {"sku": "A1", "title": "Produto A", "affiliate_url": "https://www.amazon.com.br/a"},
            {"sku": "A1", "title": "Produto A", "affiliate_url": "https://www.amazon.com.br/a"},
            {"sku": "X", "title": "Inválido", "affiliate_url": "https://example.com/x"}],
            "next_cursor": "next"},
        "next": {"items": [
            {"sku": "B2", "title": "Produto B", "affiliate_url": "https://www.amazon.com.br/b"}],
            "next_cursor": None}
    }
    result = discover(lambda cursor: pages[cursor], "amazon",
                      {"www.amazon.com.br"})
    assert result["unique_candidates"] == 2
    assert result["rejected"] == 1
    assert result["pages"] == 2
    assert result["publication_enabled"] is False
