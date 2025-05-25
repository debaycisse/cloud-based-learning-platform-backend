from flask_mail import Message
from flask import current_app
from app import mail

def send_reset_email(to_email, token, username):
    try:

        reset_link = f"{current_app.config['FRONTEND_DOMAIN']}/reset-password/{token}"

        subject = "Password Reset Request"

        body = f"""Hello, {username},

        To reset your password, please click the following link:
        {reset_link}
        
        If you did not make this request, please ignore this email.

        Best regards,
        CBLP
        """

        msg = Message(subject=subject, recipients=[to_email], body=body)
    
        mail.send(msg)

        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")
        return False

def send_login_email(to_email, user_name):
    try:

        reset_link = f"{current_app.config['FRONTEND_DOMAIN']}/login"

        subject = "Registration Confirmation"

        body = f"""Hello, {user_name},

        To verify your account and login, please click the following link:
        {reset_link}
        
        If you did not make this request, please ignore this email.

        Best regards,
        CBLP
        """

        msg = Message(subject=subject, recipients=[to_email], body=body)
    
        mail.send(msg)

        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")
        return False

def contact_support_email(from_email, subject, message):
    try:
        support_email = current_app.config['SUPPORT_EMAIL']
        
        msg = Message(
            subject=subject,
            recipients=[support_email],
            body=message,
            sender=from_email
        )

        mail.send(msg)
        
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send support email: {e}")
        return False
