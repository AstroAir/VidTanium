import asyncio
import json
import csv
import argparse
import time
import re
from typing import Dict, Set, List, Optional, Any, cast
from urllib.parse import urlparse
from datetime import datetime

from playwright.async_api import (
    async_playwright,
    Request,
    Response,
    Error as PlaywrightError,
    Browser,
    BrowserContext,
    Page,
    ProxySettings
)


class ResourceAnalyzer:
    def __init__(self,
                 url: str,
                 headless: bool = True,
                 timeout: int = 30000,
                 user_agent: Optional[str] = None,
                 proxy: Optional[Dict[str, str]] = None,
                 wait_time: int = 2000,
                 screenshot: bool = False,
                 download_dir: Optional[str] = None,
                 include_pattern: Optional[str] = None,
                 exclude_pattern: Optional[str] = None) -> None:
        """
        Initialize the resource analyzer
        """
        self.url = url
        self.headless = headless
        self.timeout = timeout
        self.user_agent = user_agent
        self.proxy = proxy
        self.wait_time = wait_time
        self.screenshot = screenshot
        self.download_dir = download_dir
        self.include_pattern = re.compile(
            include_pattern) if include_pattern else None
        self.exclude_pattern = re.compile(
            exclude_pattern) if exclude_pattern else None

        # Resource storage
        self.resources: Dict[str, Set[str]] = {
            'document': set(),   # HTML documents
            'stylesheet': set(),  # CSS stylesheets
            'image': set(),      # Images
            'media': set(),      # Media files
            'font': set(),       # Fonts
            'script': set(),     # Scripts
            'xhr': set(),        # XHR requests
            'fetch': set(),      # Fetch requests
            'websocket': set(),  # WebSockets
            'manifest': set(),   # Web manifests
            'other': set()       # Other resources
        }

        # Performance metrics
        self.performance_metrics: Dict[str, Any] = {}
        self.start_time = 0
        self.end_time = 0

        # Response data
        self.response_data: Dict[str, Dict[str, Any]] = {}

        # Page content
        self.page_title = ""
        self.page_links: List[Dict[str, str]] = []

    async def _should_process_url(self, url: str) -> bool:
        """Check if URL should be processed based on include/exclude patterns"""
        if self.include_pattern and not self.include_pattern.search(url):
            return False
        if self.exclude_pattern and self.exclude_pattern.search(url):
            return False
        return True

    async def _on_request(self, request: Request) -> None:
        """Handle request events"""
        resource_type = request.resource_type
        url = request.url

        if not await self._should_process_url(url):
            return

        if resource_type in self.resources:
            self.resources[resource_type].add(url)
        else:
            self.resources['other'].add(url)

    async def _on_response(self, response: Response) -> None:
        """Handle response events"""
        url = response.url

        if not await self._should_process_url(url):
            return

        # Store response metrics
        try:
            self.response_data[url] = {
                'status': response.status,
                'headers': dict(response.headers),
                'size': len(await response.body()) if response.status == 200 else 0,
                'time': time.time() - self.start_time
            }
        except:
            # Handle cases where body() might fail
            self.response_data[url] = {
                'status': response.status,
                'headers': dict(response.headers),
                'size': 0,
                'time': time.time() - self.start_time
            }

    async def analyze(self) -> Dict[str, Any]:
        """
        Analyze the target URL and collect resource information

        Returns:
            Dict containing analysis results
        """
        self.start_time = time.time()

        try:
            async with async_playwright() as p:
                # Launch browser with options
                # 修复：使用正确的类型为 launch 方法准备参数
                browser_options: Dict[str, Any] = {"headless": self.headless}
                
                # 修复：将 proxy 对象转换为 Playwright 期望的 ProxySettings 类型
                if self.proxy:
                    browser_options["proxy"] = cast(ProxySettings, self.proxy)

                browser: Browser = await p.chromium.launch(**browser_options)

                # Create new page with options
                # 修复：使用正确的类型为 new_context 方法准备参数
                context_options: Dict[str, Any] = {}
                if self.user_agent:
                    context_options["user_agent"] = self.user_agent

                context: BrowserContext = await browser.new_context(**context_options)
                page: Page = await context.new_page()

                # Set event listeners
                page.on("request", self._on_request)
                page.on("response", self._on_response)

                # Navigate to URL
                try:
                    print(f"Navigating to {self.url}...")
                    response = await page.goto(self.url,
                                               wait_until="networkidle",
                                               timeout=self.timeout)

                    if not response:
                        raise Exception("No response received from page")

                    if response.status >= 400:
                        raise Exception(f"HTTP error: {response.status}")

                    # Scroll to load lazy resources
                    print("Scrolling page to trigger lazy loading...")
                    await page.evaluate("""
                        (async () => {
                            await new Promise((resolve) => {
                                let totalHeight = 0;
                                const distance = 100;
                                const timer = setInterval(() => {
                                    const scrollHeight = document.body.scrollHeight;
                                    window.scrollBy(0, distance);
                                    totalHeight += distance;
                                    
                                    if(totalHeight >= scrollHeight){
                                        clearInterval(timer);
                                        resolve();
                                    }
                                }, 100);
                            });
                        })()
                    """)

                    # Wait additional time for any delayed resources
                    await page.wait_for_timeout(self.wait_time)

                    # Take screenshot if requested
                    if self.screenshot:
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        netloc = urlparse(self.url).netloc
                        domain = netloc.replace(':', '_') if netloc else "unknown"
                        screenshot_path = f"screenshot_{domain}_{timestamp}.png"
                        await page.screenshot(path=screenshot_path, full_page=True)
                        print(f"Screenshot saved to: {screenshot_path}")

                    # Extract page information
                    self.page_title = await page.title()

                    # Extract links
                    self.page_links = await page.evaluate("""
                        Array.from(document.querySelectorAll('a[href]')).map(a => {
                            return {
                                text: a.innerText.trim(),
                                href: a.href,
                                rel: a.rel
                            }
                        })
                    """)

                    # Get performance metrics
                    self.performance_metrics = await page.evaluate("""
                        (() => {
                            const perfData = window.performance.timing;
                            const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                            const dnsTime = perfData.domainLookupEnd - perfData.domainLookupStart;
                            const connectTime = perfData.connectEnd - perfData.connectStart;
                            const requestTime = perfData.responseStart - perfData.requestStart;
                            const responseTime = perfData.responseEnd - perfData.responseStart;
                            const domProcessingTime = perfData.domComplete - perfData.domLoading;
                            
                            return {
                                pageLoad: pageLoadTime,
                                dns: dnsTime,
                                connect: connectTime,
                                request: requestTime,
                                response: responseTime,
                                domProcessing: domProcessingTime
                            };
                        })()
                    """)

                except PlaywrightError as e:
                    print(f"Navigation error: {str(e)}")
                finally:
                    # Close browser
                    await browser.close()

        except Exception as e:
            print(f"Error during analysis: {str(e)}")

        self.end_time = time.time()

        # Prepare and return results
        return self._prepare_results()

    def _prepare_results(self) -> Dict[str, Any]:
        """Prepare the final results dictionary"""
        # 修复：明确指定 results 的类型
        results: Dict[str, Any] = {
            "url": self.url,
            "analysis_time": {
                "start": self.start_time,
                "end": self.end_time,
                "duration": self.end_time - self.start_time
            },
            "page_info": {
                "title": self.page_title,
                "links_count": len(self.page_links)
            },
            "resources": {k: list(v) for k, v in self.resources.items()},
            "resources_count": {k: len(v) for k, v in self.resources.items()},
            "total_resources": sum(len(v) for v in self.resources.values()),
            "performance_metrics": self.performance_metrics
        }

        # Add domain analysis
        domain_resources: Dict[str, int] = {}
        for resource_set in self.resources.values():
            for url in resource_set:
                netloc = urlparse(url).netloc
                if netloc:  # 确保 netloc 不为空
                    domain_resources[netloc] = domain_resources.get(netloc, 0) + 1

        results["domain_analysis"] = {
            "domains": domain_resources,
            "unique_domains": len(domain_resources)
        }

        return results

    def export_results(self, output_format: str, filename: str) -> None:
        """
        Export results to a file

        Args:
            output_format: Format to export ('json', 'csv', 'txt')
            filename: Output filename
        """
        results = self._prepare_results()

        if output_format == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)

        elif output_format == 'csv':
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow(['Resource Type', 'URL'])

                # Write data
                for resource_type, urls in self.resources.items():
                    for url in urls:
                        writer.writerow([resource_type, url])

        elif output_format == 'txt':
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"URL: {self.url}\n")
                f.write(
                    f"Analysis Time: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(
                    f"Total Resources: {sum(len(v) for v in self.resources.values())}\n\n")

                for resource_type, urls in self.resources.items():
                    if urls:
                        f.write(f"{resource_type.upper()} ({len(urls)}):\n")
                        for url in sorted(urls):
                            f.write(f"  {url}\n")
                        f.write("\n")

        print(f"Results exported to {filename}")


async def main() -> None:
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Web resource analyzer")
    parser.add_argument("url", help="Target URL to analyze")
    parser.add_argument("--headless", action="store_true",
                        help="Run in headless mode")
    parser.add_argument("--timeout", type=int, default=30000,
                        help="Page load timeout in ms")
    parser.add_argument("--user-agent", help="Custom user agent string")
    parser.add_argument(
        "--proxy", help="Proxy server (e.g., http://proxy.example.com:8080)")
    parser.add_argument("--wait-time", type=int, default=2000,
                        help="Additional wait time after page load in ms")
    parser.add_argument("--screenshot", action="store_true",
                        help="Take a screenshot of the page")
    parser.add_argument("--include", help="Regex pattern for URLs to include")
    parser.add_argument("--exclude", help="Regex pattern for URLs to exclude")
    parser.add_argument("--output", choices=["json", "csv", "txt"], default="txt",
                        help="Output format (default: txt)")
    parser.add_argument("--output-file", help="Output file name")

    args = parser.parse_args()

    # Set up proxy configuration if provided
    proxy = None
    if args.proxy:
        # 修复：使用正确的 ProxySettings 格式
        proxy = {
            "server": args.proxy
        }

    # Initialize the analyzer
    analyzer = ResourceAnalyzer(
        url=args.url,
        headless=args.headless,
        timeout=args.timeout,
        user_agent=args.user_agent,
        proxy=proxy,
        wait_time=args.wait_time,
        screenshot=args.screenshot,
        include_pattern=args.include,
        exclude_pattern=args.exclude
    )

    print(f"Analyzing resources for {args.url}...")
    results = await analyzer.analyze()

    # Display summary
    print(f"\nAnalysis complete for: {args.url}")
    print(f"Page title: {results['page_info']['title']}")
    print(f"Total resources: {results['total_resources']}")
    print(f"Unique domains: {results['domain_analysis']['unique_domains']}")

    # Print resource counts by type
    print("\nResource counts by type:")
    for resource_type, count in results['resources_count'].items():
        if count > 0:
            print(f"  {resource_type}: {count}")

    # Export results
    if args.output_file:
        output_file = args.output_file
    else:
        # Generate default filename
        netloc = urlparse(args.url).netloc
        domain = netloc.replace(':', '_') if netloc else "unknown"
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        output_file = f"resources_{domain}_{timestamp}.{args.output}"

    analyzer.export_results(args.output, output_file)


if __name__ == "__main__":
    asyncio.run(main())
