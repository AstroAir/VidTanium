import asyncio
import os
import json
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set, Tuple, Optional, Any, TypeVar, Union, Callable, TypedDict, TypeAlias

try:
    from bs4 import BeautifulSoup, Tag
    from bs4.element import PageElement
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext, PlaywrightContextManager
    import aiofiles
    import aiosqlite
    from dataclasses import dataclass, asdict, field
    import hashlib
    import logging
except ImportError as e:
    print(f"请安装必要的依赖: {e}")
    raise

# Set up logger
logger = logging.getLogger(__name__)

# 自定义类型
T = TypeVar('T')

# 定义链接字典的类型
class LinkDict(TypedDict):
    url: str
    text: str
    title: str
    is_internal: bool

# 图片字典类型
class ImageDict(TypedDict):
    url: str
    alt: str
    title: str

# 分页链接字典类型
class PaginationLinkDict(TypedDict):
    url: str
    type: str
    text: str

# 类型别名
LinkList = List[LinkDict]
ImageList = List[ImageDict]
PaginationLinkList = List[PaginationLinkDict]


@dataclass
class PageInfo:
    """网页信息数据类"""
    url: str
    title: str = ""
    content_text: str = ""
    links: List[Dict[str, Union[str, bool]]] = field(default_factory=list)
    meta_description: str = ""
    meta_keywords: str = ""
    images: List[Dict[str, str]] = field(default_factory=list)
    h1: List[str] = field(default_factory=list)
    status_code: int = 0
    content_type: str = ""
    crawl_time: str = ""
    screenshot_path: str = ""
    pdf_path: str = ""
    page_depth: int = 0
    pagination_links: List[Dict[str, str]] = field(default_factory=list)
    error: str = ""
    word_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WebAnalyzer:
    def __init__(self,
                 start_url: str,
                 headless: bool = True,
                 output_dir: str = "results",
                 db_path: Optional[str] = None,
                 screenshots: bool = True,
                 save_pdfs: bool = False,
                 follow_external_links: bool = False,
                 max_external_depth: int = 0,
                 user_agent: Optional[str] = None,
                 proxy: Optional[str] = None,
                 timeout: int = 30000,
                 max_pages_per_domain: int = 100,
                 respect_robots_txt: bool = True,
                 extract_content: bool = True,
                 keywords: Optional[List[str]] = None,
                 max_internal_depth_limit: int = 3) -> None:  # Added for run's max_depth

        self.start_url = start_url
        self.base_domain = urlparse(start_url).netloc
        self.headless = headless
        self.output_dir = output_dir
        self.db_path = db_path or os.path.join(output_dir, "crawl_data.db")
        self.screenshots = screenshots
        self.save_pdfs = save_pdfs
        self.follow_external_links = follow_external_links
        self.max_external_depth = max_external_depth
        self.timeout = timeout
        self.max_pages_per_domain = max_pages_per_domain
        self.respect_robots_txt = respect_robots_txt
        self.extract_content = extract_content
        self.keywords = keywords or []
        self.max_internal_depth_limit = max_internal_depth_limit

        # 设置用户代理
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        self.proxy = proxy

        # 爬取状态
        self.visited_urls: Set[str] = set()
        self.domain_pages_count: Dict[str, int] = {}
        self.pages_info: List[PageInfo] = []
        self.current_task_count: int = 0
        self.max_concurrent_tasks: int = 5
        self.robots_txt_rules: Dict[str, List[str]] = {}

        # Playwright属性
        self.playwright: Optional[PlaywrightContextManager] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.db: Optional[aiosqlite.Connection] = None

        # 创建输出目录
        os.makedirs(os.path.join(self.output_dir,
                                 "screenshots"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "pdfs"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "content"), exist_ok=True)

    async def initialize(self) -> None:
        """初始化Playwright和数据库"""
        logger.info("初始化分析器...")

        # 初始化Playwright
        self.playwright = await async_playwright().start()
        browser_args: List[str] = []

        if self.proxy:
            browser_args.append(f'--proxy-server={self.proxy}')

        if self.playwright:
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )

        if self.browser:
            self.context = await self.browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1280, 'height': 800}
            )

        # 初始化数据库
        await self._init_database()

        # 如果需要，获取robots.txt规则
        if self.respect_robots_txt and self.context:
            await self._fetch_robots_txt(self.start_url)

    async def _init_database(self) -> None:
        """初始化SQLite数据库"""
        if self.db_path:
            self.db = await aiosqlite.connect(self.db_path)
            await self.db.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                content_text TEXT,
                meta_description TEXT,
                meta_keywords TEXT,
                status_code INTEGER,
                content_type TEXT,
                crawl_time TEXT,
                screenshot_path TEXT,
                pdf_path TEXT,
                page_depth INTEGER,
                word_count INTEGER,
                domain TEXT,
                error TEXT
            )
            ''')

            await self.db.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT,
                target_url TEXT,
                link_text TEXT,
                is_internal INTEGER,
                UNIQUE(source_url, target_url)
            )
            ''')

            await self.db.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_url TEXT,
                image_url TEXT,
                alt_text TEXT,
                UNIQUE(page_url, image_url)
            )
            ''')

            await self.db.commit()

    async def _fetch_robots_txt(self, url: str) -> None:
        """获取robots.txt规则"""
        if not self.context:
            logger.warning(
                "Playwright context not initialized, skipping robots.txt fetch.")
            return

        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

        try:
            page = await self.context.new_page()
            await page.goto(robots_url, timeout=10000)
            content = await page.content()
            await page.close()

            soup = BeautifulSoup(content, 'html.parser')
            robots_content = soup.get_text()

            # 简单解析robots.txt
            disallowed_paths: List[str] = []
            current_agent: Optional[str] = None

            for line in robots_content.split('\n'):
                line = line.strip().lower()
                if line.startswith('user-agent:'):
                    agent = line.split(':', 1)[1].strip()
                    if self.user_agent and (agent == '*' or self.user_agent.lower() in agent):
                        current_agent = agent
                    else:
                        current_agent = None
                elif current_agent and line.startswith('disallow:'):
                    path = line.split(':', 1)[1].strip()
                    if path:
                        disallowed_paths.append(path)

            self.robots_txt_rules[parsed_url.netloc] = disallowed_paths
            logger.info(
                f"已加载 {parsed_url.netloc} 的robots.txt规则: {len(disallowed_paths)}条")

        except Exception as e:
            logger.warning(f"获取robots.txt失败: {robots_url} - {e}")
            self.robots_txt_rules[parsed_url.netloc] = []

    def _can_fetch_url(self, url: str) -> bool:
        """检查URL是否可以根据robots.txt规则抓取"""
        if not self.respect_robots_txt:
            return True

        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path

        if domain not in self.robots_txt_rules:
            # If no rules fetched for the domain (e.g., fetch failed), assume allowed
            return True

        for disallowed in self.robots_txt_rules.get(domain, []):
            if path.startswith(disallowed):
                return False
        return True

    async def get_soup(self, url: str, page: Optional[Page] = None) -> Tuple[Optional[BeautifulSoup], int, str]:
        """获取BeautifulSoup对象"""
        if not self.context and not page:
            logger.error(
                "Playwright context not available to create a new page.")
            return None, 0, ""

        close_after = False
        current_page: Optional[Page] = page
        if current_page is None and self.context:
            current_page = await self.context.new_page()
            close_after = True

        if not current_page:
            logger.error(f"Failed to obtain a page object for URL: {url}")
            return None, 0, ""

        try:
            response = await current_page.goto(url, wait_until="networkidle", timeout=self.timeout)
            html = await current_page.content()
            status = response.status if response else 0
            content_type = response.headers.get(
                "content-type", "") if response else ""

            return BeautifulSoup(html, 'html.parser'), status, content_type
        except Exception as e:
            logger.error(f"Error getting soup for {url}: {e}")
            return None, 0, ""
        finally:
            if close_after and current_page:
                await current_page.close()

    def find_pagination(self, soup: BeautifulSoup, url: str) -> List[Dict[str, str]]:
        """查找页面中的翻页元素"""
        pagination_links_data: List[Dict[str, str]] = []

        # 查找分页容器
        pagination_containers_results = soup.find_all(
            ['div', 'nav', 'ul'],
            class_=["pagination", "pager", "pages"]
        )
        pagination_containers: List[Tag] = [
            tag for tag in pagination_containers_results if isinstance(tag, Tag)]

        # 查找"下一页"链接
        next_page_patterns = ['next', '下一页', '下一頁',
                              '>', '››', 'nextpage', '后一页', '后一頁']
        next_link_elements: List[Tag] = []

        for pattern in next_page_patterns:
            # Lambda for string matching
            str_match_lambda: Callable[[
                str], bool] = lambda t, p=pattern: p.lower() in t.lower()

            results_string = soup.find_all('a', string=str_match_lambda)
            next_link_elements.extend(
                [tag for tag in results_string if isinstance(tag, Tag)])

            results_title = soup.find_all(
                'a', attrs={"title": str_match_lambda})
            next_link_elements.extend(
                [tag for tag in results_title if isinstance(tag, Tag)])

            results_class = soup.find_all(
                'a', attrs={"class": str_match_lambda})
            next_link_elements.extend(
                [tag for tag in results_class if isinstance(tag, Tag)])

        # 查找数字页码链接
        page_number_link_elements: List[Tag] = []
        all_a_tags = soup.find_all('a')
        for el in all_a_tags:
            if isinstance(el, Tag):
                href_val = _get_attr_str(el, 'href')
                el_string = el.string
                if href_val and el_string:
                    if str(el_string).strip().isdigit():
                        page_number_link_elements.append(el)

        # 查找无限滚动加载元素
        load_more_patterns = ['load more', 'show more', '加载更多']
        load_more_lambda: Callable[[str], bool] = lambda t: any(
            p in t.lower() for p in load_more_patterns)

        load_more_a_results = soup.find_all('a', string=load_more_lambda)
        load_more_elements: List[Tag] = [
            tag for tag in load_more_a_results if isinstance(tag, Tag)]

        load_more_button_results = soup.find_all(
            'button', string=load_more_lambda)
        load_more_elements.extend(
            [tag for tag in load_more_button_results if isinstance(tag, Tag)])

        # 合并所有候选项
        all_candidates: List[Tuple[Tag, str]] = []
        for container_tag in pagination_containers:
            links_in_container = container_tag.find_all('a')
            all_candidates.extend([(link_tag, 'container')
                                  for link_tag in links_in_container if isinstance(link_tag, Tag) and _get_attr_str(link_tag, 'href')])

        all_candidates.extend([(link_tag, 'next')
                              for link_tag in next_link_elements if _get_attr_str(link_tag, 'href')])
        # Already filtered for href
        all_candidates.extend([(link_tag, 'number')
                              for link_tag in page_number_link_elements])
        all_candidates.extend([(link_tag, 'load_more')
                              for link_tag in load_more_elements if _get_attr_str(link_tag, 'href')])

        # 处理并返回绝对URL
        for link_tag, link_type in all_candidates:
            href_val = _get_attr_str(link_tag, 'href')
            if href_val:
                abs_url = urljoin(url, href_val)
                if abs_url != url and abs_url not in self.visited_urls:
                    link_text = link_tag.get_text(strip=True) or ""
                    pagination_links_data.append({
                        "url": abs_url,
                        "type": link_type,
                        "text": link_text
                    })
        return pagination_links_data

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Union[str, bool]]]:
        """提取页面中的所有链接"""
        extracted_links: List[Dict[str, Union[str, bool]]] = []
        domain = urlparse(base_url).netloc

        for element in soup.find_all('a', href=True):
            if not isinstance(element, Tag):
                continue

            a_tag: Tag = element
            href_val = _get_attr_str(a_tag, 'href')

            if href_val and not href_val.startswith(('javascript:', '#', 'mailto:', 'tel:')):
                abs_url = urljoin(base_url, href_val)

                # 过滤掉常见的非HTML内容
                if not any(ext in abs_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.mp3', '.mp4']):
                    link_domain = urlparse(abs_url).netloc
                    is_internal = domain == link_domain
                    link_text = a_tag.get_text(strip=True) or "[无文本]"
                    title_val = _get_attr_str(a_tag, 'title')

                    extracted_links.append({
                        "url": abs_url,
                        "text": link_text,
                        "title": title_val,
                        "is_internal": is_internal
                    })
        return extracted_links

    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """提取页面中的所有图片"""
        extracted_images: List[Dict[str, str]] = []

        for element in soup.find_all('img', src=True):
            if not isinstance(element, Tag):
                continue
            img_tag: Tag = element
            src_val = _get_attr_str(img_tag, 'src')

            if src_val:
                abs_url = urljoin(base_url, src_val)
                alt_val = _get_attr_str(img_tag, 'alt')
                title_val = _get_attr_str(img_tag, 'title')
                extracted_images.append({
                    "url": abs_url,
                    "alt": alt_val,
                    "title": title_val
                })
        return extracted_images

    def extract_meta_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """提取页面元信息"""
        meta_info_data = {
            "description": "",
            "keywords": ""
        }

        meta_desc_element = soup.find('meta', attrs={'name': 'description'})
        if isinstance(meta_desc_element, Tag):
            content = _get_attr_str(meta_desc_element, 'content')
            if content:
                meta_info_data["description"] = content

        meta_keywords_element = soup.find('meta', attrs={'name': 'keywords'})
        if isinstance(meta_keywords_element, Tag):
            content = _get_attr_str(meta_keywords_element, 'content')
            if content:
                meta_info_data["keywords"] = content
        return meta_info_data

    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """智能提取主要内容区域"""

        # Lambdas for matching attributes
        id_lambda: Callable[[str],
                            bool] = lambda x: 'content' in x or 'article' in x
        class_lambda: Callable[[str],
                               bool] = lambda x: 'content' in x or 'article' in x

        content_containers_candidates: List[Optional[PageElement]] = [
            soup.find('article'),
            soup.find('main'),
            soup.find(['div', 'section'], id=id_lambda),
            soup.find(['div', 'section'], attrs={"class": class_lambda})
        ]

        valid_containers: List[Tag] = [
            c for c in content_containers_candidates if isinstance(c, Tag)]

        for container_tag in valid_containers:
            # 移除脚本、样式、导航等无关内容
            for el_to_remove in container_tag.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                el_to_remove.extract()

            text = container_tag.get_text(separator='\n', strip=True)
            if len(text) > 100:  # 确保内容足够长
                return text

        # 如果找不到明确的内容容器，尝试智能识别
        paragraphs_results = soup.find_all('p')
        paragraphs: List[Tag] = [
            p for p in paragraphs_results if isinstance(p, Tag)]
        if paragraphs:
            text = '\n'.join([p.get_text(strip=True) for p in paragraphs])
            if len(text) > 100:
                return text

        # 如果还找不到，返回整个body的文本，但移除无关内容
        body_tag = soup.find('body')
        if isinstance(body_tag, Tag):
            for el_to_remove in body_tag.find_all(['script', 'style', 'nav', 'header', 'footer']):
                el_to_remove.extract()
            text = body_tag.get_text(separator='\n', strip=True)
            return text
        return ""

    async def take_screenshot(self, page: Page, url: str) -> str:
        """对页面进行截图"""
        if not self.screenshots:
            return ""
        try:
            url_hash = hashlib.md5(url.encode()).hexdigest()
            screenshot_path = os.path.join(
                self.output_dir, "screenshots", f"{url_hash}.png")
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=screenshot_path, full_page=True)
            return screenshot_path
        except Exception as e:
            logger.error(f"截图失败: {url} - {str(e)}")
            return ""

    async def save_pdf(self, page: Page, url: str) -> str:
        """保存页面为PDF"""
        if not self.save_pdfs:
            return ""
        try:
            url_hash = hashlib.md5(url.encode()).hexdigest()
            pdf_path = os.path.join(self.output_dir, "pdfs", f"{url_hash}.pdf")
            await page.wait_for_load_state("networkidle")
            await page.pdf(path=pdf_path)
            return pdf_path
        except Exception as e:
            logger.error(f"保存PDF失败: {url} - {str(e)}")
            return ""

    async def save_content(self, url: str, content: str) -> None:
        """保存页面内容为文本文件"""
        if not content:
            return
        try:
            url_hash = hashlib.md5(url.encode()).hexdigest()
            content_path = os.path.join(
                self.output_dir, "content", f"{url_hash}.txt")
            async with aiofiles.open(content_path, 'w', encoding='utf-8') as f:
                await f.write(f"URL: {url}\n\n")
                await f.write(content)
        except Exception as e:
            logger.error(f"保存内容失败: {url} - {str(e)}")

    async def search_keywords(self, text: str) -> Dict[str, int]:
        """在文本中搜索关键词"""
        if not self.keywords:
            return {}
        results: Dict[str, int] = {}
        for keyword in self.keywords:
            try:
                count = len(re.findall(
                    rf'\b{re.escape(keyword)}\b', text, re.IGNORECASE))
                if count > 0:
                    results[keyword] = count
            except re.error as e:
                logger.error(
                    f"Regex error searching for keyword '{keyword}': {e}")
        return results

    async def save_page_to_db(self, page_info: PageInfo) -> None:
        """保存页面信息到数据库"""
        if not self.db:
            logger.error("Database not initialized, cannot save page info.")
            return
        try:
            await self.db.execute('''
            INSERT OR REPLACE INTO pages
            (url, title, content_text, meta_description, meta_keywords, status_code,
            content_type, crawl_time, screenshot_path, pdf_path, page_depth, word_count, domain, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                page_info.url,
                page_info.title,
                page_info.content_text,
                page_info.meta_description,
                page_info.meta_keywords,
                page_info.status_code,
                page_info.content_type,
                page_info.crawl_time,
                page_info.screenshot_path,
                page_info.pdf_path,
                page_info.page_depth,
                page_info.word_count,
                urlparse(page_info.url).netloc,
                page_info.error
            ))

            for link_data in page_info.links:
                await self.db.execute('''
                INSERT OR IGNORE INTO links (source_url, target_url, link_text, is_internal)
                VALUES (?, ?, ?, ?)
                ''', (
                    page_info.url,
                    link_data['url'],  # 
                    link_data['text'],  # 
                    1 if link_data['is_internal'] else 0
                ))

            for img_data in page_info.images:
                await self.db.execute('''
                INSERT OR IGNORE INTO images (page_url, image_url, alt_text)
                VALUES (?, ?, ?)
                ''', (
                    page_info.url,
                    img_data['url'],
                    img_data['alt']
                ))
            await self.db.commit()
        except Exception as e:
            logger.error(f"保存数据到数据库失败: {page_info.url} - {str(e)}")
            if self.db:
                await self.db.rollback()

    async def analyze_page(self, url: str, page_depth: int = 0) -> Optional[Tuple[PageInfo, List[Tuple[str, int]]]]:
        """分析单个页面"""
        self.current_task_count += 1
        try:
            if url in self.visited_urls:
                return None
            if not self._can_fetch_url(url):
                logger.info(f"根据robots.txt规则跳过URL: {url}")
                return None

            domain = urlparse(url).netloc
            if self.domain_pages_count.get(domain, 0) >= self.max_pages_per_domain:
                logger.info(f"已达到域名 {domain} 的最大页面限制")
                return None
            self.domain_pages_count[domain] = self.domain_pages_count.get(
                domain, 0) + 1
            self.visited_urls.add(url)

            page_info = PageInfo(url=url, page_depth=page_depth,
                                 crawl_time=datetime.now().isoformat())

            if not self.context:
                logger.error(
                    f"Playwright context not available for analyzing {url}")
                page_info.error = "Playwright context not available"
                await self.save_page_to_db(page_info)
                return page_info, []

            page = await self.context.new_page()
            logger.info(f"分析页面: {url} (深度: {page_depth})")

            try:
                soup_result, status_code, content_type = await self.get_soup(url, page)
                page_info.status_code = status_code
                page_info.content_type = content_type

                if soup_result is None:  # Error in get_soup
                    page_info.error = f"Failed to retrieve content for soup (status: {status_code})"
                    await self.save_page_to_db(page_info)
                    return page_info, []

                soup: BeautifulSoup = soup_result

                page_info.title = await page.title()

                if self.extract_content:
                    page_info.content_text = self.extract_main_content(soup)
                    page_info.word_count = len(page_info.content_text.split())
                    await self.save_content(url, page_info.content_text)

                h1_tag_results = soup.find_all('h1')
                page_info.h1 = [h1.get_text(
                    strip=True) for h1 in h1_tag_results if isinstance(h1, Tag)]

                meta_data = self.extract_meta_info(soup)
                page_info.meta_description = meta_data["description"]
                page_info.meta_keywords = meta_data["keywords"]

                page_info.links = self.extract_links(soup, url)
                page_info.images = self.extract_images(soup, url)
                page_info.pagination_links = self.find_pagination(soup, url)

                page_info.screenshot_path = await self.take_screenshot(page, url)
                page_info.pdf_path = await self.save_pdf(page, url)

                if page_info.content_text and self.keywords:
                    keyword_results = await self.search_keywords(page_info.content_text)
                    if keyword_results:
                        logger.info(f"关键词搜索结果 for {url}: {keyword_results}")

                await self.save_page_to_db(page_info)
                self.pages_info.append(page_info)

                next_urls_to_crawl: List[Tuple[str, int]] = []

                # Pagination links (high priority, same depth or +1, limited)
                # Taking only the first pagination link for simplicity, adjust if needed
                if page_info.pagination_links and page_depth < self.max_internal_depth_limit:  # Limit pagination crawl depth
                    # Assuming pagination links are for the next logical page, so depth might increase or stay same
                    # For simplicity, let's use current depth for the first pagination link found
                    # or page_depth + 1 if it's truly a "next" page in sequence.
                    # Here, we'll use page_depth + 1 but cap it.
                    next_page_url = page_info.pagination_links[0]["url"]
                    if next_page_url not in self.visited_urls and (page_depth + 1) <= self.max_internal_depth_limit:
                        next_urls_to_crawl.append(
                            (next_page_url, page_depth + 1))

                for link_data in page_info.links:
                    link_url = str(link_data["url"])  # Ensure it's string
                    current_link_depth = page_depth + 1

                    if link_data["is_internal"]:
                        if link_url not in self.visited_urls and current_link_depth <= self.max_internal_depth_limit:
                            next_urls_to_crawl.append(
                                (link_url, current_link_depth))
                    elif self.follow_external_links:
                        # External links use their own depth limit
                        if link_url not in self.visited_urls and current_link_depth <= self.max_external_depth:
                            next_urls_to_crawl.append(
                                (link_url, current_link_depth))

                return page_info, next_urls_to_crawl

            except Exception as e:
                error_msg = f"分析页面出错: {url} - {str(e)}"
                logger.error(error_msg, exc_info=True)
                page_info.error = error_msg
                await self.save_page_to_db(page_info)  # Save error state
                return page_info, []
            finally:
                await page.close()
        finally:
            self.current_task_count -= 1

    async def crawler_worker(self, queue: 'asyncio.Queue[Tuple[str, int]]') -> None:
        """工作线程函数，不断从队列获取URL进行处理"""
        while True:
            try:
                url, depth = await queue.get()
                result = await self.analyze_page(url, depth)
                if result:
                    _, next_urls = result
                    for next_url, next_depth in next_urls:
                        # Heuristic to avoid overly large queue
                        if len(self.visited_urls) + queue.qsize() < self.max_pages_per_domain * 2:
                            await queue.put((next_url, next_depth))
                queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作线程错误: {str(e)}", exc_info=True)
                queue.task_done()  # Ensure task_done is called even on unexpected error

    async def export_to_json(self) -> None:
        """导出数据为JSON格式"""
        json_path = os.path.join(self.output_dir, "crawl_results.json")
        data = [page.to_dict() for page in self.pages_info]
        try:
            async with aiofiles.open(json_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            logger.info(f"已导出数据到JSON: {json_path}")
        except Exception as e:
            logger.error(f"导出JSON失败: {e}")

    async def export_to_csv(self) -> None:
        """导出基本数据为CSV格式"""
        import csv
        csv_path = os.path.join(self.output_dir, "crawl_results.csv")
        fieldnames = ['url', 'title', 'status_code',
                      'crawl_time', 'word_count', 'meta_description']

        try:
            async with aiofiles.open(csv_path, 'w', encoding='utf-8', newline='') as f:
                # Using aiofiles doesn't directly support csv.writer, so manual CSV line construction
                await f.write(','.join(fieldnames) + '\n')  # Header

                for page in self.pages_info:
                    row_values: List[str] = []
                    for field_name in fieldnames:
                        value = getattr(page, field_name, "")
                        # Basic CSV escaping: replace " with "" and wrap in " if it contains comma, newline or quote
                        str_value = str(value).replace('"', '""')
                        if ',' in str_value or '"' in str_value or '\n' in str_value:
                            str_value = f'"{str_value}"'
                        row_values.append(str_value)
                    await f.write(','.join(row_values) + '\n')
            logger.info(f"已导出数据到CSV: {csv_path}")
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")

    async def generate_sitemap(self) -> None:
        """生成网站地图"""
        sitemap_path = os.path.join(self.output_dir, "sitemap.xml")
        sitemap_urls: List[str] = []
        for page in self.pages_info:
            if page.status_code == 200 and urlparse(page.url).netloc == self.base_domain:
                sitemap_urls.append(page.url)

        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        for site_url in sitemap_urls:
            xml_content += '  <url>\n'
            # Basic escaping might be needed for XML special chars in URL if not already handled
            xml_content += f'    <loc>{site_url}</loc>\n'
            xml_content += f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
            xml_content += '  </url>\n'
        xml_content += '</urlset>'

        try:
            async with aiofiles.open(sitemap_path, 'w', encoding='utf-8') as f:
                await f.write(xml_content)
            logger.info(f"已生成网站地图: {sitemap_path}")
        except Exception as e:
            logger.error(f"生成网站地图失败: {e}")

    async def run(self, max_internal_depth: int = 3, max_pages: int = 100) -> None:
        """运行爬虫"""
        self.max_internal_depth_limit = max_internal_depth  # Set the depth limit from run params
        # Set max pages from run params (or rename for clarity)
        self.max_pages_per_domain = max_pages

        try:
            await self.initialize()
            start_time = time.time()

            url_queue: asyncio.Queue[Tuple[str, int]] = asyncio.Queue()
            if self.start_url:
                url_queue.put_nowait((self.start_url, 0))

            workers: List[asyncio.Task[None]] = []
            for _ in range(self.max_concurrent_tasks):
                worker = asyncio.create_task(self.crawler_worker(url_queue))
                workers.append(worker)

            # Main loop to monitor queue and limits
            processed_count = 0
            while True:
                await asyncio.sleep(1)  # Check periodically
                processed_count = len(self.visited_urls)
                logger.info(
                    f"当前进度: 已访问 {processed_count} 个URL，队列中 {url_queue.qsize()} 个待处理, "
                    f"活跃任务: {self.current_task_count}"
                )

                if processed_count >= max_pages:
                    logger.info(f"达到最大页面数限制 ({max_pages})。正在停止...")
                    break

                if url_queue.empty() and self.current_task_count == 0:
                    logger.info("队列为空且所有任务已完成。正在停止...")
                    break

            # Cancel and await worker tasks
            for worker_task in workers:
                worker_task.cancel()

            # Wait for all tasks to complete or be cancelled
            await asyncio.gather(*workers, return_exceptions=True)

            # Ensure queue is fully processed after cancellation signal if needed
            # This might be redundant if workers handle cancellation gracefully and finish current item
            await url_queue.join()

            await self.export_to_json()
            await self.export_to_csv()
            await self.generate_sitemap()

            end_time = time.time()
            duration = end_time - start_time
            logger.info(
                f"爬取完成! 总计爬取 {len(self.visited_urls)} 个URL，耗时 {duration:.2f} 秒")
            logger.info(f"结果保存在目录: {self.output_dir}")
            self._generate_report(duration)

        except Exception as e:
            logger.error(f"爬虫运行错误: {str(e)}", exc_info=True)
        finally:
            if self.db:
                await self.db.close()
            await self.close()

    def _generate_report(self, duration: float) -> None:
        """生成简单的爬取报告"""
        report_path = os.path.join(self.output_dir, "crawl_report.txt")
        total_pages_visited = len(self.visited_urls)
        successful_pages = sum(
            1 for page in self.pages_info if page.status_code == 200 and not page.error)
        error_pages = sum(
            1 for page in self.pages_info if page.error or page.status_code != 200)

        domains_data: Dict[str, int] = {}
        for page in self.pages_info:
            domain = urlparse(page.url).netloc
            domains_data[domain] = domains_data.get(domain, 0) + 1

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("=== 网页分析爬取报告 ===\n\n")
                f.write(f"开始URL: {self.start_url}\n")
                f.write(
                    f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总耗时: {duration:.2f} 秒\n\n")
                f.write("=== 数量统计 ===\n")
                f.write(f"总访问URL (尝试): {total_pages_visited}\n")
                f.write(f"总处理页面 (有PageInfo记录): {len(self.pages_info)}\n")
                f.write(f"成功页面 (HTTP 200, 无错误): {successful_pages}\n")
                f.write(f"错误/失败页面: {error_pages}\n\n")
                f.write("=== 域名分布 (基于PageInfo记录) ===\n")
                for domain_name, count in domains_data.items():
                    f.write(f"{domain_name}: {count} 页\n")
                f.write("\n=== 完成 ===\n")
            logger.info(f"已生成爬取报告: {report_path}")
        except Exception as e:
            logger.error(f"生成报告失败: {e}")

    async def close(self) -> None:
        """关闭资源"""
        logger.info("正在关闭分析器资源...")
        if self.context:
            try:
                await self.context.close()
                logger.info("Playwright context closed.")
            except Exception as e:
                logger.error(f"Error closing Playwright context: {e}")
        if self.browser:
            try:
                await self.browser.close()
                logger.info("Playwright browser closed.")
            except Exception as e:
                logger.error(f"Error closing Playwright browser: {e}")
        if self.playwright:
            try:
                # Note: playwright.stop() is not an async function
                # self.playwright.stop() # This might cause issues in async if not handled correctly
                logger.info(
                    "Playwright stopped (or would be if stop() was async and called).")
            except Exception as e:
                logger.error(f"Error stopping Playwright: {e}")
        logger.info("分析器资源关闭完成.")


# 使用示例
async def main() -> None:
    # 要分析的URL
    start_url = "https://example.com"  # 替换为你的目标URL

    # 初始化分析器
    analyzer = WebAnalyzer(
        start_url=start_url,
        headless=True,                # 无头模式运行
        output_dir="crawl_results",   # 结果保存目录
        screenshots=True,             # 保存截图
        save_pdfs=False,              # 不保存PDF
        follow_external_links=False,   # 跟踪外部链接
        # 外部链接最大深度 (if follow_external_links is True)
        max_external_depth=0,
        # max_pages_per_domain is now set by max_pages in run()
        extract_content=True,         # 提取页面内容
        keywords=["example", "test"]  # 要搜索的关键词
    )

    # 运行分析器
    # max_internal_depth is for internal links, max_pages is total pages to crawl
    await analyzer.run(max_internal_depth=2, max_pages=10)


if __name__ == "__main__":
    asyncio.run(main())
