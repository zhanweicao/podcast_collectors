#!/usr/bin/env python3
"""
Web-based verification tool for Stage 2 candidates
Uses web search to verify if each podcast is truly single-authored
"""
import json
import os
from typing import Dict, List, Tuple
from collections import defaultdict

class WebVerifier:
    """Web-based verification using search capabilities"""
    
    def __init__(self, input_file: str = "stage2_passed_candidates.json", 
                 cache_file: str = "web_verification_cache.json"):
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
                print(f"📁 Loaded existing web verification cache")
                return cache
            except Exception as e:
                print(f"⚠️  Error loading cache: {e}, starting fresh")
        
        return {}
    
    def _save_cache(self) -> None:
        """Save verification cache"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved web verification cache with {len(self.cache)} entries")
    
    def _get_cache_key(self, index: int) -> str:
        """Generate cache key for candidate"""
        if index >= len(self.candidates):
            return ""
        candidate = self.candidates[index]['candidate']
        title = candidate.get('title', '')
        author = candidate.get('author', '')
        return f"{index}_{title}_{author}"
    
    def get_unverified_candidates(self) -> List[int]:
        """Get list of unverified candidate indices"""
        unverified = []
        for i in range(len(self.candidates)):
            cache_key = self._get_cache_key(i)
            if cache_key not in self.cache:
                unverified.append(i)
        return unverified
    
    def search_podcast_info(self, candidate: Dict) -> Dict:
        """
        Search for podcast information using web search
        This function will be called by the LLM with web search capabilities
        """
        title = candidate.get('title', '')
        author = candidate.get('author', '')
        
        # Prepare search queries
        search_queries = [
            f'"{title}" podcast host author',
            f'"{title}" "{author}" podcast creator',
            f'"{title}" podcast who writes scripts',
            f'"{author}" podcast single host author'
        ]
        
        # Return structure for web search analysis
        verification_request = {
            'title': title,
            'author': author,
            'description': candidate.get('description', ''),
            'search_queries': search_queries,
            'analysis_needed': [
                "Is this podcast hosted/written by a single person?",
                "Does the author field represent an individual or organization/team?", 
                "Are the episodes written by multiple people or just one host?",
                "Is this a solo show or does it have co-hosts/team members?",
                "Are the scripts/transcripts written by the host themselves?"
            ]
        }
        
        return verification_request
    
    def verify_candidate_with_web_search(self, index: int) -> Dict:
        """
        Verify a single candidate using web search results
        This will be implemented to use actual web search
        """
        if index >= len(self.candidates):
            return {}
        
        candidate_data = self.candidates[index]
        candidate = candidate_data['candidate']
        
        # Get verification request for web search
        verification_request = self.search_podcast_info(candidate)
        
        # This is where we would use the web search tool
        # For now, we'll return the structure for manual web search
        
        result = {
            'index': index,
            'title': candidate.get('title', 'Unknown'),
            'author': candidate.get('author', 'N/A'),
            'verification_request': verification_request,
            'verification_method': 'web_search_needed'
        }
        
        return result
    
    def run_web_verification_batch(self, batch_size: int = 10) -> None:
        """Run web verification on a batch of unverified candidates"""
        unverified_indices = self.get_unverified_candidates()
        
        if not unverified_indices:
            print("✅ All candidates already verified!")
            return
        
        print(f"🔍 Found {len(unverified_indices)} unverified candidates")
        print(f"📊 Processing batch of {min(batch_size, len(unverified_indices))}")
        
        # Process batch
        batch_indices = unverified_indices[:batch_size]
        
        for i, candidate_index in enumerate(batch_indices):
            try:
                candidate_data = self.candidates[candidate_index]
                candidate = candidate_data['candidate']
                
                title = candidate.get('title', 'Unknown')
                author = candidate.get('author', 'N/A')
                
                print(f"\n🔍 VERIFYING CANDIDATE {i+1}/{len(batch_indices)}")
                print(f"📋 Title: {title}")
                print(f"👤 Author: {author}")
                
                # Prepare verification request
                verification_request = self.search_podcast_info(candidate)
                
                print(f"\n🔗 SEARCH QUERIES FOR WEB SEARCH:")
                for j, query in enumerate(verification_request['search_queries'], 1):
                    print(f"  {j}. {query}")
                
                print(f"\n🤖 ANALYSIS NEEDED:")
                for j, question in enumerate(verification_request['analysis_needed'], 1):
                    print(f"  {j}. {question}")
                
                # For now, we'll just save the verification request
                # In practice, this would trigger actual web search and LLM analysis
                result = {
                    'index': candidate_index,
                    'title': title,
                    'author': author,
                    'verification_request': verification_request,
                    'status': 'pending_web_search',
                    'verification_method': 'web_search_request'
                }
                
                # Cache the result
                cache_key = self._get_cache_key(candidate_index)
                self.cache[cache_key] = result
                
                print(f"\n💾 Saved verification request for web search analysis")
                
            except Exception as e:
                print(f"❌ Error processing candidate {candidate_index}: {e}")
        
        # Save batch progress
        self._save_cache()
        print(f"\n💾 Batch completed and saved")
    
    def show_verification_requests(self, count: int = 20) -> None:
        """Show pending verification requests that need web search"""
        pending_requests = []
        
        for result in self.cache.values():
            if result.get('status') == 'pending_web_search':
                pending_requests.append(result)
        
        if not pending_requests:
            print("📊 No pending web search requests")
            return
        
        print(f"\n🔍 PENDING WEB SEARCH REQUESTS ({len(pending_requests)} total):")
        
        for i, request in enumerate(pending_requests[:count], 1):
            print(f"\n{i:2d}. {request['title']}")
            print(f"    Author: {request['author']}")
            
            queries = request['verification_request']['search_queries']
            print(f"    Search queries:")
            for j, query in enumerate(queries[:2], 1):  # Show first 2 queries
                print(f"      {j}. {query}")

def main():
    print("🌐 WEB-BASED VERIFICATION TOOL")
    print("=" * 50)
    print("This tool prepares web search requests for each candidate")
    print("to verify if they are truly single-authored podcasts.")
    print()
    
    verifier = WebVerifier()
    
    if not verifier.candidates:
        print("❌ No candidates loaded. Exiting.")
        return
    
    try:
        # Process a batch of candidates
        verifier.run_web_verification_batch(batch_size=20)
        
        # Show pending requests
        verifier.show_verification_requests()
        
        print(f"\n🎯 NEXT STEPS:")
        print("1. Use web search to investigate each pending request")
        print("2. Analyze the search results to determine if each podcast is single-authored")
        print("3. Update the cache with verification results")
                
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Verification interrupted by user")
        verifier._save_cache()
        print("💾 Progress saved")

if __name__ == "__main__":
    main()
