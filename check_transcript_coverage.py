#!/usr/bin/env python3
"""
Check transcript coverage in the current 525 candidates
"""
import json

def check_transcript_coverage():
    print("=== CHECKING TRANSCRIPT COVERAGE ===")
    
    try:
        with open('stage2_passed_candidates.json', 'r', encoding='utf-8') as f:
            passed_candidates = json.load(f)
        
        print(f"\n📊 Analyzing {len(passed_candidates)} candidates for transcript availability")
        
        candidates_with_transcripts = 0
        total_episodes_with_transcripts = 0
        total_episodes = 0
        
        transcript_stats_by_year = {2020: 0, 2021: 0, 2022: 0, 2023: 0, 2024: 0}
        episodes_by_year = {2020: 0, 2021: 0, 2022: 0, 2023: 0, 2024: 0}
        
        for result in passed_candidates[:50]:  # Check first 50 for speed
            candidate = result.get('candidate', {})
            episodes_by_year_dict = result.get('episodes_by_year', {})
            transcript_episodes = result.get('transcript_episodes', [])
            
            title = candidate.get('title', 'Unknown')
            
            # Count transcripts by year
            candidate_has_transcripts = False
            for year in [2020, 2021, 2022, 2023, 2024]:
                # Get episodes for this year
                year_episodes = episodes_by_year_dict.get(year, episodes_by_year_dict.get(str(year), []))
                episodes_by_year[year] += len(year_episodes)
                
                # Count transcripts for this year in this candidate
                year_transcript_count = 0
                for episode in year_episodes:
                    if episode.get('has_transcript', False):
                        year_transcript_count += 1
                        total_episodes_with_transcripts += 1
                    total_episodes += 1
                
                transcript_stats_by_year[year] += year_transcript_count
                
                if year_transcript_count > 0:
                    candidate_has_transcripts = True
            
            if candidate_has_transcripts:
                candidates_with_transcripts += 1
            
            # Show sample for first few
            if len([r for r in passed_candidates[:10] if r == result]) <= 10:
                transcript_count = len(transcript_episodes)
                print(f"\n{candidate.get('title', 'Unknown')[:50]}")
                print(f"  Transcript episodes: {transcript_count}")
                
                # Show transcript distribution by year
                for year in [2020, 2021, 2022, 2023, 2024]:
                    year_episodes = episodes_by_year_dict.get(year, episodes_by_year_dict.get(str(year), []))
                    year_transcripts = sum(1 for ep in year_episodes if ep.get('has_transcript', False))
                    year_total = len(year_episodes)
                    if year_total > 0:
                        print(f"  {year}: {year_transcripts}/{year_total} episodes with transcripts")
        
        # Summary statistics
        print(f"\n📈 TRANSCRIPT COVERAGE SUMMARY (First 50 candidates):")
        print(f"Candidates with at least some transcripts: {candidates_with_transcripts}/{min(50, len(passed_candidates))} ({candidates_with_transcripts/min(50, len(passed_candidates))*100:.1f}%)")
        
        if total_episodes > 0:
            overall_transcript_rate = total_episodes_with_transcripts / total_episodes * 100
            print(f"Overall transcript coverage: {total_episodes_with_transcripts}/{total_episodes} ({overall_transcript_rate:.1f}%)")
        
        print(f"\n📅 TRANSCRIPT COVERAGE BY YEAR:")
        for year in [2020, 2021, 2022, 2023, 2024]:
            year_total = episodes_by_year[year]
            year_transcripts = transcript_stats_by_year[year]
            if year_total > 0:
                rate = year_transcripts / year_total * 100
                print(f"  {year}: {year_transcripts}/{year_total} episodes ({rate:.1f}%)")
        
        if overall_transcript_rate < 50:  # Less than 50% have transcripts
            print(f"\n🚨 ISSUE: Low transcript coverage!")
            print(f"   We need to add transcript validation to Stage 2 filtering.")
            print(f"   Currently selecting candidates without ensuring transcript availability.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_transcript_coverage()
