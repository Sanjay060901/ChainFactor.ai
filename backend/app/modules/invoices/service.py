"""Invoice upload service: S3 upload + DB record creation."""

import logging
import uuid

import boto3
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.invoice import Invoice
from app.models.user import User

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB (Textract synchronous limit)
ALLOWED_CONTENT_TYPES = {"application/pdf"}


def _get_s3_client():
    """Create an S3 client for the primary AWS region."""
    return boto3.client("s3", region_name=settings.AWS_REGION)


async def upload_to_s3(file_bytes: bytes, s3_key: str) -> str:
    """Upload file bytes to S3 and return the key.

    This is a thin wrapper so tests can mock it without touching boto3.
    """
    client = _get_s3_client()
    client.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=s3_key,
        Body=file_bytes,
        ContentType="application/pdf",
    )
    logger.info("Uploaded to S3: s3://%s/%s", settings.S3_BUCKET_NAME, s3_key)
    return s3_key


async def validate_upload(file: UploadFile) -> bytes:
    """Validate uploaded file: must be PDF, max 5MB. Returns file bytes."""
    # Content type check
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    # Read and check size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 5MB)",
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )

    return file_bytes


async def create_invoice_record(
    db: AsyncSession,
    user: User,
    file_name: str,
    s3_key: str,
) -> Invoice:
    """Create an Invoice record in the database with status 'uploaded'."""
    invoice = Invoice(
        id=uuid.uuid4(),
        user_id=user.id,
        invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
        status="uploaded",
        file_key=s3_key,
        file_name=file_name,
    )
    db.add(invoice)
    await db.flush()
    logger.info("Created invoice %s for user %s", invoice.id, user.id)
    return invoice
