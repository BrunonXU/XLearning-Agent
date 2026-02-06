# 贡献指南

感谢你对 XLearning-Agent 的关注！欢迎任何形式的贡献。

## 🚀 快速开始

### 1. Fork 并克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/XLearning-Agent.git
cd XLearning-Agent
```

### 2. 创建虚拟环境

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys
```

## 📝 贡献流程

1. **Fork** 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 **Pull Request**

## 🎯 贡献方向

我们欢迎以下类型的贡献：

- 🐛 **Bug 修复** - 发现问题请提交 Issue 或直接 PR
- ✨ **新功能** - 欢迎提出新想法
- 📝 **文档** - 改进文档、添加示例
- 🧪 **测试** - 增加测试覆盖率
- 🌐 **翻译** - 支持更多语言

## 📋 代码规范

- 使用 **Python 3.10+**
- 遵循 **PEP 8** 代码风格
- 添加适当的 **类型注解**
- 编写清晰的 **文档字符串**
- 保持代码简洁易读

## 🧪 测试

我们提供了一套完整的测试套件。在提交代码前，请确保通过所有测试。

### 运行测试

使用 `pytest` 运行测试：

```bash
# 运行所有测试
pytest tests/ -v

# 运行冒烟测试（验证核心功能）
pytest tests/test_smoke.py -v
```

### 测试目录结构

- `tests/test_smoke.py`: 冒烟测试，验证 API 连接和核心骨架
- `tests/test_providers.py`: Provider 单元测试
- `tests/test_rag.py`: RAG 模块单元测试

### 编写测试

请确保为新功能编写对应的测试用例。测试文件应放在 `tests/` 目录下，命名以 `test_` 开头。

## 📄 许可证

贡献的代码将采用 [MIT License](LICENSE) 开源。

## 💬 联系方式

如有问题，欢迎：
- 提交 [Issue](https://github.com/BrunonXU/XLearning-Agent/issues)
- 发起 [Discussion](https://github.com/BrunonXU/XLearning-Agent/discussions)

---

再次感谢你的贡献！ 🎉
