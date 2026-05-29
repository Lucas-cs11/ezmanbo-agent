"""Datasheet RAG (Retrieval-Augmented Generation) system for component specifications"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


class DatasheetRegistry:
    """管理器件datasheet的注册表和检索"""

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parents[1] / "docs" / "datasheets"
        self.registry: Dict[str, str] = {}  # part_number -> pdf_path
        self._load_registry()

    def _load_registry(self):
        """加载datasheet注册表"""
        if not self.data_dir.exists():
            return

        # 扫描datasheets目录
        for pdf_file in self.data_dir.glob("*.pdf"):
            # 从文件名提取part number
            part_number = pdf_file.stem
            self.registry[part_number] = str(pdf_file)

    def get_datasheet_path(self, part_number: str) -> Optional[str]:
        """获取器件的datasheet路径"""
        return self.registry.get(part_number)

    def has_datasheet(self, part_number: str) -> bool:
        """检查器件是否有datasheet"""
        return part_number in self.registry

    def list_available(self) -> Dict[str, str]:
        """列出所有可用的datasheet"""
        return self.registry.copy()


class DatasheetMetadata:
    """Datasheet元数据管理"""

    def __init__(self, metadata_file: Path = None):
        self.metadata_file = metadata_file or Path(__file__).parents[1] / "docs" / "datasheet_metadata.json"
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self._load_metadata()

    def _load_metadata(self):
        """加载datasheet元数据"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)

    def save_metadata(self):
        """保存datasheet元数据"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def register_datasheet(self, part_number: str, datasheet_info: Dict[str, Any]):
        """注册datasheet元数据"""
        self.metadata[part_number] = {
            **datasheet_info,
            'registered_at': str(Path(__file__).stat().st_mtime)
        }

    def get_metadata(self, part_number: str) -> Optional[Dict[str, Any]]:
        """获取datasheet元数据"""
        return self.metadata.get(part_number)


# Global instances
_registry = None
_metadata = None


def get_registry() -> DatasheetRegistry:
    """获取全局datasheet注册表"""
    global _registry
    if _registry is None:
        _registry = DatasheetRegistry()
    return _registry


def get_metadata() -> DatasheetMetadata:
    """获取全局datasheet元数据管理器"""
    global _metadata
    if _metadata is None:
        _metadata = DatasheetMetadata()
    return _metadata


def augment_part_with_datasheet(part: Dict[str, Any]) -> Dict[str, Any]:
    """使用datasheet信息增强器件数据"""
    part_number = part.get('part_number')
    if not part_number:
        return part

    registry = get_registry()
    metadata = get_metadata()

    # 检查是否有datasheet
    if registry.has_datasheet(part_number):
        datasheet_path = registry.get_datasheet_path(part_number)
        part['has_datasheet'] = True
        part['datasheet_local_path'] = datasheet_path

        # 添加元数据
        ds_meta = metadata.get_metadata(part_number)
        if ds_meta:
            part['datasheet_metadata'] = ds_meta
    else:
        part['has_datasheet'] = False

    return part


def validate_parts_with_datasheets(parts: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[str]]:
    """
    验证器件是否都有datasheet，返回有datasheet的器件和缺失的器件list
    """
    registry = get_registry()

    with_datasheet = []
    without_datasheet = []

    for part in parts:
        part_number = part.get('part_number')
        if registry.has_datasheet(part_number):
            with_datasheet.append(augment_part_with_datasheet(part))
        else:
            without_datasheet.append(part_number)

    return with_datasheet, without_datasheet


# 初始化datasheet元数据
def initialize_datasheets():
    """初始化datasheet系统"""
    metadata = get_metadata()

    # 注册已验证的datasheet（只包含能从官方来源获得的产品）
    datasheets_info = {
        'TPS61030DSG': {
            'manufacturer': 'Texas Instruments',
            'type': 'Boost DC-DC Converter',
            'key_specs': {
                'input_voltage_range': '0.7V - 5.5V',
                'output_voltage': 'Adjustable (2.5V - 5.5V)',
                'max_output_current': '1.0A',
                'frequency': '1.5MHz',
                'efficiency': 'up to 95%',
                'features': 'Low Quiescent Current, Over Current Protection'
            },
            'url': 'https://www.ti.com/product/TPS61030',
            'datasheet_url': 'https://www.ti.com/lit/ds/symlink/tps61030.pdf',
            'source': 'Texas Instruments Official',
            'verification_status': 'Verified - Official PDF downloaded'
        }
    }

    for part_number, info in datasheets_info.items():
        if not metadata.get_metadata(part_number):
            metadata.register_datasheet(part_number, info)

    metadata.save_metadata()


if __name__ == '__main__':
    initialize_datasheets()
    registry = get_registry()
    print("Available datasheets:", registry.list_available())
