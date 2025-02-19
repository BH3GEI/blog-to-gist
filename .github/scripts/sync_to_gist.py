# .github/scripts/sync_to_gist.py
import github
from github import Github, GithubException
import os
import json
import logging
import requests
from urllib.parse import quote
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Dict

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 常量配置
BLOG_REPO = "BH3GEI/blog"
BRANCH = "main"
LIST_JSON_PATH = "list.json"  # 根据实际路径调整
MAX_RETRIES = 3

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=lambda _: logger.warning("请求失败，准备重试...")
)
def fetch_remote_content(url: str, token: str = None) -> str:
    """安全获取远程内容（自动重试）"""
    headers = {"User-Agent": "BlogSync/1.0"}
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        if len(response.content) == 0:
            raise ValueError("响应内容为空")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e.response.status_code if e.response else '无响应'} - {url}")
        raise

def generate_raw_url(file_path: str) -> str:
    """生成GitHub Raw URL（自动编码路径）"""
    encoded_path = quote(file_path.strip('/'), safe='/')
    return f"https://raw.githubusercontent.com/{BLOG_REPO}/{BRANCH}/{encoded_path}"


def load_blog_list(token: str) -> List[Dict]:
    """加载远程博客列表"""
    list_url = generate_raw_url(LIST_JSON_PATH)
    logger.info(f"正在获取博客列表: {list_url}")
    
    try:
        content = fetch_remote_content(list_url, token)
        data = json.loads(content)
        
        # 校验数据结构
        if not isinstance(data, list):
            raise ValueError("list.json 应该是一个数组")
        required_fields = ['title', 'file', 'time']
        for idx, item in enumerate(data):
            if not all(field in item for field in required_fields):
                raise ValueError(f"第 {idx+1} 项缺少必要字段")
        return data
    except json.JSONDecodeError:
        logger.error("JSON解析失败，请检查list.json格式")
        raise

def format_gist_content(title: str, date: str, content: str) -> str:
    """生成带元数据的Gist内容"""
    return f"""# {title}

> Published on {date}

---

{content}
"""

def sync_to_gist():
    try:
        # 获取环境变量
        gh_token = os.environ.get('GH_TOKEN')
        if not gh_token:
            raise EnvironmentError("缺少 GH_TOKEN 环境变量")

        # 初始化GitHub客户端
        gh = Github(gh_token, timeout=30)
        user = gh.get_user()
        logger.info(f"已认证为: {user.login}")

        # 获取博客列表
        posts = load_blog_list(gh_token)
        logger.info(f"成功加载 {len(posts)} 篇文章")

        # 获取现有Gist
        existing_gists = {gist.description: gist for gist in user.get_gists() if gist.description}

        # 处理每篇文章
        success_count = 0
        for idx, post in enumerate(posts, 1):
            try:
                # 校验数据
                title = post['title']
                date = post['time']
                file_path = post['file']
                description = f"📝 {title} | {date}"
                
                if not all([title, date, file_path]):
                    raise ValueError("文章数据不完整")

                # 获取文章内容
                file_url = generate_raw_url(file_path)
                logger.debug(f"正在获取: {file_url}")
                content = fetch_remote_content(file_url, gh_token)
                
                # 构建Gist内容
                full_content = format_gist_content(title, date, content)
                filename = os.path.basename(file_path)

                # 同步逻辑
                if description in existing_gists:
                    gist = existing_gists[description]
                    current_content = next(iter(gist.files.values())).content
                    
                    if current_content == full_content:
                        logger.info(f"#{idx} [SKIP] 无变化: {title}")
                        continue
                    
                    gist.edit(
                        description=description,
                        files={filename: {'content': full_content}}
                    )
                    logger.info(f"#{idx} [UPDATE] 更新成功: {title}")
                else:
                    user.create_gist(
                        public=True,
                        description=description,
                        files={filename: {'content': full_content}}
                    )
                    logger.info(f"#{idx} [CREATE] 创建成功: {title}")
                
                success_count += 1

            except Exception as e:
                logger.error(f"#{idx} 处理失败: {title} - {str(e)}")
                continue

        logger.info(f"同步完成: 成功 {success_count}/{len(posts)} 篇文章")

    except Exception as e:
        logger.critical(f"致命错误: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    sync_to_gist()
