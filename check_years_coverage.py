#!/usr/bin/env python3
"""
Check if the Stage 2 candidates actually have episodes in ALL years 2020-2024
"""
import json
from collections import defaultdict


def analyze_years_coverage():
    print("=== CHECKING YEARS COVERAGE (2020-2024) ===")

    try:
        with open("stage2_passed_candidates.json", "r", encoding="utf-8") as f:
            passed_candidates = json.load(f)

        print(f"\n📊 Analyzing {len(passed_candidates)} passed candidates")

        years_coverage_stats = {2020: 0, 2021: 0, 2022: 0, 2023: 0, 2024: 0}

        candidates_with_all_years = 0
        candidates_missing_years = []

        for i, result in enumerate(
            passed_candidates[:100]
        ):  # Check first 100 for speed
            candidate = result.get("candidate", {})
            episodes_by_year = result.get("episodes_by_year", {})

            title = candidate.get("title", "Unknown")

            # Count which years have episodes
            years_with_episodes = []
            years_without_episodes = []

            for year in [2020, 2021, 2022, 2023, 2024]:
                year_episodes = episodes_by_year.get(year, [])
                if year_episodes:
                    years_coverage_stats[year] += 1
                    years_with_episodes.append(year)
                else:
                    years_without_episodes.append(year)

            if len(years_with_episodes) == 5:  # All 5 years
                candidates_with_all_years += 1
            else:
                candidates_missing_years.append(
                    {
                        "title": title,
                        "missing_years": years_without_episodes,
                        "years_with_episodes": years_with_episodes,
                    }
                )

        # Summary
        total_checked = min(100, len(passed_candidates))
        print(f"\n📈 YEARS COVERAGE (Checked first {total_checked} candidates):")
        for year in [2020, 2021, 2022, 2023, 2024]:
            count = years_coverage_stats[year]
            percentage = count / total_checked * 100
            print(f"  {year}: {count} candidates ({percentage:.1f}%)")

        print(
            f"\n✅ Candidates with ALL 5 years (2020-2024): {candidates_with_all_years}/{total_checked} ({candidates_with_all_years/total_checked*100:.1f}%)"
        )

        if candidates_missing_years:
            print(f"\n❌ Candidates missing some years (first 10):")
            for i, cand in enumerate(candidates_missing_years[:10]):
                print(f"  {i+1}. {cand['title']}")
                print(f"     Missing: {cand['missing_years']}")
                print(f"     Has: {cand['years_with_episodes']}")

        # This is the problem!
        if candidates_with_all_years < total_checked * 0.5:  # Less than 50%
            print(f"\n🚨 ISSUE IDENTIFIED:")
            print(f"   Most candidates do NOT have episodes in all years 2020-2024!")
            print(f"   Our Stage 2 validation is incomplete.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    analyze_years_coverage()
