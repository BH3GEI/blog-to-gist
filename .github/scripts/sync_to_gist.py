import os
import json
import requests
from github import Github
from datetime import datetime

def format_gist_description(title, time):
    date_obj = datetime.strptime(time, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%B %d, %Y')
    return f"📝 {title} | {formatted_date}"

def get_post_content(file_path):
    try:
        full_path = os.path.join('blog', file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return None

def sync_to_gist():
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GitHub token not found!")

    g = Github(github_token)
    user = g.get_user()
    
    with open('blog/list.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    existing_gists = {gist.description: gist for gist in user.get_gists()}
    
    for post in posts:
        title = post['title']
        file_path = post['file']
        time = post['time']
        
        try:
            content = get_post_content(file_path)
            if not content:
                continue
                
            gist_description = format_gist_description(title, time)
            filename = os.path.basename(file_path)
            
            content_with_meta = f"""# {title}

> Published on {time}

---

{content}"""
            
            if gist_description in existing_gists:
                gist = existing_gists[gist_description]
                gist.edit(
                    description=gist_description,
                    files={filename: {'content': content_with_meta}}
                )
                print(f"Updated: {title}")
            else:
                user.create_gist(
                    public=True,
                    description=gist_description,
                    files={filename: {'content': content_with_meta}}
                )
                print(f"Created: {title}")
                
        except Exception as e:
            print(f"Error processing {title}: {str(e)}")

if __name__ == "__main__":
    sync_to_gist()
