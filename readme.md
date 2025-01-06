# Gmail Noiser

A privacy-focused toolkit for analyzing and simulating engagement with marketing emails. This project consists of two main components:

1. `tracker_scanner.py`: Extracts and analyzes tracking links from emails
2. `link_clicker.py`: Simulates natural browsing patterns with extracted links

## Purpose

This toolkit helps users understand and control their digital footprint by:
- Identifying marketing tracking parameters in emails
- Analyzing engagement tracking methods
- Generating controlled noise in tracking analytics
- Protecting privacy through randomized interaction patterns

## Features

### Email Link Extractor
- IMAP email connection support (Gmail, etc.)
- Tracking parameter identification
- Click ID detection
- Domain-based analytics
- Historical email analysis (configurable timeframe)
- CSV report generation

### Link Interactor
- Concurrent link processing
- Natural browsing simulation
- Domain-level deduplication
- Intelligent URL filtering
- Random delays and scrolling
- Progress tracking
- CSV logging

## Prerequisites

- Python 3.6 or higher
- Access to email account via IMAP
- For Gmail users: App Password if 2FA is enabled

## Installation

1. Install required Python packages:
```bash
pip install imaplib email-validator pandas playwright requests
playwright install chromium
```

2. Clone this repository or download the scripts:
```bash
git clone https://github.com/yourusername/email-marketing-analyzer
cd email-marketing-analyzer
```

### Gmail-Specific Setup

If you're using Gmail with 2-Factor Authentication:
1. Go to your Google Account settings
2. Navigate to Security → App passwords
3. Select "Other (custom name)" from the app dropdown
4. Name it "Email Marketing Analyzer" or similar
5. Generate and copy the 16-character app password
6. Use this app password instead of your regular password
7. Important: Delete this app password after completing your analysis

## Usage

### 1. Extract Links from Emails

```bash
python email_link_extractor.py -e your.email@example.com -p "your-password" -m 6
```

Options:
- `-e, --email`: Email address
- `-p, --password`: Email password or app password
- `-m, --months`: Number of months to scan (default: 6)
- `-s, --server`: IMAP server (default: imap.gmail.com)

### 2. Simulate Link Interactions

```bash
python link_interactor.py latest_domain_tracking_20250106_122135.csv -c 3
```

Options:
- `csv_file`: Path to CSV file containing URLs
- `-c, --concurrent`: Maximum concurrent connections (default: 3)

## Example Output

```csv
domain,timestamp,status,visited_at
www.example.com,2025-01-05T15:04:19+00:00,successful,2025-01-06 12:21:35
store.example.com,2025-01-05T15:04:19+00:00,successful,2025-01-06 12:21:35
track.example.com,2025-01-05T15:04:19+00:00,skipped,2025-01-06 12:21:40
cdn.example.com,2025-01-05T15:04:19+00:00,skipped,2025-01-06 12:21:40
```

## Privacy and Security

### Data Protection
- All operations run locally on your machine
- No data is sent to external servers except for link visits
- Credentials are used only for IMAP connection
- All scan results are stored locally
- Scripts don't modify or delete any emails

### Security Checklist
After completing your analysis, remember to:
1. Delete the temporary Google App Password
   - Go to Google Account → Security → App passwords
   - Remove the "Email Marketing Analyzer" app password
2. Clean up local files:
   - Delete generated CSV files containing email data
   - Remove browser data and logs
   - Clear any stored credentials or tokens
3. Review your Google Account:
   - Check recent security events
   - Verify IMAP access settings
   - Monitor for any unusual activity

### Best Practices
- Use a dedicated directory for all generated files
- Review CSV contents before deletion to ensure no needed data is lost
- Consider encrypting sensitive output files if keeping them
- Run scripts on a secure, private network
- Keep Python and all dependencies updated
- Monitor resource usage during concurrent operations
- Store credentials securely
- Review domain allowlists before running
- Monitor resource usage during concurrent operations

## Limitations

- Only processes the inbox folder
- Requires IMAP access to be enabled
- May be affected by email provider's IMAP restrictions
- Processing time increases with email volume and concurrent operations
- Some unsubscribe links may require manual intervention
- Certain tracking parameters might not be detected

## Disclaimer

This tool is for personal use in analyzing your own email accounts. Be sure to comply with your email provider's terms of service and any applicable privacy laws. The link interaction functionality should be used responsibly and in accordance with website terms of service and robot policies.

## License

MIT License

Copyright (c) 2025 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.