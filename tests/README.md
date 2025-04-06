# 测试说明

本目录包含项目的单元测试。

## 测试结构

- `test_manus.py`: 测试`ManusAgent`类的主要功能
- `test_react_flow.py`: 测试`ReactFlow`类的主要功能
- `run_tests.py`: 测试运行器，用于运行所有测试

## 运行测试

### 方法1: 使用测试运行器

```bash
# 在项目根目录下运行
python -m tests.run_tests
```

### 方法2: 使用unittest直接运行

```bash
# 运行所有测试
python -m unittest discover -s tests

# 运行特定测试文件
python -m unittest tests.test_manus

# 运行特定测试类
python -m unittest tests.test_manus.TestManusAgent

# 运行特定测试方法
python -m unittest tests.test_manus.TestManusAgent.test_initialization
```

### 方法3: 使用pytest (如果已安装)

```bash
# 安装pytest
pip install pytest

# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_manus.py

# 运行特定测试类
pytest tests/test_manus.py::TestManusAgent

# 运行特定测试方法
pytest tests/test_manus.py::TestManusAgent::test_initialization
```

## 测试覆盖率

要生成测试覆盖率报告，可以使用`coverage`工具：

```bash
# 安装coverage
pip install coverage

# 运行测试并收集覆盖率数据
coverage run -m tests.run_tests

# 生成覆盖率报告
coverage report

# 生成HTML格式的覆盖率报告
coverage html
```

生成的HTML报告将保存在`htmlcov`目录中，可以在浏览器中打开`htmlcov/index.html`查看详细报告。 