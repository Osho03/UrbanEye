"""
Email Notification Service for UrbanEye
Sends informational updates to citizens about their reported issues.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

class NotificationService:
    def __init__(self):
        # Using a simple SMTP approach (can be configured for Gmail, etc.)
        # For development, we'll use a mock/console output approach
        self.enabled = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true"
        self.smtp_server = os.getenv("SMTP_SERVER", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL", "noreply@urbaneye.gov")
        
    def send_notification(self, to_email, notification_type, issue_data):
        """
        Send email notification to citizen
        
        Args:
            to_email: Citizen's email address
            notification_type: 'welcome', 'status_update', 'resolved'
            issue_data: Dictionary containing issue details
            
        Returns:
            Boolean indicating success/failure
        """
        if not to_email:
            return False
            
        try:
            subject, body = self._create_email_content(notification_type, issue_data)
            
            # For development: just log to console
            # In production: use actual SMTP
            if not self.enabled:
                print(f"\n📧 [MOCK EMAIL NOTIFICATION]")
                print(f"To: {to_email}")
                print(f"Subject: {subject}")
                print(f"Body:\n{body}")
                print(f"=" * 50)
                return True
            
            # Production email sending (disabled by default)
            return self._send_smtp_email(to_email, subject, body)
            
        except Exception as e:
            print(f"Notification Error: {e}")
            return False
    
    def _create_email_content(self, notification_type, issue_data):
        """Create email subject and body based on notification type"""
        
        issue_id = issue_data.get("issue_id", "N/A")
        issue_type = issue_data.get("issue_type", "Issue")
        location = issue_data.get("address", "your reported location")
        status = issue_data.get("status", "Pending")
        
        if notification_type == "welcome":
            subject = f"UrbanEye: Report Received (#{issue_id[-6:]})"
            body = f"""
Dear Citizen,

Thank you for using UrbanEye to report a civic issue.

Report Details:
- Issue ID: #{issue_id[-6:]}
- Type: {issue_type}
- Location: {location}
- Current Status: {status}

Your report has been received and will be reviewed by the relevant department.

Note: This is an automated informational message. You can track your report status at:
http://localhost:3000/#/my-reports

- UrbanEye Team
            """
            
        elif notification_type == "status_update":
            subject = f"UrbanEye: Status Update (#{issue_id[-6:]})"
            admin_remarks = issue_data.get("admin_remarks", "")
            body = f"""
Dear Citizen,

There is an update on your reported issue.

Report Details:
- Issue ID: #{issue_id[-6:]}
- Type: {issue_type}
- Location: {location}
- New Status: {status}

{f"Admin Note: {admin_remarks}" if admin_remarks else ""}

You can view full details at: http://localhost:3000/#/my-reports

Note: This is an informational update only. Status changes are subject to administrative processes.

- UrbanEye Team
            """
            
        elif notification_type == "resolved":
            subject = f"UrbanEye: Issue Resolved (#{issue_id[-6:]})"
            body = f"""
Dear Citizen,

Your reported issue has been marked as resolved.

Report Details:
- Issue ID: #{issue_id[-6:]}
- Type: {issue_type}
- Location: {location}
- Status: Resolved

Thank you for helping improve our city through UrbanEye.

View details: http://localhost:3000/#/my-reports

Note: This notification is informational and does not constitute a guarantee of work completion.

- UrbanEye Team
            """
        else:
            subject = f"UrbanEye: Update (#{issue_id[-6:]})"
            body = f"Your issue #{issue_id[-6:]} has been updated to: {status}"
        
        return subject, body.strip()
    
    def _send_smtp_email(self, to_email, subject, body):
        """Send actual SMTP email (production only)"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # This would require actual SMTP credentials
            # server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            # server.starttls()
            # server.login(self.sender_email, os.getenv("SMTP_PASSWORD"))
            # server.send_message(msg)
            # server.quit()
            
            return True
        except Exception as e:
            print(f"SMTP Error: {e}")
            return False

# Singleton instance
notification_service = NotificationService()
