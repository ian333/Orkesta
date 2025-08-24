"""
Advanced web scraping agent for MercadoLibre and e-commerce catalog extraction
"""
from typing import Dict, Any, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium_stealth import stealth
import time
import random
import re
import asyncio
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
import json

from ..core.base_agent import BaseAgent
from ..core.state import (
    CatalogExtractionState, 
    AgentType, 
    SourceType,
    ExtractionPattern,
    ProductData,
    WebScrapingState
)


class MercadoLibreExtractor:
    """Specialized extractor for MercadoLibre patterns"""
    
    LISTING_SELECTORS = {
        "product_containers": [
            ".ui-search-results__item",
            ".ui-search-result",
            ".results-item"
        ],
        "product_titles": [
            ".ui-search-item__title",
            "h2.ui-search-item__title a",
            ".item-title"
        ],
        "product_prices": [
            ".andes-money-amount__fraction",
            ".price-tag-fraction", 
            ".ui-search-price__part"
        ],
        "product_images": [
            "img.ui-search-result-image__element",
            ".ui-search-result__image img",
            ".ui-search-result img"
        ],
        "product_links": [
            ".ui-search-item__group__element a",
            ".ui-search-result__content a"
        ]
    }
    
    DETAIL_SELECTORS = {
        "title": [
            ".ui-pdp-title",
            "h1.ui-pdp-title"
        ],
        "price": [
            ".andes-money-amount__fraction",
            ".notranslate.andes-money-amount__fraction"
        ],
        "description": [
            ".ui-pdp-description__content",
            ".item-description p"
        ],
        "images": [
            ".ui-pdp-image img",
            ".gallery-image img"
        ],
        "brand": [
            ".ui-pdp-subtitle",
            ".item-brand"
        ],
        "category": [
            ".andes-breadcrumb__item",
            ".breadcrumb-item"
        ]
    }

    @classmethod
    def extract_product_listing(cls, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract products from listing page"""
        products = []
        
        for container_selector in cls.LISTING_SELECTORS["product_containers"]:
            containers = soup.select(container_selector)
            if containers:
                break
        else:
            return products
        
        for container in containers[:20]:  # Limit to first 20 products
            try:
                product = cls._extract_single_listing_item(container, base_url)
                if product:
                    products.append(product)
            except Exception as e:
                logging.warning(f"Error extracting product from container: {e}")
        
        return products
    
    @classmethod
    def _extract_single_listing_item(cls, container, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract single product from listing container"""
        
        # Extract title
        title = None
        for selector in cls.LISTING_SELECTORS["product_titles"]:
            title_elem = container.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        if not title:
            return None
        
        # Extract price
        price_text = None
        for selector in cls.LISTING_SELECTORS["product_prices"]:
            price_elem = container.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                break
        
        # Parse price
        price = None
        if price_text:
            price_numbers = re.findall(r'[\d,]+', price_text.replace('.', ''))
            if price_numbers:
                try:
                    price = float(price_numbers[0].replace(',', ''))
                except ValueError:
                    pass
        
        # Extract image
        image_url = None
        for selector in cls.LISTING_SELECTORS["product_images"]:
            img_elem = container.select_one(selector)
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url:
                    image_url = urljoin(base_url, image_url)
                break
        
        # Extract product link
        product_url = None
        for selector in cls.LISTING_SELECTORS["product_links"]:
            link_elem = container.select_one(selector)
            if link_elem:
                href = link_elem.get('href')
                if href:
                    product_url = urljoin(base_url, href)
                break
        
        return {
            "name": title,
            "price": price,
            "currency": "MXN",
            "image_url": image_url,
            "product_url": product_url,
            "source": "mercadolibre_listing",
            "extraction_confidence": 0.85
        }


class WebScrapingAgent(BaseAgent):
    """
    Advanced web scraping agent with MercadoLibre specialization
    """
    
    def __init__(self):
        super().__init__(AgentType.WEB_SCRAPER, "web_scraper")
        self.driver = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
    
    def _setup_driver(self, headless: bool = True, stealth_mode: bool = True) -> webdriver.Chrome:
        """Setup Chrome driver with anti-detection"""
        
        options = Options()
        
        if headless:
            options.add_argument("--headless")
        
        # Anti-detection measures
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Random user agent
        user_agent = random.choice(self.user_agents)
        options.add_argument(f"--user-agent={user_agent}")
        
        # Window size randomization
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        options.add_argument(f"--window-size={width},{height}")
        
        try:
            driver = webdriver.Chrome(options=options)
            
            if stealth_mode:
                stealth(driver,
                       languages=["es-MX", "es", "en"],
                       vendor="Google Inc.",
                       platform="Win32",
                       webgl_vendor="Intel Inc.",
                       renderer="Intel Iris OpenGL Engine")
            
            # Additional anti-detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": user_agent,
                "acceptLanguage": "es-MX,es;q=0.9,en;q=0.8"
            })
            
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to setup Chrome driver: {e}")
            raise
    
    async def process(self, state: CatalogExtractionState, **kwargs) -> CatalogExtractionState:
        """Process web sources for product extraction"""
        
        self.logger.info("Starting web scraping process")
        
        try:
            # Filter web sources
            web_sources = [s for s in state["sources"] if s.type == SourceType.WEB]
            
            if not web_sources:
                return self.update_state(state, {
                    "current_step": "web_scraping_skipped",
                    "raw_products": state.get("raw_products", [])
                })
            
            all_products = []
            
            # Process each web source
            for source in web_sources:
                try:
                    products = await self._scrape_source(source)
                    all_products.extend(products)
                    
                    # Add delay between sources
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                    
                except Exception as e:
                    error_msg = f"Failed to scrape source {source.url}: {e}"
                    self.logger.error(error_msg)
                    state = self.add_error(state, error_msg, {"source": source.url})
            
            return self.update_state(state, {
                "current_step": "web_scraping_completed",
                "raw_products": state.get("raw_products", []) + all_products,
                "completed_sources": state.get("completed_sources", 0) + len(web_sources)
            })
            
        except Exception as e:
            error_msg = f"Web scraping agent failed: {e}"
            self.logger.error(error_msg)
            return self.add_error(state, error_msg)
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
    
    async def _scrape_source(self, source) -> List[Dict[str, Any]]:
        """Scrape single source"""
        
        if not source.url:
            return []
        
        domain = urlparse(source.url).netloc.lower()
        
        # MercadoLibre specialized extraction
        if "mercadolibre" in domain or "mercadolivre" in domain:
            return await self._scrape_mercadolibre(source)
        
        # Generic e-commerce extraction
        return await self._scrape_generic_ecommerce(source)
    
    async def _scrape_mercadolibre(self, source) -> List[Dict[str, Any]]:
        """Specialized MercadoLibre scraping"""
        
        self.logger.info(f"Scraping MercadoLibre: {source.url}")
        
        try:
            if not self.driver:
                self.driver = self._setup_driver()
            
            # Navigate to URL
            self.driver.get(source.url)
            
            # Wait for content to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ui-search-results"))
            )
            
            # Random scroll to simulate human behavior
            await self._human_like_scroll()
            
            # Extract products using BeautifulSoup for better parsing
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            products = MercadoLibreExtractor.extract_product_listing(soup, source.url)
            
            # Check for pagination
            if source.config.get("follow_pagination", False):
                additional_products = await self._handle_pagination(source, max_pages=3)
                products.extend(additional_products)
            
            self.logger.info(f"Extracted {len(products)} products from MercadoLibre")
            return products
            
        except TimeoutException:
            self.logger.warning("MercadoLibre page load timeout")
            return []
        except Exception as e:
            self.logger.error(f"MercadoLibre scraping error: {e}")
            return []
    
    async def _scrape_generic_ecommerce(self, source) -> List[Dict[str, Any]]:
        """Generic e-commerce site scraping"""
        
        self.logger.info(f"Scraping generic e-commerce: {source.url}")
        
        try:
            if not self.driver:
                self.driver = self._setup_driver()
            
            self.driver.get(source.url)
            
            # Wait for page load
            await asyncio.sleep(3)
            await self._human_like_scroll()
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Try common product selectors
            products = await self._extract_generic_products(soup, source.url)
            
            self.logger.info(f"Extracted {len(products)} products from generic site")
            return products
            
        except Exception as e:
            self.logger.error(f"Generic e-commerce scraping error: {e}")
            return []
    
    async def _extract_generic_products(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract products using common e-commerce selectors"""
        
        products = []
        
        # Common product container selectors
        container_selectors = [
            ".product", ".product-item", ".item", 
            "[data-product]", ".card", ".product-card"
        ]
        
        containers = []
        for selector in container_selectors:
            containers = soup.select(selector)
            if len(containers) > 5:  # Found likely product containers
                break
        
        if not containers:
            return products
        
        for container in containers[:15]:  # Limit results
            try:
                product = await self._extract_generic_product(container, base_url)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.debug(f"Error extracting generic product: {e}")
        
        return products
    
    async def _extract_generic_product(self, container, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract single product from generic container"""
        
        # Title extraction
        title_selectors = ["h1", "h2", "h3", ".title", ".name", ".product-name"]
        title = None
        
        for selector in title_selectors:
            title_elem = container.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if len(title) > 10:  # Valid title length
                    break
        
        if not title:
            return None
        
        # Price extraction
        price_selectors = [".price", ".cost", ".amount", "[data-price]"]
        price = None
        
        for selector in price_selectors:
            price_elem = container.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_numbers = re.findall(r'[\d,]+\.?\d*', price_text)
                if price_numbers:
                    try:
                        price = float(price_numbers[0].replace(',', ''))
                        break
                    except ValueError:
                        continue
        
        # Image extraction
        img_elem = container.select_one("img")
        image_url = None
        if img_elem:
            image_url = img_elem.get('src') or img_elem.get('data-src')
            if image_url:
                image_url = urljoin(base_url, image_url)
        
        return {
            "name": title,
            "price": price,
            "currency": "MXN",
            "image_url": image_url,
            "source": "generic_web",
            "extraction_confidence": 0.75
        }
    
    async def _human_like_scroll(self):
        """Simulate human-like scrolling behavior"""
        
        if not self.driver:
            return
        
        # Random scroll pattern
        scroll_pause = random.uniform(0.5, 1.5)
        
        # Scroll down in steps
        for i in range(3):
            scroll_y = random.randint(300, 800)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_y});")
            await asyncio.sleep(scroll_pause)
        
        # Scroll back up a bit
        self.driver.execute_script("window.scrollBy(0, -200);")
        await asyncio.sleep(scroll_pause)
    
    async def _handle_pagination(self, source, max_pages: int = 3) -> List[Dict[str, Any]]:
        """Handle pagination for additional products"""
        
        products = []
        current_page = 1
        
        while current_page < max_pages:
            try:
                # Look for next page button
                next_button = None
                next_selectors = [
                    ".andes-pagination__button--next",
                    ".ui-search-pagination .andes-pagination__button",
                    "a[aria-label='Siguiente']"
                ]
                
                for selector in next_selectors:
                    try:
                        next_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except TimeoutException:
                        continue
                
                if not next_button or "disabled" in next_button.get_attribute("class"):
                    break
                
                # Click next page
                self.driver.execute_script("arguments[0].click();", next_button)
                
                # Wait for new content
                await asyncio.sleep(random.uniform(3.0, 5.0))
                
                # Extract products from new page
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                page_products = MercadoLibreExtractor.extract_product_listing(soup, source.url)
                products.extend(page_products)
                
                current_page += 1
                self.logger.info(f"Scraped page {current_page}, found {len(page_products)} products")
                
            except Exception as e:
                self.logger.warning(f"Pagination error on page {current_page}: {e}")
                break
        
        return products
    
    def __del__(self):
        """Cleanup driver on deletion"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass