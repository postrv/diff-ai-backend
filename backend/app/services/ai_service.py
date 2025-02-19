# backend/app/services/ai_service.py
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from anthropic import Anthropic
from pydantic import BaseModel
import json
import re

from backend.app.config import settings

# Set up logging
logger = logging.getLogger(__name__)


class AIRequest(BaseModel):
    """Model for AI analysis request"""
    doc_a: str
    doc_b: str
    diff_data: Optional[Dict[str, Any]] = None
    conflict_resolution: str = "latest"
    guidance: Optional[Dict[str, Any]] = None


class AIService:
    """Service for AI-powered document analysis and processing"""

    def __init__(self):
        """Initialize the AI service with API client"""
        self.client = Anthropic(api_key=settings.ai_api_key)
        self.model = settings.ai_model_name
        self.max_tokens = settings.ai_max_tokens
        self.max_content_length = 15000  # Max characters to send to AI service

    async def analyze_diff(self, doc_a: str, doc_b: str, diff_data: Dict[str, Any]) -> str:
        """
        Generate an AI summary of differences between two documents.

        Args:
            doc_a: Content of the first document
            doc_b: Content of the second document
            diff_data: Pre-computed diff statistics

        Returns:
            AI-generated summary of the changes
        """
        try:
            prompt = self._build_diff_analysis_prompt(doc_a, doc_b, diff_data)

            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text
            return self._clean_ai_response(summary)

        except Exception as e:
            logger.error(f"Error in AI diff analysis: {str(e)}")
            # Fallback to a basic summary based on diff statistics
            return self._generate_fallback_summary(diff_data)

    async def smart_merge(self, request: AIRequest) -> Dict[str, Any]:
        """
        Perform an AI-assisted merge of two documents with intelligent conflict resolution.

        Args:
            request: AIRequest containing documents and merge preferences

        Returns:
            Dict containing merged document and merge report
        """
        try:
            prompt = self._build_merge_prompt(request)

            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            result = response.content[0].text

            # Extract JSON content from response
            json_match = re.search(r'```json\n(.*?)```', result, re.DOTALL)
            if json_match:
                merge_result = json.loads(json_match.group(1))
            else:
                # Try to parse entire response as JSON if no code blocks
                try:
                    merge_result = json.loads(result)
                except:
                    # Last resort: extract just the merged content
                    merge_result = {
                        "merged_content": self._extract_content(result),
                        "report": {
                            "conflicts_resolved": 0,
                            "strategy_applied": request.conflict_resolution,
                            "summary": "Merge completed with basic strategy."
                        }
                    }

            # Ensure merged content isn't too large
            if len(merge_result.get("merged_content", "")) > self.max_content_length * 2:
                merge_result["merged_content"] = merge_result["merged_content"][:self.max_content_length * 2]
                if "report" in merge_result:
                    merge_result["report"]["truncated"] = True

            return merge_result

        except Exception as e:
            logger.error(f"Error in AI-assisted merge: {str(e)}")
            # Fallback to basic merge strategy
            if request.conflict_resolution == "latest":
                content = request.doc_b
            elif request.conflict_resolution == "original":
                content = request.doc_a
            else:
                # Simple concatenation for "both" strategy
                content = f"{request.doc_a}\n\n=== MERGED WITH ===\n\n{request.doc_b}"

            return {
                "merged_content": content[:self.max_content_length * 2],
                "report": {
                    "conflicts_resolved": 0,
                    "strategy_applied": request.conflict_resolution,
                    "summary": "Fallback merge strategy applied due to AI service error."
                }
            }

    def _build_diff_analysis_prompt(self, doc_a: str, doc_b: str, diff_data: Dict[str, Any]) -> str:
        """Build prompt for diff analysis"""
        # Calculate document sizes and limit if needed
        max_content_len = self.max_content_length
        doc_a_trimmed = doc_a[:max_content_len] + ("..." if len(doc_a) > max_content_len else "")
        doc_b_trimmed = doc_b[:max_content_len] + ("..." if len(doc_b) > max_content_len else "")

        # Extract key stats
        added_lines = diff_data.get("added_lines", 0)
        removed_lines = diff_data.get("removed_lines", 0)
        changed_ratio = diff_data.get("change_ratio", 0)

        prompt = f"""As an expert document analyst, provide only a concise analysis of the differences between these two documents. Focus on key changes without prefacing or unnecessary introductions.

Document A:
```
{doc_a_trimmed}
```

Document B:
```
{doc_b_trimmed}
```

Diff Statistics:
- {added_lines} lines added
- {removed_lines} lines removed 
- {changed_ratio}% of document changed

Your analysis should:
1. Summarize key differences in 2-3 sentences
2. Identify main types of changes (additions, deletions, modifications)
3. Mention any significant structural changes
4. Note unchanged sections
5. Keep your response under 200 words

Respond with only the analysis - no introductory phrases like "Here's my analysis" or "The summary is"."""

        return prompt

    def _build_merge_prompt(self, request: AIRequest) -> str:
        """Build prompt for AI-assisted document merging"""
        # Extract merge preferences
        doc_a = request.doc_a[:self.max_content_length] + (
            "..." if len(request.doc_a) > self.max_content_length else "")
        doc_b = request.doc_b[:self.max_content_length] + (
            "..." if len(request.doc_b) > self.max_content_length else "")
        conflict_strategy = request.conflict_resolution

        # Process guidance if available
        guidance_text = ""
        if request.guidance:
            priorities = request.guidance.get("priorities", [])
            if priorities:
                guidance_text += f"Priorities: {', '.join(priorities)}\n"

            preserve_sections = request.guidance.get("preserve_sections", [])
            if preserve_sections:
                guidance_text += f"Preserve these sections: {', '.join(preserve_sections)}\n"

            custom_rules = request.guidance.get("custom_rules", [])
            if custom_rules:
                guidance_text += "Custom rules:\n"
                for rule in custom_rules:
                    guidance_text += f"- {rule}\n"

            notes = request.guidance.get("notes")
            if notes:
                guidance_text += f"Additional notes: {notes}\n"

        prompt = f"""As an expert document merge specialist, merge these two documents using intelligent conflict resolution.

Document A (Original):
```
{doc_a}
```

Document B (Modified):
```
{doc_b}
```

Merge strategy: {conflict_strategy}

{guidance_text}

Follow these rules:
1. Use the specified merge strategy as the default approach
2. If strategy is "latest", prefer Document B content for conflicts
3. If strategy is "original", prefer Document A content for conflicts
4. If strategy is "both", include both versions for conflicts with clear markers
5. If strategy is "custom", apply the provided custom rules
6. Apply intelligent resolution where appropriate (fix formatting, clear redundancies)
7. Maintain document structure and avoid duplication
8. Keep output under {self.max_content_length * 2} characters

Return your response as a JSON object with the following structure:
```json
{{
  "merged_content": "The full merged document content",
  "report": {{
    "conflicts_resolved": 5,
    "strategy_applied": "latest",
    "summary": "Brief description of how the merge was performed"
  }}
}}
```"""

        return prompt

    def _extract_content(self, text: str) -> str:
        """Extract content block from AI response if present"""
        # Try to find content between possible markers
        content_match = re.search(r'```(?:text)?\n(.*?)```', text, re.DOTALL)
        if content_match:
            return content_match.group(1)

        # Try to find content section
        section_match = re.search(r'(?:merged content|merged document|merged result):\n\n(.*)',
                                  text, re.DOTALL, re.IGNORECASE)
        if section_match:
            return section_match.group(1)

        # Return original text if no patterns match
        return text

    def _clean_ai_response(self, response: str) -> str:
        """Clean up AI response by removing artifacts and standardizing format"""
        # Remove common AI response artifacts and preambles
        common_prefixes = [
            r'^(here\'s|sure\.|i\'ll|the summary|this is|below is|a concise|here is)',
            r'^(my analysis|the analysis|an analysis|as requested|the differences)'
        ]

        cleaned = response
        for prefix_pattern in common_prefixes:
            cleaned = re.sub(prefix_pattern, '', cleaned, flags=re.IGNORECASE)

        # Remove markdown code blocks
        cleaned = re.sub(r'```(?:diff|text|markdown|json|)\n?', '', cleaned)
        cleaned = re.sub(r'```$', '', cleaned)

        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()

        return cleaned

    def _generate_fallback_summary(self, diff_data: Dict[str, Any]) -> str:
        """Generate a basic summary based on diff statistics when AI fails"""
        added_lines = diff_data.get("added_lines", 0)
        removed_lines = diff_data.get("removed_lines", 0)
        unchanged_lines = diff_data.get("unchanged_lines", 0)
        change_ratio = diff_data.get("change_ratio", 0)

        if added_lines == 0 and removed_lines == 0:
            return "The documents are identical with no detectable changes."

        # Determine significance of change
        if change_ratio < 5:
            significance = "minor"
        elif change_ratio < 20:
            significance = "moderate"
        else:
            significance = "significant"

        return (f"The comparison shows {added_lines} line(s) added and {removed_lines} line(s) removed, "
                f"representing a {significance} change ({change_ratio}% of the document). "
                f"{unchanged_lines} line(s) remained unchanged.")


# Create singleton instance
ai_service = AIService()