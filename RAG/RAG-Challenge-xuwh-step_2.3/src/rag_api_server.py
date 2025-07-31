import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from pipeline import Pipeline, RunConfig
import pandas as pd

app = Flask(__name__)
CORS(app)

PRESET_QUESTIONS_PATH = Path(__file__).parent.parent / 'data' / 'test_set' / 'questions.json'
print("PRESET_QUESTIONS_PATH:",PRESET_QUESTIONS_PATH)

with open(PRESET_QUESTIONS_PATH, 'r', encoding='utf-8') as f:
    preset_questions = json.load(f)

@app.route('/preset_questions', methods=['GET'])
def get_preset_questions():
    return jsonify(preset_questions)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question')
    # 这里假设pipeline.main(question)返回结构化答案dict
    answer = get_answer(question)
    return jsonify(answer)

def get_answer(question):
    # 设置数据集根目录
    root_path = Path(__file__).parent.parent / 'data' / 'test_set'
    pipeline = Pipeline(root_path, run_config=RunConfig())
    answer = pipeline.answer_single_question(question)
    # 新增：查找公司所有文档名
    # 尝试从answer中获取company_name
    company_name = None
    # 1. 尝试value字段
    value = answer.get('value')
    if value:
        try:
            value_dict = json.loads(value)
            company_name = value_dict.get('company_name')
        except Exception:
            pass
    # 2. 兜底：直接取answer的company_name
    if not company_name:
        company_name = answer.get('company_name')
    company_files = []
    if company_name:
        subset_path = root_path / 'subset.csv'
        try:
            df = pd.read_csv(subset_path, encoding='utf-8')
        except Exception:
            df = pd.read_csv(subset_path, encoding='gbk')
        company_files = df[df['company_name'] == company_name]['file_name'].drop_duplicates().tolist()
    answer['company_files'] = company_files
    return answer

if __name__ == '__main__':
    app.run(port=5000, debug=True) 