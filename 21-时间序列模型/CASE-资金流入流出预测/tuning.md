你的问题非常专业，下面是关于ARIMA模型超参数选择的建议，帮助你获得更准确的预测结果：

---

### 1. **参数含义回顾**
- **p**：自回归项数（AR），反映序列自身的滞后影响。
- **d**：差分阶数（I），用于使非平稳序列变为平稳。
- **q**：滑动平均项数（MA），反映误差项的滞后影响。

---

### 2. **参数选择建议**

#### （1）差分阶数 d
- 先用adfuller检验判断序列是否平稳。
- 若p-value < 0.05，d=0；否则尝试d=1，甚至d=2（极少用到2）。
- 差分后再adfuller检验，直到序列平稳。

#### （2）p、q的选择
- **画ACF/PACF图**：
  - ACF（自相关函数）：用于判断q。
  - PACF（偏自相关函数）：用于判断p。
- **经验法则**：
  - PACF在某一阶后截尾，p取截尾阶数。
  - ACF在某一阶后截尾，q取截尾阶数。
- **自动选参**：
  - 使用`statsmodels.tsa.stattools.arma_order_select_ic`或`pmdarima.auto_arima`自动选参，依据AIC/BIC最小原则。

#### （3）模型评估
- 用AIC/BIC/残差分析/交叉验证等方法评估模型优劣。
- 残差应近似白噪声（无自相关）。

---

### 3. **实用自动调参代码示例**

推荐用`pmdarima`库自动选参：

```python
import pmdarima as pm

# purchase_series和redeem_series为你的历史数据
auto_model_purchase = pm.auto_arima(purchase_series, seasonal=False, stepwise=True, trace=True)
print('申购金额最佳参数:', auto_model_purchase.order)

auto_model_redeem = pm.auto_arima(redeem_series, seasonal=False, stepwise=True, trace=True)
print('赎回金额最佳参数:', auto_model_redeem.order)
```
- 这样可以自动给出(p,d,q)最优组合。

---

### 4. **其他建议**
- 预测前先对数据做归一化/标准化处理，预测后再还原。
- 若有明显季节性，可考虑SARIMA模型。
- 预测结果与实际数据对比，持续微调参数。

---

#### 总结
- **先adfuller检验决定d，再ACF/PACF或auto_arima决定p、q。**
- **自动调参+人工微调+残差分析**，是获得好超参的最佳实践。

如需具体代码实现自动调参或ACF/PACF分析，请告知，我可以帮你直接集成到你的脚本中！