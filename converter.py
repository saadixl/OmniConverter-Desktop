"""Conversion engine — shared by GUI and CLI."""

import html
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # pymupdf
from ebooklib import epub

INPUT_EXTENSIONS = {".pdf", ".txt", ".html", ".htm"}
OUTPUT_FORMATS = ["epub", "pdf"]


@dataclass
class Image:
    filename: str
    data: bytes
    media_type: str


@dataclass
class Chapter:
    title: str
    html: str
    images: list[Image] = field(default_factory=list)


@dataclass
class Book:
    title: str
    author: str
    chapters: list[Chapter] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------

def read_pdf(path: Path) -> Book:
    doc = fitz.open(path)
    title = doc.metadata.get("title") or path.stem
    author = doc.metadata.get("author") or "Unknown"
    book = Book(title=title, author=author)
    img_counter = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        parts = [f"<h2>Page {page_num + 1}</h2>"]
        images = []

        text = page.get_text("text").strip()
        if text:
            for para in text.split("\n\n"):
                clean = para.strip().replace("\n", " ")
                if clean:
                    parts.append(f"<p>{html.escape(clean)}</p>")

        for img_info in page.get_images(full=True):
            base_image = doc.extract_image(img_info[0])
            if base_image:
                img_counter += 1
                ext = base_image["ext"]
                fname = f"img_{page_num}_{img_counter}.{ext}"
                images.append(Image(fname, base_image["image"], f"image/{ext}"))
                parts.append(f'<img src="images/{fname}" alt="{fname}"/>')

        book.chapters.append(Chapter(f"Page {page_num + 1}", "\n".join(parts), images))

    doc.close()
    return book


def read_txt(path: Path) -> Book:
    text = path.read_text(encoding="utf-8", errors="replace")
    paragraphs = text.split("\n\n")
    chapters = []
    chunk_size = 50

    for i in range(0, len(paragraphs), chunk_size):
        chunk = paragraphs[i : i + chunk_size]
        title = f"Section {i // chunk_size + 1}"
        body = "\n".join(
            f"<p>{html.escape(p.strip())}</p>" for p in chunk if p.strip()
        )
        chapters.append(Chapter(title, f"<h2>{title}</h2>\n{body}"))

    if not chapters:
        chapters.append(Chapter("Empty", "<p>(empty file)</p>"))

    return Book(title=path.stem, author="Unknown", chapters=chapters)


def read_html(path: Path) -> Book:
    content = path.read_text(encoding="utf-8", errors="replace")
    chapter = Chapter(title=path.stem, html=content)
    return Book(title=path.stem, author="Unknown", chapters=[chapter])


READERS = {
    ".pdf": read_pdf,
    ".txt": read_txt,
    ".html": read_html,
    ".htm": read_html,
}


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_epub(book: Book, out_stem: Path) -> Path:
    eb = epub.EpubBook()
    eb.set_identifier(f"omniconverter-{out_stem.name}")
    eb.set_title(book.title)
    eb.set_language("en")
    eb.add_author(book.author)

    epub_chapters = []
    for i, ch in enumerate(book.chapters):
        for img in ch.images:
            item = epub.EpubImage()
            item.file_name = f"images/{img.filename}"
            item.media_type = img.media_type
            item.content = img.data
            eb.add_item(item)

        ec = epub.EpubHtml(title=ch.title, file_name=f"ch_{i + 1}.xhtml", lang="en")
        ec.content = ch.html
        eb.add_item(ec)
        epub_chapters.append(ec)

    eb.toc = epub_chapters
    eb.add_item(epub.EpubNcx())
    eb.add_item(epub.EpubNav())
    eb.spine = ["nav"] + epub_chapters

    out = out_stem.with_suffix(".epub")
    epub.write_epub(str(out), eb)
    return out


def write_pdf(book: Book, out_stem: Path) -> Path:
    doc = fitz.open()
    for ch in book.chapters:
        page = doc.new_page()
        text_lines = []
        for line in ch.html.split("\n"):
            stripped = line.strip()
            if stripped.startswith("<img"):
                continue
            clean = stripped
            for tag in ["<h2>", "</h2>", "<p>", "</p>", "<h1>", "</h1>"]:
                clean = clean.replace(tag, "")
            clean = html.unescape(clean).strip()
            if clean:
                text_lines.append(clean)

        y = 72
        for line in text_lines:
            if y > 750:
                page = doc.new_page()
                y = 72
            page.insert_text((72, y), line, fontsize=11)
            y += 16

        for img in ch.images:
            if y > 600:
                page = doc.new_page()
                y = 72
            try:
                img_doc = fitz.open(stream=img.data, filetype=img.media_type.split("/")[-1])
                rect = fitz.Rect(72, y, 400, y + 200)
                page.insert_image(rect, stream=img.data)
                y += 210
                img_doc.close()
            except Exception:
                pass

    out = out_stem.with_suffix(".pdf")
    doc.save(str(out))
    doc.close()
    return out


WRITERS = {
    "epub": write_epub,
    "pdf": write_pdf,
}


def convert_file(filepath, output_dir, formats):
    """Convert a single file to the requested formats.
    Returns list of (format, output_path_or_error) tuples.
    """
    reader = READERS.get(filepath.suffix.lower())
    if not reader:
        return [(fmt, f"Unsupported input: {filepath.suffix}") for fmt in formats]

    try:
        book = reader(filepath)
    except Exception as e:
        return [(fmt, f"Read error: {e}") for fmt in formats]

    results = []
    for fmt in formats:
        try:
            out = WRITERS[fmt](book, output_dir / filepath.stem)
            results.append((fmt, str(out)))
        except Exception as e:
            results.append((fmt, f"Error: {e}"))
    return results
