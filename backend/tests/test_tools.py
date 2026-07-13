from app.tools import build_tools


def test_history_tool_exposes_summary_alias():
    tools = build_tools(db=object())
    names = [getattr(tool, "name", None) for tool in tools]
    assert "summarize_hcp_history" in names
    assert "summary_hcp_history" in names
