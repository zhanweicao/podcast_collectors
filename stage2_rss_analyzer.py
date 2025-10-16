#!/usr/bin/env python3
"""
Stage 2: RSS Analysis and Episode Filtering
Analyzes RSS feeds from Stage 1 candidates to find episodes in target years (2020-2024)
"""
import os
import sys
import json
import logging
import feedparser
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RSSAnalyzer:
    """Analyzes RSS feeds to filter episodes by year and transcript availability"""

    def __init__(self):
        self.target_years = {2020, 2021, 2022, 2023, 2024}

    def analyze_podcast_rss(self, candidate: Dict) -> Dict:
        """
        Analyze RSS feed for a single podcast candidate

        Returns:
            {
                'candidate': original_candidate,
                'rss_available': bool,
                'episodes_by_year': Dict[int, List],  # {2020: [episodes], 2021: [episodes], ...}
                'episodes_2024_count': int,
                'total_target_episodes': int,
                'has_sufficient_2024': bool,  # ≥2 episodes in 2024
                'transcript_episodes': List,   # Episodes with transcript links
                'validation_passed': bool,
                'issues': List[str]
            }
        """

        rss_url = candidate.get("url")
        podcast_title = candidate.get("title", "Unknown")

        if not rss_url:
            return {
                "candidate": candidate,
                "rss_available": False,
                "episodes_by_year": {},
                "episodes_2024_count": 0,
                "total_target_episodes": 0,
                "has_sufficient_2024": False,
                "transcript_episodes": [],
                "validation_passed": False,
                "issues": ["No RSS URL provided"],
            }

        try:
            logger.info(f"Analyzing RSS for: {podcast_title}")
            feed = feedparser.parse(rss_url)

            if feed.get("status") != 200:
                return {
                    "candidate": candidate,
                    "rss_available": False,
                    "episodes_by_year": {},
                    "episodes_2024_count": 0,
                    "total_target_episodes": 0,
                    "has_sufficient_2024": False,
                    "transcript_episodes": [],
                    "validation_passed": False,
                    "issues": [
                        f'RSS feed returned status {feed.get("status", "unknown")}'
                    ],
                }

            # Parse episodes and categorize by year
            episodes_by_year = {year: [] for year in self.target_years}
            transcript_episodes = []
            issues = []

            for entry in feed.get("entries", []):
                episode_info = self._parse_episode(entry)

                if episode_info["year"] in self.target_years:
                    episodes_by_year[episode_info["year"]].append(episode_info)

                    # Check for transcript availability
                    if episode_info.get("has_transcript", False):
                        transcript_episodes.append(episode_info)

            # Calculate metrics - handle both integer and string keys
            episodes_2024_count = len(
                episodes_by_year.get(2024, episodes_by_year.get(str(2024), []))
            )
            total_target_episodes = sum(
                len(episodes) for episodes in episodes_by_year.values()
            )
            has_sufficient_2024 = episodes_2024_count >= 2

            # NEW VALIDATION: Must have ≥2 episodes in EACH year (2020-2024) WITH TRANSCRIPTS
            # Handle both integer and string keys (JSON serialization converts int keys to strings)
            years_insufficient = []
            years_insufficient_transcripts = []

            for year in self.target_years:
                # Try both integer and string key access
                year_episodes = episodes_by_year.get(
                    year, episodes_by_year.get(str(year), [])
                )
                episodes_count = len(year_episodes)

                # Count episodes with transcripts for this year
                episodes_with_transcripts = sum(
                    1 for ep in year_episodes if ep.get("has_transcript", False)
                )

                if episodes_count < 2:
                    years_insufficient.append(f"{year}({episodes_count}ep)")
                elif episodes_with_transcripts < 2:
                    years_insufficient_transcripts.append(
                        f"{year}({episodes_with_transcripts}tx/{episodes_count}ep)"
                    )

            has_sufficient_all_years = (
                len(years_insufficient) == 0
                and len(years_insufficient_transcripts) == 0
            )
            validation_passed = has_sufficient_all_years

            if years_insufficient:
                issues.append(
                    f"Insufficient episodes in years: {', '.join(years_insufficient)} (need ≥2 each year)"
                )
            if years_insufficient_transcripts:
                issues.append(
                    f"Insufficient transcripts in years: {', '.join(years_insufficient_transcripts)} (need ≥2 with transcripts each year)"
                )
            elif not has_sufficient_2024:
                issues.append(f"Only {episodes_2024_count} episodes in 2024, need ≥2")

            # Log detailed year-by-year breakdown with transcript info
            year_counts = []
            transcript_counts = []
            total_transcripts = 0

            for year in sorted(self.target_years):
                year_episodes = episodes_by_year.get(
                    year, episodes_by_year.get(str(year), [])
                )
                count = len(year_episodes)
                transcript_count = sum(
                    1 for ep in year_episodes if ep.get("has_transcript", False)
                )
                total_transcripts += transcript_count

                year_counts.append(f"{year}:{count}")
                transcript_counts.append(f"{year}:{transcript_count}tx")

            logger.info(
                f"Episodes by year: {' '.join(year_counts)}, "
                f"transcripts: {' '.join(transcript_counts)}, "
                f"total: {total_target_episodes} episodes ({total_transcripts} with transcripts)"
            )

            return {
                "candidate": candidate,
                "rss_available": True,
                "episodes_by_year": episodes_by_year,
                "episodes_2024_count": episodes_2024_count,
                "total_target_episodes": total_target_episodes,
                "has_sufficient_2024": has_sufficient_2024,
                "has_sufficient_all_years": has_sufficient_all_years,
                "transcript_episodes": transcript_episodes,
                "validation_passed": validation_passed,
                "issues": issues,
            }

        except Exception as e:
            logger.error(f"Error analyzing RSS for {podcast_title}: {e}")
            return {
                "candidate": candidate,
                "rss_available": False,
                "episodes_by_year": {},
                "episodes_2024_count": 0,
                "total_target_episodes": 0,
                "has_sufficient_2024": False,
                "transcript_episodes": [],
                "validation_passed": False,
                "issues": [f"RSS parsing error: {str(e)}"],
            }

    def _parse_episode(self, entry: Dict) -> Dict:
        """Parse individual episode from RSS entry"""

        title = entry.get("title", "No title")
        published = entry.get("published", "")
        published_parsed = entry.get("published_parsed")

        # Extract year
        year = None
        if published_parsed:
            try:
                year = datetime(*published_parsed[:6]).year
            except (ValueError, TypeError):
                pass

        # Check for transcript links
        has_transcript = False
        transcript_links = []

        for link in entry.get("links", []):
            link_type = link.get("type", "").lower()
            href = link.get("href", "").lower()
            rel = link.get("rel", "").lower()

            # Check for transcript indicators
            if any(
                indicator in link_type for indicator in ["text/", "html", "transcript"]
            ):
                has_transcript = True
                transcript_links.append(link.get("href", ""))
            elif any(indicator in href for indicator in ["transcript", "text"]):
                has_transcript = True
                transcript_links.append(link.get("href", ""))

        return {
            "title": title,
            "published": published,
            "year": year,
            "has_transcript": has_transcript,
            "transcript_links": transcript_links,
            "summary": entry.get("summary", ""),
            "links": entry.get("links", []),
        }

    def analyze_candidates(
        self, candidates: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Analyze multiple candidates and return only those meeting criteria"""

        logger.info(f"Starting RSS analysis for {len(candidates)} candidates")

        analyzed_results = []
        passed_candidates = []

        for i, candidate in enumerate(candidates, 1):
            logger.info(
                f"Analyzing {i}/{len(candidates)}: {candidate.get('title', 'Unknown')}"
            )
            result = self.analyze_podcast_rss(candidate)
            analyzed_results.append(result)

            if result["validation_passed"]:
                passed_candidates.append(result)
                logger.info(
                    f"✅ {candidate.get('title', 'Unknown')}: "
                    f"has ≥2 episodes per year (2020-2024)"
                )
            else:
                issues = result.get("issues", [])
                issue_msg = issues[0] if issues else "validation failed"
                logger.debug(f"❌ {candidate.get('title', 'Unknown')}: {issue_msg}")

        logger.info(
            f"RSS analysis complete. {len(passed_candidates)} candidates "
            f"passed all-years episode criteria (≥2 per year 2020-2024)"
        )

        return analyzed_results, passed_candidates

    def save_analysis_results(
        self, analyzed_results: List[Dict], filename: str = "rss_analysis_results.json"
    ) -> bool:
        """Save detailed analysis results to JSON file"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(
                    analyzed_results, f, indent=2, ensure_ascii=False, default=str
                )
            logger.info(f"Saved detailed analysis results to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            return False

    def save_passed_candidates(
        self,
        passed_candidates: List[Dict],
        filename: str = "stage2_passed_candidates.json",
    ) -> bool:
        """Save candidates that passed RSS criteria to JSON file"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(
                    passed_candidates, f, indent=2, ensure_ascii=False, default=str
                )
            logger.info(
                f"Saved {len(passed_candidates)} passed candidates to {filename}"
            )
            return True
        except Exception as e:
            logger.error(f"Error saving passed candidates: {e}")
            return False


def main():
    """Test the RSS analyzer"""

    analyzer = RSSAnalyzer()

    # Load candidates from Stage 1 if available
    try:
        with open("api_candidates.json", "r", encoding="utf-8") as f:
            candidates = json.load(f)
            logger.info(f"Loaded {len(candidates)} candidates from Stage 1")
    except FileNotFoundError:
        logger.warning("No api_candidates.json found. Run Stage 1 first.")
        candidates = []

    if candidates:
        logger.info(
            f"Starting comprehensive RSS analysis of {len(candidates)} candidates"
        )

        # Analyze ALL candidates (not just first 20)
        analyzed_results, passed_candidates = analyzer.analyze_candidates(candidates)

        # Save detailed results
        analyzer.save_analysis_results(analyzed_results, "rss_analysis_results.json")
        analyzer.save_passed_candidates(
            passed_candidates, "stage2_passed_candidates.json"
        )

        # Summary statistics
        logger.info(f"\n📊 STAGE 2 COMPLETE RESULTS:")
        logger.info(f"Total analyzed: {len(analyzed_results)}")
        logger.info(
            f"Passed all-years criteria (≥2 episodes per year 2020-2024): {len(passed_candidates)}"
        )
        logger.info(
            f"Success rate: {len(passed_candidates)/len(analyzed_results)*100:.1f}%"
        )

        # Show sample results with year breakdown
        logger.info(f"\n📋 SAMPLE PASSED CANDIDATES:")
        for i, result in enumerate(passed_candidates[:5]):  # Show first 5 passed
            candidate = result["candidate"]
            episodes_by_year = result.get("episodes_by_year", {})
            logger.info(f"{i+1}. {candidate.get('title', 'Unknown')}")

            # Show episode count per year
            year_counts = []
            for year in sorted([2020, 2021, 2022, 2023, 2024]):
                count = len(
                    episodes_by_year.get(year, episodes_by_year.get(str(year), []))
                )
                year_counts.append(f"{year}:{count}")
            logger.info(f"   Episodes by year: {' '.join(year_counts)}")
            logger.info(f"   Total target episodes: {result['total_target_episodes']}")

        logger.info(f"\n✅ Stage 2 complete! Results saved to:")
        logger.info(f"  - rss_analysis_results.json (detailed results)")
        logger.info(f"  - stage2_passed_candidates.json (passed candidates)")
        logger.info(f"Next: Run Stage 3 single author filtering")

    else:
        logger.error("No candidates to analyze. Run api_podcast_collector.py first.")


if __name__ == "__main__":
    main()
