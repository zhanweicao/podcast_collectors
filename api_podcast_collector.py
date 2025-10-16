#!/usr/bin/env python3
"""
API-based podcast collector for the first stage of our collection pipeline
"""
import os
import sys
import requests
import hashlib
import time
import json
from typing import List, Dict
import logging

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PodcastAPICollector:
    """Collect podcast candidates via PodcastIndex API"""

    def __init__(self):
        self.api_key = "DSB4MHAG3KJTMKNAT9HA"
        self.api_secret = "dca#tw6eXRcn7cN2rAKK4esE4z#4e6PBSTvQq$Zx"
        self.base_url = "https://api.podcastindex.org/api/1.0"

    def _make_authenticated_request(
        self, url: str, params: dict = None
    ) -> requests.Response:
        """Make authenticated API request to PodcastIndex"""
        timestamp = str(int(time.time()))
        auth_string = self.api_key + self.api_secret + timestamp
        sha1_auth = hashlib.sha1(auth_string.encode("utf-8")).hexdigest()

        headers = {
            "User-Agent": "PodcastCollector/1.0",
            "X-Auth-Key": self.api_key,
            "X-Auth-Date": timestamp,
            "Authorization": sha1_auth,
        }

        response = requests.get(url, headers=headers, params=params or {}, timeout=10)
        response.raise_for_status()
        return response

    def collect_candidates(self, target_count: int = 5000) -> List[Dict]:
        """
        Collect podcast candidates from multiple categories

        Target: 5000+ candidates optimized for transcript-rich content
        Strategy (Two-phase approach):
        - Phase 1: 16 explicit transcript searches × 200 results
        - Phase 2: 38 categories × 10 transcript-optimized terms × 200 results
        - Total potential: 80,000+ searches focused on scripted content
        - Basic filtering: ~50% loss → 2500+ remaining
        - Stage 2 (RSS time + transcript): ~40% loss → 1500 remaining (better rates due to focus)
        - Stage 3 (single author filter): ~75% loss → 375 remaining
        - Stage 4 (final selection): ~50% loss → 187 final
        """
        logger.info(f"Starting API collection with target: {target_count} candidates")

        all_candidates = []
        seen_ids = set()

        # Search categories that typically have transcript/scripted content
        # Focus on educational, academic, and structured content types
        categories = [
            # Core educational/academic (high transcript probability)
            "lecture",
            "academic",
            "university",
            "college",
            "teaching",
            "education",
            # Structured analytical content (likely scripted)
            "philosophy",
            "analysis",
            "research",
            "economics",
            "history",
            "science",
            # Individual reflection/thought content (often prepared)
            "reflection",
            "monologue",
            "thoughts",
            "personal",
            "individual",
            # Written/spoken content with scripts
            "storytelling",
            "literature",
            "books",
            "writing",
            "reading",
            # Specialty areas that often have transcripts
            "psychology",
            "theology",
            "ethics",
            "morality",
            "mindfulness",
            "meditation",
            "spirituality",
            # Business/professional (often structured)
            "business",
            "technology",
            "health",
            "medicine",
        ]

        # First, try specific transcript-oriented searches
        transcript_searches = [
            "transcript podcast",
            "scripted podcast",
            "written podcast",
            "prepared speech",
            "lecture podcast",
            "academic podcast",
            "monologue podcast",
            "reflection podcast",
            "analysis podcast",
            "philosophy lecture",
            "history lecture",
            "science lecture",
            "education lecture",
            "research podcast",
            "university podcast",
            "college lecture",
        ]

        logger.info("Phase 1: Searching for explicitly transcript-oriented content")
        for term in transcript_searches:
            if len(all_candidates) >= target_count:
                break
            try:
                candidates = self._search_podcasts(term, max_results=200)
                new_count = 0
                for candidate in candidates:
                    candidate_id = candidate.get("id")
                    if candidate_id and candidate_id not in seen_ids:
                        if self._basic_filter(candidate):
                            all_candidates.append(candidate)
                            seen_ids.add(candidate_id)
                            new_count += 1
                logger.info(
                    f"  Transcript search '{term}': Found {new_count} new candidates"
                )
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error searching '{term}': {e}")

        logger.info("Phase 2: Searching by categories")
        for category in categories:
            if len(all_candidates) >= target_count:
                break

            logger.info(f"Searching category: {category}")

            # Search terms optimized for transcript-rich content
            search_terms = [
                f"{category} lecture",
                f"{category} podcast",
                f"{category} analysis",
                f"{category} thoughts",
                f"{category} reflection",
                f"{category} monologue",
                f"{category} script",
                f"{category} written",
                f"{category} prepared",
                f"{category} academic",
            ]

            for term in search_terms:
                if len(all_candidates) >= target_count:
                    break

                try:
                    candidates = self._search_podcasts(
                        term, max_results=200
                    )  # Increased from 100

                    # Add unique candidates
                    new_count = 0
                    for candidate in candidates:
                        candidate_id = candidate.get("id")
                        if candidate_id and candidate_id not in seen_ids:
                            if self._basic_filter(candidate):  # Basic filtering
                                all_candidates.append(candidate)
                                seen_ids.add(candidate_id)
                                new_count += 1

                    logger.info(f"  Term '{term}': Found {new_count} new candidates")
                    time.sleep(1)  # Rate limiting

                except Exception as e:
                    logger.error(f"Error searching '{term}': {e}")

        logger.info(
            f"Collection complete. Total unique candidates: {len(all_candidates)}"
        )
        return all_candidates

    def _search_podcasts(self, query: str, max_results: int = 200) -> List[Dict]:
        """Search podcasts using API"""
        url = f"{self.base_url}/search/byterm"
        params = {
            "q": query,
            "max": min(max_results, 500),  # API limit is 500
            "pretty": "true",
        }

        response = self._make_authenticated_request(url, params)
        data = response.json()
        return data.get("feeds", [])

    def _basic_filter(self, candidate: Dict) -> bool:
        """
        Basic filtering for Stage 1 - ONLY basic criteria

        NOTE: Single author filtering happens in Stage 3, not here!
        """

        # Must have basic required fields
        if not candidate.get("id") or not candidate.get("url"):
            return False

        # Language filtering (English only)
        language = candidate.get("language", "").lower()
        if not (language.startswith("en") or language == "english"):
            return False

        # Episode count check (need substantial content for 5 years)
        episode_count = candidate.get("episodeCount", 0)
        if episode_count < 20:  # At least 20 episodes (5 years × 4 per year minimum)
            return False

        # Activity check for 2020-2024 target period
        # Goal: Ensure podcast was active until 2024+ so we can find episodes in 2024
        last_update = candidate.get("lastUpdateTime", 0)
        newest_episode = candidate.get("newestItemPubdate", 0)

        if last_update > 0 and newest_episode > 0:
            from datetime import datetime

            # Convert timestamps to dates
            last_update_date = datetime.fromtimestamp(last_update)
            newest_date = datetime.fromtimestamp(newest_episode)

            # Check 1: Must have been active at least until 2024-01-01
            # This ensures we can potentially find episodes during 2024
            if last_update_date.year < 2024:
                logger.debug(
                    f"Podcast {candidate.get('title', 'Unknown')} inactive before 2024: "
                    f"last updated {last_update_date.strftime('%Y-%m-%d')}"
                )
                return False

            # Check 2: Must have at least one episode from 2024+ (basic check)
            # Detailed 2024 episode count (≥2) will be verified in Stage 2 RSS analysis
            if newest_date.year < 2024:
                logger.debug(
                    f"Podcast {candidate.get('title', 'Unknown')} no episodes in 2024: "
                    f"newest episode {newest_date.strftime('%Y-%m-%d')}"
                )
                return False

            # Note: Stage 2 will verify ≥2 episodes in 2024-01-01 to 2024-12-31

        # DO NOT filter by author patterns here - that's Stage 3!
        # We want to collect candidates like:
        # - "Whisper.fm" (organization - will be filtered later)
        # - "Mark & Adam Bishop" (multi-person - will be filtered later)
        # - "solgoodmedia.com" (company - will be filtered later)

        return True

    def save_candidates(
        self, candidates: List[Dict], filename: str = "api_candidates.json"
    ) -> bool:
        """Save collected candidates to JSON file"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(candidates, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(candidates)} candidates to {filename}")
            return True

        except Exception as e:
            logger.error(f"Error saving candidates: {e}")
            return False

    def load_candidates(self, filename: str = "api_candidates.json") -> List[Dict]:
        """Load candidates from JSON file"""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                candidates = json.load(f)

            logger.info(f"Loaded {len(candidates)} candidates from {filename}")
            return candidates

        except FileNotFoundError:
            logger.warning(f"File {filename} not found")
            return []
        except Exception as e:
            logger.error(f"Error loading candidates: {e}")
            return []


def main():
    """Main collection function"""
    collector = PodcastAPICollector()

    # We need a large number due to heavy filtering in later stages
    TARGET_CANDIDATES = 5000  # Increased from 2000 for better coverage

    logger.info("=" * 60)
    logger.info("🎯 PODCAST API COLLECTION - STAGE 1")
    logger.info("=" * 60)
    logger.info(f"Target: {TARGET_CANDIDATES} candidates")
    logger.info("Rationale:")
    logger.info("  - RSS time filtering (2020-2024 + transcript): ~60% loss")
    logger.info("  - Single author filtering: ~75% loss")
    logger.info("  - Final selection (2 per year): ~50% loss")
    logger.info("  - Expected final result: ~100 podcasts")

    # Collect candidates
    candidates = collector.collect_candidates(target_count=TARGET_CANDIDATES)

    # Save results
    if candidates:
        collector.save_candidates(candidates)

        # Summary statistics
        logger.info("\n📊 COLLECTION SUMMARY:")
        logger.info(f"Total candidates collected: {len(candidates)}")

        # Analyze by author patterns (from our test data)
        org_count = 0
        multi_person_count = 0

        for candidate in candidates:
            author = candidate.get("author", "").lower()
            if any(
                indicator in author for indicator in [".com", ".fm", ".org", ".net"]
            ):
                org_count += 1
            elif any(
                indicator in author for indicator in ["&", " and ", "co-", "hosts"]
            ):
                multi_person_count += 1

        logger.info(f"Organization authors: {org_count}")
        logger.info(f"Multi-person authors: {multi_person_count}")
        logger.info(
            f"Potential single authors: {len(candidates) - org_count - multi_person_count}"
        )

        logger.info(f"\n✅ Stage 1 complete! Candidates saved to 'api_candidates.json'")
        logger.info("Next: Run RSS analysis on these candidates")

    else:
        logger.error("No candidates collected!")


if __name__ == "__main__":
    main()
