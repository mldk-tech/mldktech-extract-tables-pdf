import cv2
import camelot
import json
import pandas as pd
from pdf2image import convert_from_path
import os

def find_and_extract_tables(pdf_path, output_dir="output"):
    """
    Finds tables in a PDF, including those without borders, extracts them,
    and saves them as JSON and Markdown files.

    Args:
        pdf_path (str): The path to the input PDF file.
        output_dir (str): The directory to save the output files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Convert PDF pages to images
    print("Step 1: Converting PDF pages to high-resolution images...")
    images = convert_from_path(pdf_path, dpi=300)

    all_tables_data = []

    for page_num, image in enumerate(images):
        page_image_path = os.path.join(output_dir, f'page_{page_num + 1}.png')
        image.save(page_image_path, 'PNG')
        
        print(f"\n--- Processing Page {page_num + 1} ---")
        
        # 2. Use OpenCV to detect table-like structures (contours)
        img = cv2.imread(page_image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding to get a binary image
        binary = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -2)

        # Find contours
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        potential_tables = []
        
        # 3. Filter contours to identify potential tables
        print("Step 2 & 3: Detecting potential table areas using layout analysis...")
        for i, contour in enumerate(contours):
            # Approximate the contour to a polygon
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            # We are looking for large rectangular shapes
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                
                # Filter based on size and aspect ratio to avoid noise (e.g., small boxes, full page)
                # These values may need tuning for different document types
                if w > 300 and h > 100 and w < (img.shape[1] * 0.95) and h < (img.shape[0] * 0.9):
                    # Check if it's not a nested contour (e.g., a box inside another box)
                    if hierarchy[0][i][3] == -1: # No parent
                        potential_tables.append((x, y, w, h))
                        # For visualization: draw a green rectangle around potential tables
                        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)

        if not potential_tables:
            print("No potential tables found on this page based on layout.")
            continue
            
        # Save the visualized image
        visualization_path = os.path.join(output_dir, f'page_{page_num + 1}_detected.png')
        cv2.imwrite(visualization_path, img)
        print(f"Saved visualization with detected areas to: {visualization_path}")

        # 4. Extract data from the detected areas using Camelot
        print("Step 4: Extracting data from detected areas with Camelot...")
        img_height, img_width, _ = img.shape
        
        for i, (x, y, w, h) in enumerate(potential_tables):
            # Convert image coordinates to PDF coordinates for Camelot
            # Camelot's coordinate system is (x1, y1, x2, y2) with top-left origin
            # y-coordinates are measured from the bottom of the page in PDF space
            pdf_y1 = img_height - (y + h)
            pdf_y2 = img_height - y
            table_area_coords = f"{x},{pdf_y2},{x+w},{pdf_y1}" # x1,y1,x2,y2 (y1 is top)

            try:
                # Use Camelot's 'lattice' for bordered tables and 'stream' for borderless
                # Here we use 'stream' as it is more robust for our use case
                tables = camelot.read_pdf(
                    pdf_path,
                    pages=str(page_num + 1),
                    flavor='stream', # 'stream' is designed for tables without borders
                    table_areas=[table_area_coords]
                )

                if tables.n > 0:
                    print(f"  > Successfully extracted {tables.n} table(s) from area {i+1} on page {page_num + 1}")
                    for table_index, table in enumerate(tables):
                        df = table.df
                        
                        # A simple heuristic to check if extraction was successful
                        if df.shape[0] > 1 and df.shape[1] > 1:
                            all_tables_data.append({
                                "page": page_num + 1,
                                "table_number": len(all_tables_data) + 1,
                                "data": df
                            })
                else:
                    print(f"  > Camelot found no structured table in area {i+1} on page {page_num + 1}.")
            
            except Exception as e:
                print(f"Error processing area {i+1} on page {page_num + 1} with Camelot: {e}")

    # 5. Convert extracted data to JSON and Markdown
    print("\nStep 5: Converting all extracted tables to JSON and Markdown formats...")
    if not all_tables_data:
        print("Extraction complete. No valid tables were found in the document.")
        return

    # JSON Output
    json_output_path = os.path.join(output_dir, "extracted_tables.json")
    json_data = []
    for table_info in all_tables_data:
        df_dict = table_info['data'].to_dict(orient='records')
        json_data.append({
            "page": table_info['page'],
            "table_number": table_info['table_number'],
            "table_data": df_dict
        })

    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)
    print(f"Successfully saved all tables as JSON to: {json_output_path}")

    # Markdown Output
    markdown_output_path = os.path.join(output_dir, "extracted_tables.md")
    with open(markdown_output_path, 'w', encoding='utf-8') as f:
        for table_info in all_tables_data:
            f.write(f"## Page: {table_info['page']}, Table: {table_info['table_number']}\n\n")
            markdown_table = table_info['data'].to_markdown(index=False)
            f.write(markdown_table)
            f.write("\n\n---\n\n")
    print(f"Successfully saved all tables as Markdown to: {markdown_output_path}")

# --- USAGE EXAMPLE ---
if __name__ == "__main__":
    # Replace 'your_document.pdf' with the path to your PDF file
    pdf_file_path = "your_document.pdf" 
    if os.path.exists(pdf_file_path):
        find_and_extract_tables(pdf_file_path)
    else:
        print(f"Error: The file '{pdf_file_path}' was not found. Please update the path.")