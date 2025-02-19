# backend/tests/test_diff_merge.py
import pytest
import asyncio
from backend.app.services.diff_merge import compute_diff, compute_enhanced_diff, merge_documents


def test_compute_diff():
    """Test basic diff computation."""
    doc_a = "line1\nline2\nline3"
    doc_b = "line1\nline2 modified\nline3"

    diff = compute_diff(doc_a, doc_b)

    # Check that the diff contains at least one added and one removed change
    added = any(change for change in diff if change["type"] == "added")
    removed = any(change for change in diff if change["type"] == "removed")

    assert added and removed
    assert len(diff) > 0


@pytest.mark.asyncio
async def test_compute_enhanced_diff():
    """Test enhanced diff with statistics."""
    doc_a = "This is the first line.\nThis is the second line.\nThis is the third line."
    doc_b = "This is the first line.\nThis is the modified second line.\nThis is the third line.\nThis is a new line."

    result = await compute_enhanced_diff(doc_a, doc_b)

    # Check that result has expected structure
    assert hasattr(result, 'diff_lines')
    assert hasattr(result, 'stats')
    assert hasattr(result, 'ai_summary')

    # Check stats are correctly calculated
    assert result.stats['added_lines'] > 0
    assert result.stats['removed_lines'] > 0
    assert 'change_ratio' in result.stats
    assert 'words_added' in result.stats
    assert 'words_removed' in result.stats

    # Check AI summary is generated
    assert result.ai_summary is not None
    assert len(result.ai_summary) > 0


def test_merge_documents():
    """Test document merging with different strategies."""
    doc_a = "line1\nline2\nline3"
    doc_b = "line1\nline2 modified\nline3\nline4"

    # Test "latest" strategy
    latest_merge = merge_documents(doc_a, doc_b, "latest")
    assert latest_merge == doc_b

    # Test "original" strategy
    original_merge = merge_documents(doc_a, doc_b, "original")
    assert original_merge == doc_a

    # Test "both" strategy
    both_merge = merge_documents(doc_a, doc_b, "both")
    assert "line1" in both_merge
    assert "line2 modified" in both_merge
    assert "line4" in both_merge

    # Test invalid strategy
    with pytest.raises(ValueError):
        merge_documents(doc_a, doc_b, "invalid_strategy")


@pytest.mark.asyncio
async def test_smart_merge_documents():
    """Test smart document merging with AI."""
    from backend.app.services.diff_merge import smart_merge_documents

    doc_a = "This document contains important information about the project timeline."
    doc_b = "This document contains critical information about the updated project timeline and budget."

    # Test with default strategy
    result = await smart_merge_documents(doc_a, doc_b)

    assert "merged_content" in result
    assert "report" in result
    assert isinstance(result["report"], dict)
    assert "strategy_applied" in result["report"]

    # Test with custom guidance
    guidance = {
        "priorities": ["accuracy", "completeness"],
        "preserve_sections": ["timeline"],
        "custom_rules": ["Keep all dates from Document B"]
    }

    result_with_guidance = await smart_merge_documents(
        doc_a, doc_b, conflict_resolution="custom", guidance=guidance
    )

    assert "merged_content" in result_with_guidance
    assert len(result_with_guidance["merged_content"]) > 0