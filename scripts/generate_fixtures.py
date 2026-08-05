"""
Generate dummy fixture files for testing the file type detector.
"""
from pathlib import Path


def generate_fixtures():
    fixtures_dir = Path("tests/fixtures")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    # 1. PDF (Minimal valid PDF with text "Hello MNEMOSYNE PDF")
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 53 >>\nstream\n"
        b"BT\n/F1 24 Tf\n100 700 Td\n(Hello MNEMOSYNE PDF) Tj\nET\n"
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        b"0000000115 00000 n \n0000000234 00000 n \n0000000336 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n424\n%%EOF\n"
    )
    with open(fixtures_dir / "sample.pdf", "wb") as f:
        f.write(pdf_content)

    # 2. DOCX (Valid DOCX file with text "Hello MNEMOSYNE DOCX")
    try:
        from docx import Document

        doc = Document()
        doc.add_paragraph("Hello MNEMOSYNE DOCX")
        doc.save(fixtures_dir / "sample.docx")
    except ImportError:
        print("Warning: python-docx not installed, generating empty docx zip")
        import io
        import zipfile

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("[Content_Types].xml", "<Types></Types>")
        with open(fixtures_dir / "sample.docx", "wb") as f:
            f.write(zip_buffer.getvalue())

    # 3. TXT
    txt_content = b"This is a plain text file.\n"
    with open(fixtures_dir / "sample.txt", "wb") as f:
        f.write(txt_content)

    # 4. PNG (Generated with Pillow to contain text)
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (200, 100), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((10, 40), "Hello MNEMOSYNE Image", fill=(0, 0, 0))
        img.save(fixtures_dir / "sample.png")
    except ImportError:
        print("Warning: Pillow not installed, generating binary PNG")
        png_content = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00"
            b"\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        )
        with open(fixtures_dir / "sample.png", "wb") as f:
            f.write(png_content)

    # 5. JPG
    jpg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"
    with open(fixtures_dir / "sample.jpg", "wb") as f:
        f.write(jpg_content)

    # 6. MP3 (ID3 tag)
    mp3_content = b"ID3\x03\x00\x00\x00\x00\x00\x00"
    with open(fixtures_dir / "sample.mp3", "wb") as f:
        f.write(mp3_content)

    # 7. MP4
    mp4_content = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00"
    with open(fixtures_dir / "sample.mp4", "wb") as f:
        f.write(mp4_content)

    # 8. EML
    eml_content = b"From: a@b.com\nTo: c@d.com\nDate: Mon, 1 Jan 2024\n\nBody"
    with open(fixtures_dir / "sample.eml", "wb") as f:
        f.write(eml_content)

    # 9. PST
    pst_content = b"!BDN"  # standard PST signature
    with open(fixtures_dir / "sample.pst", "wb") as f:
        f.write(pst_content)

    # 10. E01 (EnCase Image)
    e01_content = b"EVF\x09\x0d\x0a\xff\x00"
    with open(fixtures_dir / "sample.e01", "wb") as f:
        f.write(e01_content)

    # 11. Mislabeled file (PDF content with .txt extension)
    with open(fixtures_dir / "mislabeled.txt", "wb") as f:
        f.write(pdf_content)

    print("Fixtures generated successfully.")


if __name__ == "__main__":
    generate_fixtures()
