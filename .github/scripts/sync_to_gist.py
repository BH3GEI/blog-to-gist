import os
import json
import requests
from github import Github

def sync_to_gist():
    # 获取 token
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GitHub token not found!")

    # 初始化 Github 客户端
    g = Github(github_token)
    user = g.get_user()
    
    # 读取博客列表
    with open('blog/list.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    # 获取现有的 gists
    existing_gists = {}
    for gist in user.get_gists():
        existing_gists[gist.description] = gist
    
    # 处理每篇文章
    for post in posts:
        try:
            # 读取文章内容
            file_path = os.path.join('blog', post['file'])
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 准备 Gist 内容
            title = post['title']
            time = post['time']
            description = f"📝 {title} | {time}"
            filename = os.path.basename(post['file'])
            
            # 添加元数据到内容
            full_content = f"# {title}\n\n> Published on {time}\n\n---\n\n{content}"
            
            # 创建或更新 Gist
            if description in existing_gists:
                # 更新现有 Gist
                gist = existing_gists[description]
                gist.edit(
                    description=description,
                    files={filename: {'content': full_content}}
                )
                print(f"Updated: {title}")
            else:
                # 创建新 Gist
                user.create_gist(
                    public=True,
                    description=description,
                    files={filename: {'content': full_content}}
                )
                print(f"Created: {title}")
                
        except Exception as e:
            print(f"Error processing {title}: {str(e)}")

if __name__ == "__main__":
    sync_to_gist()
