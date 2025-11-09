# process_excel.py
import pandas as pd
import tempfile
import os
from typing import List
from pathlib import Path

def safe_save_uploaded(uploaded_file, save_dir: str) -> str:
    """
    把 streamlit UploadedFile 保存到临时目录，返回文件路径
    """
    filename = uploaded_file.name
    safe_path = os.path.join(save_dir, filename)
    # uploaded_file.read() 返回 bytes
    with open(safe_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return safe_path

def simple_process_merge(file_paths: List[str], out_dir: str) -> str:
    """
    示例处理逻辑：
    - 如果上传了两张表，尝试按共同列名进行外连接并输出
    - 否则：对单表添加一列“处理时间戳”
    返回输出文件路径
    """
    if len(file_paths) >= 2:
        # 读取所有表
        dfs = [pd.read_excel(p) for p in file_paths]
        # 找出第一个与第二个共有列作为 join key（示例）
        common_cols = set(dfs[0].columns) & set(dfs[1].columns)
        if common_cols:
            key = list(common_cols)[0]
            merged = dfs[0].merge(dfs[1], on=key, how="outer", suffixes=("_A", "_B"))
            # 如果还有更多表，依次 merge
            for df in dfs[2:]:
                common_cols = set(merged.columns) & set(df.columns)
                if common_cols:
                    key = list(common_cols)[0]
                    merged = merged.merge(df, on=key, how="outer")
                else:
                    merged = pd.concat([merged, df], axis=1)
            out_path = os.path.join(out_dir, "merged_result.xlsx")
            merged.to_excel(out_path, index=False)
            return out_path
        else:
            # 无共有列，简单拼接
            concat = pd.concat(dfs, ignore_index=True, sort=False)
            out_path = os.path.join(out_dir, "concat_result.xlsx")
            concat.to_excel(out_path, index=False)
            return out_path
    else:
        # 单表：添加处理列
        df = pd.read_excel(file_paths[0])
        df["处理状态"] = "已处理"
        out_path = os.path.join(out_dir, "processed_result.xlsx")
        df.to_excel(out_path, index=False)
        return out_path

def process_files(uploaded_files, max_files=10):
    """
    主入口：接收 streamlit 上传的文件列表（或单文件），
    在一个独立临时目录中保存上传文件 -> 调用处理 -> 返回生成文件路径
    注意：调用者负责在使用完后删除返回的输出文件（或在此处也可删除）
    """
    # 支持传入单个 UploadedFile 或 list
    if not uploaded_files:
        raise ValueError("没有上传文件")

    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    # 限制文件数量
    if len(uploaded_files) > max_files:
        raise ValueError(f"最多支持上传 {max_files} 个文件")

    # 创建临时目录（会在函数结束时仍存在，调用方负责清理输出）
    tempdir = tempfile.mkdtemp(prefix="excel_proc_")

    saved_paths = []
    try:
        for uf in uploaded_files:
            p = safe_save_uploaded(uf, tempdir)
            saved_paths.append(p)

        # 调用示例处理函数（把你的逻辑放这里）
        output_path = simple_process_merge(saved_paths, tempdir)

        return output_path, tempdir  # 返回输出文件路径及临时目录，调用方负责清理 tempdir
    except Exception as e:
        # 发生异常时尝试清理
        try:
            for p in saved_paths:
                if os.path.exists(p):
                    os.remove(p)
            if os.path.isdir(tempdir):
                os.rmdir(tempdir)
        except Exception:
            pass
        raise e
