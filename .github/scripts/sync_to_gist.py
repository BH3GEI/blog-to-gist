from github import Github
import os
import json

def main():
    # 获取 GitHub token
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("Error: GITHUB_TOKEN not found in environment variables")
        return

    try:
        # 初始化 GitHub API
        gh = Github(token)
        user = gh.get_user()

        # 读取博客列表
        with open('blog/list.json', 'r', encoding='utf-8') as f:
            posts = json.load(f)

        # 获取所有现有的 gists
        gists = {gist.description: gist for gist in user.get_gists()}

        # 处理每篇文章
        for post in posts:
            try:
                # 准备数据
                title = post['title']
                description = f"📝 {title} | {post['time']}"
                filename = os.path.basename(post['file'])

                # 读取文章内容
                with open(f"blog/{post['file']}", 'r', encoding='utf-8') as f:
                    content = f.read()

                # 添加元信息
                full_content = f"# {title}\n\n> Published on {post['time']}\n\n---\n\n{content}"

                # 创建或更新 gist
                if description in gists:
                    # 更新现有 gist
                    gists[description].edit(
                        description=description,
                        files={filename: {'content': full_content}}
                    )
                    print(f"✅ Updated: {title}")
                else:
                    # 创建新 gist
                    user.create_gist(
                        public=True,
                        description=description,
                        files={filename: {'content': full_content}}
                    )
                    print(f"✨ Created: {title}")

            except Exception as e:
                print(f"❌ Error processing {title}: {str(e)}")

    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")

if __name__ == "__main__":
    main()
