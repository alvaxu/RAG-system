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

- `main`: 主分支，用于发布稳定版本，**不允许直接修改**
- `develop`: 开发分支，用于功能集成，**不允许直接开发**
- `feature/*`: 功能分支，用于具体功能开发
- `hotfix/*`: 紧急修复分支，用于生产环境紧急修复

#### 分支使用规范

**重要原则**：

- ✅ **允许**：在feature分支上进行开发
- ✅ **允许**：在hotfix分支上进行紧急修复
- ❌ **禁止**：直接在main分支上开发
- ❌ **禁止**：直接在develop分支上开发
- ✅ **允许**：通过Pull Request/Merge Request合并代码

## 工作流程

### 1. 日常开发

```bash
# 1. 确保main分支是最新的
git checkout main
git pull origin main

# 2. 切换到开发分支并同步main的最新内容
git checkout develop
git merge main

# 3. 推送更新后的develop分支到远程
git push origin develop

# 4. 从develop分支创建功能分支
git checkout -b feature/新功能

# 5. 开发完成后合并到develop
git checkout develop
git merge feature/新功能

# 6. 推送develop分支到远程
git push origin develop

# 7. 删除功能分支
git branch -d feature/新功能

# 8. 功能稳定后，将develop分支合并到main分支
git checkout main
git merge develop

# 9. 推送main分支到远程仓库
git push origin main

# 10. 创建版本标签（可选）
git tag -a v1.1.0 -m "版本 1.1.0 发布"
git push origin v1.1.0
```

#### 功能分支同步说明

**重要提醒**：如果功能分支创建时间较早，可能需要同步最新的main分支内容：

```bash
# 方法1：在功能分支上直接合并main分支
git checkout feature/新功能
git merge main

# 方法2：重新基于最新的develop分支创建功能分支
git checkout develop
git checkout -b feature/新功能_v2

# 方法3：重置功能分支到最新的develop分支
git checkout feature/新功能
git reset --hard develop
```

#### 功能发布到main分支说明

**何时发布到main分支**：

- ✅ 功能开发完成并通过测试
- ✅ 代码审查通过
- ✅ 功能稳定，无已知bug
- ✅ 准备发布新版本

**发布流程**：

```bash
# 1. 确保develop分支是最新的
git checkout develop
git pull origin develop

# 2. 运行测试确保功能正常
python -m pytest tests/
# 或其他测试命令

# 3. 合并到main分支
git checkout main
git merge develop

# 4. 推送到远程仓库
git push origin main

# 5. 创建版本标签
git tag -a v1.1.0 -m "版本 1.1.0 发布"
git push origin v1.1.0

# 6. 更新版本管理文件
python V100_git_version_manager.py release --type minor --changes "新增功能A" "优化性能B"
```

**注意事项**：

- 发布前必须确保所有功能都经过充分测试
- 建议在发布前创建发布候选版本（RC版本）
- 发布后要及时更新CHANGELOG.md和README.md

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
6. **分支保护**：main和develop分支不允许直接推送，必须通过Pull Request
7. **代码审查**：所有合并到main和develop分支的代码必须经过审查
8. **代码迁移**：禁止直接在文件系统中复制粘贴代码，必须使用Git方法迁移

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

### Q: 为什么不能在main分支上直接开发？

**原因**：

1. **稳定性**：main分支应该始终保持稳定可发布状态
2. **协作安全**：避免多人同时修改导致冲突
3. **版本控制**：便于追踪每个版本的变更
4. **回滚能力**：出现问题时可以快速回滚到稳定版本

**正确做法**：

```bash
# ❌ 错误：直接在main分支开发
git checkout main
# 修改代码...
git commit -m "feat: 新功能"

# ✅ 正确：在feature分支开发
git checkout -b feature/新功能
# 修改代码...
git commit -m "feat: 新功能"
git checkout develop
git merge feature/新功能
```

### Q: 如何正确迁移外部代码到项目中？

**❌ 错误做法**：直接在文件系统中复制粘贴代码

**✅ 正确做法**：

#### 方法1：使用Git子模块（推荐）

```bash
# 添加外部仓库作为子模块
git submodule add https://github.com/外部项目/仓库.git external/模块名

# 更新子模块
git submodule update --init --recursive

# 提交子模块变更
git add .gitmodules external/
git commit -m "feat: 添加外部模块作为子模块"
```

#### 方法2：使用Git远程仓库

```bash
# 添加外部仓库作为远程
git remote add external https://github.com/外部项目/仓库.git

# 获取外部代码
git fetch external

# 合并特定分支或提交
git checkout -b feature/集成外部代码
git merge external/main --allow-unrelated-histories
```

#### 方法3：手动迁移（如果必须）

```bash
# 1. 创建专门的分支
git checkout -b feature/迁移外部代码

# 2. 拷贝外部文件到项目目录
cp /path/to/external/文件1.py ./
cp /path/to/external/文件2.py ./

# 3. 手动调整文件内容（如果需要）
# 4. 逐个文件添加，保留历史
git add 文件1.py
git commit -m "feat: 迁移外部代码 - 文件1"

git add 文件2.py
git commit -m "feat: 迁移外部代码 - 文件2"

# 4. 添加迁移说明文档
echo "## 外部代码迁移说明
- 来源：外部项目名称
- 版本：v1.0.0
- 迁移日期：2024-01-01
- 变更：适配项目结构" > MIGRATION_NOTES.md

git add MIGRATION_NOTES.md
git commit -m "docs: 添加外部代码迁移说明"
```

### Q: 在开发分支上直接拷贝代码可以吗？

**答案**：虽然比在main分支上拷贝好，但仍然不是最佳实践。

#### 相对优势

- ✅ 不会影响稳定版本（main分支）
- ✅ 可以在功能分支上自由实验
- ✅ 便于回滚和撤销

#### 仍然存在的问题

- ❌ Git历史不完整，无法追踪代码来源
- ❌ 团队协作困难，其他开发者无法了解代码背景
- ❌ 维护困难，无法知道原始版本和修改历史
- ❌ 可能与现有代码产生意外冲突

#### 在开发分支上的最佳实践

```bash
# 1. 确保在正确的功能分支上
git checkout feature/新功能

# 2. 创建专门的迁移分支（推荐）
git checkout -b feature/迁移外部代码

# 3. 拷贝外部代码文件到项目目录
# 方法A：逐个文件拷贝
cp /path/to/external/文件1.py ./external/
cp /path/to/external/文件2.py ./external/

# 方法B：批量拷贝整个目录
cp -r /path/to/external/project/* ./external/

# 4. 使用Git方法迁移代码
# 方法A：逐个文件添加，保留迁移历史
git add external/文件1.py
git commit -m "feat: 迁移外部代码 - 文件1 (来源: 项目名称 v1.0.0)"

git add external/文件2.py
git commit -m "feat: 迁移外部代码 - 文件2 (来源: 项目名称 v1.0.0)"

# 方法B：批量添加但保留说明
git add external/
git commit -m "feat: 批量迁移外部代码

来源: 外部项目名称
版本: v1.0.0
迁移日期: 2024-01-01
变更说明: 适配项目结构，移除不必要的依赖"

# 4. 创建迁移说明文档
cat > MIGRATION_NOTES.md << 'EOF'
# 外部代码迁移说明

## 基本信息
- **来源项目**: 外部项目名称
- **原始版本**: v1.0.0
- **迁移日期**: 2024-01-01
- **迁移分支**: feature/迁移外部代码

## 迁移内容
- 文件1: 功能描述
- 文件2: 功能描述

## 适配修改
- 修改1: 适配项目结构
- 修改2: 移除外部依赖

## 注意事项
- 需要测试的功能点
- 可能存在的兼容性问题
EOF

git add MIGRATION_NOTES.md
git commit -m "docs: 添加外部代码迁移说明文档"

# 5. 合并回功能分支
git checkout feature/新功能
git merge feature/迁移外部代码

# 6. 清理迁移分支
git branch -d feature/迁移外部代码
```

#### 如果已经直接拷贝了怎么办？

```bash
# 1. 创建备份分支
git checkout -b backup/直接拷贝备份

# 2. 提交当前状态作为备份
git add .
git commit -m "backup: 直接拷贝的外部代码备份"

# 3. 回到功能分支
git checkout feature/新功能

# 4. 重置到拷贝前的状态
git reset --hard HEAD~1  # 或者指定具体的提交

# 5. 使用正确方法重新迁移
# （按照上面的最佳实践操作）
```

#### 总结

- **短期**：在开发分支上直接拷贝可以接受，但要注意记录
- **长期**：建议使用Git方法迁移，保持历史完整性
- **团队项目**：必须使用Git方法迁移，便于团队协作

### Q: Feature分支是否需要设置远程跟踪？

**答案**：根据具体情况决定，一般不建议设置。

#### 什么情况下设置远程跟踪

**✅ 适合设置远程跟踪的场景**：
- **团队协作**：多人共同开发同一个功能
- **长期开发**：功能开发周期较长（几周或几个月）
- **备份需要**：需要远程备份开发进度
- **多设备开发**：需要在不同设备间同步代码

#### 什么情况下不建议设置

**❌ 不建议设置远程跟踪的场景**：
- **短期开发**：功能开发几天内完成
- **个人开发**：只有一个人开发
- **实验性功能**：不确定是否会保留的功能

#### 设置远程跟踪的方法

```bash
# 1. 切换到feature分支
git checkout feature/新功能

# 2. 设置上游跟踪
git branch --set-upstream-to=origin/feature/新功能

# 3. 验证设置
git branch -vv
# 输出示例：feature/新功能 1234567 [origin/feature/新功能] 最新提交信息
```

#### 取消远程跟踪的方法

```bash
# 1. 取消本地分支的远程跟踪
git branch --unset-upstream

# 2. 删除远程feature分支（如果存在）
git push origin --delete feature/新功能

# 3. 验证结果
git branch -vv
# 输出示例：feature/新功能 1234567 最新提交信息（无远程跟踪）
```

#### 设置默认上游分支

**问题**：Cursor等IDE默认会打开远程仓库的默认分支（通常是main）

**解决方案**：
```bash
# 方法1：设置本地默认分支
git checkout feature/新功能
git branch --set-upstream-to=origin/feature/新功能

# 方法2：在IDE中手动切换
# 打开IDE后，使用Git面板切换到feature分支

# 方法3：创建工作区配置
# 在项目根目录创建 .vscode/settings.json 文件
```

#### 最佳实践建议

**一般做法**：
```bash
# 开发时
git checkout -b feature/新功能
# 不设置远程跟踪，除非需要

# 需要推送到远程时
git push origin feature/新功能

# 开发完成后
git checkout develop
git merge feature/新功能
git branch -d feature/新功能
git push origin :feature/新功能  # 删除远程分支
```

**总结**：
- **个人开发项目**：通常不需要设置远程跟踪
- **团队项目**：根据协作需求决定是否设置
- **长期功能**：建议设置远程跟踪便于协作
- **短期功能**：不建议设置，保持远程仓库整洁

## 联系支持

如有问题，请参考：

1. Git官方文档
2. 项目README.md
