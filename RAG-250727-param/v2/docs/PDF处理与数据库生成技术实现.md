# PDF处理与数据库生成技术实现

## 1. 技术架构总览

### 1.1 整体架构
PDF处理系统采用多阶段管道架构，支持从原始PDF到向量数据库的完整流程：

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   PDF文件   │───→│  解析提取   │───→│  内容处理   │───→│  向量化存储 │
│  (输入)     │    │  (文本/图像)│    │  (分块/增强)│    │  (数据库)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 1.2 技术特点
- **多模态处理**: 支持文本、图像、表格的统一处理
- **增量更新**: 支持文档的增量处理和更新
- **元数据管理**: 完整的文档元数据提取和管理
- **向量化存储**: 基于FAISS的高效向量检索

## 2. PDF解析与内容提取

### 2.1 PDF处理器核心实现

```python
class PDFProcessor:
    """PDF文档处理器"""
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """处理单个PDF文件"""
        result = {
            'file_path': pdf_path,
            'pages': [],
            'metadata': {},
            'processing_time': 0
        }
        
        start_time = time.time()
        
        # 1. 提取PDF元数据
        result['metadata'] = self._extract_metadata(pdf_path)
        
        # 2. 逐页处理
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(pdf_reader.pages)):
                page_result = self._process_page(pdf_reader.pages[page_num], page_num)
                result['pages'].append(page_result)
        
        result['processing_time'] = time.time() - start_time
        return result
```

### 2.2 多模态内容提取

**文本提取**:
```python
def _extract_text(self, page) -> str:
    """提取页面文本"""
    text = page.extract_text()
    # 文本清理和标准化
    text = self._clean_text(text)
    return text

def _clean_text(self, text: str) -> str:
    """清理和标准化文本"""
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    # 标准化换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # 移除控制字符
    text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
    return text.strip()
```

**图像提取**:
```python
def extract_images_from_page(self, page, page_num: int) -> List[Dict[str, Any]]:
    """从页面提取图像"""
    images = []
    
    if '/XObject' in page['/Resources']:
        xObject = page['/Resources']['/XObject'].get_object()
        
        for obj_name in xObject:
            obj = xObject[obj_name]
            
            if obj['/Subtype'] == '/Image':
                image_info = self._process_image_object(obj, obj_name, page_num)
                if image_info:
                    images.append(image_info)
    
    return images
```

**表格提取**:
```python
def _detect_tables_by_text(self, page) -> List[Dict[str, Any]]:
    """基于文本分析检测表格"""
    text = page.extract_text()
    lines = text.split('\n')
    
    # 分析文本结构，寻找表格特征
    table_candidates = self._find_table_candidates(lines)
    
    tables = []
    for candidate in table_candidates:
        if self._validate_table_structure(candidate):
            table_data = self._extract_table_data(candidate)
            tables.append({
                'type': 'text_table',
                'data': table_data,
                'confidence': candidate['confidence']
            })
    
    return tables
```

## 3. 内容处理与分块

### 3.1 智能分块策略

```python
class EnhancedChunker:
    """增强文档分块器"""
    
    def _semantic_chunking(self, text: str, doc: Document) -> List[Document]:
        """语义感知分块"""
        chunks = []
        
        # 1. 按段落分割
        paragraphs = self._split_into_paragraphs(text)
        
        # 2. 语义相似性分析
        semantic_groups = self._group_by_semantic_similarity(paragraphs)
        
        # 3. 生成分块
        for group in semantic_groups:
            chunk_content = '\n\n'.join(group)
            
            if len(chunk_content) >= self.min_chunk_size:
                chunk = self._create_chunk(doc, chunk_content, 'semantic')
                chunks.append(chunk)
        
        return chunks

def _group_by_semantic_similarity(self, paragraphs: List[str]) -> List[List[str]]:
    """基于语义相似性分组段落"""
    if len(paragraphs) <= 1:
        return [paragraphs]
    
    groups = []
    current_group = [paragraphs[0]]
    
    for i in range(1, len(paragraphs)):
        current_para = paragraphs[i]
        
        # 计算与当前组的相似性
        similarity = self._calculate_group_similarity(current_para, current_group)
        
        if similarity >= self.config.get('semantic_threshold', 0.6):
            # 添加到当前组
            current_group.append(current_para)
        else:
            # 开始新组
            if current_group:
                groups.append(current_group)
            current_group = [current_para]
    
    # 添加最后一组
    if current_group:
        groups.append(current_group)
    
    return groups
```

### 3.2 图像内容增强

```python
class ImageEnhancer:
    """图像内容增强器"""
    
    def enhance_image(self, image_path: str, metadata: dict) -> Dict[str, Any]:
        """增强图像内容"""
        enhanced_info = {
            'original_path': image_path,
            'enhanced_content': '',
            'ocr_text': '',
            'image_features': {}
        }
        
        try:
            # 1. OCR文本提取
            if self.ocr_enabled:
                enhanced_info['ocr_text'] = self._extract_ocr_text(image_path)
            
            # 2. 图像特征分析
            if self.image_analysis_enabled:
                enhanced_info['image_features'] = self._analyze_image_features(image_path)
            
            # 3. 生成增强内容
            enhanced_info['enhanced_content'] = self._generate_enhanced_content(
                enhanced_info['ocr_text'], 
                enhanced_info['image_features']
            )
            
        except Exception as e:
            logger.error(f"图像增强失败: {image_path}, 错误: {str(e)}")
        
        return enhanced_info

def _extract_ocr_text(self, image_path: str) -> str:
    """提取OCR文本"""
    try:
        # 使用PaddleOCR进行文本识别
        from paddleocr import PaddleOCR
        
        ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        result = ocr.ocr(image_path, cls=True)
        
        if not result or not result[0]:
            return ""
        
        # 提取文本内容
        texts = []
        for line in result[0]:
            if line and len(line) >= 2:
                text = line[1][0]  # 文本内容
                confidence = line[1][1]  # 置信度
                
                # 过滤低置信度的结果
                if confidence >= self.config.get('ocr_confidence_threshold', 0.7):
                    texts.append(text)
        
        return '\n'.join(texts)
        
    except Exception as e:
        logger.warning(f"OCR提取失败: {image_path}, 错误: {str(e)}")
        return ""
```

## 4. 向量化与存储

### 4.1 向量生成器

```python
class VectorGenerator:
    """向量生成器"""
    
    def create_vector_store(self, documents: List[Document], 
                           store_path: str) -> FAISS:
        """创建向量存储"""
        try:
            # 1. 生成文档向量
            embeddings = self._generate_embeddings(documents)
            
            # 2. 创建FAISS索引
            index = self._create_faiss_index(embeddings)
            
            # 3. 保存索引和元数据
            self._save_vector_store(index, documents, store_path)
            
            return index
            
        except Exception as e:
            logger.error(f"向量存储创建失败: {str(e)}")
            raise

def _generate_embeddings(self, documents: List[Document]) -> np.ndarray:
    """生成文档向量"""
    embeddings = []
    
    # 批量处理
    for i in range(0, len(documents), self.batch_size):
        batch = documents[i:i + self.batch_size]
        batch_embeddings = self._process_batch(batch)
        embeddings.extend(batch_embeddings)
    
    return np.array(embeddings)

def _prepare_text_for_embedding(self, doc: Document) -> str:
    """准备用于向量化的文本"""
    text_parts = []
    
    # 添加主要内容
    if doc.content:
        text_parts.append(doc.content)
    
    # 添加元数据信息
    if doc.metadata:
        if 'doc_type' in doc.metadata:
            text_parts.append(f"文档类型: {doc.metadata['doc_type']}")
        
        if 'page_number' in doc.metadata:
            text_parts.append(f"页面: {doc.metadata['page_number']}")
        
        if 'file_name' in doc.metadata:
            text_parts.append(f"文件: {doc.metadata['file_name']}")
    
    # 组合文本
    combined_text = ' '.join(text_parts)
    
    # 截断到模型最大长度
    max_length = self.config.get('max_text_length', 8000)
    if len(combined_text) > max_length:
        combined_text = combined_text[:max_length]
    
    return combined_text
```

### 4.2 FAISS索引管理

```python
def _create_faiss_index(self, embeddings: np.ndarray) -> FAISS:
    """创建FAISS索引"""
    try:
        # 选择索引类型
        index_type = self.config.get('index_type', 'IVFFlat')
        
        if index_type == 'IVFFlat':
            # 使用IVF索引，适合大规模数据
            dimension = embeddings.shape[1]
            nlist = min(100, max(1, embeddings.shape[0] // 100))
            
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            
            # 训练索引
            if embeddings.shape[0] >= nlist:
                index.train(embeddings)
                index.add(embeddings)
            else:
                # 数据量不足，使用Flat索引
                index = faiss.IndexFlatL2(dimension)
                index.add(embeddings)
                
        else:
            # 默认使用Flat索引
            index = faiss.IndexFlatL2(embeddings.shape[1])
            index.add(embeddings)
        
        return index
        
    except Exception as e:
        logger.error(f"FAISS索引创建失败: {str(e)}")
        raise
```

## 5. 元数据管理

### 5.1 元数据结构设计

```python
class DocumentMetadata:
    """文档元数据"""
    
    def __init__(self):
        # 基础信息
        self.file_path: str = ""
        self.file_name: str = ""
        self.file_size: int = 0
        self.file_type: str = "pdf"
        self.created_time: datetime = None
        self.modified_time: datetime = None
        
        # 处理信息
        self.processing_time: float = 0.0
        self.processing_status: str = "pending"
        self.processing_errors: List[str] = []
        
        # 内容信息
        self.total_pages: int = 0
        self.total_chunks: int = 0
        self.text_length: int = 0
        self.image_count: int = 0
        self.table_count: int = 0
        
        # 向量信息
        self.vector_dimension: int = 1536
        self.embedding_model: str = ""
        self.index_type: str = ""
        
        # 自定义标签
        self.tags: List[str] = []
        self.category: str = ""
        self.priority: int = 0
```

### 5.2 元数据存储

```python
class MetadataManager:
    """元数据管理器"""
    
    def _init_metadata_db(self):
        """初始化元数据库"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建文档元数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS document_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER,
                    file_type TEXT,
                    processing_status TEXT,
                    total_pages INTEGER,
                    total_chunks INTEGER,
                    vector_dimension INTEGER,
                    embedding_model TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建分块元数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chunk_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id TEXT UNIQUE NOT NULL,
                    source_document TEXT NOT NULL,
                    chunk_type TEXT,
                    page_number INTEGER,
                    content_length INTEGER,
                    quality_score REAL,
                    embedding_model TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("元数据库初始化成功")
            
        except Exception as e:
            logger.error(f"元数据库初始化失败: {str(e)}")
            raise
```

## 6. 增量处理与更新

### 6.1 增量更新策略

```python
class IncrementalPipeline:
    """增量处理管道"""
    
    def process_incremental_update(self, pdf_dir: str, 
                                 vector_db_path: str) -> bool:
        """处理增量更新"""
        try:
            # 1. 扫描目录变化
            changes = self._scan_directory_changes(pdf_dir)
            
            if not changes:
                logger.info("没有检测到变化")
                return True
            
            # 2. 加载现有向量存储
            self.vector_store = self._load_vector_store(vector_db_path)
            
            # 3. 处理新增文件
            for new_file in changes['new_files']:
                self._process_new_file(new_file)
            
            # 4. 处理修改文件
            for modified_file in changes['modified_files']:
                self._process_modified_file(modified_file)
            
            # 5. 处理删除文件
            for deleted_file in changes['deleted_files']:
                self._process_deleted_file(deleted_file)
            
            # 6. 保存更新后的向量存储
            self._save_vector_store(vector_db_path)
            
            logger.info("增量更新处理完成")
            return True
            
        except Exception as e:
            logger.error(f"增量更新处理失败: {str(e)}")
            return False

def _scan_directory_changes(self, pdf_dir: str) -> Dict[str, List[str]]:
    """扫描目录变化"""
    changes = {
        'new_files': [],
        'modified_files': [],
        'deleted_files': []
    }
    
    try:
        # 获取当前文件列表
        current_files = set(self._get_pdf_files(pdf_dir))
        
        # 获取数据库中的文件列表
        stored_files = set(self.metadata_manager.get_stored_files())
        
        # 检测新增文件
        changes['new_files'] = list(current_files - stored_files)
        
        # 检测删除文件
        changes['deleted_files'] = list(stored_files - current_files)
        
        # 检测修改文件
        for file_path in current_files & stored_files:
            if self._is_file_modified(file_path):
                changes['modified_files'].append(file_path)
        
        logger.info(f"检测到变化: 新增 {len(changes['new_files'])}, "
                   f"修改 {len(changes['modified_files'])}, "
                   f"删除 {len(changes['deleted_files'])}")
        
    except Exception as e:
        logger.error(f"目录扫描失败: {str(e)}")
    
    return changes
```

## 7. 关键技术点总结

### 7.1 PDF处理技术
- **多模态提取**: 文本、图像、表格的统一处理
- **智能分块**: 语义感知的文档分块策略
- **内容增强**: OCR文本提取和图像特征分析

### 7.2 向量化技术
- **批量处理**: 高效的批量向量生成
- **索引优化**: 基于FAISS的高性能向量检索
- **模型选择**: 支持多种嵌入模型

### 7.3 元数据管理
- **结构化存储**: 完整的文档和分块元数据
- **增量更新**: 智能的增量处理机制
- **质量评估**: 内容质量和置信度评估

### 7.4 性能优化
- **并行处理**: 多线程文档处理
- **内存管理**: 高效的内存使用策略
- **缓存机制**: 多层缓存优化

## 8. 与V2版本的集成

### 8.1 技术兼容性
- **统一接口**: 新老版本使用相同的处理接口
- **配置共享**: 配置文件兼容性设计
- **数据格式**: 统一的数据结构和元数据格式

### 8.2 功能增强
- **V1基础**: 提供基础的PDF处理能力
- **V2扩展**: 支持高级优化和实时处理
- **平滑升级**: 支持从V1到V2的平滑迁移

这套PDF处理技术为新老版本系统提供了统一、高效、可扩展的文档处理能力，是整个RAG系统的重要基础。
