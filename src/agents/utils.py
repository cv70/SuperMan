from typing import Dict, List, Any, Optional
from datetime import datetime, date
import uuid
import json


def format_timestamp(dt: datetime) -> str:
    """将datetime格式化为ISO格式字符串。

    Args:
        dt: 要格式化的datetime对象

    Returns:
        ISO格式的datetime字符串 (YYYY-MM-DDTHH:MM:SS)
    """
    return dt.isoformat()


def generate_id(prefix: str = "id") -> str:
    """生成唯一标识符。

    Args:
        prefix: 要添加到ID前缀的字符串

    Returns:
        格式为 prefix_{uuid4} 的唯一ID
    """
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def safe_get(data: dict, key: str, default: Any = None) -> Any:
    """从字典中安全地获取值。

    Args:
        data: 要从中获取值的字典
        key: 要查找的键
        default: 如果键不存在或值为None时的默认值

    Returns:
        与键关联的值或默认值
    """
    if not isinstance(data, dict):
        return default

    value = data.get(key, default)
    return value if value is not None else default


def validate_dict_fields(data: dict, required_fields: list) -> bool:
    """验证字典中是否包含所有必需字段。

    Args:
        data: 要验证的字典
        required_fields: 必须存在的字段名列表

    Returns:
        如果所有必需字段都存在则返回True，否则返回False
    """
    if not isinstance(data, dict):
        return False

    if not isinstance(required_fields, list):
        return False

    return all(field in data and data[field] is not None for field in required_fields)


def parse_datetime(dt_str: str) -> datetime:
    """解析ISO格式的datetime字符串。

    Args:
        dt_str: ISO格式的datetime字符串 (YYYY-MM-DDTHH:MM:SS)

    Returns:
        解析后的datetime对象

    Raises:
        ValueError: 如果字符串无法解析
    """
    if not isinstance(dt_str, str):
        raise ValueError("输入必须是字符串")

    dt_str = dt_str.strip()

    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        pass

    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"无法解析datetime字符串: {dt_str}")


def convert_to_serializable(obj: Any) -> Any:
    """将对象转换为JSON可序列化格式。

    Args:
        obj: 要转换的对象（可以是datetime、dataclass等）

    Returns:
        JSON可序列化的表示
    """
    if isinstance(obj, datetime):
        return format_timestamp(obj)
    elif isinstance(obj, date):
        return obj.isoformat()
    elif hasattr(obj, "__dict__"):
        return convert_to_serializable(obj.__dict__)
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj

    return str(obj)


def merge_dicts(*dicts: dict) -> dict:
    """合并多个字典，后面的字典优先级更高。

    Args:
        *dicts: 要合并的字典

    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result


def chunk_list(items: list, chunk_size: int) -> list:
    """将列表按指定大小分块。

    Args:
        items: 要分块的列表
        chunk_size: 每块的最大大小

    Returns:
        分块后的列表
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size必须为正数")

    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def calculate_duration(start: datetime, end: datetime) -> float:
    """计算两个datetime之间的持续时间（秒）。

    Args:
        start: 开始datetime
        end: 结束datetime

    Returns:
        持续时间（秒）
    """
    delta = end - start
    return delta.total_seconds()


def round_float(value: float, precision: int = 2) -> float:
    """将浮点数四舍五入到指定精度。

    Args:
        value: 要四舍五入的浮点数值
        precision: 小数位数

    Returns:
        四舍五入后的浮点数值
    """
    return round(value, precision)
