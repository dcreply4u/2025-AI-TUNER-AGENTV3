"""
Email Service

Simple email service for sending data logging files.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

LOGGER = logging.getLogger(__name__)


class EmailService:
    """Simple email service for sending log files."""

    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
    ) -> None:
        """
        Initialize email service.

        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: Email username (or None to use system defaults)
            password: Email password or app-specific password
            use_tls: Use TLS encryption
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def send_files(
        self,
        to_address: str,
        subject: str,
        body: str,
        file_paths: List[Path | str],
        from_address: Optional[str] = None,
    ) -> bool:
        """
        Send email with attached files.

        Args:
            to_address: Recipient email address
            subject: Email subject
            body: Email body text
            file_paths: List of file paths to attach
            from_address: Sender email address (uses username if not provided)

        Returns:
            True if email sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_address or self.username or "ai-tuner@local"
            msg["To"] = to_address
            msg["Subject"] = subject

            # Add body
            msg.attach(MIMEText(body, "plain"))

            # Attach files
            for file_path in file_paths:
                path = Path(file_path)
                if not path.exists():
                    LOGGER.warning("File not found: %s", path)
                    continue

                with open(path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=path.name)
                    part["Content-Disposition"] = f'attachment; filename="{path.name}"'
                    msg.attach(part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                if self.username and self.password:
                    server.login(self.username, self.password)

                server.send_message(msg)

            LOGGER.info("Email sent successfully to %s", to_address)
            return True

        except Exception as e:
            LOGGER.error("Failed to send email: %s", e)
            return False

    def send_log_files(
        self,
        to_address: str,
        log_files: List[Path | str],
        subject: Optional[str] = None,
        body: Optional[str] = None,
    ) -> bool:
        """
        Convenience method to send log files.

        Args:
            to_address: Recipient email address
            log_files: List of log file paths
            subject: Email subject (auto-generated if None)
            body: Email body (auto-generated if None)

        Returns:
            True if email sent successfully
        """
        if not subject:
            subject = f"AI Tuner Log Files - {len(log_files)} file(s)"

        if not body:
            file_list = "\n".join([f"- {Path(f).name}" for f in log_files])
            body = f"Attached are {len(log_files)} log file(s) from AI Tuner:\n\n{file_list}\n\nGenerated automatically."

        return self.send_files(to_address, subject, body, log_files)


__all__ = ["EmailService"]

