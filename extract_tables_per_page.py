import cv2
import json
import pandas as pd
from pdf2image import convert_from_path
import os
import re
import pytesseract
from PIL import Image

# ----------------- OCR CONFIGURATION -----------------
# For Windows users: Update this path to where Tesseract is installed.
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except Exception:
    print("Tesseract not found at specified path. Ensure it's installed and the path is correct or in your system's PATH.")
# -----------------------------------------------------

def post_process_and_structure(raw_text):
    """
    Analyzes raw text to build a structured JSON object.
    This function is used for both full-document and per-page analysis.
    """
    structured_output = {
        "document_type": "Unknown", "invoice_number": None, "date": None,
        "summary": {"subtotal": None, "vat": None, "total": None},
        "detected_line_items": []
    }
    
    full_text_for_analysis = raw_text.replace('  ', ' ')

    if re.search(r'חשבונית מס', full_text_for_analysis): structured_output['document_type'] = 'Tax Invoice'
    elif re.search(r'קבלה', full_text_for_analysis): structured_output['document_type'] = 'Receipt'

    date_match = re.search(r'(\d{2}[./]\d{2}[./]\d{2,4})', full_text_for_analysis)
    if date_match: structured_output['date'] = date_match.group(1)

    invoice_num_match = re.search(r'(?:חשבונית מס|חשבונית|מספר|invoice no\.?)\s*:?\s*([א-תA-Za-z0-9-]+)', full_text_for_analysis, re.IGNORECASE)
    if invoice_num_match: structured_output['invoice_number'] = invoice_num_match.group(1)

    lines = full_text_for_analysis.split('\n')
    for line in lines:
        if re.search(r'(סה"כ לתשלום|סך הכל|סה"כ|Total)', line, re.IGNORECASE):
            amount_match = re.search(r'(\d{1,3}(,\d{3})*|\d+)(\.\d{2})?', line)
            if amount_match and not structured_output["summary"]["total"]:
                structured_output["summary"]["total"] = float(amount_match.group(0).replace(',', ''))
        
        if re.search(r'(מע"מ|VAT|מ\.ע\.מ)', line, re.IGNORECASE):
            amount_match = re.search(r'(\d{1,3}(,\d{3})*|\d+)(\.\d{2})?', line)
            if amount_match and not structured_output["summary"]["vat"]:
                structured_output["summary"]["vat"] = float(amount_match.group(0).replace(',', ''))
    
    line_items = []
    for line in lines:
        if len(re.findall(r'\d+\.?\d*', line)) >= 2 and len(line) > 15:
            line_items.append(line)
    structured_output['detected_line_items'] = line_items

    return structured_output


def analyze_scanned_document_with_ocr(pdf_path, output_dir="output"):
    """
    Main orchestrator for scanned/image-based PDFs.
    Provides full-document analysis, per-page breakdown, and saves page images.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Step 1: Converting PDF pages to high-resolution images...")
    images = convert_from_path(pdf_path, dpi=300)
    
    pages_content = []

    for page_num, image in enumerate(images):
        print(f"\n--- Processing Page {page_num + 1} ---")
        
        # --- NEW: Save the image of the current page ---
        page_image_path = os.path.join(output_dir, f'page_{page_num + 1}.png')
        image.save(page_image_path, 'PNG')
        print(f"Saved page image to: {page_image_path}")
        
        # --- OCR STEP ---
        print(f"Step 2: Performing OCR on page {page_num + 1}...")
        try:
            page_text = pytesseract.image_to_string(image, lang='heb+eng')
            pages_content.append({
                "page_number": page_num + 1,
                "text": page_text
            })
            print(f"Successfully extracted text from page {page_num + 1}.")
        except Exception as e:
            print(f"Error during OCR on page {page_num + 1}: {e}")
            continue

    print("\nStep 3: Performing semantic analysis...")
    if not pages_content:
        print("OCR process failed to extract any text from the document.")
        return

    # --- Full Document Analysis ---
    print("Analyzing the document as a whole...")
    full_text_from_all_pages = "\n\n".join([page['text'] for page in pages_content])
    document_analysis = post_process_and_structure(full_text_from_all_pages)

    # --- Per-Page Analysis ---
    print("Analyzing each page individually...")
    per_page_analysis = []
    for page_data in pages_content:
        page_analysis = post_process_and_structure(page_data['text'])
        per_page_analysis.append({
            "page_number": page_data['page_number'],
            "analysis": page_analysis,
            "raw_text": page_data['text']
        })

    # --- Combine into final structure ---
    final_output = {
        "document_analysis": document_analysis,
        "per_page_analysis": per_page_analysis
    }

    json_output_path = os.path.join(output_dir, "structured_document_with_pages.json")
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)
        
    print(f"\n✅ Analysis complete! Structured data saved to: {json_output_path}")
    print("\n--- Final Structured Data ---")
    print(json.dumps(final_output, ensure_ascii=False, indent=4))

# --- USAGE EXAMPLE ---
if __name__ == "__main__":
    pdf_file_path = "your_scanned_document.pdf" 
    
    if os.path.exists(pdf_file_path):
        analyze_scanned_document_with_ocr(pdf_file_path)
    else:
        print(f"Error: The file '{pdf_file_path}' was not found. Please update the path.")