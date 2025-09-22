"""
Notification service for PromoWeb Africa.
Handles email and SMS notifications using various providers.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import jinja2
import httpx

from app.core.config import get_settings
from app.core.database import get_db_context
from app.models.user import User
from app.models.order import Order

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationType(str, Enum):
    """Types of notifications."""
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    ORDER_CONFIRMATION = "order_confirmation"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    STOCK_ALERT = "stock_alert"
    PRICE_DROP_ALERT = "price_drop_alert"
    PROMOTION_NOTIFICATION = "promotion_notification"
    ACCOUNT_SECURITY = "account_security"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


@dataclass
class NotificationResult:
    """Result of a notification sending attempt."""
    success: bool
    message: str
    channel: NotificationChannel
    provider: Optional[str] = None
    external_id: Optional[str] = None
    error_code: Optional[str] = None


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME or "PromoWeb Africa"
        
        # Initialize Jinja2 for email templates
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("app/templates/email"),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        template_name: str,
        context: Dict[str, Any],
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> NotificationResult:
        """Send email using template."""
        try:
            # Load and render template
            template = self.template_env.get_template(f"{template_name}.html")
            html_body = template.render(**context)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return NotificationResult(
                success=True,
                message="Email sent successfully",
                channel=NotificationChannel.EMAIL,
                provider="smtp"
            )
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return NotificationResult(
                success=False,
                message=str(e),
                channel=NotificationChannel.EMAIL,
                provider="smtp",
                error_code="SMTP_ERROR"
            )


class SMSService:
    """Service for sending SMS using multiple providers."""
    
    def __init__(self):
        self.providers = []
        
        # Initialize Twilio if configured
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.providers.append({
                "name": "twilio",
                "priority": 1,
                "config": {
                    "account_sid": settings.TWILIO_ACCOUNT_SID,
                    "auth_token": settings.TWILIO_AUTH_TOKEN,
                    "from_number": settings.TWILIO_PHONE_NUMBER
                }
            })
        
        # Initialize AfricasTalking if configured
        if settings.AFRICASTALKING_USERNAME and settings.AFRICASTALKING_API_KEY:
            self.providers.append({
                "name": "africastalking",
                "priority": 2,
                "config": {
                    "username": settings.AFRICASTALKING_USERNAME,
                    "api_key": settings.AFRICASTALKING_API_KEY
                }
            })
    
    async def send_sms(self, phone_number: str, message: str) -> NotificationResult:
        """Send SMS using available providers."""
        # Normalize phone number (ensure it starts with +237 for Cameroon)
        if not phone_number.startswith("+"):
            if phone_number.startswith("237"):
                phone_number = "+" + phone_number
            elif phone_number.startswith("6") or phone_number.startswith("2"):
                phone_number = "+237" + phone_number
        
        # Try providers in priority order
        for provider in sorted(self.providers, key=lambda x: x["priority"]):
            try:
                if provider["name"] == "twilio":
                    result = await self._send_twilio_sms(
                        phone_number, message, provider["config"]
                    )
                elif provider["name"] == "africastalking":
                    result = await self._send_africastalking_sms(
                        phone_number, message, provider["config"]
                    )
                else:
                    continue
                
                if result.success:
                    return result
                
            except Exception as e:
                logger.warning(f"SMS provider {provider['name']} failed: {e}")
                continue
        
        return NotificationResult(
            success=False,
            message="All SMS providers failed",
            channel=NotificationChannel.SMS,
            error_code="ALL_PROVIDERS_FAILED"
        )
    
    async def _send_twilio_sms(
        self, phone_number: str, message: str, config: Dict[str, str]
    ) -> NotificationResult:
        """Send SMS via Twilio."""
        try:
            from twilio.rest import Client
            
            client = Client(config["account_sid"], config["auth_token"])
            
            twilio_message = client.messages.create(
                body=message,
                from_=config["from_number"],
                to=phone_number
            )
            
            logger.info(f"SMS sent via Twilio to {phone_number}: {twilio_message.sid}")
            return NotificationResult(
                success=True,
                message="SMS sent successfully",
                channel=NotificationChannel.SMS,
                provider="twilio",
                external_id=twilio_message.sid
            )
            
        except Exception as e:
            logger.error(f"Twilio SMS failed: {e}")
            return NotificationResult(
                success=False,
                message=str(e),
                channel=NotificationChannel.SMS,
                provider="twilio",
                error_code="TWILIO_ERROR"
            )
    
    async def _send_africastalking_sms(
        self, phone_number: str, message: str, config: Dict[str, str]
    ) -> NotificationResult:
        """Send SMS via Africa's Talking."""
        try:
            import africastalking
            
            # Initialize the SDK
            africastalking.initialize(config["username"], config["api_key"])
            sms = africastalking.SMS
            
            # Send message
            response = sms.send(message, [phone_number])
            
            if response['SMSMessageData']['Recipients']:
                recipient = response['SMSMessageData']['Recipients'][0]
                if recipient['status'] == 'Success':
                    logger.info(f"SMS sent via Africa's Talking to {phone_number}")
                    return NotificationResult(
                        success=True,
                        message="SMS sent successfully",
                        channel=NotificationChannel.SMS,
                        provider="africastalking",
                        external_id=recipient.get('messageId')
                    )
            
            return NotificationResult(
                success=False,
                message="SMS delivery failed",
                channel=NotificationChannel.SMS,
                provider="africastalking",
                error_code="DELIVERY_FAILED"
            )
            
        except Exception as e:
            logger.error(f"Africa's Talking SMS failed: {e}")
            return NotificationResult(
                success=False,
                message=str(e),
                channel=NotificationChannel.SMS,
                provider="africastalking",
                error_code="AFRICASTALKING_ERROR"
            )


class NotificationService:
    """Main notification service orchestrating all channels."""
    
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
    
    async def send_email_verification(self, user_email: str, verification_token: str) -> NotificationResult:
        """Send email verification notification."""
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
        context = {
            "verification_url": verification_url,
            "site_name": "PromoWeb Africa",
            "support_email": settings.SUPPORT_EMAIL
        }
        
        return await self.email_service.send_email(
            to_email=user_email,
            subject="Verify your PromoWeb Africa account",
            template_name="email_verification",
            context=context
        )
    
    async def send_password_reset(self, user_email: str, reset_token: str) -> NotificationResult:
        """Send password reset notification."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        context = {
            "reset_url": reset_url,
            "site_name": "PromoWeb Africa",
            "support_email": settings.SUPPORT_EMAIL,
            "expiry_hours": 24
        }
        
        return await self.email_service.send_email(
            to_email=user_email,
            subject="Reset your PromoWeb Africa password",
            template_name="password_reset",
            context=context
        )
    
    async def send_order_confirmation(
        self, 
        user_email: str, 
        user_phone: Optional[str],
        order: Order,
        send_sms: bool = True
    ) -> Dict[str, NotificationResult]:
        """Send order confirmation via email and optionally SMS."""
        results = {}
        
        # Email notification
        context = {
            "order": order,
            "order_url": f"{settings.FRONTEND_URL}/orders/{order.id}",
            "site_name": "PromoWeb Africa",
            "support_email": settings.SUPPORT_EMAIL
        }
        
        email_result = await self.email_service.send_email(
            to_email=user_email,
            subject=f"Order Confirmation #{order.order_number}",
            template_name="order_confirmation",
            context=context
        )
        results["email"] = email_result
        
        # SMS notification
        if send_sms and user_phone:
            sms_message = f"Order #{order.order_number} confirmed! Total: {order.total_amount} XAF. Track: {settings.FRONTEND_URL}/orders/{order.id}"
            
            sms_result = await self.sms_service.send_sms(user_phone, sms_message)
            results["sms"] = sms_result
        
        return results
    
    async def send_payment_success(
        self, 
        user_email: str, 
        user_phone: Optional[str],
        order: Order,
        payment_amount: float
    ) -> Dict[str, NotificationResult]:
        """Send payment success notification."""
        results = {}
        
        # Email notification
        context = {
            "order": order,
            "payment_amount": payment_amount,
            "order_url": f"{settings.FRONTEND_URL}/orders/{order.id}",
            "site_name": "PromoWeb Africa"
        }
        
        email_result = await self.email_service.send_email(
            to_email=user_email,
            subject=f"Payment Received - Order #{order.order_number}",
            template_name="payment_success",
            context=context
        )
        results["email"] = email_result
        
        # SMS notification
        if user_phone:
            sms_message = f"Payment of {payment_amount} XAF received for order #{order.order_number}. Thank you!"
            
            sms_result = await self.sms_service.send_sms(user_phone, sms_message)
            results["sms"] = sms_result
        
        return results
    
    async def send_order_shipped(
        self, 
        user_email: str, 
        user_phone: Optional[str],
        order: Order,
        tracking_number: str
    ) -> Dict[str, NotificationResult]:
        """Send order shipped notification."""
        results = {}
        
        # Email notification
        context = {
            "order": order,
            "tracking_number": tracking_number,
            "tracking_url": f"{settings.FRONTEND_URL}/track/{tracking_number}",
            "site_name": "PromoWeb Africa"
        }
        
        email_result = await self.email_service.send_email(
            to_email=user_email,
            subject=f"Your Order Has Shipped - #{order.order_number}",
            template_name="order_shipped",
            context=context
        )
        results["email"] = email_result
        
        # SMS notification
        if user_phone:
            sms_message = f"Order #{order.order_number} shipped! Track: {tracking_number}"
            
            sms_result = await self.sms_service.send_sms(user_phone, sms_message)
            results["sms"] = sms_result
        
        return results
    
    async def send_price_drop_alert(
        self, 
        user_email: str, 
        product_title: str,
        old_price: float,
        new_price: float,
        product_url: str
    ) -> NotificationResult:
        """Send price drop alert."""
        savings = old_price - new_price
        savings_percent = (savings / old_price) * 100
        
        context = {
            "product_title": product_title,
            "old_price": old_price,
            "new_price": new_price,
            "savings": savings,
            "savings_percent": round(savings_percent, 1),
            "product_url": product_url,
            "site_name": "PromoWeb Africa"
        }
        
        return await self.email_service.send_email(
            to_email=user_email,
            subject=f"Price Drop Alert: {product_title}",
            template_name="price_drop_alert",
            context=context
        )
    
    async def send_stock_alert(
        self, 
        user_email: str, 
        product_title: str,
        product_url: str
    ) -> NotificationResult:
        """Send back in stock alert."""
        context = {
            "product_title": product_title,
            "product_url": product_url,
            "site_name": "PromoWeb Africa"
        }
        
        return await self.email_service.send_email(
            to_email=user_email,
            subject=f"Back in Stock: {product_title}",
            template_name="stock_alert",
            context=context
        )
    
    async def send_bulk_notification(
        self, 
        user_emails: List[str],
        subject: str,
        template_name: str,
        context: Dict[str, Any]
    ) -> List[NotificationResult]:
        """Send bulk email notification."""
        results = []
        
        # Send emails concurrently (in batches to avoid overwhelming the server)
        batch_size = 10
        for i in range(0, len(user_emails), batch_size):
            batch = user_emails[i:i + batch_size]
            tasks = [
                self.email_service.send_email(email, subject, template_name, context)
                for email in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(NotificationResult(
                        success=False,
                        message=str(result),
                        channel=NotificationChannel.EMAIL,
                        error_code="BATCH_ERROR"
                    ))
                else:
                    results.append(result)
        
        return results


# Global notification service instance
notification_service = NotificationService()


# Convenience functions
async def send_email_verification(user_email: str, verification_token: str) -> NotificationResult:
    """Send email verification."""
    return await notification_service.send_email_verification(user_email, verification_token)


async def send_password_reset(user_email: str, reset_token: str) -> NotificationResult:
    """Send password reset email."""
    return await notification_service.send_password_reset(user_email, reset_token)


async def send_order_confirmation(
    user_email: str, 
    user_phone: Optional[str], 
    order: Order
) -> Dict[str, NotificationResult]:
    """Send order confirmation."""
    return await notification_service.send_order_confirmation(user_email, user_phone, order)


async def send_payment_success(
    user_email: str, 
    user_phone: Optional[str], 
    order: Order, 
    payment_amount: float
) -> Dict[str, NotificationResult]:
    """Send payment success notification."""
    return await notification_service.send_payment_success(user_email, user_phone, order, payment_amount)
