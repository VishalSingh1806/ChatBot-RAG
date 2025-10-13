import requests
import PyPDF2
import google.generativeai as genai
import pandas as pd
import os
import logging
from dotenv import load_dotenv
import io

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def download_pdf(url: str) -> bytes:
    """Download PDF from URL"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        return None

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF content"""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return ""

def generate_faqs_from_text(text: str, batch_size: int = 5000) -> list:
    """Generate FAQs from text using Gemini"""
    
    # Split text into manageable chunks
    chunks = [text[i:i+batch_size] for i in range(0, len(text), batch_size)]
    all_faqs = []
    
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1}/{len(chunks)}")
        
        prompt = f"""
        Extract comprehensive FAQs from this EPR (Extended Producer Responsibility) document text.
        
        TEXT:
        {chunk}
        
        Generate FAQs in this exact JSON format:
        [
          {{
            "question": "Clear, specific question",
            "answer": "Detailed, actionable answer with steps/requirements",
            "category": "registration|compliance|penalties|documents|recycling|reporting|exemptions|definitions",
            "priority": "high|medium|low",
            "keywords": "relevant search keywords separated by commas"
          }}
        ]
        
        Requirements:
        1. Extract 10-15 FAQs per chunk
        2. Focus on practical, actionable information
        3. Include specific procedures, requirements, deadlines
        4. Cover all aspects: registration, compliance, penalties, documents, etc.
        5. Make answers comprehensive but concise
        6. Use proper categories and keywords for search
        
        Return only valid JSON array.
        """
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            # Parse JSON response
            import json
            faqs = json.loads(response.text.strip())
            all_faqs.extend(faqs)
            
        except Exception as e:
            logger.error(f"Error processing chunk {i+1}: {e}")
            continue
    
    return all_faqs

def process_pdf_to_faqs(pdf_url: str) -> str:
    """Main function to process PDF URL and generate FAQ CSV"""
    
    logger.info(f"Starting PDF processing from: {pdf_url}")
    
    # Download PDF
    pdf_content = download_pdf(pdf_url)
    if not pdf_content:
        return "Failed to download PDF"
    
    # Extract text
    text = extract_text_from_pdf(pdf_content)
    if not text:
        return "Failed to extract text from PDF"
    
    logger.info(f"Extracted {len(text)} characters from PDF")
    
    # Generate FAQs
    faqs = generate_faqs_from_text(text)
    
    if not faqs:
        return "Failed to generate FAQs"
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(faqs)
    df['id'] = range(1, len(df) + 1)
    
    # Reorder columns
    df = df[['id', 'question', 'answer', 'category', 'priority', 'keywords']]
    
    # Save to CSV
    output_file = './data/epr_faqs_extracted.csv'
    df.to_csv(output_file, index=False)
    
    logger.info(f"✅ Generated {len(faqs)} FAQs and saved to {output_file}")
    
    return f"Successfully generated {len(faqs)} FAQs from PDF"

if __name__ == "__main__":
    # Example usage
    pdf_url = input("Enter PDF URL: ")
    result = process_pdf_to_faqs(pdf_url)
    print(result)