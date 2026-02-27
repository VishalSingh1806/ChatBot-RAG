"""
CPCB Data Scraper - Automated EPR Portal Data Collection
Intelligent scraping using Gemini 2.0 Experimental to fetch latest notifications, rules, and updates
"""

import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Optional
from datetime import datetime
import json
import time
import re
import urllib3

# Disable SSL warnings for government sites with cert issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))


class CPCBDataScraper:
    def __init__(self, output_dir: str = "./scraped_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Session for better performance with SSL verification disabled
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.session.verify = False  # Disable SSL verification for govt sites

        # Gemini model
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch webpage content safely"""
        try:
            print(f"  📡 Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()

            # Get clean text
            text = soup.get_text(separator='\n', strip=True)
            text = re.sub(r'\n\s*\n', '\n\n', text)

            print(f"  ✅ Fetched {len(text)} characters")
            return text.strip()

        except Exception as e:
            print(f"  ⚠️  Error fetching {url}: {type(e).__name__}")
            return None

    def gemini_web_research(self, topic: str) -> Optional[str]:
        """Use Gemini to research and provide comprehensive information"""
        try:
            prompt = f"""You are an expert on Indian environmental regulations, specifically CPCB (Central Pollution Control Board) and plastic EPR (Extended Producer Responsibility).

Research and provide comprehensive, factual, and up-to-date information about: {topic}

Include:
1. Latest notifications and updates (with dates if available)
2. Current rules, regulations, and amendments
3. Important deadlines and compliance requirements
4. Registration and filing procedures
5. Recent changes or extensions
6. Penalty provisions if applicable

Format the response as a detailed, well-structured document with clear sections.
Be specific with dates, numbers, and requirements.
If you mention any deadline extensions or changes, be very explicit about:
- What changed
- Original deadline vs new deadline
- Effective date of the change
- Who is affected

Provide accurate information only. If unsure about something, indicate that clearly."""

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            print(f"  ⚠️  Gemini research error: {e}")
            return None

    def gemini_analyze_webpage(self, url: str, content: str) -> Optional[Dict]:
        """Use Gemini to analyze and extract relevant EPR information from webpage"""
        try:
            # Limit content size for Gemini
            if len(content) > 30000:
                content = content[:30000] + "\n... [content truncated]"

            prompt = f"""Analyze this webpage content from {url} and extract ALL information related to:
- Plastic EPR (Extended Producer Responsibility)
- CPCB notifications and updates
- Plastic Waste Management rules
- Registration requirements
- Filing deadlines and extensions
- Compliance requirements
- Penalties and regulations

Webpage content:
{content}

If there is relevant EPR/plastic waste information, provide:
1. A comprehensive summary of all relevant information
2. Key dates and deadlines mentioned
3. Important requirements or changes
4. Links to documents if mentioned

If there is NO relevant information, respond with just: "NO_RELEVANT_CONTENT"

Be thorough and extract all EPR-related details."""

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            if result_text == "NO_RELEVANT_CONTENT" or len(result_text) < 100:
                return None

            return {
                "type": "webpage_analysis",
                "content": result_text,
                "source_url": url,
                "date": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"  ⚠️  Gemini analysis error: {e}")
            return None

    def scrape_and_analyze_url(self, url: str) -> List[Dict]:
        """Fetch and analyze a URL using Gemini"""
        print(f"\n🌐 Analyzing: {url}")
        documents = []

        content = self.fetch_page_content(url)
        if not content or len(content) < 500:
            print("  ⏭️  Insufficient content, skipping")
            return documents

        # Use Gemini to analyze the content
        result = self.gemini_analyze_webpage(url, content)
        if result:
            documents.append(result)
            print(f"  ✅ Extracted relevant EPR information")
        else:
            print(f"  ⏭️  No relevant EPR content found")

        return documents

    def research_specific_topics(self) -> List[Dict]:
        """Use Gemini to research specific EPR topics comprehensively"""
        print("\n" + "="*70)
        print("🔬 Conducting Intelligent Research on EPR Topics")
        print("="*70)

        topics = [
            # Critical current topics
            "CPCB plastic EPR annual return filing deadline 2024 - original June deadline extended to November 2024 - full details",

            # Registration and compliance
            "CPCB plastic EPR registration process 2024 - requirements, documents, certificates, and timeline",

            # Rules and regulations
            "Plastic Waste Management Rules 2022 - latest amendments, updates, and compliance requirements",

            # Filing requirements
            "CPCB EPR quarterly return filing for plastic - Q1 Q2 Q3 Q4 deadlines, format, and submission process 2024-2025",

            # Portal and technical
            "CPCB EPR portal eprplastic.cpcb.gov.in - registration, login, filing process, technical updates 2024",

            # Obligations and targets
            "Plastic EPR targets and obligations in India - brand owners, importers, and PIBOs - 2024-2025 compliance",

            # PWM Rules comprehensive
            "Plastic Waste Management PWM Rules India - producer responsibility, collection targets, EPR certificate trading",

            # Recent notifications
            "Latest CPCB notifications and circulars for plastic EPR - 2024 updates, deadline extensions, new requirements",

            # Penalties and enforcement
            "CPCB plastic EPR penalties and enforcement - non-compliance consequences, fines, legal actions 2024",

            # Categories and materials
            "CPCB EPR plastic categories 1 2 3 4 - definitions, different requirements, and compliance for each category",
        ]

        documents = []

        for i, topic in enumerate(topics, 1):
            print(f"\n📚 Research {i}/{len(topics)}: {topic[:80]}...")

            content = self.gemini_web_research(topic)

            if content and len(content) > 200:
                documents.append({
                    "type": "research_document",
                    "content": content,
                    "topic": topic,
                    "date": datetime.now().isoformat(),
                    "source": "Gemini 2.0 Exp Intelligent Research"
                })
                print(f"  ✅ Generated comprehensive research document ({len(content)} chars)")

                # Rate limiting
                time.sleep(3)
            else:
                print(f"  ⚠️  Research failed or insufficient content")

        print(f"\n✅ Completed {len(documents)}/{len(topics)} research documents")
        return documents

    def try_scrape_known_urls(self) -> List[Dict]:
        """Try to scrape known CPCB/EPR URLs"""
        print("\n" + "="*70)
        print("🌐 Attempting to Scrape Known URLs")
        print("="*70)

        urls_to_try = [
            "https://cpcb.nic.in",
            "https://eprplastic.cpcb.gov.in",
            "https://moef.gov.in",
            "https://cpcb.nic.in/plastic-waste-management/",
        ]

        documents = []

        for url in urls_to_try:
            try:
                docs = self.scrape_and_analyze_url(url)
                documents.extend(docs)
                time.sleep(2)  # Be respectful
            except Exception as e:
                print(f"  ❌ Failed to process {url}: {e}")

        return documents

    def generate_faq_content(self) -> List[Dict]:
        """Generate comprehensive FAQ content using Gemini"""
        print("\n" + "="*70)
        print("❓ Generating FAQ and Common Queries Content")
        print("="*70)

        faqs = [
            "What is the plastic EPR annual return filing deadline for 2024? Was it extended from June to November?",
            "How to register for plastic EPR on CPCB portal? Step by step process",
            "What are the different plastic categories under EPR? Category 1, 2, 3, 4 explained",
            "What are quarterly filing requirements for plastic EPR? When are Q1, Q2, Q3, Q4 due?",
            "What documents are needed for plastic EPR registration?",
            "What are the penalties for non-compliance with plastic EPR regulations?",
            "How does EPR certificate trading work in India?",
            "What are the plastic collection targets for brand owners and PIBOs?",
            "What is the difference between brand owner, importer, and PIBO under plastic EPR?",
            "How to file plastic EPR returns on CPCB portal - technical process",
        ]

        documents = []

        for i, faq in enumerate(faqs, 1):
            print(f"\n❓ FAQ {i}/{len(faqs)}: {faq[:60]}...")

            try:
                prompt = f"""You are an expert on India's plastic EPR regulations. Answer this question comprehensively:

Question: {faq}

Provide:
1. Clear, detailed answer with current information (2024-2025)
2. Specific dates, deadlines, and requirements
3. Step-by-step process if applicable
4. References to relevant rules or notifications
5. Practical tips for compliance

Be accurate and thorough."""

                response = self.model.generate_content(prompt)
                content = response.text

                if content and len(content) > 100:
                    documents.append({
                        "type": "faq",
                        "content": f"Q: {faq}\n\nA: {content}",
                        "question": faq,
                        "date": datetime.now().isoformat(),
                        "source": "Gemini 2.0 Exp FAQ Generation"
                    })
                    print(f"  ✅ Generated FAQ answer ({len(content)} chars)")
                    time.sleep(2)

            except Exception as e:
                print(f"  ⚠️  FAQ generation error: {e}")

        print(f"\n✅ Generated {len(documents)} FAQ documents")
        return documents

    def scrape_all(self) -> List[Dict]:
        """Main method - comprehensive intelligent data collection"""
        print("\n" + "="*70)
        print("🚀 CPCB Intelligent Data Scraper - Gemini 2.0 Exp Powered")
        print("="*70)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        all_documents = []

        # Strategy 1: Deep research on specific topics (Most Reliable)
        print("\n🎯 STRATEGY 1: Comprehensive Topic Research")
        research_docs = self.research_specific_topics()
        all_documents.extend(research_docs)

        # Strategy 2: Generate FAQ content (Very Useful)
        print("\n🎯 STRATEGY 2: FAQ Generation")
        faq_docs = self.generate_faq_content()
        all_documents.extend(faq_docs)

        # Strategy 3: Try to scrape actual websites (Best Effort)
        print("\n🎯 STRATEGY 3: Website Scraping")
        web_docs = self.try_scrape_known_urls()
        all_documents.extend(web_docs)

        # Save to JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.output_dir, f"cpcb_data_{timestamp}.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_documents, f, indent=2, ensure_ascii=False)

        # Print summary
        print("\n" + "="*70)
        print("✅ Intelligent Scraping Complete!")
        print("="*70)
        print(f"\n📊 Total documents collected: {len(all_documents)}")
        print(f"💾 Saved to: {output_file}")

        # Document breakdown
        types = {}
        for doc in all_documents:
            doc_type = doc.get('type', 'unknown')
            types[doc_type] = types.get(doc_type, 0) + 1

        print(f"\n📈 Document breakdown:")
        for doc_type, count in types.items():
            print(f"   {doc_type}: {count}")

        print("="*70)

        return all_documents


def main():
    """Test the scraper"""
    scraper = CPCBDataScraper()
    documents = scraper.scrape_all()

    print(f"\n✅ Successfully collected {len(documents)} documents")


if __name__ == "__main__":
    main()
