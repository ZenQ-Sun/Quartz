#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 ObsidianBlog/01-Post 全量同步到 content：
- 同步前清空 content（包含清空 image 子目录内容）
- 递归复制全部文件，保持子目录结构
- 处理 Markdown 图片：
  1) 将 Obsidian 语法 ![[...]] 转为 <img src="..." ...>，并复制图片到 content/image（支持 |WxH 尺寸）
  2) 将标准 Markdown 本地图片路径复制到 content/image，并改写为 <img src="image/文件名">（外链保持不变）
"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional


class ObsidianPostSync:
    def __init__(
        self,
        source_dir: str = "~/Projects/Quartz/ObsidianBlog/01-Post",
        target_dir: str = "~/Projects/Quartz/content",
        attachment_dir: str = "~/Projects/Quartz/ObsidianBlog/attachment",
    ) -> None:
        self.source_dir = Path(os.path.expanduser(source_dir)).resolve()
        self.target_dir = Path(os.path.expanduser(target_dir)).resolve()
        self.attachment_dir = Path(os.path.expanduser(attachment_dir)).resolve()

        self.image_dir = self.target_dir / "image"
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)

        print("=== 同步配置 ===")
        print(f"源目录: {self.source_dir}")
        print(f"目标目录: {self.target_dir}")
        print(f"附件目录: {self.attachment_dir}\n")

    def sync(self) -> None:
        print("开始同步...")
        self._clear_target()
        self._copy_all_recursively()
        self._process_all_markdown_images()
        print("\n✅ 同步完成！")

    def _clear_target(self) -> None:
        """清空 target_dir（包含 image 子目录内容），但保留目录本身。"""
        print("🔄 清空 content 目录（包含 image 内容）...")

        # 删除 target_dir 下所有文件与文件夹
        for item in self.target_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        # 重建 image 目录
        self.image_dir.mkdir(parents=True, exist_ok=True)

    def _copy_all_recursively(self) -> None:
        """递归复制 source_dir 下所有文件到 target_dir，保留子目录结构。"""
        print("\n📄 递归复制文件（保留子目录结构）...")

        # 复制所有文件（包含 .md 与其他资源），保持结构
        for src in self.source_dir.rglob("*"):
            if src.is_dir():
                continue
            if src.name == ".DS_Store":
                continue

            rel = src.relative_to(self.source_dir)
            dst = self.target_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"复制: {rel}")

    def _process_all_markdown_images(self) -> None:
        """处理所有 .md 文件中的图片引用，复制图片到 image 并改写为标准 Markdown。"""
        print("\n🖼️  处理 Markdown 图片引用...")
        for md_path in self.target_dir.rglob("*.md"):
            if md_path.name == ".DS_Store":
                continue
            self._process_single_markdown(md_path)

    def _process_single_markdown(self, md_path: Path) -> None:
        rel = md_path.relative_to(self.target_dir)
        print(f"处理文件: {rel}")

        try:
            content = md_path.read_text(encoding="utf-8")
        except Exception as exc:
            print(f"⚠️  读取失败 {rel}: {exc}")
            return

        original_content = content

        # 1) 处理 Obsidian 语法: ![[name]] 或 ![[name|WxH]]
        #    捕获可选尺寸参数并转为 <img src="..." width="W" height="H">
        def repl_obsidian(match: re.Match) -> str:
            token = match.group(1).strip()
            param = match.group(2)
            image_file = self._locate_image_by_token(token)
            if not image_file:
                print(f"⚠️  未找到图片: {token}")
                return match.group(0)
            copied = self._copy_image_to_image_dir(image_file)

            width_attr = ""
            height_attr = ""
            if param:
                dims = param.strip("|")
                m = re.match(r"(\d+)x(\d+)$", dims)
                if m:
                    w, h = m.group(1), m.group(2)
                    width_attr = f" width=\"{w}\""
                    height_attr = f" height=\"{h}\""
            return f"<img src=\"image/{copied.name}\"{width_attr}{height_attr}>"

        content = re.sub(r"!\[\[([^|\]]+)(\|[^\]]+)?\]\]", repl_obsidian, content)

        # 2) 处理标准 Markdown 图片: ![alt](path) → <img src="...">
        # 忽略 http/https/数据 URI
        md_img_pattern = r"!\[[^\]]*\]\(([^)]+)\)"
        def replace_md_img(match: re.Match) -> str:
            raw_path = match.group(1).strip()
            if raw_path.startswith("http://") or raw_path.startswith("https://") or raw_path.startswith("data:"):
                return match.group(0)  # 外链保持为 Markdown，不改写

            # 已经是 image/ 路径则跳过
            if raw_path.startswith("image/"):
                return match.group(0)

            # 解析为文件路径（相对当前 md 文件）
            candidate = (md_path.parent / raw_path).resolve()
            image_file: Optional[Path] = None
            if candidate.exists() and candidate.is_file():
                image_file = candidate
            else:
                # 尝试在附件目录通过文件名查找
                image_file = self._locate_image_by_token(Path(raw_path).name)

            if not image_file:
                return match.group(0)

            copied = self._copy_image_to_image_dir(image_file)

            # 返回 <img>，不含尺寸（标准 Markdown 无尺寸信息）
            return f"<img src=\"image/{copied.name}\">"

        content = re.sub(md_img_pattern, replace_md_img, content)

        if content != original_content:
            try:
                md_path.write_text(content, encoding="utf-8")
            except Exception as exc:
                print(f"⚠️  写入失败 {rel}: {exc}")

    def _locate_image_by_token(self, token: str) -> Optional[Path]:
        """在附件目录递归查找与 token 匹配的图片文件。
        token 既可能是文件名（含/不含后缀），也可能包含扩展名。
        """
        exts = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"]

        # 若 token 已带扩展名，先直接尝试
        name = Path(token).name
        has_ext = Path(name).suffix != ""
        candidates = [name]
        if not has_ext:
            candidates.extend([name + ext for ext in exts])
            # 处理如 foo.png 被写作 foopng
            base = name.replace(".", "")
            candidates.extend([base + ext for ext in exts])

        for cand in candidates:
            # 先在附件根查找
            p = self.attachment_dir / cand
            if p.exists():
                return p
            # 再递归附件目录
            for found in self.attachment_dir.rglob(cand):
                if found.exists():
                    return found

        return None

    def _copy_image_to_image_dir(self, src: Path) -> Path:
        """复制图片到 content/image，若重名则添加 _1, _2 等后缀。"""
        dst = self.image_dir / src.name
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"复制图片: {src.name} → image/{dst.name}")
            return dst

        stem, ext = dst.stem, dst.suffix
        idx = 1
        while True:
            alt = self.image_dir / f"{stem}_{idx}{ext}"
            if not alt.exists():
                shutil.copy2(src, alt)
                print(f"复制图片: {src.name} → image/{alt.name}")
                return alt
            idx += 1


def main() -> None:
    try:
        sync = ObsidianPostSync()
        sync.sync()
    except Exception as exc:
        print(f"\n❌ 同步失败: {exc}")


if __name__ == "__main__":
    main()



