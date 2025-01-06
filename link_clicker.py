import asyncio
import random
import argparse
from datetime import datetime
from typing import List, Set
from urllib.parse import urlparse
import pandas as pd
from playwright.async_api import async_playwright, Page, Response

class LinkInteractor:
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.visited_domains = pd.DataFrame(columns=['domain', 'timestamp', 'status', 'visited_at'])
        self._load_visited_domains()

    def _load_visited_domains(self):
        try:
            self.visited_domains = pd.read_csv('visited_domains.csv')
        except FileNotFoundError:
            pass

    def _save_visited_domains(self):
        self.visited_domains.to_csv('visited_domains.csv', index=False)

    @staticmethod
    def get_domain(url: str) -> str:
        return urlparse(url).netloc.lower()

    @staticmethod
    def should_skip_url(url: str) -> bool:
        skip_extensions = ('.png', '.jpg', '.gif', '.ico', '.svg', '.css', '.js')
        skip_keywords = (
            'unsubscribe', 'track.', 'email.', 'click.', 'links.', 
            'notification.', 'redirect.', 'mail.', 'news.', 'link.',
            'analytics.', 'pixel.', 'beacon.', 'open.', 'image.'
        )
        
        parsed = urlparse(url.lower())
        path_lower = parsed.path.lower()
        
        return (
            url.endswith(skip_extensions) or
            any(kw in parsed.netloc for kw in skip_keywords) or
            'unsub' in path_lower or
            'track' in path_lower or
            'proc.php' in path_lower or
            'click' in path_lower or
            'open' in path_lower or
            'pixel' in path_lower or
            'beacon' in path_lower or
            '/e/' in path_lower or
            '/o/' in path_lower or
            'ls/click' in path_lower
        )

    @staticmethod
    async def _setup_page(page: Page):
        await page.set_viewport_size({"width": 1366, "height": 768})
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "DNT": "1"
        })

    async def visit_url(self, url: str, timestamp: str, page: Page) -> None:
        domain = self.get_domain(url)
        visited_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if self.should_skip_url(url):
            print(f"Skipping URL: {url}")
            self.visited_domains.loc[len(self.visited_domains)] = [domain, timestamp, 'skipped', visited_at]
            self._save_visited_domains()
            return

        if domain in self.visited_domains['domain'].values:
            print(f"Skipping domain: {domain}")
            return

        try:
            response = await page.goto(url, timeout=15000)
            if not response:
                raise Exception("No response received")
            if not response.ok:
                raise Exception(f"HTTP {response.status}")

            await page.evaluate("""() => {
                const scrollAmount = Math.floor(Math.random() * window.innerHeight);
                window.scrollBy(0, scrollAmount);
            }""")
            
            await asyncio.sleep(random.uniform(1, 2))
            
            self.visited_domains.loc[len(self.visited_domains)] = [domain, timestamp, 'successful', visited_at]
            self._save_visited_domains()
            print(f"Successfully visited {url} [HTTP {response.status}]")

        except Exception as e:
            print(f"Error visiting {url}: {str(e)}")
            self.visited_domains.loc[len(self.visited_domains)] = [domain, timestamp, 'failed', visited_at]
            self._save_visited_domains()

    async def run(self, csv_path: str) -> None:
        df = pd.read_csv(csv_path)
        urls_data = []
        domains_seen = set()

        for _, row in df.iterrows():
            if pd.isna(row['Latest URLs']):
                continue
            
            for url in row['Latest URLs'].split(';'):
                url = url.strip()
                if url.startswith('http'):
                    domain = self.get_domain(url)
                    if domain not in domains_seen and domain not in self.visited_domains['domain'].values:
                        domains_seen.add(domain)
                        urls_data.append((url, row['Latest Timestamp']))

        print(f"Found {len(urls_data)} unique domains to process")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            pages = []
            for _ in range(self.max_concurrent):
                page = await context.new_page()
                await self._setup_page(page)
                pages.append(page)

            try:
                batch_size = self.max_concurrent
                for i in range(0, len(urls_data), batch_size):
                    batch = urls_data[i:i + batch_size]
                    tasks = [self.visit_url(url, timestamp, pages[j % len(pages)]) 
                            for j, (url, timestamp) in enumerate(batch)]
                    await asyncio.gather(*tasks)
                    
                    if i + batch_size < len(urls_data):
                        delay = random.uniform(1, 3)
                        print(f"Waiting {delay:.1f}s before next batch...")
                        await asyncio.sleep(delay)
                        
            finally:
                await browser.close()

async def main():
    parser = argparse.ArgumentParser(description='Visit URLs from CSV with domain deduplication')
    parser.add_argument('csv_file', help='Path to CSV file containing URLs')
    parser.add_argument('-c', '--concurrent', type=int, default=3, 
                       help='Maximum number of concurrent connections (default: 3)')
    args = parser.parse_args()

    interactor = LinkInteractor(max_concurrent=args.concurrent)
    await interactor.run(args.csv_file)

if __name__ == "__main__":
    asyncio.run(main())