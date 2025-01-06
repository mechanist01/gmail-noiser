import imaplib
import email
import re
import csv
import argparse
from collections import defaultdict
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse
from email.utils import parseaddr
from typing import Dict, Set, List, Tuple

class EmailLinkExtractor:
    def __init__(self, email_address: str, password: str, imap_server: str = "imap.gmail.com"):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        # Restructure to track by domain instead of email_id
        self.domain_tracking = defaultdict(lambda: {
            'latest_urls': set(),  # Only most recent URLs
            'latest_tracking_params': defaultdict(set),
            'latest_click_ids': set(),
            'latest_source_email': '',
            'latest_timestamp': None,
            'latest_campaign_ids': set()
        })
        
    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email_address, self.password)
            return True
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return False

    def extract_tracking_params(self, url: str) -> Dict[str, str]:
        """Extract known tracking parameters from URLs"""
        tracking_params = {}
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Common tracking parameters
        tracking_patterns = {
            'utm_': 'Google Analytics',
            'fbclid': 'Facebook',
            'gclid': 'Google Ads',
            'mc_eid': 'Mailchimp',
            'ml_subscriber': 'MailerLite',
            'sb_': 'Sendgrid',
            'ct0': 'Twitter',
            'yclid': 'Yandex',
            'msclkid': 'Microsoft',
            '_hsenc': 'HubSpot',
            'wickedid': 'WickedReports',
            'ref': 'Referral',
            'source': 'Source tracking',
            'medium': 'Medium tracking',
            'campaign': 'Campaign tracking',
            'term': 'Keyword tracking',
            'content': 'Content tracking',
            'affiliate': 'Affiliate tracking',
            'sid': 'Session ID',
            'uid': 'User ID',
            'cid': 'Campaign ID',
            'lid': 'Link ID',
            'pid': 'Product ID',
            'rid': 'Referral ID',
            'tid': 'Tracking ID',
            'vid': 'Visitor ID',
            'mid': 'Member ID',
            'tag': 'Tag tracking',
            'hsCtaTracking': 'HubSpot CTA',
            'redirect': 'Redirect tracking'
        }

        for param in query_params:
            for pattern, tracker_type in tracking_patterns.items():
                if pattern in param.lower():
                    tracking_params[param] = query_params[param][0]
                    
        return tracking_params

    def is_promotional_link(self, url: str, email_content: str) -> bool:
        """Determine if a URL is likely a promotional or marketing link"""
        promo_indicators = [
            r'offer', r'deal', r'discount', r'save', r'sale', r'promo',
            r'buy', r'shop', r'order', r'purchase', r'subscribe',
            r'campaign', r'special', r'limited', r'exclusive', r'marketing',
            r'newsletter', r'unsubscribe', r'click', r'track', r'analytics',
            r'product', r'store', r'marketplace', r'cart', r'checkout',
            r'catalog', r'collection', r'brand', r'partner'
        ]
        
        url_lower = url.lower()
        
        # Check URL structure
        if any(indicator in url_lower for indicator in promo_indicators):
            return True
            
        # Check surrounding content (simplified)
        content_lower = email_content.lower()
        url_index = content_lower.find(url_lower)
        if url_index != -1:
            # Check content around the URL
            window_size = 100
            start = max(0, url_index - window_size)
            end = min(len(content_lower), url_index + window_size)
            surrounding_content = content_lower[start:end]
            
            if any(indicator in surrounding_content for indicator in promo_indicators):
                return True
                
        return False

    def update_domain_tracking(self, domain: str, url: str, tracking_params: Dict, 
                             timestamp: datetime, sender: str, click_ids: Set[str]):
        """Update domain tracking data if timestamp is more recent"""
        current_data = self.domain_tracking[domain]
        
        # Ensure timestamps are timezone-aware
        if timestamp and timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=datetime.now().astimezone().tzinfo)
            
        if current_data['latest_timestamp'] and current_data['latest_timestamp'].tzinfo is None:
            current_data['latest_timestamp'] = current_data['latest_timestamp'].replace(
                tzinfo=datetime.now().astimezone().tzinfo
            )
        
        # Update only if this is the first entry or if timestamp is more recent
        if (current_data['latest_timestamp'] is None or 
            timestamp > current_data['latest_timestamp']):
            
            current_data['latest_urls'] = {url}  # Reset to only include latest URL
            current_data['latest_tracking_params'] = defaultdict(set)
            for param, value in tracking_params.items():
                current_data['latest_tracking_params'][param].add(value)
            current_data['latest_click_ids'] = click_ids
            current_data['latest_source_email'] = sender
            current_data['latest_timestamp'] = timestamp
            
        elif timestamp == current_data['latest_timestamp']:
            # If same timestamp, add to existing data
            current_data['latest_urls'].add(url)
            for param, value in tracking_params.items():
                current_data['latest_tracking_params'][param].add(value)
            current_data['latest_click_ids'].update(click_ids)

    def extract_links_from_email(self, email_message):
        """Extract and process links from email content"""
        try:
            timestamp = email.utils.parsedate_to_datetime(email_message['date'])
            sender = email_message['from']

            for part in email_message.walk():
                if part.get_content_type() in ["text/plain", "text/html"]:
                    content = part.get_payload(decode=True)
                    if content:
                        try:
                            decoded_content = content.decode()
                        except UnicodeDecodeError:
                            decoded_content = content.decode('latin-1', errors='ignore')

                        # Extract URLs
                        urls = re.findall(r'https?://[^\s<>"\']+', decoded_content)
                        
                        for url in urls:
                            if self.is_promotional_link(url, decoded_content):
                                domain = urlparse(url).netloc
                                tracking_params = self.extract_tracking_params(url)
                                
                                # Extract click IDs
                                click_patterns = [r'click[_-]?id=([^&]+)', r'cid=([^&]+)']
                                click_ids = set()
                                for pattern in click_patterns:
                                    found_ids = re.findall(pattern, url)
                                    click_ids.update(found_ids)
                                
                                self.update_domain_tracking(
                                    domain, url, tracking_params, 
                                    timestamp, sender, click_ids
                                )

        except Exception as e:
            print(f"Error processing email: {str(e)}")

    def scan_inbox(self, months_back: int = 6):
        """Scan inbox for tracking and promotional links"""
        if not hasattr(self, 'mail'):
            print("Not connected to email server")
            return

        date = (datetime.now() - timedelta(days=30 * months_back)).strftime("%d-%b-%Y")
        self.mail.select('inbox')
        _, messages = self.mail.search(None, f'(SINCE {date})')
        
        email_ids = messages[0].split()
        total_emails = len(email_ids)
        
        print(f"\nFound {total_emails} emails to scan from the past {months_back} months")
        
        for index, email_id in enumerate(email_ids, 1):
            try:
                progress = (index / total_emails) * 100
                print(f"\rProgress: {index}/{total_emails} emails scanned ({progress:.1f}%)", end="", flush=True)
                
                _, msg_data = self.mail.fetch(email_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                self.extract_links_from_email(email_message)
                
            except Exception as e:
                print(f"\nError processing message {email_id}: {str(e)}")
                continue

    def save_to_csv(self):
        """Save latest tracking data per domain to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"latest_domain_tracking_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Domain',
                'Latest Timestamp',
                'Latest Sender',
                'Latest URLs',
                'Latest Tracking Parameters',
                'Latest Click IDs'
            ])
            
            # Sort domains by timestamp for better readability
            sorted_domains = sorted(
                self.domain_tracking.items(),
                key=lambda x: x[1]['latest_timestamp'] or datetime.min,
                reverse=True
            )
            
            for domain, data in sorted_domains:
                if data['latest_timestamp']:  # Only save domains with data
                    writer.writerow([
                        domain,
                        data['latest_timestamp'].isoformat() if data['latest_timestamp'] else '',
                        data['latest_source_email'],
                        '; '.join(data['latest_urls']),
                        '; '.join([f"{k}={v}" for k, params in data['latest_tracking_params'].items() 
                                 for v in params]),
                        '; '.join(data['latest_click_ids'])
                    ])
                    
        print(f"\nSaved latest tracking data per domain to: {filename}")

    def close(self):
        if hasattr(self, 'mail'):
            self.mail.close()
            self.mail.logout()

def main():
    parser = argparse.ArgumentParser(description='Email Marketing Link Extractor')
    parser.add_argument('-e', '--email', required=True, help='Email address')
    parser.add_argument('-p', '--password', required=True, help='Email password or app password')
    parser.add_argument('-m', '--months', type=int, default=6, help='Number of months to scan (default: 6)')
    parser.add_argument('-s', '--server', default='imap.gmail.com', help='IMAP server (default: imap.gmail.com)')
    
    args = parser.parse_args()
    
    extractor = EmailLinkExtractor(args.email, args.password, args.server)
    
    if extractor.connect():
        print(f"\nStarting email scan for marketing links...")
        extractor.scan_inbox(months_back=args.months)
        extractor.save_to_csv()
        extractor.close()
        print("\nProcess finished!")
    else:
        print("Failed to connect to email server.")

if __name__ == "__main__":
    main()