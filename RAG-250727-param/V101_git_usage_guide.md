# Git版本管理使用指南

## 概述

本文档介绍了RAG-250727-param项目的Git版本管理使用方法。

## 版本管理工具

### 1. 自动版本管理脚本

项目提供了自动化的版本管理脚本：`V100_git_version_manager.py`

#### 基本用法

```bash
# 查看当前版本
python V100_git_version_manager.py version

# 创建新版本发布（补丁版本）
python V100_git_version_manager.py release

# 创建新版本发布（次要版本）
python V100_git_version_manager.py release --type minor

# 创建新版本发布（主要版本）
python V100_git_version_manager.py release --type major

# 创建新版本发布（指定更新内容）
python V100_git_version_manager.py release --changes "修复bug" "新增功能" "性能优化"

# 查看Git状态
python V100_git_version_manager.py status
```

#### 版本类型说明

- **patch（补丁版本）**：修复bug和小问题（1.0.0 → 1.0.1）
- **minor（次要版本）**：新增功能，向后兼容（1.0.0 → 1.1.0）
- **major（主要版本）**：重大更改，可能不兼容（1.0.0 → 2.0.0）

### 2. 手动版本管理

#### 查看版本信息

```bash
# 查看所有标签
git tag -l

# 查看标签详细信息
git show v1.0.0

# 查看版本历史
git log --oneline --decorate
```

#### 创建新版本

```bash
# 1. 更新版本号（手动编辑version.json）
# 2. 提交更改
git add version.json CHANGELOG.md
git commit -m "发布版本 X.X.X"

# 3. 创建标签
git tag -a vX.X.X -m "版本 X.X.X 发布"

# 4. 推送到远程
git push
git push --tags
```

## 版本管理规范

### 1. 提交信息规范

- 使用中文提交信息
- 格式：`类型: 描述`
- 类型包括：
  - `feat`: 新功能
  - `fix`: 修复bug
  - `docs`: 文档更新
  - `style`: 代码格式调整
  - `refactor`: 代码重构
  - `test`: 测试相关
  - `chore`: 构建过程或辅助工具的变动

### 2. 版本号规范

遵循语义化版本控制（Semantic Versioning）：

- **主版本号**：不兼容的API修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 3. 分支管理

- `main`: 主分支，用于发布
- `develop`: 开发分支
- `feature/*`: 功能分支
- `hotfix/*`: 紧急修复分支

## 工作流程

### 1. 日常开发

```bash
# 1. 切换到开发分支
git checkout develop

# 2. 创建功能分支
git checkout -b feature/新功能

# 3. 开发完成后合并到develop
git checkout develop
git merge feature/新功能

# 4. 删除功能分支
git branch -d feature/新功能
```

### 2. 版本发布

```bash
# 1. 使用版本管理脚本
python V100_git_version_manager.py release --type minor --changes "新增功能A" "优化性能B"

# 2. 或者手动发布
# - 更新version.json
# - 更新CHANGELOG.md
# - 提交更改
# - 创建标签
# - 推送到远程
```

### 3. 紧急修复

```bash
# 1. 从main分支创建hotfix分支
git checkout -b hotfix/紧急修复

# 2. 修复问题
# 3. 提交修复
git commit -m "fix: 修复紧急问题"

# 4. 合并到main和develop
git checkout main
git merge hotfix/紧急修复
git checkout develop
git merge hotfix/紧急修复

# 5. 删除hotfix分支
git branch -d hotfix/紧急修复
```

### 4. 分支同步到远程仓库

#### 同步main分支

```bash
# 1. 切换到main分支
git checkout main

# 2. 确保工作目录干净
git status

# 3. 拉取远程最新更改（如果有其他协作者）
git pull origin main

# 4. 推送main分支到远程仓库
git push origin main

# 5. 设置上游跟踪（首次推送时）
git push -u origin main
```

#### 同步develop分支

```bash
# 1. 切换到develop分支
git checkout develop

# 2. 确保工作目录干净
git status

# 3. 拉取远程最新更改（如果有其他协作者）
git pull origin develop

# 4. 推送develop分支到远程仓库
git push origin develop

# 5. 设置上游跟踪（首次推送时）
git push -u origin develop
```

#### 批量同步所有分支

```bash
# 1. 查看所有本地分支
git branch

# 2. 同步所有分支到远程仓库
git push --all origin

# 3. 设置所有分支的上游跟踪
git push --all -u origin
```

#### 验证同步结果

```bash
# 查看远程分支
git branch -r

# 查看所有分支（本地和远程）
git branch -a

# 检查远程仓库配置
git remote -v
```

## 注意事项

1. **版本号管理**：每次发布前确保版本号正确更新
2. **标签管理**：重要版本必须创建标签
3. **文档更新**：版本发布时同步更新README和CHANGELOG
4. **测试验证**：发布前确保代码通过测试
5. **备份重要数据**：发布前备份重要配置文件和数据

## 常见问题

### Q: 如何回退到之前的版本？

```bash
# 查看版本历史
git log --oneline

# 回退到指定版本
git reset --hard <commit-hash>

# 或者回退到指定标签
git reset --hard v1.0.0
```

### Q: 如何删除错误的标签？

```bash
# 删除本地标签
git tag -d v1.0.0

# 删除远程标签
git push origin :refs/tags/v1.0.0
```

### Q: 如何查看版本差异？

```bash
# 查看两个版本之间的差异
git diff v1.0.0 v1.1.0

# 查看特定文件的差异
git diff v1.0.0 v1.1.0 -- path/to/file
```

## 联系支持

如有问题，请参考：

1. Git官方文档
2. 项目README.md
