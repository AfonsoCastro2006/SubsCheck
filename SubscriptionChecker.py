import os
import json
import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import configparser
import sys

class SubscriptionChecker:
    def __init__(self, smtp_server, smtp_port, sender_email, sender_password, receiver_email, subscriptions_file):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.receiver_email = receiver_email
        self.subscriptions_file = subscriptions_file
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self.check_subscriptions).start()

    def stop(self):
        self.running = False

    def check_subscriptions(self):
        first_run = True
        while self.running:
            # Get the time until the next 10 o'clock
            now = datetime.now()
            next_check = datetime(now.year, now.month, now.day, 10, 0, 0)
            if now >= next_check:
                next_check += timedelta(days=1)  # Next day if already past 10 o'clock today
            sleep_time = (next_check - now).total_seconds()

            if first_run:
                print("SubscriptionChecker is running for the first time.")
                first_run = False

            time.sleep(sleep_time)  # Sleep until the next 10 o'clock
            self.load_subscriptions()
            self.send_email_notifications()

    def load_subscriptions(self):
        self.subscriptions = []
        with open(self.subscriptions_file, "r") as file:
            self.subscriptions = json.load(file)

    def send_email_notifications(self):
        today = datetime.today().date()
        for subscription in self.subscriptions:
            if isinstance(subscription, dict):
                end_date_str = subscription.get("end_date")
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                    # Check if the subscription is due for a warning 45 days before expiration
                    if today + timedelta(days=45) == end_date:
                        self.send_warning_email(subscription)
                    elif end_date == today:
                        self.send_email(subscription)

    def send_warning_email(self, subscription):
        client_name = subscription["client_name"]
        product_name = subscription["product_name"]
        end_date = subscription["end_date"]
        subject = f"Aviso de Expiração da Assinatura: {client_name}"
        body = f"Prezado usuário,\n\nSua assinatura para {product_name} (cliente: {client_name}) está expirando em 45 dias ({end_date}).\nPor favor, considere renová-la.\n\nAtenciosamente,\nSeu Gerenciador de Assinaturas"

        message = MIMEMultipart()
        message['From'] = self.sender_email
        message['To'] = self.receiver_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp_server:
                smtp_server.login(self.sender_email, self.sender_password)
                smtp_server.sendmail(self.sender_email, self.receiver_email, message.as_string())
            print(f"Warning email sent for subscription: {client_name}")
        except Exception as e:
            print(f"Error sending warning email: {e}")

    def send_email(self, subscription):
        client_name = subscription["client_name"]
        product_name = subscription["product_name"]
        end_date = subscription["end_date"]
        subject = f"Expiração da Assinatura: {client_name}"
        body = f"Prezado usuário,\n\nSua assinatura para {product_name} (cliente: {client_name}) está expirando hoje ({end_date}).\n\nAtenciosamente,\nSeu Gerenciador de Assinaturas"

        message = MIMEMultipart()
        message['From'] = self.sender_email
        message['To'] = self.receiver_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp_server:
                smtp_server.login(self.sender_email, self.sender_password)
                smtp_server.sendmail(self.sender_email, self.receiver_email, message.as_string())
            print(f"Email notification sent for subscription: {client_name}")
        except Exception as e:
            print(f"Error sending email: {e}")

def main():
    # Get the directory where the script is located
    if getattr(sys, 'frozen', False):
        # If the script is frozen by PyInstaller
        script_dir = os.path.dirname(sys.argv[0])
    else:
        # If the script is run as a .py file
        script_dir = os.path.dirname(os.path.abspath(__file__))

    config_file = os.path.join(script_dir, 'config.ini')

    if not os.path.exists(config_file):
        print("Config file 'config.ini' not found in the script directory:", script_dir)
        return
    
    # Read SMTP settings from config.ini
    config = configparser.ConfigParser()
    config.read(config_file)

    if 'SMTP' not in config:
        print("SMTP section not found in config.ini.")
        return

    smtp_server = config.get('SMTP', 'smtp_server', fallback='your_smtp_server')
    smtp_port = config.getint('SMTP', 'smtp_port', fallback=587)
    sender_email = config.get('SMTP', 'sender_email', fallback='your_sender_email')
    sender_password = config.get('SMTP', 'sender_password', fallback='your_sender_password')
    receiver_email = config.get('SMTP', 'receiver_email', fallback='your_receiver_email')
    subscriptions_file = os.path.join(script_dir, 'subscriptions.json')

    checker = SubscriptionChecker(smtp_server, smtp_port, sender_email, sender_password, receiver_email, subscriptions_file)
    checker.start()

    # Send a test email
    send_test_email(sender_email, sender_password, smtp_server, smtp_port, receiver_email)

# The rest of the code remains unchanged


def send_test_email(sender_email, sender_password, smtp_server, smtp_port, receiver_email):
    subject = "Test Email"
    body = "Este é um email de teste quando inicia o script."

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp_server:
            smtp_server.login(sender_email, sender_password)
            smtp_server.sendmail(sender_email, receiver_email, message.as_string())
        print("Test email sent successfully.")
    except Exception as e:
        print(f"Error sending test email: {e}")

if __name__ == "__main__":
    main()
