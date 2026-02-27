#!/usr/bin/env python3
"""
Recreate UDB (Updated Database) with correct 768-dimensional embeddings
for ARF deadline queries
"""
import chromadb
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# UDB path in production
UDB_PATH = "/var/lib/chatbot/UDB/Updated_DB"

print(f"Connecting to UDB at: {UDB_PATH}")
client = chromadb.PersistentClient(path=UDB_PATH)

# Delete existing collection and recreate
try:
    client.delete_collection(name="updated_db")
    print("✓ Deleted old updated_db collection")
except:
    print("ℹ No existing collection to delete")

collection = client.get_or_create_collection(name="updated_db")
print(f"✓ Created fresh updated_db collection")
print(f"Current documents in UDB: {collection.count()}")

# Updated timeline data for 2024-25 and 2025-26 with correct deadline
timeline_data = [
    {
        "text": "The latest applicable deadline for filing the EPR Annual Return for the financial year 2024–2025 is 31 January 2026 as per the most recent extension issued by the Central Pollution Control Board under the Plastic Waste Management Rules.",
        "metadata": {"source": "CPCB_2024-25_Update", "year": "2024-25", "type": "annual_return_deadline"}
    },
    {
        "text": "For FY 2024-25 (April 1, 2024 to March 31, 2025), the Annual Report Filing (ARF) deadline for plastic EPR is January 31, 2026 as per CPCB notification.",
        "metadata": {"source": "CPCB_2024-25_Update", "year": "2024-25", "type": "annual_return_deadline"}
    },
    {
        "text": "The last date for filing the plastic waste EPR Annual Return for financial year 2024-25 is 31st January 2026 according to CPCB guidelines.",
        "metadata": {"source": "CPCB_2024-25_Update", "year": "2024-25", "type": "annual_return_deadline"}
    },
    {
        "text": "All registered entities are required to complete EPR credit generation, transfer, utilization, and annual compliance reporting for FY 2024–25 by 31 January 2026 on the CPCB EPR Portal.",
        "metadata": {"source": "CPCB_2024-25_Compliance", "year": "2024-25", "type": "compliance_requirements"}
    },
    {
        "text": "EPR compliance workflows for FY 2024–25 remain aligned with the extended submission window ending 31 January 2026, including reconciliation of EPR credits and final return submission.",
        "metadata": {"source": "CPCB_2024-25_Compliance", "year": "2024-25", "type": "compliance_workflow"}
    },
    {
        "text": "For the financial year 2025-26 (April 1, 2025 – March 31, 2026), the deadline for filing the Plastic EPR Annual Return is June 30, 2026 as per CPCB notification.",
        "metadata": {"source": "CPCB_2025-26_Update", "year": "2025-26", "type": "annual_return_deadline"}
    },
    {
        "text": "The annual report filing deadline for FY 2025-26 is June 30, 2026 as per CPCB notification.",
        "metadata": {"source": "CPCB_2025-26_Update", "year": "2025-26", "type": "annual_return_deadline"}
    },
    {
        "text": "EPR certificates for plastic waste collected and recycled must be obtained quarterly throughout 2025-26. Q1 (April-June 2025): July 31, 2025. Q2 (July-September 2025): October 31, 2025. Q3 (October-December 2025): January 31, 2026. Q4 (January-March 2026): April 30, 2026. Upload them to the portal within the quarterly return deadlines to avoid Environmental Compensation.",
        "metadata": {"source": "CPCB_2025-26_Quarterly", "year": "2025-26", "type": "quarterly_obligations"}
    },
    {
        "text": "Barcode and QR code traceability on all plastic packaging is mandatory from 1 July 2025 onwards for Producers, Importers and Brand Owners and continues to apply for all future compliance periods.",
        "metadata": {"source": "PWM_Amendment_2024", "year": "2025-26", "type": "compliance_requirements"}
    },
    {
        "text": "Importers are required to ensure barcode or QR code compliance and valid CPCB EPR portal registration, which is verified by customs authorities from 2 July 2025 onwards in line with EPR compliance requirements.",
        "metadata": {"source": "PWM_Amendment_2024", "year": "2025-26", "type": "importer_requirements"}
    },
    {
        "text": "Mandatory use of recycled plastic content in plastic packaging applies on a progressive basis from 2025–26 and continues to increase through 2026–27, 2027–28, and 2028–29 onwards as per category-specific requirements.",
        "metadata": {"source": "PWM_Amendment_2024", "year": "2025-26", "type": "recycled_content"}
    },
    {
        "text": "Recycling target levels increase further from financial year 2027–28 onwards including higher targets for rigid and flexible plastic packaging categories.",
        "metadata": {"source": "PWM_Rules", "year": "2027-28", "type": "recycling_targets"}
    },
    {
        "text": "The Plastic Waste Management Amendment Rules notified on 14 March 2024 form the current legal framework governing EPR obligations, recycling targets and compliance timelines for plastic packaging.",
        "metadata": {"source": "PWM_Amendment_2024", "year": "2024", "type": "legal_framework"}
    },
    {
        "text": "Recycled plastic content reporting and additional compliance metrics will be implemented on a phased basis from FY 2025–26 onwards, subject to official notifications issued by CPCB and MoEFCC.",
        "metadata": {"source": "PWM_Amendment_2024", "year": "2025-26", "type": "reporting_requirements"}
    },
    {
        "text": "State Pollution Control Boards and Pollution Control Committees may issue state-specific enforcement directions applicable during FY 2025–26 and FY 2026–27, based on CPCB guidance and compliance assessments.",
        "metadata": {"source": "PWM_Rules", "year": "2025-26", "type": "state_enforcement"}
    }
]

# Generate embeddings and add to collection using correct 768-dimensional embeddings
print("\nAdding updated timeline data to UDB with 768-dimensional embeddings...")
for i, item in enumerate(timeline_data):
    # Generate embedding with correct dimensionality
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=item["text"],
        task_type="retrieval_document",
        output_dimensionality=768  # CRITICAL: Use 768 dimensions to match other databases
    )
    embedding = result['embedding']

    # Add to collection
    collection.add(
        documents=[item["text"]],
        embeddings=[embedding],
        metadatas=[item["metadata"]],
        ids=[f"timeline_update_{i}"]
    )
    print(f"[{i+1}/{len(timeline_data)}] Added: {item['metadata']['year']} - {item['metadata']['type']}")

print(f"\n✓ UDB updated successfully!")
print(f"✓ Total documents: {collection.count()}")
print(f"✓ All documents use 768-dimensional embeddings")
