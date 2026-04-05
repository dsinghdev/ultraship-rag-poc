import json
from typing import Dict, Optional
import google.generativeai as genai
from app.config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE


class StructuredExtractor:
    """Extract structured shipment data from document text."""
    
    def __init__(self):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(LLM_MODEL)
    
    def extract(self, full_text: str) -> Dict:
        """
        Extract structured shipment data from document text.
        Returns JSON with nulls for missing fields.
        """
        extraction_prompt = f"""You are an AI assistant for a Transportation Management System (TMS). 
Extract the following structured data from the logistics document text provided below.

DOCUMENT TEXT:
{full_text}

Extract the following fields. If a field is not found, return null for that field.
CRITICAL: YOUR ENTIRE RESPONSE MUST BE A SINGLE VALID JSON OBJECT ENCLOSED IN DOUBLE QUOTES.
- Do NOT use newlines inside JSON values. Use spaces instead.
- Do NOT include any markdown formatting (like ```json) or text outside the brackets. 
- Ensure every opening quote has a closing quote.

FIELDS TO EXTRACT (Exact keys required):
- shipment_id: string (shipment or reference number)
- shipper: string (shipper name/company)
- consignee: string (consignee name/company)
- pickup_datetime: string (pickup date and time, keep original format)
- delivery_datetime: string (delivery date and time, keep original format)
- equipment_type: string (e.g., Dry Van, Reefer, Flatbed)
- mode: string (e.g., FTL, LTL, Intermodal, Air, Ocean)
- rate: number (numeric value only, no currency symbol)
- currency: string (e.g., USD, EUR, CAD)
- weight: number (numeric value only, in lbs or kg)
- carrier_name: string (carrier or trucking company name)

JSON OUTPUT ONLY:"""

        response = self.model.generate_content(
            extraction_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=LLM_TEMPERATURE,
                max_output_tokens=1200
            )
        )
        
        extracted_text = response.text.strip()
        
        # Robust JSON cleaning and repair
        try:
            # 1. Clean markdown headers unconditionally
            extracted_text = extracted_text.strip()
            if extracted_text.startswith("```json"):
                extracted_text = extracted_text[7:]
            elif extracted_text.startswith("```"):
                extracted_text = extracted_text[3:]
                
            if extracted_text.endswith("```"):
                extracted_text = extracted_text[:-3]

            # 2. Force start at first { and end at last } if possible. If truncated, just start at {
            start = extracted_text.find("{")
            if start >= 0:
                extracted_text = extracted_text[start:]
                
            # 3. Handle unterminated strings (Common with truncated LLM output)
            if extracted_text.count('"') % 2 != 0:
                if extracted_text.rstrip().endswith(":"):
                    extracted_text += ' null'
                elif not extracted_text.rstrip().endswith('"'):
                    extracted_text += '"'

            # 4. Aggressive closing of JSON object
            extracted_text = extracted_text.strip()
            if not extracted_text.endswith("}"):
                extracted_text += "}"
                
            # 5. Fix common trailing commas before the newly added closing brace
            import re
            extracted_text = re.sub(r",\s*}", "}", extracted_text)

            extracted_data = json.loads(extracted_text)
            
            # Ensure all expected fields exist

            expected_fields = [
                "shipment_id", "shipper", "consignee", "pickup_datetime",
                "delivery_datetime", "equipment_type", "mode", "rate",
                "currency", "weight", "carrier_name"
            ]
            
            for field in expected_fields:
                if field not in extracted_data:
                    extracted_data[field] = None
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            return {
                "error": f"Failed to parse extracted JSON: {str(e)}",
                "raw_output": extracted_text
            }


structured_extractor = StructuredExtractor()
