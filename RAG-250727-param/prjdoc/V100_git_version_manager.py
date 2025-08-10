"""
程序说明：

## 1. Git版本管理脚本
- 用于自动化Git版本管理流程
- 支持版本标签管理
- 提供版本发布功能

## 2. 主要功能
- 自动版本号递增
- 创建版本标签
- 生成版本日志
- 备份重要文件
"""

import os
import subprocess
import json
import datetime
from pathlib import Path

class GitVersionManager:
    """
    Git版本管理器
    """
    
    def __init__(self, project_root="."):
        """
        初始化版本管理器
        
        :param project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.version_file = self.project_root / "version.json"
        self.changelog_file = self.project_root / "CHANGELOG.md"
        
    def get_current_version(self):
        """
        获取当前版本号
        
        :return: 当前版本号字符串
        """
        if self.version_file.exists():
            with open(self.version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
                return version_data.get('version', '1.0.0')
        return '1.0.0'
    
    def increment_version(self, version_type='patch'):
        """
        递增版本号
        
        :param version_type: 版本类型 ('major', 'minor', 'patch')
        :return: 新版本号
        """
        current_version = self.get_current_version()
        major, minor, patch = map(int, current_version.split('.'))
        
        if version_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif version_type == 'minor':
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
            
        new_version = f"{major}.{minor}.{patch}"
        
        # 保存新版本号
        version_data = {
            'version': new_version,
            'last_updated': datetime.datetime.now().isoformat(),
            'version_type': version_type
        }
        
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, indent=2, ensure_ascii=False)
            
        return new_version
    
    def create_version_tag(self, version, message=None):
        """
        创建版本标签
        
        :param version: 版本号
        :param message: 标签消息
        """
        if not message:
            message = f"版本 {version} 发布"
            
        try:
            # 创建标签
            subprocess.run(['git', 'tag', '-a', f'v{version}', '-m', message], 
                         cwd=self.project_root, check=True)
            print(f"✅ 成功创建版本标签 v{version}")
        except subprocess.CalledProcessError as e:
            print(f"❌ 创建版本标签失败: {e}")
    
    def push_tags(self):
        """
        推送标签到远程仓库
        """
        try:
            subprocess.run(['git', 'push', '--tags'], cwd=self.project_root, check=True)
            print("✅ 成功推送标签到远程仓库")
        except subprocess.CalledProcessError as e:
            print(f"❌ 推送标签失败: {e}")
    
    def generate_changelog(self, version, changes=None):
        """
        生成版本更新日志
        
        :param version: 版本号
        :param changes: 更新内容列表
        """
        if not changes:
            changes = ["功能优化和bug修复"]
            
        changelog_entry = f"""
## 版本 {version} - {datetime.datetime.now().strftime('%Y-%m-%d')}

### 更新内容
"""
        for change in changes:
            changelog_entry += f"- {change}\n"
            
        changelog_entry += "\n---\n"
        
        # 读取现有日志
        existing_content = ""
        if self.changelog_file.exists():
            with open(self.changelog_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # 写入新日志
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            f.write(changelog_entry + existing_content)
            
        print(f"✅ 成功生成版本 {version} 的更新日志")
    
    def commit_version_changes(self, version):
        """
        提交版本相关更改
        
        :param version: 版本号
        """
        try:
            # 添加版本文件
            subprocess.run(['git', 'add', 'version.json', 'CHANGELOG.md'], 
                         cwd=self.project_root, check=True)
            
            # 提交更改
            commit_message = f"发布版本 {version}"
            subprocess.run(['git', 'commit', '-m', commit_message], 
                         cwd=self.project_root, check=True)
            
            print(f"✅ 成功提交版本 {version} 的更改")
        except subprocess.CalledProcessError as e:
            print(f"❌ 提交版本更改失败: {e}")
    
    def create_release(self, version_type='patch', changes=None, push=True):
        """
        创建完整版本发布
        
        :param version_type: 版本类型
        :param changes: 更新内容
        :param push: 是否推送到远程
        """
        print(f"🚀 开始创建版本发布...")
        
        # 1. 递增版本号
        new_version = self.increment_version(version_type)
        print(f"📝 新版本号: {new_version}")
        
        # 2. 生成更新日志
        self.generate_changelog(new_version, changes)
        
        # 3. 提交更改
        self.commit_version_changes(new_version)
        
        # 4. 创建标签
        self.create_version_tag(new_version)
        
        # 5. 推送到远程
        if push:
            try:
                subprocess.run(['git', 'push'], cwd=self.project_root, check=True)
                self.push_tags()
                print(f"🎉 版本 {new_version} 发布成功！")
            except subprocess.CalledProcessError as e:
                print(f"❌ 推送到远程失败: {e}")
        
        return new_version
    
    def get_git_status(self):
        """
        获取Git状态信息
        
        :return: Git状态信息
        """
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  cwd=self.project_root, capture_output=True, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "无法获取Git状态"

def main():
    """
    主函数 - 提供命令行接口
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Git版本管理器')
    parser.add_argument('action', choices=['version', 'release', 'status'], 
                       help='执行的操作')
    parser.add_argument('--type', choices=['major', 'minor', 'patch'], 
                       default='patch', help='版本类型')
    parser.add_argument('--changes', nargs='+', help='更新内容列表')
    parser.add_argument('--no-push', action='store_true', help='不推送到远程')
    
    args = parser.parse_args()
    
    manager = GitVersionManager()
    
    if args.action == 'version':
        current_version = manager.get_current_version()
        print(f"当前版本: {current_version}")
        
    elif args.action == 'release':
        changes = args.changes if args.changes else ["功能优化和bug修复"]
        new_version = manager.create_release(
            version_type=args.type,
            changes=changes,
            push=not args.no_push
        )
        print(f"✅ 版本 {new_version} 发布完成")
        
    elif args.action == 'status':
        status = manager.get_git_status()
        if status:
            print("Git状态:")
            print(status)
        else:
            print("工作目录干净")

if __name__ == "__main__":
    main()
