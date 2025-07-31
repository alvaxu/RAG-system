# 酒店内容推荐系统项目说明文档

---

## 一、项目简介

本项目为一个基于内容的酒店推荐系统，用户可通过网页前端选择一个酒店，系统会推荐3个与之最相似的酒店，并展示其名称、简介和相似度分数。系统采用 Flask 作为后端API服务，前端为简单的HTML页面，通过下拉选择和按钮交互实现推荐功能。

---

## 二、项目结构

```
hotel_recommendation-250725/
├─ Seattle_Hotels.csv                # 酒店数据（含名称、地址、简介）
├─ V100_hotel_recommend_api.py       # Flask后端API，含数据清洗、建模、推荐接口
├─ static/
│    └─ V100_hotel_recommend_front.html  # 前端页面（放在static目录下，供Flask服务）
├─ V100_hotel_recommend_doc.md       # 项目说明文档（本文件）
```

---

## 三、使用说明

### 1. 启动后端服务

在命令行运行：

```bash
python V100_hotel_recommend_api.py
```

默认监听 `http://127.0.0.1:5000/`。

### 2. 访问前端页面

在浏览器中访问：

```
http://127.0.0.1:5000/
```

即可看到下拉选择和推荐结果。

---

## 四、主要功能

- **酒店下拉选择**：前端自动加载所有酒店名称，供用户选择。
- **内容推荐**：基于酒店简介（desc）内容，计算TF-IDF特征，返回最相似的3家酒店。
- **结果展示**：显示推荐酒店的名称、简介（截断120字）和相似度分数。

---

## 五、核心算法与参数说明

### 1. 数据清洗

- 去除简介（desc）为空或全空格的行
- 去除简介长度小于30的行
- 替换常见乱码和特殊字符（如`?`、`\n`、`\r`、`\t`等）
- 多空格合并为单一空格
- 去重（同一简介只保留一条）

### 2. 特征提取（TF-IDF向量化）

采用 `sklearn.feature_extraction.text.TfidfVectorizer`，参数如下：

| 参数名         | 取值/说明                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------ |
| input          | 'content'，输入为原始文本内容                                                              |
| encoding       | 'utf-8'，文本编码                                                                          |
| decode_error   | 'strict'，解码错误时抛出异常                                                                |
| strip_accents  | None，不做重音符号处理                                                                     |
| lowercase      | True，全部转为小写                                                                          |
| preprocessor   | None，不自定义预处理                                                                        |
| tokenizer      | None，不自定义分词                                                                          |
| stop_words     | 'english'，过滤英文停用词（如the, is, and等）                                               |
| ngram_range    | (1, 3)，统计1-gram、2-gram、3-gram（单词、短语、三元组）                                    |
| analyzer       | 'word'，按单词分词                                                                         |
| max_df         | 1.0，不过滤高频词（所有词都保留）                                                           |
| min_df         | 0.01，只保留在至少1%文档中出现过的词，过滤极少见的“冷门词”                                  |
| max_features   | None，不限制特征数量                                                                        |
| vocabulary     | None，自动生成词表                                                                         |
| binary         | False，TF-IDF权重为浮点数                                                                  |
| dtype          | float，特征类型为float（会自动转为np.float64）                                              |
| norm           | 'l2'，特征向量归一化                                                                       |
| use_idf        | True，使用逆文档频率（IDF）                                                                |
| smooth_idf     | True，平滑IDF，避免除零错误                                                                |
| sublinear_tf   | False，不对词频取对数                                                                      |

**参数说明举例：**
- `ngram_range=(1, 3)`：不仅统计单个单词，还统计连续2个、3个单词的短语特征，提升语义表达能力。
- `min_df=0.01`：如果有100条简介，某个词只在1条中出现，则会被保留；如果只在1条以下出现，则被过滤。
- `stop_words='english'`：去除常见英文停用词，减少无意义特征。

### 3. 相似度计算

- 使用 `sklearn.metrics.pairwise.cosine_similarity` 计算用户选择酒店与所有酒店简介的余弦相似度。
- 排除自身，取相似度最高的3家酒店作为推荐结果。

---

## 六、接口说明

### 1. `/hotels`  (GET)

- **功能**：返回所有酒店名称及编号
- **返回示例**：
  ```json
  {
    "hotels": [
      { "id": 0, "name": "Hilton Garden Seattle Downtown" },
      { "id": 1, "name": "Sheraton Grand Seattle" },
      ...
    ]
  }
  ```

### 2. `/recommend` (POST)

- **功能**：根据酒店编号返回3个最相似酒店
- **请求参数**：
  ```json
  { "hotel_id": 0 }
  ```
- **返回示例**：
  ```json
  {
    "results": [
      {
        "name": "Sheraton Grand Seattle",
        "desc": "Located in the city's vibrant core, the Sheraton Grand Seattle provides ...",
        "similarity": 0.512
      },
      ...
    ]
  }
  ```

---

## 七、前端页面说明

- 自动加载酒店列表到下拉框
- 选择酒店后，点击“获取相似酒店推荐”按钮，显示推荐结果
- 推荐结果包括：酒店名称、简介（前120字）和相似度分数

---

## 八、注意事项

- **前端页面需通过Flask服务访问**，即 `http://localhost:5000/`，不要直接用文件协议打开HTML。
- **如需调整推荐算法参数**，可在 `V100_hotel_recommend_api.py` 的 `TfidfVectorizer` 部分修改。
- **如需支持中文或其他语言**，需调整分词、停用词等参数。

---

## 九、扩展建议

- 支持多条件筛选（如地理位置、价格等）
- 增加酒店图片、评分等信息
- 支持用户自定义输入文本进行推荐
- 前端美化与移动端适配

---

如有更多需求或问题，欢迎随时联系开发者！
