from datetime import datetime, timezone

from src.ai_news_digest import Article, render_html, score_article


def test_score_prioritizes_robotics_research_terms():
    robotics = score_article(
        "University paper introduces a robotics benchmark for manipulation",
        "dataset for robot grasping and sim-to-real evaluation",
        "arXiv Robotics",
    )
    generic = score_article("New LLM chatbot model", "marketing launch", "Business News")
    assert robotics > generic


def test_business_noise_is_penalized():
    robotics = score_article("Robot control paper", "university research", "arXiv")
    business = score_article("Robotics startup earnings", "stock marketing and IPO", "News")
    assert robotics > business


def test_render_html_includes_robotics_context_and_article_links():
    articles = [
        Article("Robot Title", "https://example.com/robot", "Source", "Summary", datetime(2026, 1, 1, tzinfo=timezone.utc), 10)
    ]
    page = render_html(articles, generated_at=datetime(2026, 1, 2, tzinfo=timezone.utc))
    assert "ロボットAI研究ニュース" in page
    assert "Robot Title" in page
    assert "https://example.com/robot" in page
    assert "研究で見る観点" in page
