"""小红书爬虫模块"""
import asyncio
import json
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Page, Browser
from core.exceptions import CrawlerError, AuthError, RateLimitError
from core.logger import setup_logger
from core.retry import retry_on_exception

logger = setup_logger("xhs_crawler")


@dataclass
class XHSPost:
    """小红书帖子数据"""
    post_id: str
    title: str
    content: str
    author: str
    author_id: str
    likes: int
    collects: int
    comments: int
    shares: int
    url: str
    images: List[str]
    tags: List[str]
    published_time: str


class XHSCrawler:
    """小红书爬虫"""

    # 需要重试的异常类型
    RETRY_EXCEPTIONS = (
        CrawlerError,
        ConnectionError,
        TimeoutError,
    )

    def __init__(self, headless: bool = True, max_retries: int = 3):
        """初始化爬虫

        Args:
            headless: 是否使用无头模式
            max_retries: 最大重试次数
        """
        self.headless = headless
        self.max_retries = max_retries
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None

    async def __aenter__(self):
        ctx_mgr = async_playwright()
        self._playwright = await ctx_mgr.__aenter__()
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-web-security',
            ]
        )
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1366, 'height': 768},
        )
        self.page = await context.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.__aexit__(exc_type, exc_val, exc_tb)

    async def _wait_for_post_load(self, timeout: int = 10000) -> None:
        """等待帖子加载完成"""
        try:
            await self.page.wait_for_selector(
                'div.x1x986xx, div.note-detail, div.carousel-items, '
                'div.comment-list, div.author-info',
                timeout=timeout
            )
        except Exception as e:
            logger.warning(f"Post load detection timeout or failed: {e}")

    async def _extract_post_data(self) -> Dict:
        """从页面提取帖子数据"""
        data = {}

        # 提取标题
        try:
            title_element = await self.page.query_selector('h1, div[class*="title"]')
            if title_element:
                data['title'] = (await title_element.inner_text()).strip()
        except Exception:
            data['title'] = ""

        # 提取内容
        try:
            content_selectors = [
                'div[class*="content"] div',
                'span[class*="text"]',
                'div[class*="note-text"]',
                '.note-desc'
            ]
            for selector in content_selectors:
                elements = await self.page.query_selector_all(selector)
                texts = [await e.inner_text() for e in elements]
                if texts and any(t.strip() for t in texts):
                    data['content'] = '\n'.join(t.strip() for t in texts if t.strip())
                    break
        except Exception:
            data['content'] = ""

        # 提取作者信息
        try:
            author_selectors = [
                'div[class*="author"] span[class*="name"]',
                'div[class*="user-name"]',
                'a[class*="author"]'
            ]
            for selector in author_selectors:
                author_element = await self.page.query_selector(selector)
                if author_element:
                    data['author'] = (await author_element.inner_text()).strip()
                    break
        except Exception:
            data['author'] = "Unknown"

        # 提取统计数据（点赞、收藏、评论、分享）
        try:
            data['likes'] = 0
            data['collects'] = 0
            data['comments'] = 0
            data['shares'] = 0

            # 尝试从页面中提取数字
            stats_selectors = [
                'div[class*="count"] span',
                'div[class*="stat"] span',
                'div[class*="like"]',
                'div[class*="collect"]',
            ]
            for selector in stats_selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    numbers = self._extract_numbers(text)
                    if numbers:
                        if 'like' in selector or '赞' in element.text_content():
                            data['likes'] = numbers[0]
                        elif 'collect' in selector or '收藏' in element.text_content():
                            data['collects'] = numbers[0]
                        elif 'comment' in selector or '评论' in element.text_content():
                            data['comments'] = numbers[0]
                        elif 'share' in selector or '分享' in element.text_content():
                            data['shares'] = numbers[0]
        except Exception:
            pass

        # 提取图片
        try:
            data['images'] = []
            img_selectors = [
                'img[class*="img"]',
                'img[class*="photo"]',
                'div[class*="carousel"] img',
            ]
            for selector in img_selectors:
                images = await self.page.query_selector_all(selector)
                for img in images:
                    src = await img.get_attribute('src')
                    if src and src.startswith('http'):
                        data['images'].append(src)
            data['images'] = list(set(data['images']))[:9]  # 最多9张图
        except Exception:
            data['images'] = []

        # 提取标签
        try:
            data['tags'] = []
            tag_selectors = [
                'div[class*="tag"] a',
                'div[class*="hashtag"]',
                'a[href^="/topic"]',
            ]
            for selector in tag_selectors:
                tags = await self.page.query_selector_all(selector)
                for tag in tags:
                    text = (await tag.inner_text()).strip()
                    if text and text.startswith('#'):
                        data['tags'].append(text)
            data['tags'] = list(set(data['tags']))[:10]  # 最多10个标签
        except Exception:
            data['tags'] = []

        return data

    @staticmethod
    def _extract_numbers(text: str) -> List[int]:
        """从文本中提取数字"""
        import re
        numbers = []
        for match in re.finditer(r'(\d+\.?\d*[万kK]?)', text):
            num_str = match.group(1)
            try:
                if '万' in num_str:
                    numbers.append(int(float(num_str.replace('万', '')) * 10000))
                elif num_str[-1] in ['k', 'K']:
                    numbers.append(int(float(num_str[:-1]) * 1000))
                else:
                    numbers.append(int(float(num_str)))
            except (ValueError, IndexError):
                continue
        return numbers

    async def extract_post_id_from_url(self, url: str) -> Optional[str]:
        """从URL中提取帖子ID"""
        import re
        patterns = [
            r'/explore/([a-zA-Z0-9]+)',
            r'/note/([a-zA-Z0-9]+)',
            r'noteId=([a-zA-Z0-9]+)',
            r'article_id=([a-zA-Z0-9]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @retry_on_exception(RETRY_EXCEPTIONS, maxtries=3, backoff=2.0)
    async def scrape_post(self, url: str) -> XHSPost:
        """爬取单个帖子

        Args:
            url: 帖子URL

        Returns:
            XHSPost对象

        Raises:
            CrawlerError: 爬取失败
            AuthError: 需要登录
            RateLimitError: 频率限制
        """
        post_id = await self.extract_post_id_from_url(url)
        if not post_id:
            raise CrawlerError(f"无法从URL中提取帖子ID: {url}")

        logger.info(f"开始爬取帖子: {post_id}")

        try:
            response = await self.page.goto(
                url,
                wait_until='networkidle',
                timeout=30000,
            )

            if response and response.status == 403:
                raise AuthError("访问被拒绝，可能需要登录")

            if response and response.status == 429:
                raise RateLimitError("请求频率过高，已被限流")

            await self._wait_for_post_load()

            # 随机延迟避免被检测
            await asyncio.sleep(1 + (post_id.__hash__() % 3))

            # 滚动页面确保内容加载
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(0.5)

            data = await self._extract_post_data()

            post = XHSPost(
                post_id=post_id,
                title=data.get('title', ''),
                content=data.get('content', ''),
                author=data.get('author', 'Unknown'),
                author_id='',  # 需要从更深的页面数据中提取
                likes=data.get('likes', 0),
                collects=data.get('collects', 0),
                comments=data.get('comments', 0),
                shares=data.get('shares', 0),
                url=url,
                images=data.get('images', []),
                tags=data.get('tags', []),
                published_time='',
            )

            logger.info(f"成功爬取帖子: {post_id}, 标题: {post.title}")
            return post

        except AuthError:
            raise
        except RateLimitError:
            raise
        except Exception as e:
            logger.error(f"爬取帖子失败 {url}: {e}")
            raise CrawlerError(f"爬取帖子失败: {e}")

    async def scrape_search_results(
        self,
        keyword: str,
        max_pages: int = 3,
        per_page: int = 20,
    ) -> List[Dict[str, str]]:
        """爬取搜索结果

        Args:
            keyword: 搜索关键词
            max_pages: 最大爬取页数
            per_page: 每页结果数量

        Returns:
            搜索结果列表，每个结果包含标题、链接等信息
        """
        logger.info(f"开始搜索关键词: {keyword}")

        results = []
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"

        try:
            for page in range(1, max_pages + 1):
                logger.info(f"搜索第 {page}/{max_pages} 页")

                url_with_page = f"{search_url}&type=51&page={page}"
                await self.page.goto(
                    url_with_page,
                    wait_until='networkidle',
                    timeout=30000,
                )

                # 等待搜索结果加载
                await asyncio.sleep(2)

                # 提取搜索结果链接
                links = await self.page.query_selector_all('a[href*="/explore/"]')
                for link in links[:per_page]:
                    href = await link.get_attribute('href')
                    if href:
                        full_url = href if href.startswith('http') else f"https://www.xiaohongshu.com{href}"
                        results.append({
                            'url': full_url,
                            'keyword': keyword,
                        })

                if len(results) >= max_pages * per_page:
                    break

                # 随机延迟
                await asyncio.sleep(2)

            logger.info(f"搜索完成，获得 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise CrawlerError(f"搜索失败: {e}")

    async def scrape_multiple_posts(self, urls: List[str]) -> List[XHSPost]:
        """批量爬取帖子

        Args:
            urls: 帖子URL列表

        Returns:
            帖子列表
        """
        posts = []
        total = len(urls)

        for i, url in enumerate(urls, 1):
            try:
                logger.info(f"爬取进度: {i}/{total}")
                post = await self.scrape_post(url)
                posts.append(post)

                # 随机延迟避免被反爬
                if i < total:
                    await asyncio.sleep(2 + (i % 3))

            except (AuthError, RateLimitError):
                raise
            except Exception as e:
                logger.warning(f"跳过失败的帖子 {url}: {e}")
                continue

        logger.info(f"批量爬取完成，成功 {len(posts)}/{total}")
        return posts


async def scrape_post(url: str, headless: bool = True) -> XHSPost:
    """便捷函数：爬取单个帖子

    Args:
        url: 帖子URL
        headless: 是否使用无头模式

    Returns:
        XHSPost对象
    """
    async with XHSCrawler(headless=headless) as crawler:
        return await crawler.scrape_post(url)


async def scrape_posts(urls: List[str], headless: bool = True) -> List[XHSPost]:
    """便捷函数：批量爬取帖子

    Args:
        urls: 帖子URL列表
        headless: 是否使用无头模式

    Returns:
        帖子列表
    """
    async with XHSCrawler(headless=headless) as crawler:
        return await crawler.scrape_multiple_posts(urls)
