"""
minerU集成模块

负责与minerU API集成，实现PDF文档的解析和内容提取。
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path

class MinerUIntegration:
    """
    minerU集成类
    
    功能：
    - 调用minerU API解析PDF文档
    - 提取文本、图像、表格内容
    - 管理解析任务和结果
    - 错误处理和重试机制
    """
    
    def __init__(self, config_manager):
        """
        初始化minerU集成
        
        :param config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        
        # minerU配置
        mineru_config = self.config.get('mineru', {})
        self.api_endpoint = mineru_config.get('api_endpoint', 'https://api.mineru.com')
        self.batch_size = mineru_config.get('batch_size', 10)
        self.timeout = mineru_config.get('timeout', 300)
        self.retry_count = mineru_config.get('retry_count', 3)
        self.poll_interval = mineru_config.get('poll_interval', 10)
        
        logging.info("MinerU集成模块初始化完成")
    
    def parse_pdf_document(self, pdf_path: str, output_dir: str) -> Dict[str, Any]:
        """
        解析单个PDF文档（使用真实MinerU API）
        
        :param pdf_path: PDF文件路径
        :param output_dir: 输出目录
        :return: 解析结果
        """
        try:
            logging.info(f"开始解析PDF文档: {pdf_path}")
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 从环境变量获取API密钥
            api_key = os.getenv('MINERU_API_KEY')
            if not api_key:
                raise ValueError("未设置环境变量 MINERU_API_KEY")
            
            # 调用真实MinerU API
            parsed_content = self._call_mineru_api(pdf_path, output_dir, api_key)
            
            logging.info(f"PDF解析完成: {pdf_path}")
            return {
                'success': True,
                'pdf_path': pdf_path,
                'output_dir': output_dir,
                'parsed_content': parsed_content,
                'file_size': os.path.getsize(pdf_path)
            }
            
        except Exception as e:
            logging.error(f"PDF解析失败: {pdf_path}, 错误: {e}")
            return {
                'success': False,
                'pdf_path': pdf_path,
                'error': str(e)
            }
    
    def _call_mineru_api(self, pdf_path: str, output_dir: str, api_key: str) -> Dict[str, Any]:
        """
        调用真实MinerU API解析PDF
        
        :param pdf_path: PDF文件路径
        :param output_dir: 输出目录
        :param api_key: MinerU API密钥
        :return: 解析后的内容
        """
        try:
            logging.info(f"开始调用MinerU API解析PDF: {pdf_path}")
            
            # 1. 获取上传URL和batch_id
            upload_result = self._get_upload_url_and_batch_id(pdf_path, api_key)
            if not upload_result:
                raise RuntimeError("获取上传URL和batch_id失败")
            
            upload_url = upload_result['upload_url']
            batch_id = upload_result['batch_id']
            
            # 2. 上传PDF文件
            if not self._upload_pdf_file(pdf_path, upload_url):
                raise RuntimeError("PDF文件上传失败")
            
            # 3. 等待解析完成
            if not self._wait_for_parsing_complete(batch_id, api_key):
                raise RuntimeError("PDF解析超时或失败")
            
            # 4. 下载解析结果到临时目录
            temp_output_dir = os.path.join(output_dir, 'temp')
            os.makedirs(temp_output_dir, exist_ok=True)
            logging.info(f"创建临时目录: {temp_output_dir}")
            
            result_files = self._download_parsing_results(batch_id, api_key, temp_output_dir)
            if not result_files:
                raise RuntimeError("下载解析结果失败")
            
            logging.info(f"下载完成，共 {len(result_files)} 个文件")
            
            # 5. 处理输出文件（重命名、解压、整理）
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            # 传入根目录，让_process_output_files自己创建PDF子目录
            final_output_dir = output_dir
            logging.info(f"使用根目录作为输出目录: {final_output_dir}")
            
            processed_files = self._process_output_files(result_files, final_output_dir, pdf_name)
            logging.info(f"文件处理完成，共 {len(processed_files)} 个文件")
            
            # 6. 解析结果文件
            # 直接使用根目录，因为现在文件都在根目录下
            parsed_content = self._parse_result_files(processed_files, final_output_dir)
            
            # 7. 清理临时文件
            import shutil
            if os.path.exists(temp_output_dir):
                shutil.rmtree(temp_output_dir)
                logging.info("临时目录清理完成")
            
            logging.info(f"MinerU API调用完成: {pdf_path}")
            return parsed_content
            
        except Exception as e:
            logging.error(f"MinerU API调用失败: {e}")
            raise

    def _get_upload_url_and_batch_id(self, pdf_path: str, api_key: str) -> Optional[Dict[str, str]]:
        """获取PDF上传URL和batch_id"""
        try:
            url = 'https://mineru.net/api/v4/file-urls/batch'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            
            filename = os.path.basename(pdf_path)
            data = {
                "enable_formula": True,
                "language": "auto",
                "enable_table": True,
                "files": [{
                    "name": filename,
                    "is_ocr": True,
                    "data_id": f"auto_1"
                }]
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    data_info = result.get("data", {})
                    file_urls = data_info.get("file_urls", [])
                    batch_id = data_info.get("batch_id")
                    
                    if file_urls and batch_id:
                        return {
                            'upload_url': file_urls[0],  # 返回第一个上传URL
                            'batch_id': batch_id
                        }
            
            logging.error(f"获取上传URL和batch_id失败: {response.status_code}, {response.text}")
            return None
            
        except Exception as e:
            logging.error(f"获取上传URL和batch_id异常: {e}")
            return None

    def _upload_pdf_file(self, pdf_path: str, upload_url: str) -> bool:
        """上传PDF文件"""
        try:
            with open(pdf_path, 'rb') as f:
                response = requests.put(upload_url, data=f, timeout=60)
                if response.status_code == 200:
                    logging.info(f"PDF文件上传成功: {pdf_path}")
                    return True
                else:
                    logging.error(f"PDF文件上传失败: {response.status_code}")
                    return False
        except Exception as e:
            logging.error(f"PDF文件上传异常: {e}")
            return False

    def _wait_for_parsing_complete(self, batch_id: str, api_key: str) -> bool:
        """等待解析完成"""
        try:
            url = f'https://mineru.net/api/v4/extract-results/batch/{batch_id}'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            
            max_wait_time = 300  # 最大等待5分钟
            start_time = time.time()
            poll_count = 0
            
            logging.info("开始轮询解析状态...")
            
            while time.time() - start_time < max_wait_time:
                poll_count += 1
                elapsed_time = int(time.time() - start_time)
                
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    extract_result = result.get("data", {}).get("extract_result", [])
                    
                    if extract_result:
                        item = extract_result[0]  # 假设只有一个文件
                        state = item.get('state', 'unknown')
                        
                        if state == 'done':
                            logging.info(f"✅ PDF解析完成 (耗时: {elapsed_time}秒, 轮询: {poll_count}次)")
                            return True
                        elif state == 'failed':
                            logging.error(f"❌ PDF解析失败: {item.get('err_msg', '')}")
                            return False
                        else:
                            logging.info(f"⏳ 解析状态: {state} (耗时: {elapsed_time}秒, 轮询: {poll_count}次)")
                
                # 显示进度
                if poll_count % 3 == 0:  # 每3次轮询显示一次进度
                    logging.info(f"⏳ 等待解析完成... (耗时: {elapsed_time}秒, 轮询: {poll_count}次)")
                
                time.sleep(10)
            
            logging.error(f"❌ PDF解析超时 (耗时: {max_wait_time}秒, 轮询: {poll_count}次)")
            return False
            
        except Exception as e:
            logging.error(f"等待解析完成异常: {e}")
            return False

    def _download_parsing_results(self, batch_id: str, api_key: str, output_dir: str) -> List[str]:
        """下载解析结果"""
        try:
            url = f'https://mineru.net/api/v4/extract-results/batch/{batch_id}'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                extract_result = result.get("data", {}).get("extract_result", [])
                
                downloaded_files = []
                for item in extract_result:
                    if item.get('state') == 'done' and item.get('full_zip_url'):
                        zip_url = item['full_zip_url']
                        filename = item['file_name']
                        
                        # 下载zip文件
                        zip_path = os.path.join(output_dir, f"{filename}.zip")
                        if self._download_file(zip_url, zip_path):
                            # 直接返回zip文件路径，让后续的_process_output_files处理
                            downloaded_files.append(zip_path)
                
                return downloaded_files
            
            return []
            
        except Exception as e:
            logging.error(f"下载解析结果异常: {e}")
            return []

    def _download_file(self, url: str, local_path: str) -> bool:
        """下载文件"""
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                logging.info(f"文件下载成功: {local_path}")
                return True
            else:
                logging.error(f"文件下载失败: {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"文件下载异常: {e}")
            return False



    def _parse_result_files(self, result_files: List[str], output_dir: str) -> Dict[str, Any]:
        """解析结果文件"""
        try:
            text_chunks = []
            images = []
            tables = []
            metadata = {}
            
            # 解析markdown文件
            for file_path in result_files:
                if file_path.lower().endswith('.md'):
                    md_content = self._parse_markdown_file(file_path)
                    text_chunks.extend(md_content)
                elif file_path.lower().endswith('content_list.json'):
                    content_data = self._parse_content_list_json(file_path)
                    text_chunks.extend(content_data.get('text_chunks', []))
                    tables.extend(content_data.get('tables', []))
            
            # 查找图片文件
            images = self._find_image_files(output_dir)
            
            # 设置元数据
            metadata = {
                'document_type': 'pdf',
                'page_count': len(set(chunk.get('page', 1) for chunk in text_chunks)),
                'language': 'zh-CN',
                'processing_time': 0,
                'confidence_score': 0.9
            }
            
            logging.info(f"结果文件解析完成: {len(text_chunks)} 个文本块, {len(tables)} 个表格, {len(images)} 个图像")
            
            return {
                'text_chunks': text_chunks,
                'images': images,
                'tables': tables,
                'metadata': metadata
            }
            
        except Exception as e:
            logging.error(f"解析结果文件异常: {e}")
            raise

    def _parse_markdown_file(self, md_path: str) -> List[Dict[str, Any]]:
        """解析markdown文件"""
        try:
            text_chunks = []
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单分割markdown内容
            lines = content.split('\n')
            current_chunk = ""
            chunk_index = 0
            
            for line in lines:
                line = line.strip()
                if line:
                    if line.startswith('#'):  # 标题
                        if current_chunk:
                            text_chunks.append({
                                'type': 'text',
                                'content': current_chunk,
                                'chunk_index': chunk_index,
                                'page': 1,
                                'confidence': 0.9
                            })
                            chunk_index += 1
                            current_chunk = ""
                        
                        text_chunks.append({
                            'type': 'title',
                            'content': line,
                            'chunk_index': chunk_index,
                            'page': 1,
                            'confidence': 0.95
                        })
                        chunk_index += 1
                    else:
                        current_chunk += line + "\n"
            
            # 添加最后一个块
            if current_chunk.strip():
                text_chunks.append({
                    'type': 'text',
                    'content': current_chunk.strip(),
                    'chunk_index': chunk_index,
                    'page': 1,
                    'confidence': 0.85
                })
            
            return text_chunks
            
        except Exception as e:
            logging.error(f"解析markdown文件异常: {e}")
            return []

    def _parse_content_list_json(self, json_path: str) -> Dict[str, Any]:
        """解析content_list.json文件"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 根据实际的JSON结构进行解析
            # 这里需要根据MinerU的实际输出格式调整
            return {
                'text_chunks': data.get('text_chunks', []),
                'tables': data.get('tables', [])
            }
            
        except Exception as e:
            logging.error(f"解析content_list.json异常: {e}")
            return {'text_chunks': [], 'tables': []}

    def _find_image_files(self, output_dir: str) -> List[Dict[str, Any]]:
        """查找图片文件"""
        try:
            images = []
            
            # 现在output_dir应该是PDF子目录，直接查找images子目录
            images_dir = os.path.join(output_dir, 'images')
            
            if os.path.exists(images_dir):
                for filename in os.listdir(images_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        image_path = os.path.join(images_dir, filename)
                        # 从文件名提取PDF名称和页码信息
                        pdf_name = filename.split('_')[0] if '_' in filename else 'unknown'
                        images.append({
                            'type': 'image',
                            'image_index': len(images),
                            'page': 1,
                            'confidence': 0.9,
                            'image_path': image_path,
                            'image_size': os.path.getsize(image_path),
                            'source_pdf': pdf_name
                        })
            
            return images
            
        except Exception as e:
            logging.error(f"查找图片文件异常: {e}")
            return []

    def _process_output_files(self, result_files: List[str], final_output_dir: str, pdf_name: str) -> List[str]:
        """
        处理输出文件：重命名、解压、整理
        
        :param result_files: 原始结果文件列表
        :param final_output_dir: 最终输出目录
        :param pdf_name: PDF文件名（不含扩展名）
        :return: 处理后的文件列表
        """
        try:
            processed_files = []
            
            for file_path in result_files:
                if file_path.lower().endswith('.zip'):
                    # 解压zip文件并重命名
                    extracted_files = self._extract_and_rename_zip(file_path, final_output_dir, pdf_name)
                    processed_files.extend(extracted_files)
                    
                    # 删除zip文件
                    try:
                        os.remove(file_path)
                        logging.info(f"临时zip文件已删除: {file_path}")
                    except Exception as e:
                        logging.warning(f"删除临时zip文件失败: {e}")
                else:
                    # 直接复制并重命名其他文件
                    new_path = self._rename_file(file_path, final_output_dir, pdf_name)
                    if new_path:
                        processed_files.append(new_path)
            
            logging.info(f"输出文件处理完成: {len(processed_files)} 个文件")
            return processed_files
            
        except Exception as e:
            logging.error(f"处理输出文件异常: {e}")
            return []

    def _extract_and_rename_zip(self, zip_path: str, output_dir: str, pdf_name: str) -> List[str]:
        """
        解压zip文件并重命名
        
        :param zip_path: zip文件路径
        :param output_dir: 输出目录
        :param pdf_name: PDF文件名（不含扩展名）
        :return: 解压后的文件列表
        """
        try:
            import zipfile
            extracted_files = []
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                logging.info(f"开始解压zip文件: {zip_path}")
                # logging.info(f"zip文件内容: {zip_ref.namelist()}")
                
                for member in zip_ref.namelist():
                    # 跳过隐藏文件和系统文件
                    if member.startswith('__MACOSX') or member.startswith('.') or '/.' in member:
                        logging.info(f"跳过系统文件: {member}")
                        continue
                    
                    # 跳过PDF文件，只处理内容文件
                    if member.lower().endswith('.pdf'):
                        logging.info(f"跳过PDF文件: {member}")
                        continue
                    
                    # 确定目标文件名
                    if member.lower().endswith('.md'):
                        target_name = f"{pdf_name}.md"
                    elif member.lower().endswith('content_list.json'):
                        # 这是主要的JSON文件，重命名为_1.json
                        target_name = f"{pdf_name}_1.json"
                    elif member.lower().endswith('_1.json'):
                        # MinerU已经生成了_1.json文件，保持原名
                        target_name = member
                    elif member.lower().endswith('.json'):
                        # 其他JSON文件保持原名，避免覆盖
                        target_name = member
                    else:
                        target_name = member
                    
                    # 处理图片文件
                    if member.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        # 检查zip中是否已经有images目录结构
                        if 'images/' in member:
                            # 如果zip中已经有images目录，直接使用
                            target_path = os.path.join(output_dir, member)
                        else:
                            # 如果zip中没有images目录，创建images目录
                            images_dir = os.path.join(output_dir, 'images')
                            os.makedirs(images_dir, exist_ok=True)
                            target_path = os.path.join(images_dir, target_name)
                    else:
                        # 将md和json文件放到根目录，但要重命名
                        target_path = os.path.join(output_dir, target_name)
                    
                    # 解压文件
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                        target.write(source.read())
                    
                    extracted_files.append(target_path)
                    # 只记录关键文件，避免详细清单
                    if member.lower().endswith(('.md', '.json')):
                        logging.info(f"关键文件解压: {member} -> {target_path}")
            
            return extracted_files
            
        except Exception as e:
            logging.error(f"解压并重命名zip文件异常: {e}")
            return []

    def _rename_file(self, file_path: str, output_dir: str, pdf_name: str) -> str:
        """
        重命名文件
        
        :param file_path: 原文件路径
        :param output_dir: 输出目录
        :param pdf_name: PDF文件名（不含扩展名）
        :return: 新文件路径
        """
        try:
            filename = os.path.basename(file_path)
            if filename.lower().endswith('.md'):
                new_name = f"{pdf_name}.md"
            elif filename.lower().endswith('content_list.json') or filename.lower().endswith('.json'):
                new_name = f"{pdf_name}_1.json"
            else:
                new_name = filename
            
            # 直接将文件放到根目录
            new_path = os.path.join(output_dir, new_name)
            
            # 复制文件
            import shutil
            shutil.copy2(file_path, new_path)
            
            # 只记录关键文件，避免详细清单
            if filename.lower().endswith(('.md', '.json')):
                logging.info(f"文件重命名: {filename} -> {new_path}")
            return new_path
            
        except Exception as e:
            logging.error(f"重命名文件异常: {e}")
            return ""




