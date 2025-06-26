# -*- coding: utf-8 -*-
"""
Coze API 配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Coze API 配置 
COZE_API_TOKEN = "pat_IMUqLdFmEdJvi9UYpulE1N5rAs1yVaP7YPLCXctfLtx0J24Eblxtx2irt5v4HVcG"  # coze api token
COZE_BOT_ID = "7509094784515440681"  # 古诗入画

# Coze API 基础URL (中国区)
COZE_CN_BASE_URL = "https://api.coze.cn"

# 用户ID (可以是任意字符串，用于标识用户)
DEFAULT_USER_ID = "alpha_alpha" 