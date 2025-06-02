import os
import glob
import json
from typing import ClassVar, Any, Dict, Optional

from dotenv import load_dotenv
from langchain_core.tools import BaseTool
from aip import AipOcr

load_dotenv()

BAIDU_OCR_APP_ID = os.getenv("BAIDU_OCR_APP_ID")
BAIDU_OCR_API_KEY = os.getenv("BAIDU_OCR_API_KEY")
BAIDU_OCR_SECRET_KEY = os.getenv("BAIDU_OCR_SECRET_KEY")

class BaiduAccurateOcrTool(BaseTool):
    """
    一个用于调用百度智能云通用文字识别（高精度版）接口的 LangChain 工具。
    """
    name: ClassVar[str] = "baidu_accurate_ocr"
    description: ClassVar[str] = "使用百度智能云OCR的通用文字识别（高精度版）接口，识别图片中的文字信息。"

    app_id: str = ""
    api_key: str = ""
    secret_key: str = ""
    client: Optional[AipOcr] = None

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        self.app_id = BAIDU_OCR_APP_ID
        self.api_key = BAIDU_OCR_API_KEY
        self.secret_key = BAIDU_OCR_SECRET_KEY

        print("--- 百度OCR配置检查 ---")
        print(f"BAIDU_OCR_APP_ID (前4位): {self.app_id[:4]}..." if self.app_id else "未设置")
        print(f"BAIDU_OCR_API_KEY (前4位): {self.api_key[:4]}..." if self.api_key else "未设置")
        print(f"BAIDU_OCR_SECRET_KEY (前4位): {self.secret_key[:4]}..." if self.secret_key else "未设置")
        print("-----------------------")
        
        if not all([self.app_id, self.api_key, self.secret_key]):
            raise ValueError(
                "请确保已设置 BAIDU_OCR_APP_ID, BAIDU_OCR_API_KEY, BAIDU_OCR_SECRET_KEY 环境变量。"
            )
        
        self.client = AipOcr(self.app_id, self.api_key, self.secret_key)
        print("AipOcr 客户端初始化成功。")

    def _run(self, image_path: str) -> str:
        print(f"开始识别图片: {image_path}")
        if not os.path.exists(image_path):
            return json.dumps({"error": True, "msg": f"错误：图片文件 '{image_path}' 不存在。"})

        with open(image_path, 'rb') as f:
            image_data = f.read()

        options = {
            "detect_direction": "true",     # 检测图像朝向
            "probability": "true",          # 是否返回识别结果中每一行的置信度
            "detect_language": "true"       # 是否检测语言
        }
        result: Dict[str, Any] = self.client.basicAccurate(image_data, options)

        if 'error_code' in result:
            return json.dumps(
                {"error": True, "code": result['error_code'], "msg": result.get('error_msg', str(result))}
            )
        
        return json.dumps(result, ensure_ascii=False)

    async def _arun(self, image_path: str) -> str:
        """
        异步执行通用文字识别（高精度版）（当前为同步方法的简单封装）。
        """
        return self._run(image_path)

def process_image_for_ocr(image_path: str, ocr_tool: BaiduAccurateOcrTool, output_json_dir: str):
    """
    处理一张图片：进行 OCR 识别，并将原始 JSON 结果保存到本地文件。
    """
    print(f"\n--- 处理图片: {image_path} ---")
    
    try:
        ocr_result_json_str = ocr_tool.run(image_path)
        
        try:
            ocr_data = json.loads(ocr_result_json_str)
            if ocr_data.get("error"):
                print(f"OCR 识别失败: {ocr_data.get('msg', '未知错误')}")
                return
        except json.JSONDecodeError:
            print(f"OCR 返回结果不是有效的 JSON: {ocr_result_json_str}")
            return

        base_name = os.path.basename(image_path)
        file_name_without_ext = os.path.splitext(base_name)[0]
        json_output_path = os.path.join(output_json_dir, f"{file_name_without_ext}_ocr_result.json")

        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(ocr_data, f, ensure_ascii=False, indent=4)
        print(f"OCR原始结果已保存到文件: {json_output_path}")

        # 显示识别结果的基本信息
        if 'words_result' in ocr_data and isinstance(ocr_data['words_result'], list):
            print(f"\nOCR 识别到 {len(ocr_data['words_result'])} 行文字")
            print("识别内容预览：")
            for i, item in enumerate(ocr_data['words_result'][:10]):  # 显示前10行
                if isinstance(item, dict) and 'words' in item:
                    confidence = ""
                    if 'probability' in item:
                        confidence = f" (置信度: {item['probability']['average']:.2f})"
                    print(f"  第{i+1}行: {item['words']}{confidence}")
            if len(ocr_data['words_result']) > 10:
                print(f"  ... 还有 {len(ocr_data['words_result']) - 10} 行")
        else:
            print("未找到 'words_result' 字段或其结构不符合预期。")
            # 显示实际的数据结构
            print(f"实际返回的数据键: {list(ocr_data.keys()) if isinstance(ocr_data, dict) else 'Not a dict'}")
            
    except Exception as e:
        print(f"处理图片时发生错误: {e}")

def get_unique_image_files(image_dir: str) -> list:
    """
    获取目录中的唯一图片文件，避免重复计数
    """
    # 使用集合来存储唯一的文件路径
    unique_files = set()
    
    # 支持的图片扩展名（小写）
    extensions = ['png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff']
    
    for ext in extensions:
        # 同时搜索大写和小写扩展名
        for pattern in [f"*.{ext}", f"*.{ext.upper()}"]:
            files = glob.glob(os.path.join(image_dir, pattern))
            for file in files:
                # 使用规范化路径避免重复
                unique_files.add(os.path.normpath(file))
    
    return sorted(list(unique_files))

if __name__ == "__main__":
    # 检查所有必要的环境变量
    if not all([BAIDU_OCR_APP_ID, BAIDU_OCR_API_KEY, BAIDU_OCR_SECRET_KEY]):
        print("错误：请先设置所有必要的环境变量（BAIDU_OCR_APP_ID, BAIDU_OCR_API_KEY, BAIDU_OCR_SECRET_KEY）！")
        exit()

    # 使用您现有的图片目录
    image_dir = r"D:\Project\mix\output_dir\images\prescription"
    print(f"使用图片目录: {image_dir}")
    
    # 检查目录是否存在
    if not os.path.exists(image_dir):
        print(f"错误：图片目录 '{image_dir}' 不存在！")
        print("请检查路径是否正确。")
        exit()

    # 创建JSON输出目录（在当前工作目录下）
    output_json_dir = "ocr_json_results"
    os.makedirs(output_json_dir, exist_ok=True)
    print(f"创建JSON输出目录: {output_json_dir}")

    # 初始化百度 OCR 工具
    try:
        baidu_ocr_tool = BaiduAccurateOcrTool()
    except Exception as e:
        print(f"初始化百度OCR工具失败: {e}")
        exit()

    # 获取所有唯一的图片文件
    print("正在扫描图片文件...")
    all_image_paths = get_unique_image_files(image_dir)

    if not all_image_paths:
        print(f"在目录 '{image_dir}' 中未找到任何图片文件。")
        print("支持的格式: PNG, JPG, JPEG, BMP, GIF, TIFF")
        print("请检查图片文件是否存在于该目录中。")
    else:
        print(f"找到 {len(all_image_paths)} 个唯一的图片文件")
        print("=" * 50)
        
        # 处理每个图片
        success_count = 0
        for i, image_path in enumerate(all_image_paths, 1):
            print(f"\n[{i}/{len(all_image_paths)}] 正在处理: {os.path.basename(image_path)}")
            
            try:
                process_image_for_ocr(image_path, baidu_ocr_tool, output_json_dir)
                success_count += 1
            except Exception as e:
                print(f"处理图片失败: {e}")
                continue

    print("\n" + "=" * 50)
    print("--- 所有图片处理完毕 ---")
    if all_image_paths:
        print(f"总共处理: {len(all_image_paths)} 个图片文件")
        print(f"成功处理: {success_count} 个")
        print(f"OCR识别结果已保存在: {os.path.abspath(output_json_dir)}")
        
        # 显示生成的JSON文件
        json_files = glob.glob(os.path.join(output_json_dir, "*_ocr_result.json"))
        print(f"生成了 {len(json_files)} 个JSON结果文件")