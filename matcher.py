import os
import requests
from bs4 import BeautifulSoup
import pypdf
import io
from openai import AzureOpenAI


def fetch_url_text(url: str) -> str:
    """Fetch and extract text content from a URL."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
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
):
    """
    Use Azure OpenAI to match a CV against an assignment and produce:
    - motivation: a short cover letter / motivation text
    - requirements_match: structured analysis of how each requirement is met
    Yields text chunks for streaming.
    """
    client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    )

    prompt = f"""Assignment Description:
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

    stream = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {
                "role": "system",
                "content": """You are an expert recruitment consultant helping match IT consultants to assignments.
Your task is to analyze an assignment description and a consultant's CV, then produce:
1. A concise, professional motivation letter (3-4 paragraphs) written in first person on behalf of the consultant.
2. A structured requirement matching analysis showing which requirements are met, partially met, or not met.

Be honest and specific. Reference actual skills and experience from the CV.""",
            },
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
