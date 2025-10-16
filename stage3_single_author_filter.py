#!/usr/bin/env python3
"""
Stage 3: Single Author Filtering
Applies SingleHostScriptedFilter to candidates from Stage 2 (RSS analyzed)
"""
import os
import sys
import json
import logging
from typing import List, Dict

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SingleAuthorFilter:
    """Enhanced single author filtering based on our API/RSS analysis"""

    def __init__(self):
        # Enhanced organization indicators based on our 413 candidates analysis
        # More specific organization indicators - removed overly broad "podcast"
        # Enhanced organization indicators based on manual review
        self.org_indicators = [
            ".com", ".fm", ".org", ".net", "llc", "inc", "corp", "company",
            "university", "college", "media company", "network", "studio", "radio station",
            "center", "centre", "institute", "foundation", "research center", "salem podcast",
            "whisper.fm", "solgoodmedia.com", "buzzsprout.com", "transistor.fm",
            "trade canyon", "s&p global", "virginia museum", "u.s. army",
            "christian research", "centre for", "wolfram research",
            # Additional org patterns found in manual review
            "podcast network", "academic network", "media group", "broadcasting",
            "association", "society", "university of", "college of", "school of",
            "capital research center", "church of", "free church", "communications",
            "reformed theological seminary", "methodist communications", "baptist college"
        ]

        # Enhanced multi-person indicators based on manual review
        self.multi_person_indicators = [
            "&", " and ", ",", "co-", "hosts", "team", "partners", "with",
            "featuring", "/", "&", "mark & adam", "john and jane", "alice & bob",
            # Additional patterns from our analysis  
            "j.c stewart, kenyatta hoskins & mark liddell", "heritage and",
            "research and", "foundation and",
            # Team indicators found in manual review
            "crew", "team", "staff", "students", "faculty", "collective",
            "group", "band", "ensemble"
        ]

        # Single host positive indicators
        self.single_host_positive = [
            "solo",
            "personal",
            "individual",
            "my thoughts",
            "my podcast",
            "monologue",
            "lecture",
            "story",
            "philosophy",
            "reflection",
        ]

        # Expanded scripted content indicators
        self.scripted_indicators = [
            "written", "script", "prepared", "composed", "authored", 
            "structured", "organized", "planned", "narrative", "story",
            "lecture", "episode", "series", "chronicles", "explores",
            "recounts", "presents", "delves", "investigates", "examines",
            "analysis", "reflection", "perspective", "journey", "history"
        ]

    def filter_single_author(self, candidate: Dict) -> Dict:
        """
        Apply single author filtering to a candidate

        Returns:
            {
                'candidate': original_candidate,
                'is_single_host': bool,
                'is_scripted': bool,
                'is_self_written': bool,
                'confidence_score': float,
                'evidence': List[str],
                'issues': List[str]
            }
        """

        title = candidate.get("title", "").lower()
        description = candidate.get("description", "").lower()
        author = candidate.get("author", "").lower()

        evidence = []
        issues = []

        # 1. Check author field for organization/multi-person indicators
        author_score = self._analyze_author_field(author, evidence, issues)

        # 2. Check content for single host indicators
        single_host_score = self._analyze_single_host_content(
            title, description, evidence, issues
        )

        # 3. Check for scripted content indicators
        scripted_score = self._analyze_scripted_content(
            title, description, evidence, issues
        )

        # 4. Determine final scores (adjusted thresholds for better results)
        is_single_host = author_score > 0.4 and single_host_score > 0.3
        is_scripted = scripted_score > 0.4  # Lowered from 0.5
        is_self_written = author_score > 0.3 and is_single_host  # Lowered thresholds

        confidence_score = (
            author_score * 0.5 + single_host_score * 0.3 + scripted_score * 0.2
        )

        return {
            "candidate": candidate,
            "is_single_host": is_single_host,
            "is_scripted": is_scripted,
            "is_self_written": is_self_written,
            "confidence_score": confidence_score,
            "evidence": evidence,
            "issues": issues,
            "author_score": author_score,
            "single_host_score": single_host_score,
            "scripted_score": scripted_score,
        }

    def _analyze_author_field(
        self, author: str, evidence: List[str], issues: List[str]
    ) -> float:
        """Analyze author field for single author indicators"""
        if not author:
            issues.append("No author field")
            return 0.0

        author_lower = author.lower()
        score = 1.0  # Start positive

        # Check for organization indicators (reduced penalty)
        for indicator in self.org_indicators:
            if indicator in author_lower:
                issues.append(f"Organization indicator in author: '{indicator}'")
                score -= 0.2  # Reduced from 0.4

        # Check for multi-person indicators (moderate penalty)
        for indicator in self.multi_person_indicators:
            if indicator in author_lower:
                issues.append(f"Multi-person indicator in author: '{indicator}'")
                score -= 0.25  # Reduced from 0.3

        # Check if it looks like a personal name (positive)
        if self._looks_like_personal_name(author):
            evidence.append(f"Author appears to be personal name: '{author}'")
            score += 0.2

        return max(0.0, min(1.0, score))

    def _looks_like_personal_name(self, name: str) -> bool:
        """Enhanced check if name looks like a personal name"""
        if not name or len(name.strip()) == 0:
            return False
        
        # Handle titles like "Dr. John Smith" or "Prof. Jane Doe"
        words = name.split()
        
        # Check for common titles (Dr., Prof., Pastor, etc.)
        title_words = {"dr.", "prof.", "professor", "pastor", "rev.", "reverend"}
        
        # If starts with title, check remaining words
        if words and words[0].lower() in title_words:
            remaining_words = words[1:]
            if len(remaining_words) >= 2:  # Title + FirstName + LastName
                words = remaining_words
        
        # Must have 2-3 words to be a personal name  
        if not (2 <= len(words) <= 4):  # Allow up to 4 for complex names
            return False
        
        # All words should be alphabetic and properly capitalized
        for word in words:
            # Allow periods after titles like "Jr.", "Sr.", "III"
            clean_word = word.rstrip('.')
            if not clean_word.isalpha():
                return False
            if not clean_word[0].isupper():
                return False
        
        # Exclude obvious non-personal names
        name_lower = name.lower()
        non_personal_terms = [
            "podcast", "show", "radio", "broadcast", "media", "network",
            "crew", "team", "staff", "students", "collective", "group",
            "university", "college", "center", "institute", "foundation"
        ]
        if any(term in name_lower for term in non_personal_terms):
            return False
        
        # Check for common personal name patterns
        if len(words) == 2:
            # FirstName LastName pattern
            return words[0][0].isupper() and words[1][0].isupper()
        elif len(words) == 3:
            # FirstName MiddleName LastName or complex names
            return all(word[0].isupper() for word in words)
        elif len(words) == 4:
            # Very complex names, be more careful
            return all(word[0].isupper() for word in words)
            
        return True

    def _analyze_single_host_content(
        self, title: str, description: str, evidence: List[str], issues: List[str]
    ) -> float:
        """Analyze content for single host indicators"""
        combined_text = f"{title} {description}".lower()

        positive_count = 0
        negative_count = 0

        # Check positive indicators
        for indicator in self.single_host_positive:
            if indicator in combined_text:
                positive_count += 1
                evidence.append(f"Single host indicator: '{indicator}'")

        # Check for multi-host indicators (more specific terms)
        multi_host_terms = [
            "co-host", "hosts", "team", "together", "panel", "multiple hosts",
            "host and", "hosting with", "co-hosting", "joint hosting"
        ]
        
        # Less strict indicators that might appear in single-host content
        ambiguous_terms = ["discussion", "interview", "conversation"]
        
        for term in multi_host_terms:
            if term in combined_text:
                negative_count += 1
                issues.append(f"Multi-host indicator: '{term}'")
        
        # Handle ambiguous terms - they reduce score but don't completely disqualify
        ambiguous_count = 0
        for term in ambiguous_terms:
            if term in combined_text:
                ambiguous_count += 1
        
        # Adjusted scoring: ambiguous terms reduce score by less
        total_indicators = positive_count + negative_count + (ambiguous_count * 0.5)
        if total_indicators == 0:
            return 0.5  # Neutral
            
        if total_indicators > 0:
            adjusted_negative = negative_count + (ambiguous_count * 0.5)
            return max(0.1, positive_count / (positive_count + adjusted_negative))
        
        return 0.5

    def _analyze_scripted_content(
        self, title: str, description: str, evidence: List[str], issues: List[str]
    ) -> float:
        """Analyze content for scripted indicators"""
        combined_text = f"{title} {description}".lower()

        scripted_count = 0

        for indicator in self.scripted_indicators:
            if indicator in combined_text:
                scripted_count += 1
                evidence.append(f"Scripted indicator: '{indicator}'")

        # Improved scoring - many podcasts are scripted even without explicit indicators
        if scripted_count >= 3:
            return 0.9
        elif scripted_count >= 2:
            return 0.75
        elif scripted_count == 1:
            return 0.6
        else:
            # Default to neutral-positive for podcasts (most are at least partially scripted)
            return 0.5

    def filter_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Filter a list of candidates, returning only single-author scripted ones"""
        logger.info(f"Starting single author filtering on {len(candidates)} candidates")

        filtered_results = []

        for candidate in candidates:
            result = self.filter_single_author(candidate)

            if (
                result["is_single_host"]
                and result["is_scripted"]
                and result["is_self_written"]
            ):
                filtered_results.append(result)

                logger.info(
                    f"✅ PASSED: {candidate.get('title', 'Unknown')} "
                    f"(confidence: {result['confidence_score']:.2f})"
                )
            else:
                logger.debug(
                    f"Filtered out: {candidate.get('title', 'Unknown')} "
                    f"(single: {result['is_single_host']}, "
                    f"scripted: {result['is_scripted']}, "
                    f"self_written: {result['is_self_written']})"
                )

        logger.info(
            f"Filtering complete. {len(filtered_results)} candidates passed all criteria"
        )
        return filtered_results


def main():
    """Run Stage 3 filtering on actual Stage 2 results"""
    filter_tool = SingleAuthorFilter()

    try:
        # Load Stage 2 results
        with open('stage2_passed_candidates.json', 'r', encoding='utf-8') as f:
            stage2_results = json.load(f)
        
        logger.info("=" * 60)
        logger.info(f"🚀 STAGE 3: SINGLE AUTHOR FILTERING")
        logger.info(f"Input: {len(stage2_results)} candidates from Stage 2")
        logger.info("=" * 60)
        
        # Extract candidates from Stage 2 results
        candidates = [result['candidate'] for result in stage2_results]
        
        # Run filtering
        filtered_results = filter_tool.filter_candidates(candidates)
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 STAGE 3 RESULTS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Input candidates: {len(candidates)}")
        logger.info(f"Passed single author filter: {len(filtered_results)}")
        logger.info(f"Success rate: {len(filtered_results)/len(candidates)*100:.1f}%")
        
        if filtered_results:
            logger.info(f"\n✅ PASSED CANDIDATES (first 10):")
            for i, result in enumerate(filtered_results[:10]):
                candidate = result['candidate']
                logger.info(f"{i+1}. {candidate.get('title', 'Unknown')}")
                logger.info(f"   Author: {candidate.get('author', 'N/A')}")
                logger.info(f"   Confidence: {result['confidence_score']:.2f}")
                
            # Save results
            with open('stage3_single_authors.json', 'w', encoding='utf-8') as f:
                json.dump(filtered_results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"\n💾 Results saved to stage3_single_authors.json")
        
        else:
            logger.warning("No candidates passed the single author filter!")
            
    except FileNotFoundError:
        logger.error("stage2_passed_candidates.json not found. Run Stage 2 first.")
    except Exception as e:
        logger.error(f"Error during filtering: {e}")


if __name__ == "__main__":
    main()
