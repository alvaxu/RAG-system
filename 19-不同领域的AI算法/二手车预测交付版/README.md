# 二手车价格预测模型

## 项目简介

本项目旨在通过机器学习模型预测二手车的交易价格。我们有两个核心脚本：一个用于数据预处理和特征工程，另一个用于模型训练和预测。通过一系列特征工程步骤（包括交互特征、比值特征和交叉验证目标编码等），我们优化了XGBoost回归模型性能。

## 文件结构

-   `feature_engineering.py`: 数据预处理和特征工程脚本。运行此脚本将生成模型训练所需的数据文件。
-   `main_model.py`: 核心模型训练和预测脚本。加载 `feature_engineering.py` 生成的数据，训练XGBoost模型并生成预测结果和分析图表。
-   `used_car_train_20200313.csv`: 原始训练数据集。
-   `used_car_testB_20200421.csv`: 原始测试数据集。
-   `train_features.csv`: 经过特征工程处理的训练集数据 (由 `feature_engineering.py` 生成)。
-   `test_features.csv`: 经过特征工程处理的测试集数据 (由 `feature_engineering.py` 生成)。
-   `requirements.txt`: 项目所需的Python库及其版本列表。
-   `README.md`: 项目说明文件。

## 环境设置

1.  **安装 Python**: 确保您的系统已安装 Python 3.8 或更高版本。
2.  **创建虚拟环境 (推荐)**:
    ```bash
    python -m venv venv
    ```
3.  **激活虚拟环境**:
    -   Windows: `.\venv\Scripts\activate`
    -   macOS/Linux: `source venv/bin/activate`
4.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

## 代码运行

1.  **执行特征工程**: 首先运行 `feature_engineering.py` 来生成训练和测试特征文件：
    ```bash
    python feature_engineering.py
    ```
    运行成功后，将在项目根目录生成 `train_features.csv` 和 `test_features.csv`。

2.  **运行模型**: 接着运行 `main_model.py` 来训练模型并进行预测：
    在激活的虚拟环境中，运行主模型脚本：
    ```bash
    python main_model.py
    ```

## 模型输出

运行 `main_model.py` 后，将在项目根目录生成以下文件：

-   `main_model_price_pred_vs_true.png`: 预测价格与实际价格的散点图，用于可视化模型拟合效果。
-   `main_model_predict.csv`: 包含测试集 `SaleID` 及其对应的预测价格。
-   `main_model_importance_top30.png`: 模型特征重要性Top 30的条形图，显示了对价格预测贡献最大的特征。

## 模型概述

本项目使用的模型是 **XGBoost 回归器**。在特征工程方面，我们采用了以下策略：

-   **交互特征**:
    -   `v_0 * v_12`
    -   `regYear * power`
-   **比值特征**:
    -   `power_per_year` (power / (2020 - regYear))
-   **其他衍生特征**:
    -   `v_3` 的绝对值 (`v_3_abs`)
-   **类别特征编码**:
    -   `brand` 和 `model` 的交叉验证目标编码 (无平滑)。
    -   `regionCode` 的频率编码。

MAE 表现稳定在约 `511.3080` 左右。

## 贡献

如果您有任何疑问或改进建议，欢迎提出！ 