# sync_to_gist.py
from github import Github, GithubException
import os
import json
import logging
from pathlib import Path
from typing import Dict, List

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def load_blog_list(blog_root: str = "blog") -> List[Dict]:
    """安全加载博客列表文件"""
    list_path = Path(blog_root) / "list.json"
    try:
        with open(list_path, 'r', encoding='utf-8') as f:
            if Path(f.name).stat().st_size == 0:
                raise ValueError("list.json 文件为空")
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"博客列表文件未找到: {list_path.absolute()}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析错误: {e}")
        raise

def read_post_content(blog_root: str, post_path: str) -> str:
    """安全读取文章内容"""
    full_path = Path(blog_root) / post_path
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content:
                raise ValueError(f"文件内容为空: {post_path}")
            return content
    except UnicodeDecodeError:
        logger.error(f"文件编码错误: {post_path}")
        raise
    except FileNotFoundError:
        logger.error(f"文章文件未找到: {full_path.absolute()}")
        raise

def format_gist_content(title: str, date: str, content: str) -> str:
    """生成带元数据的Gist内容"""
    return f"""# {title}

> 文章发布于 {date}

---

{content}
"""

def sync_posts_to_gist():
    try:
        # 获取环境变量
        token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
        if not token:
            raise EnvironmentError("未找到 GH_TOKEN 或 GITHUB_TOKEN 环境变量")

        # 初始化GitHub客户端
        gh = Github(token, timeout=30)  # 设置API超时
        user = gh.get_user()

        # 加载博客列表
        blog_root = os.environ.get('BLOG_ROOT', 'blog')
        posts = load_blog_list(blog_root)
        logger.info(f"成功加载 {len(posts)} 篇文章")

        # 获取现有Gist（分页处理）
        existing_gists = {}
        for gist in user.get_gists():
            if gist.description:
                existing_gists[gist.description] = gist

        # 处理每篇文章
        success_count = 0
        for idx, post in enumerate(posts, 1):
            try:
                # 校验必要字段
                required_fields = ['title', 'file', 'time']
                if any(field not in post for field in required_fields):
                    raise ValueError(f"缺失必要字段: {post}")

                title = post['title']
                date = post['time']
                description = f"📝 {title} | {date}"

                # 读取内容
                content = read_post_content(blog_root, post['file'])
                full_content = format_gist_content(title, date, content)

                # 操作Gist
                if description in existing_gists:
                    gist = existing_gists[description]
                    # 检查是否有实际修改
                    current_content = next(iter(gist.files.values())).content
                    if current_content == full_content:
                        logger.info(f"#{idx} [SKIP] 无变化: {title}")
                        continue
                    
                    gist.edit(
                        description=description,
                        files={Path(post['file']).name: {'content': full_content}}
                    )
                    logger.info(f"#{idx} [UPDATE] 成功更新: {title}")
                else:
                    user.create_gist(
                        public=True,
                        description=description,
                        files={Path(post['file']).name: {'content': full_content}}
                    )
                    logger.info(f"#{idx} [CREATE] 成功创建: {title}")
                
                success_count += 1

            except Exception as e:
                logger.error(f"#{idx} 处理文章失败: {str(e)}", exc_info=False)
                continue

        logger.info(f"同步完成: 成功 {success_count}/{len(posts)} 篇")

    except Exception as e:
        logger.critical(f"致命错误: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    sync_posts_to_gist()
