#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步01-post文件夹（含子文件夹）中的文件到Quartz/content
处理图片引用并转换为标准markdown格式，保留子目录结构
"""

import os
import shutil
import re
from pathlib import Path
from typing import List, Tuple

class PostSync:
    def __init__(self, 
                 source_dir: str = "~/Projects/Quartz/ObsidianBlog/01-Post", 
                 target_dir: str = "~/Projects/Quartz/content",
                 attachment_dir: str = "~/Projects/Quartz/ObsidianBlog/attachment"):
        self.source_dir = Path(os.path.expanduser(source_dir)).resolve()  # 绝对路径，避免歧义
        self.target_dir = Path(os.path.expanduser(target_dir)).resolve()
        self.attachment_dir = Path(os.path.expanduser(attachment_dir)).resolve()
        
        # 自动创建目标目录和image子目录
        self.target_dir.mkdir(parents=True, exist_ok=True)
        (self.target_dir / "image").mkdir(parents=True, exist_ok=True)
        
        print(f"=== 同步配置 ===")
        print(f"源目录（含子文件夹）: {self.source_dir}")
        print(f"目标目录: {self.target_dir}")
        print(f"图片资源目录: {self.attachment_dir}\n")
        
    def sync_files(self):
        """同步所有文件（含子目录）"""
        print("开始同步文件...")
        
        # 1. 清空目标目录（保留image文件夹）
        self._clear_target_directory()
        
        # 2. 递归复制所有文件（保留子目录结构）
        self._copy_all_files_recursively()
        
        # 3. 递归处理所有Markdown文件的图片引用
        self._process_image_references_recursively()
        
        print("\n✅ 同步完成！")
    
    def _clear_target_directory(self):
        """清空目标目录，仅保留image文件夹"""
        print("🔄 清空目标目录（保留image文件夹）...")
        image_dir = self.target_dir / "image"
        
        # 删除除image外的所有文件/文件夹
        for item in self.target_dir.iterdir():
            if item == image_dir:
                continue  # 跳过image文件夹
            if item.is_file():
                item.unlink()  # 删除文件
                print(f"删除文件: {item.name}")
            elif item.is_dir():
                shutil.rmtree(item)  # 删除文件夹（含子目录）
                print(f"删除文件夹: {item.name}")
        
        # 确保image文件夹存在（防止误删）
        image_dir.mkdir(exist_ok=True)
    
    def _copy_all_files_recursively(self):
        """递归复制源目录所有文件，保留子目录结构"""
        print("\n📄 递归复制文件（保留子目录结构）...")
        
        # 1. 复制所有Markdown文件（.md）
        # rglob("**/*.md"): 递归匹配所有子目录的.md文件
        for md_file in self.source_dir.rglob("*.md"):
            if md_file.name == ".DS_Store":
                continue  # 跳过macOS隐藏文件
            
            # 计算源文件相对于source_dir的「相对路径」（关键：保留子目录结构）
            # 例：source_dir/sub1/sub2/test.md → 相对路径：sub1/sub2/test.md
            relative_path = md_file.relative_to(self.source_dir)
            # 目标路径 = 目标目录 + 相对路径
            target_md_path = self.target_dir / relative_path
            
            # 创建目标文件的父目录（如果子目录不存在）
            target_md_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件（保留元数据，如修改时间）
            shutil.copy2(md_file, target_md_path)
            print(f"复制MD文件: {relative_path}")
        
        # 2. 复制非MD文件（如banner.svg、封面图等，排除.DS_Store）
        for non_md_file in self.source_dir.rglob("*"):
            if non_md_file.is_dir():
                continue  # 跳过目录（目录会自动创建，无需单独复制）
            if non_md_file.suffix in ['.md', '.DS_Store']:
                continue  # 跳过MD文件和隐藏文件
            
            # 同样计算相对路径，保留子目录结构
            relative_path = non_md_file.relative_to(self.source_dir)
            target_non_md_path = self.target_dir / relative_path
            
            # 创建父目录
            target_non_md_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(non_md_file, target_non_md_path)
            print(f"复制其他文件: {relative_path}")
    
    def _process_image_references_recursively(self):
        """递归处理目标目录所有Markdown文件的图片引用"""
        print("\n🖼️  递归处理所有Markdown文件的图片引用...")
        
        # 递归匹配目标目录所有子目录的.md文件
        for md_file in self.target_dir.rglob("*.md"):
            if md_file.name == ".DS_Store":
                continue
            self._process_single_file(md_file)
    
    def _process_single_file(self, md_file: Path):
        """处理单个Markdown文件的图片引用（逻辑不变，适配子目录文件）"""
        # 计算文件相对于目标目录的路径，日志更清晰
        relative_md_path = md_file.relative_to(self.target_dir)
        print(f"处理文件: {relative_md_path}")
        
        try:
            content = md_file.read_text(encoding='utf-8')
            modified_content = content
            
            # 匹配Obsidian图片格式：![[图片名]] 或 ![[-图片名|参数]]
            image_pattern = r'!\[\[([^|\]]+)(?:\|[^]]*)?\]\]'
            matches = re.findall(image_pattern, content)
            
            for image_name in matches:
                # 查找图片文件（在attachment_dir中）
                image_file = self._find_image_file(image_name)
                if not image_file:
                    continue  # 未找到图片，跳过
                
                # 复制图片到统一的image文件夹
                target_image_path = self._copy_image_to_target(image_file)
                
                # 替换图片引用：![[图片名]] → ![图片名](image/图片名.后缀)
                # 1. 处理无参数引用（如![[abc.png]]）
                old_ref = f'![[{image_name}]]'
                new_ref = f'![{image_name}](image/{target_image_path.name})'
                modified_content = modified_content.replace(old_ref, new_ref)
                
                # 2. 处理带参数引用（如![[abc.png|300x200]]）
                param_pattern = rf'!\[\[{re.escape(image_name)}\|[^]]*\]\]'
                for param_match in re.findall(param_pattern, content):
                    modified_content = modified_content.replace(param_match, new_ref)
            
            # 写回修改后的内容
            md_file.write_text(modified_content, encoding='utf-8')
        
        except Exception as e:
            print(f"❌ 处理文件失败 {relative_md_path}: {str(e)}")
    
    def _find_image_file(self, image_name: str) -> Path:
        """查找图片文件（支持attachment_dir子目录，逻辑不变）"""
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']
        
        # 1. 先在attachment根目录查找
        for ext in image_extensions:
            possible_names = [
                image_name,               # 完整文件名（如abc.png）
                image_name + ext,         # 无后缀名+后缀（如abc → abc.png）
                image_name.replace('.', '') + ext  # 特殊情况（如abc.png → abcpng.png，避免重复后缀）
            ]
            for name in possible_names:
                image_path = self.attachment_dir / name
                if image_path.exists():
                    return image_path
        
        # 2. 再在attachment的子目录中查找（如attachment/202408/abc.png）
        for ext in image_extensions:
            possible_names = [image_name, image_name + ext, image_name.replace('.', '') + ext]
            for name in possible_names:
                # 递归匹配attachment所有子目录的图片文件
                for image_path in self.attachment_dir.rglob(name):
                    if image_path.exists():
                        return image_path
        
        # 未找到图片
        print(f"⚠️  未找到图片文件: {image_name}")
        return None
    
    def _copy_image_to_target(self, image_file: Path) -> Path:
        """复制图片到目标目录的image文件夹，避免文件名重复（逻辑不变）"""
        target_image_dir = self.target_dir / "image"
        target_image_path = target_image_dir / image_file.name
        
        # 处理文件名重复：如果已存在，添加数字后缀（如abc.png → abc_1.png）
        counter = 1
        original_stem = target_image_path.stem  # 文件名（无后缀）
        original_ext = target_image_path.suffix  # 后缀（如.png）
        while target_image_path.exists():
            target_image_path = target_image_dir / f"{original_stem}_{counter}{original_ext}"
            counter += 1
        
        # 复制图片
        shutil.copy2(image_file, target_image_path)
        print(f"复制图片: {image_file.name} → image/{target_image_path.name}")
        
        return target_image_path

def main():
    """主函数：初始化并执行同步"""
    try:
        sync = PostSync()
        sync.sync_files()
    except Exception as e:
        print(f"\n❌ 同步失败！全局错误: {str(e)}")

if __name__ == "__main__":
    main()
