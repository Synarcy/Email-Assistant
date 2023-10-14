import os
import json
from tkinter import filedialog
import smtplib
from email.message import EmailMessage
import socks
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from concurrent.futures import ThreadPoolExecutor

CONFIG_FILE = 'email_app_config.json'

def save_config(smtp_server, port, email, password):
    config = {
        'smtp_server': smtp_server,
        'port': port,
        'email': email,
        'password': password
    }
    with open(CONFIG_FILE, "w") as config_file:
        json.dump(config, config_file)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return None

def send_email_with_proxy(details):
    smtp_server, port, sender_email, sender_password, recipient, subject, content, proxy_type, proxy_host, proxy_port, log_callback = details

    success_count = 0
    fail_count = 0

    if proxy_type and proxy_host and proxy_port:
        socks.setdefaultproxy(proxy_type, proxy_host, proxy_port)
        socks.wrapmodule(smtplib)

    with smtplib.SMTP_SSL(smtp_server, port) as server:
        server.login(sender_email, sender_password)
        msg = EmailMessage()
        msg.set_content(content)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient
        try:
            server.send_message(msg)
            success_count += 1
            if log_callback:
                log_callback(f"[SUCCESS] Email has been sent to ---> {recipient}")
        except:
            fail_count += 1
            if log_callback:
                log_callback(f"[FAILURE] Failed to send email to ---> {recipient}")

    return success_count, fail_count

def send_emails_concurrently(smtp_server, port, sender_email, sender_password, recipients, subject, content, num_times=1, proxy_type=None, proxy_host=None, proxy_port=None, log_callback=None):
    total_success = 0
    total_failed = 0

    details_list = []
    for _ in range(num_times):
        for recipient in recipients:
            details_list.append((smtp_server, port, sender_email, sender_password, recipient, subject, content, proxy_type, proxy_host, proxy_port, log_callback))

    with ThreadPoolExecutor() as executor:
        results = executor.map(send_email_with_proxy, details_list)
        for success, fail in results:
            total_success += success
            total_failed += fail

    return total_success, total_failed

class EmailApp:
    def __init__(self, root):
        self.root = root
        root.title("Email Assistant")

        config = load_config() if load_config() else {}

        ttk.Label(root, text="SMTP Server:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.smtp_server = ttk.Entry(root)
        self.smtp_server.grid(row=0, column=1, padx=10, pady=5)
        self.smtp_server.insert(0, config.get('smtp_server', ''))

        ttk.Label(root, text="Port:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.port = ttk.Entry(root)
        self.port.grid(row=1, column=1, padx=10, pady=5)
        self.port.insert(0, config.get('port', ''))

        ttk.Label(root, text="Email:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.sender_email = ttk.Entry(root)
        self.sender_email.grid(row=2, column=1, padx=10, pady=5)
        self.sender_email.insert(0, config.get('email', ''))

        ttk.Label(root, text="Password:").grid(row=3, column=0, sticky='w', padx=10, pady=5)
        self.sender_password = ttk.Entry(root, show="*")
        self.sender_password.grid(row=3, column=1, padx=10, pady=5)
        self.sender_password.insert(0, config.get('password', ''))

        ttk.Label(root, text="Recipients (comma separated):").grid(row=4, column=0, sticky='w', padx=10, pady=5)
        self.recipients = ttk.Entry(root, width=50)
        self.recipients.grid(row=4, column=1, padx=10, pady=5)

        ttk.Label(root, text="Subject:").grid(row=5, column=0, sticky='w', padx=10, pady=5)
        self.subject = ttk.Entry(root, width=50)
        self.subject.grid(row=5, column=1, padx=10, pady=5)

        ttk.Label(root, text="Content:").grid(row=6, column=0, sticky='w', padx=10, pady=5)
        self.content = tk.Text(root, width=40, height=10)
        self.content.grid(row=6, column=1, padx=10, pady=5)

        ttk.Label(root, text="Proxy Host (optional):").grid(row=7, column=0, sticky='w', padx=10, pady=5)
        self.proxy_host = ttk.Entry(root)
        self.proxy_host.grid(row=7, column=1, padx=10, pady=5)

        ttk.Label(root, text="Proxy Port (optional):").grid(row=8, column=0, sticky='w', padx=10, pady=5)
        self.proxy_port = ttk.Entry(root)
        self.proxy_port.grid(row=8, column=1, padx=10, pady=5)

        ttk.Label(root, text="Number of Emails:").grid(row=9, column=0, sticky='w', padx=10, pady=5)
        self.num_emails = ttk.Entry(root)
        self.num_emails.grid(row=9, column=1, padx=10, pady=5)

        self.send_button = ttk.Button(root, text="Send Email", command=self.send_email)
        self.send_button.grid(row=10, column=1, pady=20)

        self.email_log_box = scrolledtext.ScrolledText(root, width=60, height=20)
        self.email_log_box.grid(row=0, column=2, rowspan=11, padx=10, pady=5)
        self.email_log_box.configure(state='disabled')

        self.proxy_file_label = ttk.Label(root, text="Proxy File (optional):")
        self.proxy_file_label.grid(row=11, column=0, sticky='w', padx=10, pady=5)

        self.proxy_file_path = ttk.Label(root, text="", relief="sunken", anchor="w")
        self.proxy_file_path.grid(row=11, column=1, sticky="we", padx=10, pady=5)

        self.proxy_file_button = ttk.Button(root, text="Choose File", command=self.select_proxy_file)
        self.proxy_file_button.grid(row=11, column=2, padx=10, pady=5)

        self.proxy_log_box = scrolledtext.ScrolledText(root, width=60, height=20)
        self.proxy_log_box.grid(row=0, column=3, rowspan=12, padx=10, pady=5)
        self.proxy_log_box.configure(state='disabled')

    def append_to_log(self, message, box_type="email"):
        if box_type == "email":
            box = self.email_log_box
        else:
            box = self.proxy_log_box

        box.configure(state='normal')
        box.insert(tk.END, message + '\n')
        box.see(tk.END)
        box.configure(state='disabled')

    def select_proxy_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            self.proxy_file_path.config(text=file_path)
            with open(file_path, 'r') as f:
                self.proxies = [line.strip() for line in f.readlines() if line.strip()]

    def send_email(self):
        smtp_server = os.environ.get("SMTP_SERVER", self.smtp_server.get())
        port = int(os.environ.get("SMTP_PORT", self.port.get()))
        email = os.environ.get("SMTP_EMAIL", self.sender_email.get())
        password = os.environ.get("SMTP_PASSWORD", self.sender_password.get())
        recipients = [r.strip() for r in self.recipients.get().split(",")]
        subject = self.subject.get()
        content = self.content.get("1.0", "end").strip()
        num_emails = int(self.num_emails.get())

        save_config(smtp_server, port, email, password)

        if not smtp_server or not port or not email or not password or not recipients or not subject or not content or not num_emails:
            messagebox.showerror("Error", "All fields must be filled!")

        def threaded_send():
            total_success = 0
            total_failed = 0

            for _ in range(num_emails):
                proxy_host = None
                proxy_port = None

                if hasattr(self, 'proxies') and self.proxies:
                    proxy_details = self.proxies.pop(0)
                    try:
                        proxy_host, proxy_port = proxy_details.split(":")
                    except ValueError:
                        self.append_to_log(f"Skipped malformed proxy: {proxy_details}")
                        continue
                    self.append_to_log(f"Using proxy: {proxy_host}:{proxy_port}", box_type="proxy")

                try:
                    success, failed = send_emails_concurrently(
                        smtp_server=smtp_server,
                        port=port,
                        sender_email=email,
                        sender_password=password,
                        recipients=recipients,
                        subject=subject,
                        content=content,
                        proxy_type=socks.SOCKS5,
                        proxy_host=proxy_host if proxy_host else None,
                        proxy_port=int(proxy_port) if proxy_port else None,
                        log_callback=self.append_to_log
                    )
                    total_success += success
                    total_failed += failed
                except Exception as e:
                    self.append_to_log(f"Error with proxy {proxy_host}:{proxy_port}: {str(e)}", box_type="proxy")

            self.append_to_log(f"Total: {total_success} emails sent successfully, {total_failed} failed.")

        threading.Thread(target=threaded_send).start()
        self.append_to_log("Status: Sending emails...")

if __name__ == "__main__":
    root = tk.Tk()
    app = EmailApp(root)
    root.mainloop()
