"""extract_invoice tool: Extracts structured data from PDF invoices.

Primary: Amazon Textract (synchronous, 5MB limit) + Claude parsing.
Fallback: Claude vision via Bedrock (if Textract fails).

Dependencies:
    - boto3 (S3, Textract, Bedrock Runtime)
    - strands (@tool decorator)
    - app.config.settings (AWS_REGION, S3_BUCKET_NAME)
    - app.modules.agents.config (BEDROCK_REGION, SONNET_MODEL_ID)
"""

import base64
import json
import logging

import boto3
from strands import tool

from app.config import settings
from app.modules.agents.config import BEDROCK_REGION, SONNET_MODEL_ID

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# System prompt for Claude to parse raw OCR text into structured invoice JSON
_PARSE_SYSTEM_PROMPT = """You are an invoice data extraction specialist for Indian GST invoices.
Given raw OCR text from an invoice, extract structured data in JSON format.
Return ONLY valid JSON with no markdown fences, no explanation.
The JSON must match this exact schema:
{
  "seller": {"name": str, "gstin": str, "address": str|null},
  "buyer": {"name": str, "gstin": str, "address": str|null},
  "invoice_number": str,
  "invoice_date": str (YYYY-MM-DD),
  "due_date": str (YYYY-MM-DD),
  "subtotal": float,
  "tax_amount": float,
  "tax_rate": float (percentage, e.g. 18.0),
  "total_amount": float,
  "line_items": [{"description": str, "hsn_code": str, "quantity": int, "rate": float, "amount": float}]
}
If a field is not found, use reasonable defaults. GSTIN is a 15-character alphanumeric code.
Dates should be in YYYY-MM-DD format. Amounts should be numbers without currency symbols."""

# System prompt for Claude vision fallback (processes raw PDF bytes)
_VISION_SYSTEM_PROMPT = """You are an invoice data extraction specialist for Indian GST invoices.
Analyze the provided invoice image/document and extract structured data in JSON format.
Return ONLY valid JSON with no markdown fences, no explanation.
The JSON must match this exact schema:
{
  "seller": {"name": str, "gstin": str, "address": str|null},
  "buyer": {"name": str, "gstin": str, "address": str|null},
  "invoice_number": str,
  "invoice_date": str (YYYY-MM-DD),
  "due_date": str (YYYY-MM-DD),
  "subtotal": float,
  "tax_amount": float,
  "tax_rate": float (percentage, e.g. 18.0),
  "total_amount": float,
  "line_items": [{"description": str, "hsn_code": str, "quantity": int, "rate": float, "amount": float}]
}
If a field is not found, use reasonable defaults. GSTIN is a 15-character alphanumeric code.
Dates should be in YYYY-MM-DD format. Amounts should be numbers without currency symbols."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_document_bytes(s3_file_key: str, bucket_name: str) -> bytes:
    """Download a document from S3 and return its raw bytes.

    Args:
        s3_file_key: The S3 object key for the document.
        bucket_name: The S3 bucket name.

    Returns:
        Raw bytes of the document.
    """
    s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
    response = s3_client.get_object(Bucket=bucket_name, Key=s3_file_key)
    return response["Body"].read()


def _extract_via_textract(document_bytes: bytes) -> list[str]:
    """Run Amazon Textract synchronous AnalyzeDocument and return extracted text lines.

    Args:
        document_bytes: Raw bytes of the PDF/image document.

    Returns:
        List of text lines extracted by Textract.

    Raises:
        Exception: If Textract API call fails.
    """
    textract_client = boto3.client("textract", region_name=settings.AWS_REGION)
    response = textract_client.analyze_document(
        Document={"Bytes": document_bytes},
        FeatureTypes=["TABLES", "FORMS"],
    )

    lines = []
    for block in response.get("Blocks", []):
        if block.get("BlockType") == "LINE" and block.get("Text"):
            lines.append(block["Text"])

    return lines


def _parse_text_with_claude(raw_text: str) -> dict:
    """Use Claude via Bedrock to parse raw OCR text into structured invoice JSON.

    Args:
        raw_text: Concatenated text lines from Textract.

    Returns:
        Parsed invoice data dict matching ExtractedData schema.
    """
    bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

    request_body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "system": _PARSE_SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": f"Extract structured invoice data from this OCR text:\n\n{raw_text}",
                }
            ],
        }
    )

    response = bedrock_client.invoke_model(
        modelId=SONNET_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=request_body,
    )

    response_body = json.loads(response["body"].read())
    result_text = response_body["content"][0]["text"]
    return json.loads(result_text)


def _extract_via_claude_vision(document_bytes: bytes) -> dict:
    """Fallback: Use Claude vision via Bedrock to extract invoice data from raw document.

    Args:
        document_bytes: Raw bytes of the PDF/image document.

    Returns:
        Parsed invoice data dict matching ExtractedData schema.
    """
    bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

    # Encode document as base64 for the vision API
    b64_doc = base64.b64encode(document_bytes).decode("utf-8")

    # Determine media type (PDF or image)
    media_type = "application/pdf"
    if document_bytes[:4] in (b"\x89PNG", b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1"):
        media_type = "image/png" if document_bytes[:4] == b"\x89PNG" else "image/jpeg"

    request_body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "system": _VISION_SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document"
                            if media_type == "application/pdf"
                            else "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64_doc,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Extract all structured invoice data from this document.",
                        },
                    ],
                }
            ],
        }
    )

    response = bedrock_client.invoke_model(
        modelId=SONNET_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=request_body,
    )

    response_body = json.loads(response["body"].read())
    result_text = response_body["content"][0]["text"]
    return json.loads(result_text)


# ---------------------------------------------------------------------------
# Strands @tool
# ---------------------------------------------------------------------------


@tool
def extract_invoice(s3_file_key: str, bucket_name: str) -> dict:
    """Extract structured data from a PDF invoice stored in S3.

    Uses Amazon Textract (primary) with Claude vision fallback.

    Args:
        s3_file_key: The S3 object key for the uploaded invoice PDF.
        bucket_name: The S3 bucket name where the invoice is stored.
    """
    logger.info("Extracting invoice data from s3://%s/%s", bucket_name, s3_file_key)

    # Step 1: Download document from S3
    document_bytes = _get_document_bytes(s3_file_key, bucket_name)
    logger.info("Downloaded %d bytes from S3", len(document_bytes))

    # Step 2: Try Textract (primary path)
    try:
        text_lines = _extract_via_textract(document_bytes)
        raw_text = "\n".join(text_lines)
        logger.info("Textract extracted %d text lines", len(text_lines))

        if not text_lines:
            raise ValueError("Textract returned no text lines")

        # Step 3: Parse raw text with Claude into structured JSON
        extracted = _parse_text_with_claude(raw_text)
        logger.info("Claude parsed Textract output successfully")
        return extracted

    except Exception as textract_err:
        logger.warning(
            "Textract failed (%s), falling back to Claude vision",
            str(textract_err),
        )

        # Step 4: Fallback to Claude vision (processes raw document bytes)
        try:
            extracted = _extract_via_claude_vision(document_bytes)
            logger.info("Claude vision fallback succeeded")
            return extracted
        except Exception as vision_err:
            logger.error("Claude vision fallback also failed: %s", str(vision_err))
            raise RuntimeError(
                f"Invoice extraction failed. Textract: {textract_err}. Claude vision: {vision_err}"
            ) from vision_err
