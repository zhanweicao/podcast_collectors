#!/usr/bin/env python3
"""
Automated verification script for Stage 2 candidates
Uses AI analysis to determine if each candidate is a single author
Includes caching mechanism to resume from where it left off
"""
import json
import os
from typing import Dict, List, Tuple
from collections import defaultdict


class SingleAuthorAnalyzer:
    """Enhanced single author detection using multiple heuristics"""

    def __init__(self):
        # Organization indicators (strong negative)
        self.org_indicators = [
            ".com",
            ".fm",
            ".org",
            ".net",
            "llc",
            "inc",
            "corp",
            "company",
            "university",
            "college",
            "center",
            "centre",
            "institute",
            "foundation",
            "research center",
            "salem podcast",
            "whisper.fm",
            "solgoodmedia.com",
            "buzzsprout.com",
            "transistor.fm",
            "trade canyon",
            "s&p global",
            "virginia museum",
            "u.s. army",
            "christian research",
            "centre for",
            "wolfram research",
            "podcast network",
            "academic network",
            "media group",
            "broadcasting",
            "association",
            "society",
            "university of",
            "college of",
            "school of",
            "capital research center",
            "church of",
            "free church",
            "communications",
            "reformed theological seminary",
            "methodist communications",
            "baptist college",
            "royal veterinary",
            "london school",
            "research center",
            "faculty",
            "staff",
            "team",
            "crew",
            "collective",
            "group",
        ]

        # Multi-person indicators (strong negative)
        self.multi_person_indicators = [
            "&",
            " and ",
            ",",
            "co-",
            "hosts",
            "team",
            "partners",
            "with",
            "featuring",
            "/",
            "mark & adam",
            "john and jane",
            "alice & bob",
            "j.c stewart, kenyatta hoskins & mark liddell",
            "heritage and",
            "research and",
            "foundation and",
            "crew",
            "team",
            "staff",
            "students",
            "collective",
            "group",
            "band",
            "ensemble",
            "friends",
            "host and",
            "hosting with",
            "co-hosting",
            "joint hosting",
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

    def analyze_author_field(self, author: str) -> Tuple[float, List[str], List[str]]:
        """Analyze author field for single author indicators"""
        if not author:
            return 0.0, [], ["No author field provided"]

        author_lower = author.lower()
        score = 1.0
        evidence = []
        issues = []

        # Check for organization indicators (strong negative)
        org_penalty = 0
        for indicator in self.org_indicators:
            if indicator in author_lower:
                org_penalty += 0.3
                issues.append(f"Organization indicator: '{indicator}'")

        if org_penalty > 0:
            score -= min(org_penalty, 0.8)  # Cap the penalty

        # Check for multi-person indicators (strong negative)
        multi_penalty = 0
        for indicator in self.multi_person_indicators:
            if indicator in author_lower:
                multi_penalty += 0.4
                issues.append(f"Multi-person indicator: '{indicator}'")

        if multi_penalty > 0:
            score -= min(multi_penalty, 0.9)  # Cap the penalty

        # Check if it looks like a personal name (positive)
        if self._looks_like_personal_name(author):
            score += 0.3
            evidence.append(f"Personal name pattern: '{author}'")

        return max(0.0, min(1.0, score)), evidence, issues

    def _looks_like_personal_name(self, name: str) -> bool:
        """Check if name looks like a personal name"""
        if not name or len(name.strip()) == 0:
            return False

        words = name.split()

        # Handle titles like "Dr. John Smith" or "Prof. Jane Doe"
        title_words = {"dr.", "prof.", "professor", "pastor", "rev.", "reverend"}

        if words and words[0].lower() in title_words:
            remaining_words = words[1:]
            if len(remaining_words) >= 2:
                words = remaining_words

        # Must have 2-4 words to be a personal name
        if not (2 <= len(words) <= 4):
            return False

        # All words should be alphabetic and properly capitalized
        for word in words:
            clean_word = word.rstrip(".")
            if not clean_word.isalpha():
                return False
            if not clean_word[0].isupper():
                return False

        # Exclude obvious non-personal names
        name_lower = name.lower()
        non_personal_terms = [
            "podcast",
            "show",
            "radio",
            "broadcast",
            "media",
            "network",
            "crew",
            "team",
            "staff",
            "students",
            "collective",
            "group",
            "university",
            "college",
            "center",
            "institute",
            "foundation",
        ]
        if any(term in name_lower for term in non_personal_terms):
            return False

        return True

    def analyze_content(
        self, title: str, description: str
    ) -> Tuple[float, List[str], List[str]]:
        """Analyze title and description for single host indicators"""
        combined_text = f"{title} {description}".lower()
        evidence = []
        issues = []

        positive_count = 0
        negative_count = 0

        # Check positive indicators
        for indicator in self.single_host_positive:
            if indicator in combined_text:
                positive_count += 1
                evidence.append(f"Single host indicator: '{indicator}'")

        # Check for multi-host indicators
        multi_host_terms = [
            "co-host",
            "hosts",
            "team",
            "together",
            "panel",
            "multiple hosts",
            "host and",
            "hosting with",
            "co-hosting",
            "joint hosting",
        ]

        for term in multi_host_terms:
            if term in combined_text:
                negative_count += 1
                issues.append(f"Multi-host indicator: '{term}'")

        # Handle ambiguous terms
        ambiguous_terms = ["discussion", "interview", "conversation"]
        ambiguous_count = 0
        for term in ambiguous_terms:
            if term in combined_text:
                ambiguous_count += 1

        total_indicators = positive_count + negative_count + (ambiguous_count * 0.5)
        if total_indicators == 0:
            return 0.5, evidence, issues

        if total_indicators > 0:
            adjusted_negative = negative_count + (ambiguous_count * 0.5)
            score = (
                max(0.1, positive_count / (positive_count + adjusted_negative))
                if (positive_count + adjusted_negative) > 0
                else 0.5
            )
            return score, evidence, issues

        return 0.5, evidence, issues

    def is_single_author(self, candidate: Dict) -> Tuple[bool, float, Dict]:
        """Determine if candidate is a single author with confidence score and reasoning"""
        title = candidate.get("title", "")
        author = candidate.get("author", "")
        description = candidate.get("description", "")

        # Analyze author field
        author_score, author_evidence, author_issues = self.analyze_author_field(author)

        # Analyze content
        content_score, content_evidence, content_issues = self.analyze_content(
            title, description
        )

        # Combine scores with weights
        overall_score = (author_score * 0.7) + (content_score * 0.3)

        # Decision threshold (can be adjusted)
        is_single = overall_score > 0.6

        reasoning = {
            "author_score": author_score,
            "content_score": content_score,
            "overall_score": overall_score,
            "author_evidence": author_evidence,
            "author_issues": author_issues,
            "content_evidence": content_evidence,
            "content_issues": content_issues,
        }

        return is_single, overall_score, reasoning


class AutoVerifier:
    """Automated verification with caching"""

    def __init__(
        self, input_file: str = None, cache_file: str = "verification_cache.json"
    ):
        # Try to load pre-filtered candidates first, fallback to original
        if input_file is None:
            if os.path.exists("prefiltered_candidates.json"):
                input_file = "prefiltered_candidates.json"
                print("🎯 Using pre-filtered candidates for better efficiency")
            else:
                input_file = "stage2_passed_candidates.json"
                print("⚠️  Pre-filtered candidates not found, using original file")

        self.input_file = input_file
        self.cache_file = cache_file
        self.analyzer = SingleAuthorAnalyzer()

        # Load candidates
        print(f"📊 Loading candidates from {input_file}...")
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                self.candidates = json.load(f)
            print(f"✅ Loaded {len(self.candidates)} candidates")
        except Exception as e:
            print(f"❌ Error loading candidates: {e}")
            self.candidates = []
            return

        # Load cache
        self.cache = self._load_cache()
        print(f"💾 Cache contains {len(self.cache)} verified candidates")

    def _load_cache(self) -> Dict:
        """Load verification cache"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                print(f"📁 Loaded existing verification cache")
                return cache
            except Exception as e:
                print(f"⚠️  Error loading cache: {e}, starting fresh")

        return {}

    def _save_cache(self) -> None:
        """Save verification cache"""
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved verification cache with {len(self.cache)} entries")

    def _get_cache_key(self, index: int) -> str:
        """Generate cache key for candidate"""
        if index >= len(self.candidates):
            return ""
        candidate = self.candidates[index]["candidate"]
        title = candidate.get("title", "")
        author = candidate.get("author", "")
        return f"{index}_{title}_{author}"

    def get_unverified_candidates(self) -> List[int]:
        """Get list of unverified candidate indices"""
        unverified = []
        for i in range(len(self.candidates)):
            cache_key = self._get_cache_key(i)
            if cache_key not in self.cache:
                unverified.append(i)
        return unverified

    def verify_candidate(self, index: int) -> Dict:
        """Verify a single candidate"""
        if index >= len(self.candidates):
            return {}

        candidate_data = self.candidates[index]
        candidate = candidate_data["candidate"]

        # Use analyzer to determine if single author
        is_single, confidence, reasoning = self.analyzer.is_single_author(candidate)

        result = {
            "index": index,
            "title": candidate.get("title", "Unknown"),
            "author": candidate.get("author", "N/A"),
            "is_single_author": is_single,
            "confidence": confidence,
            "reasoning": reasoning,
            "verification_method": "automated_analysis",
        }

        return result

    def run_verification(self, batch_size: int = 50) -> None:
        """Run verification on unverified candidates"""
        unverified_indices = self.get_unverified_candidates()

        if not unverified_indices:
            print("✅ All candidates already verified!")
            return

        print(f"🔄 Found {len(unverified_indices)} unverified candidates")
        print(f"📊 Processing in batches of {batch_size}")

        total_processed = 0
        for batch_start in range(0, len(unverified_indices), batch_size):
            batch_end = min(batch_start + batch_size, len(unverified_indices))
            batch_indices = unverified_indices[batch_start:batch_end]

            print(
                f"\n🔄 Processing batch {batch_start//batch_size + 1}: candidates {batch_start + 1}-{batch_end} of {len(unverified_indices)}"
            )

            for i, candidate_index in enumerate(batch_indices):
                try:
                    # Verify candidate
                    result = self.verify_candidate(candidate_index)
                    if result:
                        # Cache the result
                        cache_key = self._get_cache_key(candidate_index)
                        self.cache[cache_key] = result

                        total_processed += 1

                        # Print progress
                        status = (
                            "✅ SINGLE"
                            if result["is_single_author"]
                            else "❌ NOT SINGLE"
                        )
                        confidence = result["confidence"]
                        title = result["title"][:50]
                        author = result["author"][:30]

                        print(
                            f"  {total_processed:3d}. {status} ({confidence:.2f}) - {title} (by {author})"
                        )

                        # Save cache every 10 candidates
                        if total_processed % 10 == 0:
                            self._save_cache()

                except Exception as e:
                    print(f"  ❌ Error processing candidate {candidate_index}: {e}")

            # Save batch progress
            self._save_cache()
            print(f"💾 Batch {batch_start//batch_size + 1} completed and saved")

        print(f"\n🏁 Verification complete! Processed {total_processed} candidates")
        self._save_cache()
        self.show_summary()

    def show_summary(self) -> None:
        """Show verification summary"""
        if not self.cache:
            print("📊 No verification results to show")
            return

        single_count = 0
        not_single_count = 0

        for result in self.cache.values():
            if result.get("is_single_author", False):
                single_count += 1
            else:
                not_single_count += 1

        total = len(self.cache)

        print(f"\n📊 VERIFICATION SUMMARY:")
        print(f"Total verified: {total}")
        print(f"✅ Single authors: {single_count} ({single_count/total*100:.1f}%)")
        print(
            f"❌ Not single authors: {not_single_count} ({not_single_count/total*100:.1f}%)"
        )

        # Show confidence distribution
        confidences = [result.get("confidence", 0) for result in self.cache.values()]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            print(f"📈 Average confidence: {avg_confidence:.2f}")

    def export_single_authors(
        self, output_file: str = "verified_single_authors_final.json"
    ) -> None:
        """Export verified single authors with full candidate data"""
        single_authors = []

        for result in self.cache.values():
            if result.get("is_single_author", False):
                index = result["index"]
                if index < len(self.candidates):
                    single_author_data = {
                        "verification_result": result,
                        "candidate_data": self.candidates[index],
                    }
                    single_authors.append(single_author_data)

        # Sort by confidence score (highest first)
        single_authors.sort(
            key=lambda x: x["verification_result"].get("confidence", 0), reverse=True
        )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(single_authors, f, indent=2, ensure_ascii=False)

        print(
            f"\n📤 Exported {len(single_authors)} verified single authors to {output_file}"
        )

        # Show top 20
        if single_authors:
            print(f"\n🏆 TOP 20 SINGLE AUTHORS (by confidence):")
            for i, item in enumerate(single_authors[:20], 1):
                result = item["verification_result"]
                candidate = item["candidate_data"]["candidate"]
                title = candidate.get("title", "Unknown")[:60]
                author = candidate.get("author", "N/A")[:40]
                confidence = result.get("confidence", 0)
                print(f"{i:2d}. ({confidence:.2f}) {title}")
                print(f"    By: {author}")


def main():
    print("🤖 AUTOMATED STAGE 2 VERIFICATION TOOL")
    print("=" * 50)
    print("This tool will automatically analyze each candidate to determine")
    print("if they are single authors using AI analysis.")
    print("Progress is automatically saved and resumes from where it left off.")
    print()

    verifier = AutoVerifier()

    if not verifier.candidates:
        print("❌ No candidates loaded. Exiting.")
        return

    try:
        verifier.run_verification()

        # Ask if user wants to export
        while True:
            export_choice = (
                input(f"\n📤 Export verified single authors? [y/n]: ").strip().lower()
            )
            if export_choice == "y":
                verifier.export_single_authors()
                break
            elif export_choice == "n":
                break
            else:
                print("Please enter 'y' or 'n'")

    except KeyboardInterrupt:
        print(f"\n\n⏹️  Verification interrupted by user")
        verifier._save_cache()
        print("💾 Progress saved")


if __name__ == "__main__":
    main()
