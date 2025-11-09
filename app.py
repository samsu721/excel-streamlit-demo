# app.py
import streamlit as st
import os
import shutil
import time
from process_excel import process_files
from pathlib import Path

# ---- 配置 ----
st.set_page_config(page_title="Excel 自动化处理平台", page_icon="📊", layout="centered")
MAX_FILE_COUNT = 10
MAX_FILE_SIZE_MB = 20  # 每个文件上限（示例）

# 可通过环境变量设定访问密码（在 Render 上设置）
ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD", "").strip()

# ---- 界面 ----
st.title("📊 Excel 自动化处理平台（示例版）")
st.write("上传一个或多个 Excel 文件，系统会在云端处理并返回结果。")
st.warning("⚠️ 请不要上传含有敏感数据（如身份证、薪资等）的文件 —— 本示例仅用于自动化演示。")

if ACCESS_PASSWORD:
    pwd = st.text_input("访问密码", type="password")
    if pwd != ACCESS_PASSWORD:
        st.stop()

uploaded_files = st.file_uploader(
    f"上传 Excel 文件（最多 {MAX_FILE_COUNT} 个，每个不超过 {MAX_FILE_SIZE_MB} MB）",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True
)

def file_size_ok(f):
    try:
        # UploadedFile has attribute size in bytes for Streamlit >=1.12
        size = f.size
    except Exception:
        size = len(f.getbuffer())
    return (size / (1024*1024)) <= MAX_FILE_SIZE_MB

if uploaded_files:
    # 检查文件大小
    too_big = [f.name for f in uploaded_files if not file_size_ok(f)]
    if too_big:
        st.error("以下文件过大，超过限制： " + ", ".join(too_big))
    else:
        if st.button("开始处理 🚀"):
            with st.spinner("正在处理，请稍候..."):
                try:
                    output_path, tempdir = process_files(uploaded_files, max_files=MAX_FILE_COUNT)
                except Exception as e:
                    st.error(f"处理出错：{e}")
                    st.write("请检查上传的文件格式与列名是否符合预期。")
                else:
                    # 提供下载按钮
                    st.success("处理完成 ✅")
                    out_name = Path(output_path).name
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="⬇️ 下载结果文件",
                            data=f,
                            file_name=out_name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    # 清理临时目录（强烈建议立即删除）
                    try:
                        shutil.rmtree(tempdir)
                        # 确认删除
                        st.info("临时文件已清理。")
                    except Exception as e:
                        st.warning(f"临时文件未能自动清理，请手动删除：{tempdir}. 错误：{e}")

st.markdown("---")
st.markdown("**注意**：本示例会在单次处理后删除临时文件，但如果部署用于生产，请结合身份验证、日志与审计策略。")
