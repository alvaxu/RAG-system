"""
失败处理管理器

负责管理图片处理失败的情况，生成详细的失败报告，支持后续补做机制。
"""

import json
import os
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class FailureHandler:
    """
    失败处理管理器

    功能：
    - 管理图片处理失败的情况
    - 生成详细的失败报告
    - 支持后续补做机制
    - 与V502_image_enhancer_new.py配合
    """

    def __init__(self):
        """
        初始化失败处理器
        """
        self.config = {}
        self.failure_report_path = ""
        self.failed_images = []
        self.failure_report_format = "detailed"
        self.max_retries = 3
        self.retry_delay = 5

    def initialize(self, failure_config: Dict[str, Any]) -> None:
        """
        初始化失败处理器

        :param failure_config: 失败处理配置
        """
        self.config = failure_config
        self.failure_report_path = failure_config.get('failure_report_path', './logs/failure_report.json')
        self.failure_report_format = failure_config.get('failure_report_format', 'detailed')
        self.max_retries = failure_config.get('max_retries', 3)
        self.retry_delay = failure_config.get('retry_delay_seconds', 5)

        # 确保日志目录存在
        logs_dir = os.path.dirname(self.failure_report_path)
        os.makedirs(logs_dir, exist_ok=True)

        # 加载现有的失败报告
        self._load_existing_failures()

        logging.info(f"失败处理器已初始化，报告路径: {self.failure_report_path}")

    def record_failure(self, image_info: Dict[str, Any], error_type: str,
                      error_message: str, retry_count: int = 0) -> None:
        """
        记录图片处理失败

        :param image_info: 图片信息
        :param error_type: 错误类型
        :param error_message: 错误信息
        :param retry_count: 重试次数
        """
        failure_record = {
            'image_path': image_info.get('image_path', ''),
            'image_id': image_info.get('image_id', ''),
            'document_name': image_info.get('document_name', ''),
            'page_number': image_info.get('page_number', 1),
            'failure_type': error_type,
            'error_message': error_message,
            'retry_count': retry_count,
            'timestamp': int(time.time()),
            'can_retry_later': retry_count < self.max_retries,
            'status': 'failed',
            'error_category': self._categorize_error(error_type),
            'processing_stage': image_info.get('processing_stage', 'unknown')
        }

        # 检查是否已存在相同图片的失败记录
        existing_index = self._find_existing_failure(image_info.get('image_id', ''))
        if existing_index >= 0:
            # 更新现有记录
            self.failed_images[existing_index] = failure_record
        else:
            # 添加新记录
            self.failed_images.append(failure_record)

        # 实时保存失败报告
        self._save_failure_report()

        logging.warning(f"图片处理失败: {image_info.get('image_id', 'unknown')} - {error_message}")

    def _find_existing_failure(self, image_id: str) -> int:
        """
        查找是否存在相同图片的失败记录

        :param image_id: 图片ID
        :return: 记录索引，-1表示不存在
        """
        for i, failure in enumerate(self.failed_images):
            if failure.get('image_id') == image_id:
                return i
        return -1

    def _categorize_error(self, error_type: str) -> str:
        """
        分类错误类型

        :param error_type: 错误类型
        :return: 错误分类
        """
        error_categories = {
            'network': ['timeout', 'connection', 'http', 'api'],
            'image': ['corrupt', 'format', 'size', 'quality'],
            'enhancement': ['enhance', 'model', 'generation'],
            'vectorization': ['embedding', 'dimension', 'vector'],
            'file': ['not_found', 'permission', 'disk'],
            'config': ['config', 'parameter', 'validation']
        }

        for category, keywords in error_categories.items():
            if any(keyword in error_type.lower() for keyword in keywords):
                return category

        return 'unknown'

    def get_failed_images(self, failure_type: Optional[str] = None,
                         error_category: Optional[str] = None,
                         status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取失败的图片列表

        :param failure_type: 错误类型过滤
        :param error_category: 错误分类过滤
        :param status: 状态过滤
        :return: 失败图片列表
        """
        filtered_images = self.failed_images.copy()

        if failure_type:
            filtered_images = [img for img in filtered_images if img['failure_type'] == failure_type]

        if error_category:
            filtered_images = [img for img in filtered_images if img['error_category'] == error_category]

        if status:
            filtered_images = [img for img in filtered_images if img['status'] == status]

        return filtered_images

    def mark_as_retried(self, image_id: str, success: bool = True) -> bool:
        """
        标记图片为重试状态

        :param image_id: 图片ID
        :param success: 是否重试成功
        :return: 是否找到并更新了记录
        """
        for img in self.failed_images:
            if img['image_id'] == image_id:
                if success:
                    img['status'] = 'retry_success'
                    img['retry_timestamp'] = int(time.time())
                    img['can_retry_later'] = False
                else:
                    img['status'] = 'retry_failed'
                    img['retry_count'] += 1
                    img['can_retry_later'] = img['retry_count'] < self.max_retries
                    img['last_retry_time'] = int(time.time())

                self._save_failure_report()
                return True

        return False

    def get_retry_candidates(self) -> List[Dict[str, Any]]:
        """
        获取可以重试的图片列表

        :return: 可重试的图片列表
        """
        return [
            img for img in self.failed_images
            if img.get('can_retry_later', False) and img['status'] in ['failed', 'retry_failed']
        ]

    def generate_failure_report(self) -> Dict[str, Any]:
        """
        生成失败报告

        :return: 失败报告字典
        """
        total_failures = len(self.failed_images)
        retry_candidates = len(self.get_retry_candidates())

        # 按错误类型统计
        error_type_stats = {}
        error_category_stats = {}
        status_stats = {}

        for failure in self.failed_images:
            # 错误类型统计
            error_type = failure['failure_type']
            error_type_stats[error_type] = error_type_stats.get(error_type, 0) + 1

            # 错误分类统计
            error_category = failure['error_category']
            error_category_stats[error_category] = error_category_stats.get(error_category, 0) + 1

            # 状态统计
            status = failure['status']
            status_stats[status] = status_stats.get(status, 0) + 1

        report = {
            'summary': {
                'total_failures': total_failures,
                'retry_candidates': retry_candidates,
                'generation_time': datetime.now().isoformat(),
                'report_format': self.failure_report_format
            },
            'statistics': {
                'by_error_type': error_type_stats,
                'by_error_category': error_category_stats,
                'by_status': status_stats
            },
            'failures': self.failed_images if self.failure_report_format == 'detailed' else [],
            'recommendations': self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """
        生成修复建议

        :return: 建议列表
        """
        recommendations = []

        error_category_stats = {}
        for failure in self.failed_images:
            category = failure['error_category']
            error_category_stats[category] = error_category_stats.get(category, 0) + 1

        # 基于错误分类生成建议
        if error_category_stats.get('network', 0) > 0:
            recommendations.append("网络相关错误较多，建议检查网络连接和API服务状态")

        if error_category_stats.get('image', 0) > 0:
            recommendations.append("图片质量或格式问题较多，建议检查图片文件完整性")

        if error_category_stats.get('enhancement', 0) > 0:
            recommendations.append("图片增强模型错误较多，建议检查模型配置和API密钥")

        if error_category_stats.get('vectorization', 0) > 0:
            recommendations.append("向量化过程错误较多，建议检查向量模型配置")

        retry_candidates = len(self.get_retry_candidates())
        if retry_candidates > 0:
            recommendations.append(f"有 {retry_candidates} 个图片可以重试处理")

        return recommendations

    def _load_existing_failures(self) -> None:
        """
        加载现有的失败报告
        """
        if os.path.exists(self.failure_report_path):
            try:
                with open(self.failure_report_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'failures' in data:
                        self.failed_images = data['failures']
                        logging.info(f"加载了 {len(self.failed_images)} 个现有失败记录")
            except Exception as e:
                logging.warning(f"加载现有失败报告失败: {e}")

    def _save_failure_report(self) -> None:
        """
        保存失败报告
        """
        try:
            report = self.generate_failure_report()
            with open(self.failure_report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logging.debug(f"失败报告已保存到: {self.failure_report_path}")
        except Exception as e:
            logging.error(f"保存失败报告失败: {e}")

    def clear_failures(self, older_than_days: int = 30) -> int:
        """
        清理旧的失败记录

        :param older_than_days: 清理多少天前的记录
        :return: 清理的记录数量
        """
        current_time = time.time()
        cutoff_time = current_time - (older_than_days * 24 * 60 * 60)

        original_count = len(self.failed_images)
        self.failed_images = [
            failure for failure in self.failed_images
            if failure.get('timestamp', 0) > cutoff_time
        ]

        cleaned_count = original_count - len(self.failed_images)

        if cleaned_count > 0:
            self._save_failure_report()
            logging.info(f"清理了 {cleaned_count} 个旧的失败记录")

        return cleaned_count

    def get_failure_summary(self) -> Dict[str, Any]:
        """
        获取失败摘要

        :return: 失败摘要字典
        """
        total_failures = len(self.failed_images)
        retry_candidates = len(self.get_retry_candidates())

        return {
            'total_failures': total_failures,
            'retry_candidates': retry_candidates,
            'failure_rate': total_failures / max(total_failures + retry_candidates, 1),
            'most_common_error': self._get_most_common_error()
        }

    def _get_most_common_error(self) -> Optional[str]:
        """
        获取最常见的错误类型

        :return: 最常见的错误类型
        """
        if not self.failed_images:
            return None

        error_counts = {}
        for failure in self.failed_images:
            error_type = failure['failure_type']
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        return max(error_counts, key=error_counts.get) if error_counts else None


if __name__ == "__main__":
    # 测试失败处理器
    handler = FailureHandler()

    # 初始化配置
    failure_config = {
        'skip_failed_images': True,
        'max_retries': 3,
        'retry_delay_seconds': 5,
        'generate_failure_report': True,
        'failure_report_path': './logs/failure_report.json',
        'failure_report_format': 'detailed'
    }

    handler.initialize(failure_config)

    # 记录测试失败
    test_image = {
        'image_path': '/path/to/image.jpg',
        'image_id': 'test_001',
        'document_name': 'test.pdf',
        'page_number': 1,
        'processing_stage': 'enhancement'
    }

    handler.record_failure(test_image, 'network_timeout', '连接超时')

    # 生成报告
    report = handler.generate_failure_report()
    print(f"失败报告生成完成，共 {report['summary']['total_failures']} 个失败记录")
