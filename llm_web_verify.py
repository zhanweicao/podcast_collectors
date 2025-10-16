#!/usr/bin/env python3
"""
LLM Web Verification Tool
Uses web search to verify each candidate's single-author status
"""
import json
import os
from typing import Dict, List

class LLMWebVerifier:
    """LLM-powered web verification"""
    
    def __init__(self, input_file: str = "stage2_passed_candidates.json", 
                 cache_file: str = "llm_web_verification.json"):
        self.input_file = input_file
        self.cache_file = cache_file
        
        # Load candidates
        print(f"📊 Loading candidates from {input_file}...")
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
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
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                return cache
            except:
                pass
        return {}
    
    def _save_cache(self) -> None:
        """Save verification cache"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def get_next_unverified(self) -> int:
        """Get next unverified candidate index"""
        for i in range(len(self.candidates)):
            if str(i) not in self.cache:
                return i
        return -1
    
    def prepare_candidate_for_verification(self, index: int) -> Dict:
        """Prepare candidate information for LLM web verification"""
        if index >= len(self.candidates) or index < 0:
            return {}
        
        candidate_data = self.candidates[index]
        candidate = candidate_data['candidate']
        
        return {
            'index': index,
            'title': candidate.get('title', 'Unknown'),
            'author': candidate.get('author', 'N/A'),
            'description': candidate.get('description', '')[:300],
            'url': candidate.get('url', ''),
            'total_episodes': candidate_data.get('total_target_episodes', 0),
            'transcript_episodes': candidate_data.get('transcript_episodes', 0)
        }

def main():
    print("🤖 LLM WEB VERIFICATION TOOL")
    print("=" * 50)
    
    verifier = LLMWebVerifier()
    
    if not verifier.candidates:
        print("❌ No candidates loaded.")
        return
    
    # Get next candidate to verify
    next_index = verifier.get_next_unverified()
    
    if next_index == -1:
        print("✅ All candidates have been verified!")
        return
    
    candidate_info = verifier.prepare_candidate_for_verification(next_index)
    
    print(f"🔍 CANDIDATE #{next_index + 1}/{len(verifier.candidates)}")
    print(f"📋 Title: {candidate_info['title']}")
    print(f"👤 Author: {candidate_info['author']}")
    print(f"📝 Description: {candidate_info['description']}")
    print(f"🔗 URL: {candidate_info['url']}")
    print(f"📊 Episodes: {candidate_info['transcript_episodes']}/{candidate_info['total_episodes']} with transcripts")
    
    # This is where I would use the web search tools
    # The LLM will now search for information about this podcast
    
    return candidate_info

if __name__ == "__main__":
    candidate = main()
    if candidate:
        print(f"\n🎯 Ready for web search verification of: {candidate['title']}")
