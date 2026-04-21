"""
Invoice PDF parser for ConstructIQ.
Extracts vendor name, line items (material, quantity, rate, total), and grand total
from vendor invoices without using any external AI API.

Strategy:
1. Try pdfplumber text extraction (works for digital/printed PDFs)
2. If text is empty or garbled, fall back to pytesseract OCR (scanned paper)
3. Apply regex patterns to extract structured fields from the text
"""

import re
import io
import os
import json
import pdfplumber
from typing import Optional
import pytesseract
from openai import OpenAI

# Add Tesseract binary path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ── REGEX PATTERNS ────────────────────────────────────────────────────────────
# These patterns cover common Indian vendor invoice formats
# (Tally, Zoho Books, QuickBooks, Excel exports, handwritten-typed)

# Vendor/supplier name — usually on the first 3 lines
VENDOR_PATTERNS = [
    r'(?:vendor|supplier|from|bill\s+from|sold\s+by)[:\s]+([A-Za-z][\w\s&.,\-]{2,60})',
    r'^([A-Z][A-Za-z\s&.,]{3,50}(?:pvt\.?\s*ltd\.?|llp|traders?|enterprises?|co\.))',
]

# Invoice number
INVOICE_NO_PATTERNS = [
    r'(?:invoice\s*(?:no|number|#)|inv\.?\s*no\.?|bill\s*no)[:\s#]*([A-Z0-9\-/]{3,20})',
    r'(?:inv|bill|vch)[:\s#]*([A-Z0-9\-/]{3,20})',
]

# Date patterns
DATE_PATTERNS = [
    r'(?:date|dt)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
]

# Total/grand total amount — INR focused
TOTAL_PATTERNS = [
    # Grand total / net payable
    r'(?:grand\s+total|net\s+(?:total|payable|amount)|total\s+(?:amount|payable)|'
    r'amount\s+(?:payable|due)|total\s+invoice\s+(?:value|amount))'
    r'[^₹\d]*(₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)',
    # Plain total
    r'\btotal\b[^₹\d]*(₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)',
    # Just a currency amount at end of document
    r'(₹|rs\.?)\s*([\d,]{4,}(?:\.\d{1,2})?)',
]

# Material line item patterns
# Matches lines like: "Cement  50  Bags  380  19000"
# or "OPC 43 Grade Cement - 50 bags @ Rs.380 = 19,000"
LINE_ITEM_PATTERNS = [
    # Format: [material] [qty] [unit] [rate] [amount]
    r'(cement|bricks?|brick|steel|sand|aggregate|gravel|concrete|tile|rod|tmt|rebar)'
    r'\D{0,20}?([\d,]+(?:\.\d+)?)\s*'
    r'(bags?|nos?|numbers?|kg|kilogram|m3|cum|cft|sft|sqft|units?)\s*'
    r'[@×x*]?\s*(?:rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)\s*'
    r'(?:rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)',
    # Simpler: material + qty + unit + total
    r'(cement|bricks?|brick|steel|sand|aggregate|gravel|concrete|tile|rod|tmt|rebar)'
    r'\D{0,30}?([\d,]+)\s*(bags?|nos?|kg|m3|units?)[^\d]*([\d,]{3,})',
]

# Known material name normalisation
MATERIAL_MAP = {
    'cement': 'cement', 'opc': 'cement', 'ppc': 'cement',
    'brick': 'bricks', 'bricks': 'bricks',
    'steel': 'steel', 'tmt': 'steel', 'rebar': 'steel', 'rod': 'steel',
    'sand': 'sand', 'fine aggregate': 'sand',
    'aggregate': 'aggregate', 'gravel': 'aggregate', 'coarse aggregate': 'aggregate',
    'tile': 'other', 'concrete': 'other',
}

UNIT_MAP = {
    'bag': 'bags', 'bags': 'bags',
    'no': 'nos', 'nos': 'nos', 'number': 'nos', 'numbers': 'nos',
    'kg': 'kg', 'kilogram': 'kg', 'kilograms': 'kg',
    'm3': 'm³', 'cum': 'm³', 'cft': 'cft',
    'sft': 'sqft', 'sqft': 'sqft',
}


def _clean_amount(s: str) -> float:
    """Convert '19,000.00' or '19000' to float."""
    if not s:
        return 0.0
    return float(s.replace(',', '').strip())


def _extract_text_pdfplumber(pdf_bytes: bytes) -> str:
    """Extract text using pdfplumber (works on digital PDFs)."""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=3, y_tolerance=3)
                if text:
                    pages_text.append(text)
            return '\n'.join(pages_text)
    except Exception as e:
        print(f'pdfplumber extraction failed: {e}')
        return ''


def _extract_text_ocr(pdf_bytes: bytes) -> str:
    """
    Fallback: convert PDF to images and run Tesseract OCR.
    Only used when pdfplumber returns empty/garbled text.
    """
    try:
        from pdf2image import convert_from_bytes
        from PIL import Image

        images = convert_from_bytes(pdf_bytes, dpi=200)
        texts = []
        for img in images:
            text = pytesseract.image_to_string(img, lang='eng')
            texts.append(text)
        return '\n'.join(texts)
    except ImportError:
        print('pytesseract/pdf2image not available — OCR fallback skipped')
        return ''
    except Exception as e:
        print(f'OCR fallback failed: {e}')
        return ''


def _is_text_useful(text: str) -> bool:
    """Check if extracted text has enough real content to parse."""
    if not text or len(text.strip()) < 50:
        return False
    # Count actual word characters vs total chars
    word_chars = sum(c.isalpha() for c in text)
    return word_chars > 30


def _extract_vendor_name(text: str) -> Optional[str]:
    for pattern in VENDOR_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            name = match.group(1).strip().rstrip('.,')
            if 2 < len(name) < 80:
                return name
    # Fallback: first non-empty line that looks like a company name
    for line in text.split('\n')[:5]:
        line = line.strip()
        if (len(line) > 3 and line[0].isupper() and
                not any(kw in line.lower() for kw in ['invoice', 'date', 'bill', 'tax'])):
            return line
    return None


def _extract_invoice_number(text: str) -> Optional[str]:
    for pattern in INVOICE_NO_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_grand_total(text: str) -> float:
    """
    Extract the grand total. Returns the LARGEST amount found near
    total-related keywords (grand total > net payable > total).
    """
    candidates = []
    for pattern in TOTAL_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            groups = match.groups()
            # Amount is always the last group
            amount_str = groups[-1]
            try:
                amount = _clean_amount(amount_str)
                if amount > 100:  # ignore tiny amounts
                    candidates.append(amount)
            except ValueError:
                pass

    if not candidates:
        return 0.0

    # Return the maximum found (grand total is always the largest)
    return max(candidates)


def _extract_line_items(text: str) -> list:
    """
    Extract individual material line items.
    Returns list of dicts with: material, quantity, unit, rate, total
    """
    items = []
    text_lower = text.lower()

    for pattern in LINE_ITEM_PATTERNS:
        for match in re.finditer(pattern, text_lower, re.IGNORECASE):
            groups = match.groups()
            try:
                if len(groups) >= 4:
                    raw_material = groups[0].strip()
                    quantity     = _clean_amount(groups[1])
                    raw_unit     = groups[2].strip()
                    # rate and total might be in groups[3] and [4]
                    if len(groups) >= 5:
                        rate  = _clean_amount(groups[3])
                        total = _clean_amount(groups[4])
                    else:
                        total = _clean_amount(groups[3])
                        rate  = total / quantity if quantity > 0 else 0

                    material = MATERIAL_MAP.get(raw_material, 'other')
                    unit     = UNIT_MAP.get(raw_unit.rstrip('s').lower(),
                                            raw_unit.lower())

                    if quantity > 0 and total > 0:
                        items.append({
                            'material':    material,
                            'quantity':    round(quantity, 2),
                            'unit':        unit,
                            'ratePerUnit': round(rate, 2),
                            'totalCost':   round(total, 2),
                            'description': match.group(0)[:60].strip(),
                        })
            except (ValueError, ZeroDivisionError):
                pass

    # Deduplicate by unique line characteristics to prevent regex pattern overlaps
    # but allow multiple distinct line items of the same material
    seen = {}
    for item in items:
        key = (item['material'], item['quantity'], item['totalCost'])
        if key not in seen:
            seen[key] = item

    return list(seen.values())


def _extract_with_nim_ai(text: str) -> Optional[dict]:
    """Use NVIDIA NIM (Llama 3) to parse the invoice text into structured JSON."""
    api_key = os.getenv('NVIDIA_API_KEY')
    if not api_key:
        return None
        
    try:
        client = OpenAI(
            base_url=os.getenv('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1'),
            api_key=api_key
        )
        model = os.getenv('NVIDIA_MODEL', 'meta/llama-3.1-8b-instruct')
        
        prompt = f"""You are an expert accounting system. Extract the invoice details from the following raw text.
Return ONLY a valid JSON object matching this exact schema:
{{
  "vendorName": "extracted company name",
  "invoiceNumber": "extracted invoice number",
  "grandTotal": 12345.0,  // MUST be the final total amount including taxes (e.g. GST), NOT the sub-total
  "lineItems": [
    {{
      "material": "cement|bricks|steel|sand|aggregate|other",
      "quantity": 100,
      "unit": "bags|nos|kg|m3|sqft|other",
      "ratePerUnit": 50.0,
      "totalCost": 5000.0,
      "description": "extract the exact text of the line item from the invoice"
    }}
  ]
}}

IMPORTANT RULES:
1. For "description", do NOT write "Original line text" or any placeholder. You MUST extract the actual descriptive text for that item from the invoice (e.g., "OPC 43 Cement UltraTech").
2. "grandTotal" MUST be the final payable amount at the bottom of the invoice (e.g., 95580.0), not the sub-total before taxes.

Raw text to parse:
---
{text}
---
"""
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1024,
        )
        
        content = response.choices[0].message.content
        # Extract JSON if it's wrapped in markdown
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]
            
        data = json.loads(content.strip())
        return data
    except Exception as e:
        print(f"NIM AI extraction failed: {e}")
        return None


def parse_invoice_pdf(pdf_bytes: bytes) -> dict:
    """
    Main entry point. Parse an invoice PDF and return structured data.

    Returns:
    {
        'success': bool,
        'vendorName': str | None,
        'invoiceNumber': str | None,
        'lineItems': [...],
        'grandTotal': float,
        'extractionMethod': 'pdfplumber' | 'ocr' | 'manual',
        'rawTextPreview': str,   # first 300 chars for debugging
        'warnings': [str],
    }
    """
    warnings = []

    # Step 1: Try pdfplumber
    text = _extract_text_pdfplumber(pdf_bytes)
    extraction_method = 'pdfplumber'

    # Step 2: If pdfplumber fails, try OCR
    if not _is_text_useful(text):
        warnings.append('PDF text extraction returned limited content — trying OCR')
        text = _extract_text_ocr(pdf_bytes)
        extraction_method = 'ocr'

    # Step 3: If still nothing, return manual entry prompt
    if not _is_text_useful(text):
        return {
            'success': False,
            'vendorName': None,
            'invoiceNumber': None,
            'lineItems': [],
            'grandTotal': 0.0,
            'extractionMethod': 'manual',
            'rawTextPreview': '',
            'warnings': [
                'Could not extract text from this invoice. '
                'This may be a hand-written invoice or a low-quality scan. '
                'Please fill in the details manually.'
            ],
        }

    # Step 4: Try AI Extraction first if configured
    ai_data = _extract_with_nim_ai(text)
    
    if ai_data and isinstance(ai_data, dict):
        vendor_name = ai_data.get('vendorName') or _extract_vendor_name(text)
        invoice_number = ai_data.get('invoiceNumber') or _extract_invoice_number(text)
        grand_total = ai_data.get('grandTotal')
        if not grand_total:
            grand_total = _extract_grand_total(text)
        line_items = ai_data.get('lineItems', [])
        extraction_method = 'nim_ai'
    else:
        # Step 5: Fallback to Regex extraction
        vendor_name    = _extract_vendor_name(text)
        invoice_number = _extract_invoice_number(text)
        grand_total    = _extract_grand_total(text)
        line_items     = _extract_line_items(text)

    if not vendor_name:
        warnings.append('Vendor name not detected — please fill manually')
    if grand_total == 0:
        warnings.append('Total amount not detected — please fill manually')
    if not line_items:
        warnings.append('No material line items detected — please add manually')

    return {
        'success': True,
        'vendorName':     vendor_name,
        'invoiceNumber':  invoice_number,
        'lineItems':      line_items,
        'grandTotal':     grand_total,
        'extractionMethod': extraction_method,
        'rawTextPreview': text[:300],
        'warnings':       warnings,
    }
