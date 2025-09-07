# Advanced PDF Table Extractor

A powerful Python script designed to automatically detect and extract tables from PDF documents, including complex cases where tables lack visible borders. It leverages computer vision techniques for layout analysis and converts the extracted data into structured formats like JSON and Markdown.

-----

## Overview

Extracting tabular data from PDFs is a common but challenging task, especially when dealing with documents that have inconsistent formatting or tables without clear line boundaries. This tool provides a robust pipeline to overcome these challenges. It works by first converting PDF pages into images, then using OpenCV to analyze the document's layout and identify rectangular regions that likely contain tables. Finally, it uses the Camelot library to parse and extract the structured data from these identified regions.

This approach makes it highly effective for financial reports, academic papers, invoices, and other documents where tables are visually, but not structurally, defined.

## Features ✨

  * **Layout-Aware Detection**: Utilizes OpenCV to find table-like structures based on their layout, making it effective for tables with or without borders.
  * **Robust Extraction Engine**: Powered by `camelot-py`'s 'stream' flavor, which is specifically designed for parsing borderless tables.
  * **Multi-Format Output**: Exports all extracted tables into clean, machine-readable **JSON** and human-readable **Markdown** files.
  * **Visual Debugging**: Generates images of each page with detected table areas highlighted in green, allowing for easy verification and tuning.
  * **Handles Multi-Page Documents**: Processes every page of a PDF and aggregates all found tables into a single output.

## How It Works ⚙️

The script follows a multi-stage pipeline:

1.  **PDF to Image Conversion**: Each page of the input PDF is rendered as a high-resolution (300 DPI) PNG image using `pdf2image`. This is crucial for accurate visual analysis.
2.  **Image Preprocessing**: The image is converted to grayscale and then a binary format using adaptive thresholding. This step helps to isolate text blocks and other structural elements from the background.
3.  **Contour Detection**: OpenCV's `findContours` method is used to identify all the distinct shapes (contours) in the binary image.
4.  **Table Area Filtering**: A custom logic filters these contours to find potential tables. It looks for large, rectangular shapes and filters out small noise and nested boxes. This is the core step for identifying tables based on their overall shape.
5.  **Data Extraction**: For each potential table area identified, Camelot is invoked to read that specific region of the PDF. It intelligently parses the text alignment and spacing to reconstruct the table's rows and columns.
6.  **Data Serialization**: The extracted data, available as pandas DataFrames, is then serialized into a single JSON file and a single Markdown file for easy use.

-----

## Prerequisites

Before running the script, ensure you have the following dependencies installed on your system.

### System Dependencies

These are required by the underlying libraries (`camelot-py` and `pdf2image`).

  * **Python**: 3.12 or newer.
  * **Ghostscript**: Required by Camelot for processing PDFs.
      * **Linux (Debian/Ubuntu)**: `sudo apt-get install ghostscript`
      * **macOS (Homebrew)**: `brew install ghostscript`
      * **Windows**: Download and install from the [official website](https://www.ghostscript.com/download.html). Ensure the installation location is added to your system's `PATH`.
  * **Poppler**: Required by `pdf2image`.
      * **Linux (Debian/Ubuntu)**: `sudo apt-get install poppler-utils`
      * **macOS (Homebrew)**: `brew install poppler`
      * **Windows**: Download the latest binaries and add the `bin/` directory to your system's `PATH`.

### Python Libraries

The required Python packages are listed in the `requirements.txt` file.

```bash
camelot-py[cv]
opencv-python
pdf2image
pandas
```

## Installation 🚀

1.  **Clone the repository (optional):**

    ```bash
    git clone https://github.com/mldk-tech/mldktech-extract-tables-pdf.git
    cd pdf-table-extractor
    ```

2.  **Create and activate a virtual environment (recommended):**

    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the required Python packages:**

    ```bash
    python -m pip install -r requirements.txt
    ```

    *Note: If you don't have a `requirements.txt` file, you can install the packages directly with `pip install "camelot-py[cv]" opencv-python pdf2image pandas`.*

-----

## Usage Guide

1.  **Place your PDF file** in the project's root directory or note its full path.

2.  **Edit the script**: Open the `extract_tables.py` file and modify the main execution block at the bottom to point to your PDF file:

    ```python
    if __name__ == "__main__":
        # Replace 'your_document.pdf' with the path to your PDF file
        pdf_file_path = "your_document.pdf" 
        if os.path.exists(pdf_file_path):
            find_and_extract_tables(pdf_file_path)
        else:
            print(f"Error: The file '{pdf_file_path}' was not found. Please update the path.")
    ```

3.  **Run the script** from your terminal:

    ```bash
    python extract_tables.py
    ```

4.  **Check the output**: A new directory named `output/` will be created, containing:

      * `page_*.png`: The rendered image of each PDF page.
      * `page_*_detected.png`: A copy of each page image with green rectangles drawn around the areas identified as potential tables.
      * `extracted_tables.json`: A JSON file containing all the extracted tables, structured by page and table number.
      * `extracted_tables.md`: A Markdown file containing all the tables formatted for easy reading.

## Configuration and Customization

For documents with unique layouts, you may need to adjust the table detection parameters. Inside the `find_and_extract_tables` function, the primary filtering logic is here:

```python
# Filter based on size and aspect ratio to avoid noise
# These values may need tuning for different document types
if w > 300 and h > 100 and w < (img.shape[1] * 0.95) and h < (img.shape[0] * 0.9):
    # ... process contour ...
```

  * `w > 300` and `h > 100`: These are the minimum width and height (in pixels) for a detected shape to be considered a table. Increase them if the script is detecting small text blocks, or decrease them for very small tables.
  * `w < (img.shape[1] * 0.95)`: This prevents the script from identifying the entire page content as a single table.

Adjusting these values is the most effective way to improve detection accuracy for your specific use case.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contributing

Contributions, issues, and feature requests are welcome\! Please feel free to open an issue to discuss a bug or a new feature.