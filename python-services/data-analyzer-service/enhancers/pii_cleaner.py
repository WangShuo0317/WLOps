"""
隐私数据安全清洗器
采用合成替换技术处理PII，保护隐私同时保留语义完整性
"""
from typing import Dict, List, Any, Tuple
from loguru import logger
import re

class PIICleaner:
    """PII清洗器"""
    
    def __init__(self):
        # PII模式定义
        self.patterns = {
            "phone": [
                r'1[3-9]\d{9}',  # 中国手机号
                r'\d{3}-\d{4}-\d{4}',  # 美国电话
                r'\(\d{3}\)\s*\d{3}-\d{4}'
            ],
            "email": [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            "id_card": [
                r'\b\d{17}[\dXx]\b',  # 中国身份证
                r'\b\d{15}\b'
            ],
            "credit_card": [
                r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
            ],
            "ip_address": [
                r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            ],
            "address": [
                r'[\u4e00-\u9fa5]+省[\u4e00-\u9fa5]+市[\u4e00-\u9fa5]+区',
                r'[\u4e00-\u9fa5]+市[\u4e00-\u9fa5]+区[\u4e00-\u9fa5]+路\d+号'
            ]
        }
        
        # 合成替换库
        self.synthetic_replacements = {
            "phone": ["138****8888", "139****6666", "186****1234"],
            "email": ["user@example.com", "contact@domain.com", "info@company.com"],
            "id_card": ["110101199001011234", "320102198505052345"],
            "credit_card": ["6222 **** **** 1234", "5555 **** **** 4444"],
            "ip_address": ["192.168.1.1", "10.0.0.1", "172.16.0.1"],
            "name": ["张三", "李四", "王五", "赵六", "小明", "小红"],
            "address": ["北京市朝阳区某某路123号", "上海市浦东新区某某街456号"]
        }
        
        self.replacement_counter = {}
    
    def clean_text(self, text: str, preserve_semantics: bool = True) -> Tuple[str, List[Dict], Dict[str, str]]:
        """
        清洗文本中的PII
        
        Args:
            text: 原始文本
            preserve_semantics: 是否保留语义
            
        Returns:
            (清洗后的文本, 检测到的实体列表, 替换映射)
        """
        cleaned_text = text
        detected_entities = []
        replacements = {}
        
        # 1. 检测并替换结构化PII（电话、邮箱等）
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, cleaned_text)
                for match in matches:
                    original = match.group()
                    
                    # 生成合成替换
                    if preserve_semantics:
                        replacement = self._generate_semantic_replacement(original, entity_type)
                    else:
                        replacement = f"[{entity_type.upper()}]"
                    
                    cleaned_text = cleaned_text.replace(original, replacement)
                    
                    detected_entities.append({
                        "type": entity_type,
                        "original": original,
                        "start": match.start(),
                        "end": match.end()
                    })
                    
                    replacements[original] = replacement
        
        # 2. 检测并替换人名（简单规则）
        name_replacements = self._detect_and_replace_names(cleaned_text, preserve_semantics)
        cleaned_text = name_replacements["text"]
        detected_entities.extend(name_replacements["entities"])
        replacements.update(name_replacements["replacements"])
        
        logger.info(f"检测到 {len(detected_entities)} 个PII实体")
        
        return cleaned_text, detected_entities, replacements
    
    def clean_dataset(self, dataset: List[Dict]) -> Tuple[List[Dict], int]:
        """
        清洗整个数据集
        
        Args:
            dataset: 数据集
            
        Returns:
            (清洗后的数据集, 清洗的样本数)
        """
        logger.info(f"开始清洗数据集，大小: {len(dataset)}")
        
        cleaned_dataset = []
        cleaned_count = 0
        
        for item in dataset:
            cleaned_item, has_pii = self._clean_item(item)
            cleaned_dataset.append(cleaned_item)
            if has_pii:
                cleaned_count += 1
        
        logger.info(f"完成数据集清洗，清洗了 {cleaned_count} 个样本")
        return cleaned_dataset, cleaned_count
    
    def _clean_item(self, item: Dict) -> Tuple[Dict, bool]:
        """清洗单个样本"""
        cleaned_item = {}
        has_pii = False
        
        for key, value in item.items():
            if isinstance(value, str):
                cleaned_text, entities, _ = self.clean_text(value)
                cleaned_item[key] = cleaned_text
                if entities:
                    has_pii = True
            else:
                cleaned_item[key] = value
        
        if has_pii:
            cleaned_item["_pii_cleaned"] = True
        
        return cleaned_item, has_pii
    
    def _generate_semantic_replacement(self, original: str, entity_type: str) -> str:
        """
        生成语义保留的替换
        
        Args:
            original: 原始值
            entity_type: 实体类型
            
        Returns:
            替换值
        """
        # 使用计数器确保一致性替换
        if original not in self.replacement_counter:
            replacements = self.synthetic_replacements.get(entity_type, [])
            if replacements:
                idx = len(self.replacement_counter) % len(replacements)
                self.replacement_counter[original] = replacements[idx]
            else:
                self.replacement_counter[original] = f"[{entity_type.upper()}]"
        
        return self.replacement_counter[original]
    
    def _detect_and_replace_names(self, text: str, preserve_semantics: bool) -> Dict:
        """检测并替换人名"""
        entities = []
        replacements = {}
        cleaned_text = text
        
        # 简单的中文人名检测（2-4个汉字，常见姓氏开头）
        common_surnames = [
            "王", "李", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴",
            "徐", "孙", "马", "朱", "胡", "郭", "何", "林", "高", "罗"
        ]
        
        # 构建人名模式
        name_pattern = f"({'|'.join(common_surnames)})[\\u4e00-\\u9fa5]{{1,3}}"
        
        matches = re.finditer(name_pattern, text)
        for match in matches:
            original = match.group()
            
            # 避免误匹配（如"王国"、"李子"等）
            if len(original) < 2:
                continue
            
            # 检查上下文，确保是人名
            start = match.start()
            end = match.end()
            context_before = text[max(0, start-5):start]
            context_after = text[end:min(len(text), end+5)]
            
            # 简单的上下文检查
            name_indicators = ["先生", "女士", "老师", "同学", "医生", "说", "认为", "表示"]
            is_likely_name = any(indicator in context_before + context_after for indicator in name_indicators)
            
            if is_likely_name:
                if preserve_semantics:
                    replacement = self._generate_semantic_replacement(original, "name")
                else:
                    replacement = "[NAME]"
                
                cleaned_text = cleaned_text.replace(original, replacement, 1)
                
                entities.append({
                    "type": "name",
                    "original": original,
                    "start": start,
                    "end": end
                })
                
                replacements[original] = replacement
        
        return {
            "text": cleaned_text,
            "entities": entities,
            "replacements": replacements
        }
    
    def validate_cleaning(self, original: str, cleaned: str) -> Dict[str, Any]:
        """
        验证清洗质量
        
        Args:
            original: 原始文本
            cleaned: 清洗后文本
            
        Returns:
            验证结果
        """
        # 检查是否还有残留的PII
        remaining_pii = []
        
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, cleaned)
                if matches:
                    remaining_pii.extend([{
                        "type": entity_type,
                        "value": match
                    } for match in matches])
        
        # 计算语义保留度（简单的长度比较）
        length_ratio = len(cleaned) / len(original) if len(original) > 0 else 1.0
        semantic_preservation = 1.0 if 0.8 <= length_ratio <= 1.2 else 0.5
        
        return {
            "is_clean": len(remaining_pii) == 0,
            "remaining_pii": remaining_pii,
            "semantic_preservation_score": semantic_preservation,
            "length_change_ratio": length_ratio
        }
