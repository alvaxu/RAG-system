# RAG项目分支管理策略

## 概述

本文档定义了RAG-250727-param项目的分支管理策略和工作流程。

## 分支结构

### 主要分支

#### 1. `main` 分支
- **用途**：生产环境代码，用于发布
- **特点**：
  - 只包含经过测试的稳定代码
  - 每次提交都应该是一个发布版本
  - 不允许直接提交代码
  - 只能通过合并其他分支来更新

#### 2. `develop` 分支
- **用途**：开发环境代码，集成所有功能
- **特点**：
  - 包含最新的开发功能
  - 用于功能集成和测试
  - 可以包含不稳定的代码
  - 定期合并到main分支进行发布

### 辅助分支

#### 3. `feature/*` 分支
- **用途**：开发新功能
- **命名规范**：`feature/功能名称`
- **特点**：
  - 从develop分支创建
  - 开发完成后合并回develop分支
  - 生命周期较短

#### 4. `hotfix/*` 分支
- **用途**：紧急修复生产环境问题
- **命名规范**：`hotfix/问题描述`
- **特点**：
  - 从main分支创建
  - 修复完成后合并到main和develop分支
  - 优先级最高

#### 5. `release/*` 分支
- **用途**：准备发布版本
- **命名规范**：`release/版本号`
- **特点**：
  - 从develop分支创建
  - 用于版本发布前的最终测试和修复
  - 完成后合并到main和develop分支

## 工作流程

### 1. 功能开发流程

```bash
# 1. 切换到develop分支
git checkout develop
git pull origin develop

# 2. 创建功能分支
git checkout -b feature/新功能名称

# 3. 开发功能
# ... 编写代码 ...

# 4. 提交代码
git add .
git commit -m "feat: 添加新功能"

# 5. 推送到远程
git push -u origin feature/新功能名称

# 6. 创建Pull Request（在GitHub上）
# 7. 代码审查通过后合并到develop分支
# 8. 删除功能分支
git checkout develop
git branch -d feature/新功能名称
git push origin --delete feature/新功能名称
```

### 2. 版本发布流程

```bash
# 1. 从develop分支创建release分支
git checkout develop
git pull origin develop
git checkout -b release/v1.1.0

# 2. 版本发布准备
# - 更新版本号
# - 更新CHANGELOG.md
# - 最终测试

# 3. 提交发布准备
git add .
git commit -m "chore: 准备发布版本 v1.1.0"

# 4. 合并到main分支
git checkout main
git merge release/v1.1.0
git tag -a v1.1.0 -m "版本 v1.1.0 发布"

# 5. 合并到develop分支
git checkout develop
git merge release/v1.1.0

# 6. 推送到远程
git push origin main develop
git push --tags

# 7. 删除release分支
git branch -d release/v1.1.0
git push origin --delete release/v1.1.0
```

### 3. 紧急修复流程

```bash
# 1. 从main分支创建hotfix分支
git checkout main
git pull origin main
git checkout -b hotfix/紧急修复描述

# 2. 修复问题
# ... 修复代码 ...

# 3. 提交修复
git add .
git commit -m "fix: 修复紧急问题"

# 4. 合并到main分支
git checkout main
git merge hotfix/紧急修复描述
git tag -a v1.0.1 -m "紧急修复版本 v1.0.1"

# 5. 合并到develop分支
git checkout develop
git merge hotfix/紧急修复描述

# 6. 推送到远程
git push origin main develop
git push --tags

# 7. 删除hotfix分支
git branch -d hotfix/紧急修复描述
git push origin --delete hotfix/紧急修复描述
```

## 分支保护规则

### 1. main分支保护
- 禁止直接推送
- 必须通过Pull Request合并
- 需要至少一个代码审查
- 必须通过CI/CD测试

### 2. develop分支保护
- 禁止直接推送
- 必须通过Pull Request合并
- 需要至少一个代码审查

### 3. 功能分支
- 允许直接推送
- 建议定期同步develop分支

## 提交信息规范

### 格式
```
类型(范围): 描述

详细描述（可选）

脚注（可选）
```

### 类型
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

### 示例
```
feat(api): 添加用户认证接口

- 实现JWT token认证
- 添加用户登录接口
- 添加用户注册接口

Closes #123
```

## 版本管理

### 版本号规范
遵循语义化版本控制（Semantic Versioning）：
- **主版本号**：不兼容的API修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 版本发布流程
1. 使用版本管理脚本创建新版本
2. 更新CHANGELOG.md
3. 创建Git标签
4. 推送到远程仓库

## 代码审查

### 审查要点
1. **代码质量**：代码是否清晰、可读
2. **功能完整性**：功能是否按需求实现
3. **测试覆盖**：是否有足够的测试
4. **文档更新**：相关文档是否更新
5. **性能影响**：是否影响系统性能

### 审查流程
1. 开发者创建Pull Request
2. 指定审查者
3. 审查者进行代码审查
4. 如有问题，开发者修改代码
5. 审查通过后合并代码

## 注意事项

### 1. 分支管理
- 及时删除已合并的分支
- 定期同步远程分支
- 避免在main分支直接开发

### 2. 提交管理
- 提交信息要清晰明确
- 避免大文件提交
- 定期清理提交历史

### 3. 版本管理
- 重要版本必须打标签
- 版本号要遵循规范
- 及时更新文档

## 工具支持

### 1. 版本管理脚本
```bash
# 查看当前版本
python V100_git_version_manager.py version

# 创建新版本
python V100_git_version_manager.py release --type minor
```

### 2. Git别名（可选）
```bash
# 添加到 ~/.gitconfig
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    lg = log --oneline --graph --decorate
```

## 联系支持

如有问题，请参考：
1. Git官方文档
2. 项目README.md
3. 版本管理使用指南
4. 提交Issue到项目仓库

---

**更新时间**：2024-12-19  
**维护状态**：活跃维护中
