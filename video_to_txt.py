#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MP4 抽离音频并转写为文本

功能：
1. 从 input 文件夹读取 MP4 视频，抽离音频并保存为 output/MP3/{原文件名}.mp3
2. 将生成的 MP3 转写为文本，保存至 output/txt/{原文件名}.txt

依赖：moviepy（抽离音频）、openai-whisper（转写），系统需安装 ffmpeg
"""

import os
import sys
from pathlib import Path


def get_project_root() -> Path:
    """脚本所在目录视为项目根目录"""
    return Path(__file__).resolve().parent


def ensure_dirs(*dirs: Path) -> None:
    """确保目录存在，不存在则创建"""
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def extract_audio_from_mp4(mp4_path: Path, mp3_path: Path) -> bool:
    """
    从 MP4 抽离音频并保存为 MP3

    :param mp4_path: MP4 文件路径
    :param mp3_path: 输出 MP3 路径
    :return: 是否成功
    """
    try:
        from moviepy.editor import VideoFileClip
    except ImportError:
        print("请先安装 moviepy: pip install moviepy", file=sys.stderr)
        return False

    try:
        clip = VideoFileClip(str(mp4_path))
        if clip.audio is None:
            print(f"  跳过（无音轨）: {mp4_path.name}", file=sys.stderr)
            clip.close()
            return False
        clip.audio.write_audiofile(str(mp3_path), verbose=False, logger=None)
        clip.close()
        return True
    except Exception as e:
        print(f"  抽离音频失败 {mp4_path.name}: {e}", file=sys.stderr)
        return False


def transcribe_mp3_to_txt(mp3_path: Path, txt_path: Path, model_name: str = "base") -> bool:
    """
    将 MP3 转写为文本并保存

    :param mp3_path: MP3 文件路径
    :param txt_path: 输出 txt 路径
    :param model_name: whisper 模型名（tiny/base/small/medium/large）
    :return: 是否成功
    """
    try:
        import whisper
    except ImportError:
        print("请先安装 openai-whisper: pip install openai-whisper", file=sys.stderr)
        return False

    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(str(mp3_path), language=None, verbose=False)
        text = result.get("text", "").strip()
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        txt_path.write_text(text, encoding="utf-8")
        return True
    except Exception as e:
        print(f"  转写失败 {mp3_path.name}: {e}", file=sys.stderr)
        return False


def main() -> None:
    """主流程：遍历 input 下 MP4 -> 抽离为 MP3 -> 转写为 txt"""
    root = get_project_root()
    input_dir = root / "input"
    mp3_dir = root / "output" / "MP3"
    txt_dir = root / "output" / "txt"

    if not input_dir.is_dir():
        print(f"input 目录不存在: {input_dir}", file=sys.stderr)
        sys.exit(1)

    ensure_dirs(mp3_dir, txt_dir)
    mp4_files = sorted(input_dir.glob("*.mp4"))
    if not mp4_files:
        print("input 目录下没有 .mp4 文件")
        return

    for mp4_path in mp4_files:
        stem = mp4_path.stem
        mp3_path = mp3_dir / f"{stem}.mp3"
        txt_path = txt_dir / f"{stem}.txt"

        print(f"处理: {mp4_path.name}")
        if extract_audio_from_mp4(mp4_path, mp3_path):
            print(f"  已保存音频: {mp3_path.relative_to(root)}")
            if transcribe_mp3_to_txt(mp3_path, txt_path):
                print(f"  已保存文本: {txt_path.relative_to(root)}")
            else:
                print(f"  转写未完成: {mp4_path.name}")
        else:
            print(f"  抽离音频未完成: {mp4_path.name}")

    print("全部处理结束。")


if __name__ == "__main__":
    main()
