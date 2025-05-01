from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import os

def merge_pdfs(input_files, output_file):
    merger = PdfMerger()
    for file in input_files:
        merger.append(file)
    merger.write(output_file)
    merger.close()

def split_pdf(input_file, ranges, output_dir):
    reader = PdfReader(input_file)
    for idx, (start, end) in enumerate(ranges):
        writer = PdfWriter()
        for i in range(start - 1, end):  # 0-based index
            writer.add_page(reader.pages[i])
        output_path = os.path.join(output_dir, f"{os.path.basename(input_file).split('.')[0]}_{start}_{end}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)
