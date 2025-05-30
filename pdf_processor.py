import os
import PyPDF2
from pdf2image import convert_from_path
import spacy
from PIL import Image
import nltk
from nltk.tokenize import sent_tokenize
import re
import shutil
from pathlib import Path
import numpy as np


class PDFProcessor:
    def __init__(self):
        # 加载spaCy模型
        self.nlp = spacy.load("zh_core_web_sm")
        
    def process_directory(self, input_dir, output_base_dir):
        """处理指定目录下的所有PDF文件"""
        input_path = Path(input_dir)
        output_path = Path(output_base_dir)
        
        # 创建输出目录结构
        text_output_dir = output_path / "text_blocks"
        image_output_dir = output_path / "images"
        text_output_dir.mkdir(parents=True, exist_ok=True)
        image_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 遍历所有PDF文件
        for pdf_file in input_path.rglob("*.pdf"):
            # 获取相对路径，用于创建对应的输出目录结构
            rel_path = pdf_file.relative_to(input_path)
            pdf_name = pdf_file.stem
            
            # 创建对应的输出目录
            pdf_text_dir = text_output_dir / rel_path.parent / pdf_name
            pdf_image_dir = image_output_dir / rel_path.parent / pdf_name
            pdf_text_dir.mkdir(parents=True, exist_ok=True)
            pdf_image_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"\n处理文件: {pdf_file}")
            
            # 处理文本
            text_blocks = self.extract_text_blocks(str(pdf_file))
            self._save_text_blocks(text_blocks, pdf_text_dir)
            
            # 处理图片
            self.extract_images(str(pdf_file), pdf_image_dir)
    
    def _save_text_blocks(self, text_blocks, output_dir):
        """保存文本块到文件"""
        for i, block in enumerate(text_blocks, 1):
            # 清理文本块，移除多余空白
            block = re.sub(r'\s+', ' ', block).strip()
            if not block:  # 跳过空块
                continue
                
            # 保存为文本文件
            output_file = output_dir / f"block_{i:03d}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(block)
    
    def extract_text_blocks(self, pdf_path):
        """提取PDF中的文本并按语义分块"""
        text_blocks = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                if not text.strip():  # 跳过空页
                    continue
                
                # 使用spaCy进行文本分析
                doc = self.nlp(text)
                
                # 按段落分块
                current_block = []
                for sent in doc.sents:
                    # 如果当前句子是标题或段落开始，创建新块
                    if self._is_heading(sent.text) or len(current_block) == 0:
                        if current_block:
                            text_blocks.append(' '.join(current_block))
                            current_block = []
                    current_block.append(sent.text)
                
                # 添加最后一个块
                if current_block:
                    text_blocks.append(' '.join(current_block))
        
        return text_blocks
    
    def extract_images(self, pdf_path, output_dir):
        """提取PDF中的图片并保存"""
        try:
            # 将PDF转换为图片
            images = convert_from_path(pdf_path)
            
            # 保存每一页为图片
            for i, image in enumerate(images):
                # 检查图片是否包含有意义的内容
                if self._is_meaningful_image(image):
                    image_path = output_dir / f'image_{i+1:03d}.png'
                    # 优化图片质量
                    image.save(image_path, 'PNG', optimize=True, quality=85)
            
            return len(images)
        except Exception as e:
            print(f"处理图片时出错: {str(e)}")
            return 0
    
    def _is_meaningful_image(self, image):
        """检查图片是否包含有意义的内容"""
        # 转换为灰度图
        gray_image = image.convert('L')
        # 转为numpy数组
        arr = np.array(gray_image)
        # 计算方差
        variance = arr.var()
        # 如果方差太小，说明图片可能是空白的
        return variance > 100
    
    def _is_heading(self, text):
        """判断文本是否为标题"""
        text = text.strip()
        # 检查文本长度和格式特征
        if len(text) < 50:  # 标题通常较短
            # 检查是否包含数字编号
            if re.match(r'^[\d\.]+', text):
                return True
            # 检查是否全大写
            if text.isupper():
                return True
            # 检查是否以常见标题符号结尾
            if re.search(r'[：:。]$', text):
                return True
        return False

def main():
    # 使用示例
    processor = PDFProcessor()
    
    # 设置输入输出目录
    input_dir = r"D:\Project\mix\input_dir"
    output_dir = r"D:\Project\mix\output_dir"
    
    # 处理所有PDF文件
    processor.process_directory(input_dir, output_dir)
    print("\n处理完成！")

if __name__ == "__main__":
    main() 