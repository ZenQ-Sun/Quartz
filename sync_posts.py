#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步01-post文件夹中的文件到Quartz/content
处理图片引用并转换为标准markdown格式
"""

import os
import shutil
import re
from pathlib import Path
from typing import List, Tuple

class PostSync:
    def __init__(self, source_dir: str = "~/sync/person/01-post", 
                 target_dir: str = "~/Projects/Quartz/content",
                 attachment_dir: str = "~/sync/person/attachment"):
        self.source_dir = Path(os.path.expanduser(source_dir))
        self.target_dir = Path(os.path.expanduser(target_dir))
        self.attachment_dir = Path(os.path.expanduser(attachment_dir))
        # 自动创建目标目录和image子目录
        self.target_dir.mkdir(parents=True, exist_ok=True)
        (self.target_dir / "image").mkdir(parents=True, exist_ok=True)
        
    def sync_files(self):
        """同步所有文件"""
        print("开始同步文件...")
        
        # 清空目标目录
        self._clear_target_directory()
        
        # 复制所有markdown文件
        self._copy_markdown_files()
        
        # 处理图片引用
        self._process_image_references()
        
        print("同步完成！")
    
    def _clear_target_directory(self):
        """清空目标目录，保留image文件夹"""
        print("清空目标目录...")
        image_dir = self.target_dir / "image"
        
        # 删除除了image文件夹之外的所有文件
        for item in self.target_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        
        # 确保image文件夹存在
        image_dir.mkdir(exist_ok=True)
    
    def _copy_markdown_files(self):
        """复制所有markdown文件"""
        print("复制markdown文件...")
        
        for file_path in self.source_dir.glob("*.md"):
            if file_path.name == ".DS_Store":
                continue
                
            target_path = self.target_dir / file_path.name
            shutil.copy2(file_path, target_path)
            print(f"复制: {file_path.name}")
        
        # 复制其他文件（如banner.svg等）
        for file_path in self.source_dir.glob("*"):
            if file_path.is_file() and file_path.suffix not in ['.md', '.DS_Store']:
                target_path = self.target_dir / file_path.name
                shutil.copy2(file_path, target_path)
                print(f"复制: {file_path.name}")
    
    def _process_image_references(self):
        """处理图片引用"""
        print("处理图片引用...")
        
        for md_file in self.target_dir.glob("*.md"):
            if md_file.name == ".DS_Store":
                continue
                
            self._process_single_file(md_file)
    
    def _process_single_file(self, md_file: Path):
        """处理单个markdown文件的图片引用"""
        print(f"处理文件: {md_file.name}")
        
        content = md_file.read_text(encoding='utf-8')
        modified_content = content
        
        # 查找所有图片引用
        image_pattern = r'!\[\[([^|\]]+)(?:\|[^]]*)?\]\]'
        matches = re.findall(image_pattern, content)
        
        for image_name in matches:
            # 查找对应的图片文件
            image_file = self._find_image_file(image_name)
            
            if image_file:
                # 复制图片到image文件夹
                target_image_path = self._copy_image_to_target(image_file)
                
                # 替换图片引用
                old_ref = f'![[{image_name}]]'
                new_ref = f'![{image_name}](image/{target_image_path.name})'
                modified_content = modified_content.replace(old_ref, new_ref)
                
                # 处理带参数的引用
                param_pattern = rf'!\[\[{re.escape(image_name)}\|[^]]*\]\]'
                param_matches = re.findall(param_pattern, content)
                for param_match in param_matches:
                    new_ref = f'![{image_name}](image/{target_image_path.name})'
                    modified_content = modified_content.replace(param_match, new_ref)
        
        # 写回文件
        md_file.write_text(modified_content, encoding='utf-8')
    
    def _find_image_file(self, image_name: str) -> Path:
        """查找图片文件"""
        # 支持的图片扩展名
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']
        
        # 在attachment目录中查找
        for ext in image_extensions:
            # 尝试不同的文件名组合
            possible_names = [
                image_name,
                image_name + ext,
                image_name.replace('.', '') + ext
            ]
            
            for name in possible_names:
                # 在attachment根目录查找
                image_path = self.attachment_dir / name
                if image_path.exists():
                    return image_path
                
                # 在attachment/01-post/对应文件夹中查找
                for post_dir in self.attachment_dir.glob("01-post/*"):
                    if post_dir.is_dir():
                        image_path = post_dir / name
                        if image_path.exists():
                            return image_path
        
        print(f"警告: 未找到图片文件 {image_name}")
        return None
    
    def _copy_image_to_target(self, image_file: Path) -> Path:
        """复制图片到目标image文件夹"""
        target_image_path = self.target_dir / "image" / image_file.name
        
        # 如果目标文件已存在，添加数字后缀
        counter = 1
        original_name = target_image_path.stem
        original_ext = target_image_path.suffix
        
        while target_image_path.exists():
            target_image_path = self.target_dir / "image" / f"{original_name}_{counter}{original_ext}"
            counter += 1
        
        shutil.copy2(image_file, target_image_path)
        print(f"复制图片: {image_file.name} -> image/{target_image_path.name}")
        
        return target_image_path

def main():
    """主函数"""
    sync = PostSync()
    sync.sync_files()

if __name__ == "__main__":
    main() 