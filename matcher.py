import anthropic
import requests
from bs4 import BeautifulSoup
import pypdf
import io


def fetch_url_text(url: str) -> str:
    """Fetch and extract text content from a URL."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # Remove script/style noise
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def match_cv_to_assignment(
    assignment_text: str,
    cv_text: str,
    consultant_name: str,
) -> dict:
    """
    Use Claude to match a CV against an assignment and produce:
    - motivation: a short cover letter / motivation text
    - requirements_match: structured analysis of how each requirement is met
    """
    client = anthropic.Anthropic()

    system_prompt = """You are an expert recruitment consultant helping match IT consultants to assignments.
Your task is to analyze an assignment description and a consultant's CV, then produce:
1. A concise, professional motivation letter (3-4 paragraphs) written in first person on behalf of the consultant.
2. A structured requirement matching analysis showing which requirements are met, partially met, or not met.

Be honest and specific. Reference actual skills and experience from the CV."""

    user_prompt = f"""Assignment Description:
{assignment_text}

---

Consultant Name: {consultant_name}

CV / Resume:
{cv_text}

---

Please provide your analysis in the following format:

## Motivation Letter

[Write a professional motivation letter in first person on behalf of {consultant_name}]

## Requirement Matching

For each key requirement in the assignment, assess the consultant's fit:

| Requirement | Match | Evidence from CV |
|-------------|-------|-----------------|
| [requirement] | ✅ Met / ⚠️ Partial / ❌ Not met | [specific evidence] |

## Overall Assessment

[2-3 sentences summarizing the overall fit and any key gaps]
"""

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        full_text = ""
        for text in stream.text_stream:
            full_text += text
            yield text  # stream chunks to UI

    return full_text
