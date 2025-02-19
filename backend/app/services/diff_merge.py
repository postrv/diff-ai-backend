# backend/app/services/diff_merge.py
import difflib
from typing import List, Dict, Any, Optional, Tuple
import re
import asyncio
import logging

from backend.app.config import settings
from backend.app.services.ai_service import ai_service, AIRequest

# Set up logging
logger = logging.getLogger(__name__)


class DiffResult:
    """Class representing the result of a diff operation"""

    def __init__(self,
                 diff_lines: List[Dict[str, str]],
                 stats: Dict[str, Any],
                 ai_summary: Optional[str] = None):
        self.diff_lines = diff_lines
        self.stats = stats
        self.ai_summary = ai_summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert DiffResult to dictionary for API response"""
        return {
            "diff_lines": self.diff_lines,
            "stats": self.stats,
            "ai_summary": self.ai_summary
        }


def compute_diff(document_a: str, document_b: str) -> List[Dict[str, str]]:
    """
    Basic diff function that computes differences between two documents.
    Each change is represented as a dictionary with:
      - 'type': 'added', 'removed', or 'unchanged'
      - 'line': The content of the line.
    """
    diff_lines = list(difflib.ndiff(document_a.splitlines(), document_b.splitlines()))
    diff_result = []
    for line in diff_lines:
        if line.startswith("- "):
            diff_result.append({"type": "removed", "line": line[2:]})
        elif line.startswith("+ "):
            diff_result.append({"type": "added", "line": line[2:]})
        elif line.startswith("  "):
            diff_result.append({"type": "unchanged", "line": line[2:]})
        # Lines starting with "? " are hints and can be skipped.
    return diff_result


async def compute_enhanced_diff(document_a: str, document_b: str) -> DiffResult:
    """
    Enhanced diff that provides contextual information and statistics
    about the differences between documents, with AI-powered summary.
    """
    # Basic diff calculation
    diff_lines = compute_diff(document_a, document_b)

    # Calculate statistics
    added_lines = sum(1 for line in diff_lines if line["type"] == "added")
    removed_lines = sum(1 for line in diff_lines if line["type"] == "removed")
    unchanged_lines = sum(1 for line in diff_lines if line["type"] == "unchanged")

    # Calculate word-level changes
    words_added, words_removed = _calculate_word_changes(document_a, document_b)

    # Generate change statistics
    stats = {
        "total_lines": len(diff_lines),
        "added_lines": added_lines,
        "removed_lines": removed_lines,
        "unchanged_lines": unchanged_lines,
        "words_added": words_added,
        "words_removed": words_removed,
        "change_ratio": _calculate_change_ratio(added_lines, removed_lines, len(diff_lines))
    }

    # Generate AI summary if enabled
    ai_summary = None
    if settings.ai_enabled:
        try:
            ai_summary = await ai_service.analyze_diff(document_a, document_b, stats)
        except Exception as e:
            logger.error(f"AI summary generation failed: {str(e)}")
            ai_summary = _generate_ai_summary(diff_lines, stats)
    else:
        # Fallback to basic summary
        ai_summary = _generate_ai_summary(diff_lines, stats)

    return DiffResult(diff_lines, stats, ai_summary)


def _calculate_word_changes(doc_a: str, doc_b: str) -> Tuple[int, int]:
    """Calculate word-level additions and removals"""
    words_a = re.findall(r'\w+', doc_a.lower())
    words_b = re.findall(r'\w+', doc_b.lower())

    # Simple word count difference
    words_added = max(0, len(words_b) - len(words_a))
    words_removed = max(0, len(words_a) - len(words_b))

    return words_added, words_removed


def _calculate_change_ratio(added: int, removed: int, total: int) -> float:
    """Calculate the ratio of changes to total content"""
    if total == 0:
        return 0.0
    return round((added + removed) / total * 100, 2)


def _generate_ai_summary(diff_lines: List[Dict[str, str]], stats: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of the changes.
    Used as fallback when AI service is disabled or fails.
    """
    # Simple summary based on statistics
    if stats["added_lines"] == 0 and stats["removed_lines"] == 0:
        return "No changes detected between the documents."

    summary_parts = []

    if stats["added_lines"] > 0:
        summary_parts.append(f"{stats['added_lines']} line(s) were added")

    if stats["removed_lines"] > 0:
        summary_parts.append(f"{stats['removed_lines']} line(s) were removed")

    # Calculate significance of change
    if stats["change_ratio"] < 5:
        significance = "minor"
    elif stats["change_ratio"] < 20:
        significance = "moderate"
    else:
        significance = "significant"

    change_description = " and ".join(summary_parts)
    return f"There were {change_description}, representing a {significance} change " \
           f"({stats['change_ratio']}% of the document)."


async def smart_merge_documents(
        doc_a: str,
        doc_b: str,
        conflict_resolution: str = "latest",
        guidance: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    AI-powered document merge with intelligent conflict resolution.

    Args:
        doc_a: Original document
        doc_b: Modified document
        conflict_resolution: Strategy for resolving conflicts ('latest', 'original', 'both', 'custom')
        guidance: Optional guidance for the AI merge process

    Returns:
        Dictionary containing merged content and merge report
    """
    if settings.ai_enabled:
        try:
            # Pre-calculate diff to provide context
            diff_result = await compute_enhanced_diff(doc_a, doc_b)

            # Create AI request
            request = AIRequest(
                doc_a=doc_a,
                doc_b=doc_b,
                diff_data=diff_result.stats,
                conflict_resolution=conflict_resolution,
                guidance=guidance
            )

            # Get AI-powered merge result
            merge_result = await ai_service.smart_merge(request)
            return merge_result

        except Exception as e:
            logger.error(f"AI-powered merge failed: {str(e)}")
            # Fall back to basic merge
            merged_content = merge_documents(doc_a, doc_b, conflict_resolution)
            return {
                "merged_content": merged_content,
                "report": {
                    "conflicts_resolved": 0,
                    "strategy_applied": conflict_resolution,
                    "summary": "Basic merge strategy applied due to AI service error."
                }
            }
    else:
        # Use traditional merge when AI is disabled
        merged_content = merge_documents(doc_a, doc_b, conflict_resolution)
        return {
            "merged_content": merged_content,
            "report": {
                "conflicts_resolved": 0,
                "strategy_applied": conflict_resolution,
                "summary": "Used basic merge strategy (AI service disabled)."
            }
        }


def merge_documents(doc_a: str, doc_b: str, conflict_resolution: str = "latest") -> str:
    """
    Traditional merge two documents with conflict resolution strategy.

    Args:
        doc_a: Original document
        doc_b: Modified document
        conflict_resolution: Strategy for resolving conflicts ('latest', 'original', 'both')

    Returns:
        Merged document content
    """
    # This is a placeholder implementation
    # In a real system, this would use a more sophisticated merge algorithm
    if conflict_resolution == "latest":
        return doc_b
    elif conflict_resolution == "original":
        return doc_a
    elif conflict_resolution == "both":
        # Simple concatenation for demonstration purposes
        diff = compute_diff(doc_a, doc_b)
        merged_lines = []

        for item in diff:
            if item["type"] == "unchanged":
                merged_lines.append(item["line"])
            elif item["type"] == "added":
                merged_lines.append(item["line"])
            elif item["type"] == "removed":
                # For "both" strategy, keep both versions with markers
                merged_lines.append(f"<<<ORIGINAL>>> {item['line']}")

        return "\n".join(merged_lines)
    else:
        raise ValueError(f"Unknown conflict resolution strategy: {conflict_resolution}")