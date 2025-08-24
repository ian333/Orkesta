"""
Advanced PDF processing agent with multi-pass OCR and table extraction
"""
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import logging
from pathlib import Path
import tempfile
import os
from datetime import datetime
import json
import re

# PDF processing
import fitz  # PyMuPDF
from PIL import Image
import numpy as np

# OCR engines
import pytesseract
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

try:
    import easyocr
    EASY_OCR_AVAILABLE = True
except ImportError:
    EASY_OCR_AVAILABLE = False

# Table extraction
import camelot
import tabula

from ..core.base_agent import BaseAgent
from ..core.state import (
    CatalogExtractionState, 
    AgentType, 
    SourceType,
    ProductData,
    PDFProcessingState
)


class OCREngine:
    """Multi-engine OCR processor with confidence scoring"""
    
    def __init__(self):
        self.tesseract_config = r'--oem 3 --psm 6 -l spa+eng'
        self.paddle_ocr = None
        self.easy_reader = None
        
        # Initialize PaddleOCR if available
        if PADDLE_AVAILABLE:
            try:
                self.paddle_ocr = PaddleOCR(
                    use_angle_cls=True, 
                    lang='es',
                    show_log=False,
                    use_gpu=False
                )
            except Exception as e:
                logging.warning(f"PaddleOCR initialization failed: {e}")
        
        # Initialize EasyOCR if available
        if EASY_OCR_AVAILABLE:
            try:
                self.easy_reader = easyocr.Reader(['es', 'en'], gpu=False)
            except Exception as e:
                logging.warning(f"EasyOCR initialization failed: {e}")
    
    async def extract_text_multi_engine(self, image: Image.Image) -> Dict[str, Any]:
        """Extract text using multiple OCR engines and combine results"""
        
        results = {}
        
        # Tesseract OCR
        try:
            tesseract_text = pytesseract.image_to_string(image, config=self.tesseract_config)
            tesseract_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Calculate confidence
            confidences = [int(conf) for conf in tesseract_data['conf'] if int(conf) > 0]
            tesseract_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            results['tesseract'] = {
                'text': tesseract_text.strip(),
                'confidence': tesseract_confidence / 100.0,  # Normalize to 0-1
                'word_count': len(tesseract_text.split())
            }
        except Exception as e:
            logging.warning(f"Tesseract OCR failed: {e}")
            results['tesseract'] = {'text': '', 'confidence': 0.0, 'word_count': 0}
        
        # PaddleOCR
        if self.paddle_ocr:
            try:
                paddle_result = self.paddle_ocr.ocr(np.array(image), cls=True)
                if paddle_result and paddle_result[0]:
                    paddle_texts = []
                    paddle_confidences = []
                    
                    for line in paddle_result[0]:
                        if line:
                            text = line[1][0]
                            confidence = line[1][1]
                            paddle_texts.append(text)
                            paddle_confidences.append(confidence)
                    
                    paddle_text = '\n'.join(paddle_texts)
                    paddle_confidence = sum(paddle_confidences) / len(paddle_confidences) if paddle_confidences else 0
                    
                    results['paddle'] = {
                        'text': paddle_text,
                        'confidence': paddle_confidence,
                        'word_count': len(paddle_text.split())
                    }
                else:
                    results['paddle'] = {'text': '', 'confidence': 0.0, 'word_count': 0}
            except Exception as e:
                logging.warning(f"PaddleOCR failed: {e}")
                results['paddle'] = {'text': '', 'confidence': 0.0, 'word_count': 0}
        
        # EasyOCR
        if self.easy_reader:
            try:
                easy_result = self.easy_reader.readtext(np.array(image))
                easy_texts = []
                easy_confidences = []
                
                for detection in easy_result:
                    text = detection[1]
                    confidence = detection[2]
                    easy_texts.append(text)
                    easy_confidences.append(confidence)
                
                easy_text = '\n'.join(easy_texts)
                easy_confidence = sum(easy_confidences) / len(easy_confidences) if easy_confidences else 0
                
                results['easyocr'] = {
                    'text': easy_text,
                    'confidence': easy_confidence,
                    'word_count': len(easy_text.split())
                }
            except Exception as e:
                logging.warning(f"EasyOCR failed: {e}")
                results['easyocr'] = {'text': '', 'confidence': 0.0, 'word_count': 0}
        
        # Select best result based on confidence and word count
        best_result = self._select_best_ocr_result(results)
        
        return {
            'text': best_result['text'],
            'confidence': best_result['confidence'],
            'engine_used': best_result['engine'],
            'all_results': results
        }
    
    def _select_best_ocr_result(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best OCR result based on confidence and word count"""
        
        best_score = 0
        best_result = {'text': '', 'confidence': 0.0, 'engine': 'none'}
        
        for engine, result in results.items():
            if result['word_count'] == 0:
                continue
            
            # Score = confidence * word_count_factor
            word_count_factor = min(result['word_count'] / 50.0, 1.0)  # Normalize word count
            score = result['confidence'] * 0.7 + word_count_factor * 0.3
            
            if score > best_score:
                best_score = score
                best_result = {
                    'text': result['text'],
                    'confidence': result['confidence'],
                    'engine': engine
                }
        
        return best_result


class TableExtractor:
    """Advanced table extraction from PDFs"""
    
    @staticmethod
    async def extract_tables_camelot(pdf_path: str, pages: List[int] = None) -> List[Dict[str, Any]]:
        """Extract tables using Camelot"""
        
        tables = []
        
        try:
            if pages:
                page_str = ','.join(map(str, pages))
            else:
                page_str = 'all'
            
            # Try lattice method first (for tables with lines)
            try:
                camelot_tables = camelot.read_pdf(pdf_path, pages=page_str, flavor='lattice')
                
                for i, table in enumerate(camelot_tables):
                    if table.accuracy > 0.7:  # Good quality table
                        tables.append({
                            'page': table.parsing_report['page'],
                            'method': 'lattice',
                            'accuracy': table.accuracy,
                            'data': table.df.to_dict('records'),
                            'shape': table.df.shape
                        })
            except Exception as e:
                logging.debug(f"Camelot lattice method failed: {e}")
            
            # Try stream method (for tables without lines)
            try:
                camelot_tables = camelot.read_pdf(pdf_path, pages=page_str, flavor='stream')
                
                for i, table in enumerate(camelot_tables):
                    if table.accuracy > 0.6:  # Lower threshold for stream
                        tables.append({
                            'page': table.parsing_report['page'],
                            'method': 'stream',
                            'accuracy': table.accuracy,
                            'data': table.df.to_dict('records'),
                            'shape': table.df.shape
                        })
            except Exception as e:
                logging.debug(f"Camelot stream method failed: {e}")
                
        except Exception as e:
            logging.warning(f"Camelot table extraction failed: {e}")
        
        return tables
    
    @staticmethod
    async def extract_tables_tabula(pdf_path: str, pages: List[int] = None) -> List[Dict[str, Any]]:
        """Extract tables using Tabula"""
        
        tables = []
        
        try:
            if pages:
                page_list = pages
            else:
                page_list = 'all'
            
            tabula_tables = tabula.read_pdf(
                pdf_path, 
                pages=page_list, 
                multiple_tables=True,
                pandas_options={'header': 0}
            )
            
            for i, df in enumerate(tabula_tables):
                if not df.empty and df.shape[0] > 1:  # Valid table
                    tables.append({
                        'page': i + 1,
                        'method': 'tabula',
                        'data': df.to_dict('records'),
                        'shape': df.shape
                    })
                    
        except Exception as e:
            logging.warning(f"Tabula table extraction failed: {e}")
        
        return tables


class ProductExtractorPDF:
    """Extract products from PDF text using patterns"""
    
    PRODUCT_PATTERNS = {
        'catalog_with_prices': [
            r'([A-Z][A-Za-z\s\-]{10,50})\s+\$?([\d,]+\.?\d*)',
            r'([A-Z][A-Za-z\s\-]{5,30})\s+.*?\$?([\d,]+)',
            r'(\w+(?:\s+\w+){1,4})\s+.*?[\$\€\£]?([\d,]+\.?\d{0,2})'
        ],
        'simple_listing': [
            r'^[\-\*\•]\s*([A-Za-z][A-Za-z\s\-]{10,})',
            r'^\d+\.\s*([A-Za-z][A-Za-z\s\-]{10,})',
            r'^([A-Z][A-Za-z\s\-]{15,})'
        ],
        'table_rows': [
            r'([A-Za-z][A-Za-z\s\-]{5,40})\s+(\d+)\s+([\d,]+\.?\d*)',
            r'([A-Za-z][A-Za-z\s\-]{5,40})\s+([\d,]+\.?\d*)\s+(\d+)'
        ]
    }
    
    @classmethod
    def extract_products_from_text(cls, text: str, confidence: float) -> List[Dict[str, Any]]:
        """Extract products from text using pattern matching"""
        
        products = []
        lines = text.split('\n')
        
        # Try catalog with prices pattern
        for line in lines:
            line = line.strip()
            if len(line) < 10:
                continue
            
            for pattern in cls.PRODUCT_PATTERNS['catalog_with_prices']:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    price_str = match.group(2).replace(',', '')
                    
                    try:
                        price = float(price_str)
                        if 10 <= price <= 100000:  # Reasonable price range
                            products.append({
                                'name': name,
                                'price': price,
                                'currency': 'MXN',
                                'source': 'pdf_pattern',
                                'extraction_confidence': confidence * 0.9,
                                'raw_text': line
                            })
                            break
                    except ValueError:
                        continue
        
        # If no priced products found, try simple listings
        if not products:
            for line in lines:
                line = line.strip()
                if len(line) < 15:
                    continue
                
                for pattern in cls.PRODUCT_PATTERNS['simple_listing']:
                    match = re.match(pattern, line)
                    if match:
                        name = match.group(1).strip()
                        
                        # Filter out common non-product lines
                        if not cls._is_likely_product_name(name):
                            continue
                        
                        products.append({
                            'name': name,
                            'price': None,
                            'currency': 'MXN',
                            'source': 'pdf_listing',
                            'extraction_confidence': confidence * 0.7,
                            'raw_text': line
                        })
                        break
        
        return products[:50]  # Limit results
    
    @classmethod
    def _is_likely_product_name(cls, name: str) -> bool:
        """Check if text looks like a product name"""
        
        # Filter out common non-product patterns
        excluded_patterns = [
            r'^(página|page|capítulo|chapter|índice|index)',
            r'^(total|subtotal|precio|price|cantidad|quantity)',
            r'^\d+$',
            r'^[A-Z]{1,3}$'
        ]
        
        name_lower = name.lower()
        
        for pattern in excluded_patterns:
            if re.match(pattern, name_lower):
                return False
        
        # Must contain at least one letter
        if not re.search(r'[A-Za-z]', name):
            return False
        
        # Should have reasonable length
        if len(name) < 5 or len(name) > 100:
            return False
        
        return True


class PDFProcessingAgent(BaseAgent):
    """
    Advanced PDF processing agent with multi-pass OCR and intelligent extraction
    """
    
    def __init__(self):
        super().__init__(AgentType.PDF_PROCESSOR, "pdf_processor")
        self.ocr_engine = OCREngine()
        self.table_extractor = TableExtractor()
        self.product_extractor = ProductExtractorPDF()
    
    async def process(self, state: CatalogExtractionState, **kwargs) -> CatalogExtractionState:
        """Process PDF sources for product extraction"""
        
        self.logger.info("Starting PDF processing")
        
        try:
            # Filter PDF sources
            pdf_sources = [s for s in state["sources"] if s.type == SourceType.PDF]
            
            if not pdf_sources:
                return self.update_state(state, {
                    "current_step": "pdf_processing_skipped",
                    "raw_products": state.get("raw_products", [])
                })
            
            all_products = []
            
            # Process each PDF source
            for source in pdf_sources:
                try:
                    if source.file_path and os.path.exists(source.file_path):
                        products = await self._process_pdf_file(source.file_path)
                        all_products.extend(products)
                    elif source.url:
                        # Download PDF from URL first
                        temp_path = await self._download_pdf(source.url)
                        if temp_path:
                            products = await self._process_pdf_file(temp_path)
                            all_products.extend(products)
                            os.unlink(temp_path)  # Clean up
                    
                except Exception as e:
                    error_msg = f"Failed to process PDF source {source.file_path or source.url}: {e}"
                    self.logger.error(error_msg)
                    state = self.add_error(state, error_msg)
            
            return self.update_state(state, {
                "current_step": "pdf_processing_completed",
                "raw_products": state.get("raw_products", []) + all_products,
                "completed_sources": state.get("completed_sources", 0) + len(pdf_sources)
            })
            
        except Exception as e:
            error_msg = f"PDF processing agent failed: {e}"
            self.logger.error(error_msg)
            return self.add_error(state, error_msg)
    
    async def _process_pdf_file(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Process single PDF file"""
        
        self.logger.info(f"Processing PDF: {pdf_path}")
        
        try:
            # Open PDF
            pdf_document = fitz.open(pdf_path)
            total_pages = pdf_document.page_count
            
            if total_pages > 50:  # Limit processing for very large PDFs
                self.logger.warning(f"Large PDF detected ({total_pages} pages), processing first 50")
                pages_to_process = list(range(min(50, total_pages)))
            else:
                pages_to_process = list(range(total_pages))
            
            all_products = []
            
            # First try: Extract tables if present
            table_products = await self._extract_from_tables(pdf_path, pages_to_process)
            if table_products:
                all_products.extend(table_products)
                self.logger.info(f"Extracted {len(table_products)} products from tables")
            
            # Second pass: OCR text extraction
            text_products = await self._extract_from_text_ocr(pdf_document, pages_to_process)
            if text_products:
                all_products.extend(text_products)
                self.logger.info(f"Extracted {len(text_products)} products from OCR")
            
            pdf_document.close()
            
            # Deduplicate products from same PDF
            unique_products = self._deduplicate_pdf_products(all_products)
            
            self.logger.info(f"Total unique products from PDF: {len(unique_products)}")
            return unique_products
            
        except Exception as e:
            self.logger.error(f"PDF processing error: {e}")
            return []
    
    async def _extract_from_tables(self, pdf_path: str, pages: List[int]) -> List[Dict[str, Any]]:
        """Extract products from PDF tables"""
        
        products = []
        
        try:
            # Try Camelot first
            camelot_tables = await self.table_extractor.extract_tables_camelot(pdf_path, pages)
            
            for table in camelot_tables:
                table_products = self._extract_products_from_table(table['data'])
                if table_products:
                    for product in table_products:
                        product['source'] = f"pdf_table_page_{table['page']}"
                        product['extraction_method'] = table['method']
                    products.extend(table_products)
            
            # Try Tabula if Camelot didn't find much
            if len(products) < 5:
                tabula_tables = await self.table_extractor.extract_tables_tabula(pdf_path, pages)
                
                for table in tabula_tables:
                    table_products = self._extract_products_from_table(table['data'])
                    if table_products:
                        for product in table_products:
                            product['source'] = f"pdf_table_page_{table['page']}"
                            product['extraction_method'] = 'tabula'
                        products.extend(table_products)
        
        except Exception as e:
            self.logger.warning(f"Table extraction failed: {e}")
        
        return products
    
    def _extract_products_from_table(self, table_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract products from table data"""
        
        if not table_data or len(table_data) < 2:
            return []
        
        products = []
        
        # Analyze table headers to determine column mapping
        headers = list(table_data[0].keys())
        
        name_col = self._find_column_by_keywords(headers, ['nombre', 'name', 'producto', 'product', 'descripción', 'description'])
        price_col = self._find_column_by_keywords(headers, ['precio', 'price', 'costo', 'cost', 'valor', 'value'])
        quantity_col = self._find_column_by_keywords(headers, ['cantidad', 'quantity', 'stock', 'inventario'])
        
        if not name_col:
            return []
        
        for row in table_data[1:]:  # Skip header row
            try:
                name = str(row.get(name_col, '')).strip()
                
                if len(name) < 5 or name.lower() in ['', 'nan', 'none', 'null']:
                    continue
                
                price = None
                if price_col:
                    price_str = str(row.get(price_col, '')).strip()
                    price_numbers = re.findall(r'[\d,]+\.?\d*', price_str.replace(',', ''))
                    if price_numbers:
                        try:
                            price = float(price_numbers[0])
                        except ValueError:
                            pass
                
                quantity = None
                if quantity_col:
                    quantity_str = str(row.get(quantity_col, '')).strip()
                    quantity_numbers = re.findall(r'\d+', quantity_str)
                    if quantity_numbers:
                        try:
                            quantity = int(quantity_numbers[0])
                        except ValueError:
                            pass
                
                products.append({
                    'name': name,
                    'price': price,
                    'stock': quantity,
                    'currency': 'MXN',
                    'source': 'pdf_table',
                    'extraction_confidence': 0.85
                })
                
            except Exception as e:
                self.logger.debug(f"Error processing table row: {e}")
                continue
        
        return products[:30]  # Limit results
    
    def _find_column_by_keywords(self, headers: List[str], keywords: List[str]) -> Optional[str]:
        """Find column name by keywords"""
        
        for header in headers:
            header_lower = header.lower().strip()
            for keyword in keywords:
                if keyword in header_lower:
                    return header
        
        return None
    
    async def _extract_from_text_ocr(self, pdf_document, pages: List[int]) -> List[Dict[str, Any]]:
        """Extract products using OCR on PDF pages"""
        
        all_products = []
        
        for page_num in pages[:10]:  # Limit OCR pages
            try:
                page = pdf_document[page_num]
                
                # Convert page to image
                matrix = fitz.Matrix(2, 2)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=matrix)
                img_data = pix.tobytes("png")
                
                # Create PIL Image
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    temp_file.write(img_data)
                    temp_path = temp_file.name
                
                image = Image.open(temp_path)
                
                # Multi-engine OCR
                ocr_result = await self.ocr_engine.extract_text_multi_engine(image)
                
                # Clean up temp file
                os.unlink(temp_path)
                
                if ocr_result['confidence'] > 0.5 and len(ocr_result['text']) > 50:
                    # Extract products from OCR text
                    page_products = self.product_extractor.extract_products_from_text(
                        ocr_result['text'], 
                        ocr_result['confidence']
                    )
                    
                    # Add page info
                    for product in page_products:
                        product['source_page'] = page_num + 1
                        product['ocr_engine'] = ocr_result['engine_used']
                    
                    all_products.extend(page_products)
                
            except Exception as e:
                self.logger.warning(f"OCR failed for page {page_num}: {e}")
                continue
        
        return all_products
    
    def _deduplicate_pdf_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate products from same PDF"""
        
        if not products:
            return products
        
        unique_products = []
        seen_names = set()
        
        # Sort by confidence (highest first)
        products_sorted = sorted(products, key=lambda x: x.get('extraction_confidence', 0), reverse=True)
        
        for product in products_sorted:
            name = product.get('name', '').strip().lower()
            
            if not name or name in seen_names:
                continue
            
            seen_names.add(name)
            unique_products.append(product)
        
        return unique_products
    
    async def _download_pdf(self, url: str) -> Optional[str]:
        """Download PDF from URL to temporary file"""
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                            temp_file.write(content)
                            return temp_file.name
        
        except Exception as e:
            self.logger.error(f"Failed to download PDF from {url}: {e}")
        
        return None