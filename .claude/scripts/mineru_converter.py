#!/usr/bin/env python3
"""
PDF2MD - 法律文书 PDF/Word/图片转 Markdown 工具
核心转换模块（纯函数，Claude Code Agent 可直接调用）
"""

import os
import sys
import time
import zipfile
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

import requests

# ============ 常量 ============

API_BASE = "https://mineru.net/api/v4"
POLL_INTERVAL = 10  # 秒
POLL_MAX_ATTEMPTS = 120  # 最多轮询次数
TIMEOUT = 300  # 请求超时（秒）

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".pptx", ".ppt", ".png", ".jpg", ".jpeg"}

# ============ Token 管理 ============

def load_token() -> str:
    """从 api.txt 读取 Token。"""
    token_file = Path(__file__).parent / "api.txt"
    if not token_file.exists():
        raise FileNotFoundError(
            f"Token 文件不存在：{token_file}\n"
            "请将 MinerU Token 复制到 api.txt（纯文本，不要多余字符）"
        )
    token = token_file.read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError(f"Token 文件为空：{token_file}")
    return token


def get_headers(token: str) -> dict:
    """构建请求头。"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def verify_token() -> dict:
    """
    验证 Token 有效性。
    通过 GET /extract/task/{fake_id} 探测 Token 是否合法。
    - 401/403 → Token 无效
    - 200/404（服务端实际处理了认证） → Token 有效
    - 网络错误 → 网络不通
    返回 {"valid": True} 或 {"valid": False, "error": "..."}
    """
    token = load_token()
    fake_id = "00000000-0000-0000-0000-000000000000"
    try:
        resp = requests.get(
            f"{API_BASE}/extract/task/{fake_id}",
            headers=get_headers(token),
            timeout=TIMEOUT,
        )
        if resp.status_code == 401:
            return {"valid": False, "error": "Token 无效或已过期，请更新 api.txt"}
        if resp.status_code == 403:
            return {"valid": False, "error": "Token 无权访问，请检查账户权限"}
        if resp.status_code in (200, 404):
            # API 处理了认证（返回 404 说明认证通过，只是任务不存在）
            return {"valid": True}
        return {"valid": False, "error": f"API 返回状态码 {resp.status_code}: {resp.text}"}
    except requests.exceptions.RequestException as e:
        return {"valid": False, "error": f"网络错误: {e}"}


# ============ 内部核心函数 ============

def _upload_and_poll(file_path: str, token: str) -> dict:
    """
    上传文件 + 轮询结果。
    返回 {"batch_id": "...", "download_url": "..."} 或 {"error": "..."}
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return {"error": f"文件不存在: {file_path}"}

    # Step 1: 获取上传 URL
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
    except OSError as e:
        return {"error": f"读取文件失败: {e}"}

    file_size = len(file_content)
    if file_size == 0:
        return {"error": "文件为空"}

    max_size = 200 * 1024 * 1024
    if file_size > max_size:
        return {"error": f"文件超过 200 MB 限制（当前: {file_size / 1024 / 1024:.1f} MB）"}

    data_id = f"convert_{int(time.time())}_{hash(file_path.name) % 0xFFFFFFFF:08x}"

    step1_resp = requests.post(
        f"{API_BASE}/file-urls/batch",
        headers=get_headers(token),
        json={
            "enable_formula": False,
            "language": "ch",
            "enable_table": True,
            "model_version": "pipeline",
            "files": [{
                "name": file_path.name,
                "is_ocr": True,
                "data_id": data_id,
            }],
        },
        timeout=TIMEOUT,
    )

    if step1_resp.status_code == 401 or step1_resp.status_code == 403:
        return {"error": f"Token 认证失败 (HTTP {step1_resp.status_code}): {step1_resp.text}"}
    if step1_resp.status_code != 200:
        return {"error": f"获取上传URL失败 (HTTP {step1_resp.status_code}): {step1_resp.text}"}

    step1_data = step1_resp.json()

    # 从响应中提取 batch_id 和 upload_url
    batch_id = (
        step1_data.get("batch_id")
        or (step1_data.get("data", {}).get("batch_id") if isinstance(step1_data.get("data"), dict) else None)
    )
    file_urls_raw = (
        step1_data.get("file_urls")
        or (step1_data.get("data", {}).get("file_urls") if isinstance(step1_data.get("data"), dict) else None)
        or []
    )
    oss_headers = (
        step1_data.get("headers")
        or (step1_data.get("data", {}).get("headers") if isinstance(step1_data.get("data"), dict) else None)
        or []
    )

    if isinstance(file_urls_raw, str):
        upload_url = file_urls_raw
    elif isinstance(file_urls_raw, list) and len(file_urls_raw) > 0:
        upload_url = file_urls_raw[0]
    else:
        return {"error": f"上传URL响应缺少 file_urls: {step1_data}"}

    if not batch_id:
        return {"error": f"上传URL响应缺少 batch_id: {step1_data}"}

    upload_url = upload_url.strip()

    # Step 2: PUT 上传文件（含 OSS headers），不加 Content-Type 让 curl/OSS 自动处理
    put_headers = {}
    if isinstance(oss_headers, list):
        for h in oss_headers:
            if isinstance(h, dict):
                for k, v in h.items():
                    put_headers[k] = v

    try:
        put_resp = requests.put(
            upload_url,
            data=file_content,
            headers=put_headers,
            timeout=TIMEOUT,
        )
        if put_resp.status_code not in (200, 201):
            return {"error": f"文件上传失败 (HTTP {put_resp.status_code}): {put_resp.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"文件上传失败: {e}"}

    # Step 3: 轮询查询结果
    for attempt in range(1, POLL_MAX_ATTEMPTS + 1):
        time.sleep(POLL_INTERVAL)
        poll_resp = requests.get(
            f"{API_BASE}/extract-results/batch/{batch_id}",
            headers=get_headers(token),
            timeout=TIMEOUT,
        )
        if poll_resp.status_code == 401 or poll_resp.status_code == 403:
            return {"error": f"Token 认证失败 (HTTP {poll_resp.status_code}): {poll_resp.text}"}
        if poll_resp.status_code != 200:
            continue

        poll_data = poll_resp.json()
        result_list = poll_data.get("data", {}).get("extract_result", [])

        for item in result_list:
            state = item.get("state", "")
            if state == "done" and item.get("full_zip_url"):
                download_url = item["full_zip_url"]
                return {"batch_id": batch_id, "download_url": download_url}
            if state == "failed":
                msg = item.get("err_msg", "未知错误")
                return {"error": f"转换失败: {msg}"}

    return {"error": f"轮询超时（{POLL_MAX_ATTEMPTS * POLL_INTERVAL // 60} 分钟），batch_id={batch_id}"}


def _download_result(download_url: str, token: str) -> bytes:
    """下载结果 ZIP。"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(download_url, headers=headers, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise IOError(f"下载失败 (HTTP {resp.status_code}): {resp.text}")
    return resp.content


def _extract_markdown(zip_content: bytes) -> str:
    """
    解压 ZIP 并提取其中的 .md 文件内容。
    优先返回主文件（文件名不含 _images/_tables 后缀），其余追加。
    """
    parts = []
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "result.zip"
        zip_path.write_bytes(zip_content)
        with zipfile.ZipFile(zip_path, "r") as zf:
            md_files = [n for n in zf.namelist() if n.endswith(".md") and "_images" not in n and "_tables" not in n]
            other_md = [n for n in zf.namelist() if n.endswith(".md") and n not in md_files]
            for names, label in [(md_files, ""), (other_md, "_附件")]:
                for name in sorted(names):
                    raw = zf.read(name)
                    try:
                        text = raw.decode("utf-8", errors="replace")
                    except Exception:
                        text = raw.decode("gbk", errors="replace")
                    parts.append(f"\n\n<!-- {label}: {name} -->\n{text}" if label else text)
    return "\n".join(parts) if parts else ""


# ============ 公开接口 ============

def convert_file(file_path: str) -> str:
    """
    转换单个文件，返回 Markdown 内容字符串。
    失败抛出异常。
    """
    token = load_token()
    result = _upload_and_poll(file_path, token)
    if "error" in result:
        raise RuntimeError(f"[{Path(file_path).name}] {result['error']}")

    zip_content = _download_result(result["download_url"], token)
    md_content = _extract_markdown(zip_content)
    return md_content


def convert_and_save(file_path: str) -> dict:
    """
    转换单个文件并保存到 converted/ 目录。
    返回 {"success": bool, "file": str, "output": str, "error": str|None}
    """
    src = Path(file_path)
    if not src.exists():
        return {"success": False, "file": str(src), "output": "", "error": "文件不存在"}

    ext = src.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return {"success": False, "file": str(src), "output": "", "error": f"不支持的格式: {ext}"}

    out_dir = Path(__file__).parent / "converted"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{src.stem}.md"

    if out_file.exists():
        return {"success": True, "file": str(src), "output": str(out_file), "error": None, "skipped": True}

    try:
        md_content = convert_file(str(src))
        out_file.write_text(md_content, encoding="utf-8")
        return {"success": True, "file": str(src), "output": str(out_file), "error": None, "skipped": False}
    except Exception as e:
        return {"success": False, "file": str(src), "output": str(out_file), "error": str(e)}


def convert_folder(folder_path: str) -> list:
    """
    批量转换文件夹下所有支持格式的文件。
    返回结果列表:
    [{"file": "xxx.pdf", "success": true, "output": "converted/xxx.md", "error": null}, ...]
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        raise NotADirectoryError(f"不是有效目录: {folder}")

    results = []
    for ext in SUPPORTED_EXTENSIONS:
        for src in sorted(folder.rglob(f"*{ext}")):
            results.append(convert_and_save(str(src)))

    return results


def get_supported_formats() -> list:
    """返回支持的扩展名列表。"""
    return sorted(SUPPORTED_EXTENSIONS)


# ============ CLI 入口 ============

def print_banner():
    print("=" * 56)
    print("  PDF2MD - 法律文书转换工具")
    print("  将 PDF / Word / 图片 转为 Markdown")
    print("=" * 56)


def print_status(token_ok: bool, pending_files: list, converted_files: list):
    """显示当前状态"""
    print("[ 状态 ]")
    print()

    # Token 状态
    if token_ok:
        print("  [OK]  MinerU Token    已配置且有效")
    else:
        print("  [!!] MinerU Token    未配置或已失效")
        print("       -> 请将 Token 复制到 api.txt 文件中")

    print()

    # 待处理文件
    if pending_files:
        print(f"  [->] 待处理文书      {len(pending_files)} 个文件待转换")
        for f in pending_files[:5]:
            print(f"       - {f}")
        if len(pending_files) > 5:
            print(f"       - ... 还有 {len(pending_files) - 5} 个文件")
    else:
        print("  [--] 待处理文书      无待处理文件")
        print("       -> 将文件放入「待处理文书」文件夹即可")

    print()

    # 已转换文件
    if converted_files:
        print(f"  [=]  已转换文档      {len(converted_files)} 个")
        for f in converted_files[:5]:
            print(f"       - {f}")
        if len(converted_files) > 5:
            print(f"       - ... 还有 {len(converted_files) - 5} 个")
    else:
        print("  [--] 已转换文档      暂无")

    print()


def print_guide(token_ok: bool, pending_files: list):
    """显示引导建议"""
    print("[ 下一步 ]")
    print()

    if not token_ok:
        print("  1) 配置 Token")
        print("       访问 https://mineru.net/apiManage/token 申请 API Token")
        print("       将 Token 粘贴到项目根目录的 api.txt 文件中")
        print()
        print("  2) 验证 Token")
        print("       python mineru_converter.py --verify")
        print()
        print("  3) 放入文件后开始转换")
        print()
    elif not pending_files:
        print("  [*] Token 已就绪，可以开始转换了！")
        print()
        print("  将文件放入「待处理文书」文件夹，然后运行：")
        print("       python mineru_converter.py 待处理文书/")
        print()
        print("  或直接拖入单个文件：")
        print("       python mineru_converter.py 合同.pdf")
    else:
        print(f"  [*] 检测到 {len(pending_files)} 个待处理文件，现在转换吗？")
        print()
        print("  运行以下命令开始转换：")
        print("       python mineru_converter.py 待处理文书/")
        print()
        print("  转换后的 .md 文件将保存在 converted/ 文件夹")
        print("  之后可以把内容发给 Claude Code 进行法律分析")


def print_usage():
    """显示命令帮助"""
    print()
    print("[ 命令 ]")
    print()
    print("  python mineru_converter.py --verify          验证 Token 是否有效")
    print("  python mineru_converter.py 文件.pdf          转换单个文件")
    print("  python mineru_converter.py 文件夹/           批量转换文件夹")
    print()
    print("  支持格式: PDF / Word / 图片（jpg, png 等）")


def check_files(folder_path: Path) -> list:
    """获取文件夹中待处理的文件（去重）"""
    seen = set()
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        for f in sorted(folder_path.glob(f"*{ext}")):
            lower = f.name.lower()
            if lower not in seen:
                seen.add(lower)
                files.append(f.name)
    return files


def check_converted(converted_path: Path) -> list:
    """获取已转换的文件"""
    if not converted_path.exists():
        return []
    return [f.name for f in sorted(converted_path.glob("*.md"))]


def main():
    print_banner()

    # 检查 Token
    token_ok = verify_token().get("valid", False)

    # 检查文件状态
    project_root = Path(__file__).parent
    pending_dir = project_root / "待处理文书"
    converted_dir = project_root / "converted"

    pending_files = []
    converted_files = []

    if pending_dir.exists():
        pending_files = check_files(pending_dir)
    converted_files = check_converted(converted_dir)

    # 显示状态和引导
    print_status(token_ok, pending_files, converted_files)
    print_guide(token_ok, pending_files)
    print_usage()

    # 如果有参数，执行实际转换
    args = sys.argv[1:]
    if not args:
        return

    # --verify 单独处理
    if "--verify" in args:
        result = verify_token()
        print()
        if result["valid"]:
            print("[OK] Token 验证通过，API 可正常访问")
        else:
            print(f"[!!] Token 验证失败: {result['error']}")
            sys.exit(1)
        return

    # 执行转换
    target = args[0]
    path = Path(target)

    if not path.exists():
        print(f"\n[!!] 路径不存在: {target}")
        sys.exit(1)

    print(f"\n{'=' * 56}")
    print(f"  开始转换: {target}")
    print(f"{'=' * 56}\n")

    if path.is_file():
        result = convert_and_save(target)
        if result["success"]:
            skipped = result.get("skipped", False)
            action = "[--] 跳过（已存在）" if skipped else "[OK] 已转换"
            print(f"{action}: {result['file']} -> {result['output']}")
            if not skipped:
                print("\n[*] 提示：转换完成，可以将 .md 内容发给 Claude Code 进行分析")
        else:
            print(f"[!!] 失败 [{path.name}]: {result['error']}")
            sys.exit(1)
    else:
        print(f"正在批量转换: {target}")
        results = convert_folder(target)
        total = len(results)
        success = sum(1 for r in results if r["success"])
        skipped = sum(1 for r in results if r.get("skipped", False))
        failed = total - success
        print()
        for r in results:
            if r["success"]:
                tag = "[--] 跳过" if r.get("skipped") else "[OK] 成功"
                print(f"  {tag}  {Path(r['file']).name}")
            else:
                print(f"  [!!] 失败  {Path(r['file']).name}: {r['error']}")
        print()
        print(f"{'=' * 56}")
        print(f"完成: {success} 成功 / {skipped} 跳过 / {failed} 失败")
        if success > 0:
            print()
            print("[*] 提示：转换完成，可以将 .md 内容发给 Claude Code 进行分析")



if __name__ == "__main__":
    main()
