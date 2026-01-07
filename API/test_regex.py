import re

# Test the actual database content
text = """Q14: When is the half-yearly return for October 2025-March 2026 due? The second half-yearly return covering October 1, 2025 to March 31, 2026 must be submitted by April 30, 2026.
Q15: What is the deadline for filing the Annual Return for FY 2025-26? The Annual Return for FY 2025-26 (summarizing entire year's compliance) must be filed by June 30, 2026."""

requested_year = "2025-26"

# Test the regex pattern
pattern = r'Q\d+:.*?Annual Return.*?FY\s*' + re.escape(requested_year) + r'.*?([^Q]*?)(?=Q\d+|$)'
match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

print("Match found:", bool(match))
if match:
    print("Content:", repr(match.group(0)))
    date_match = re.search(r'(\w+\s+\d{1,2},?\s+\d{4})', match.group(0))
    print("Date found:", date_match.group(1) if date_match else 'No date')
else:
    print("No match found")

# Test simpler date extraction
date_matches = re.findall(r'(\w+\s+\d{1,2},?\s+\d{4})', text)
print("All dates found:", date_matches)