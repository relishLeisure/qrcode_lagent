import qrcode
import os
from typing import List, Optional, Tuple, Union

import time
import json
import pandas as pd
import requests
from io import BytesIO
from requests.exceptions import RequestException, Timeout

from modelscope import snapshot_download
import torch
from PIL import Image
import io
from requests import get
import numpy as np
import tempfile

import requests
from pathlib import Path

from lagent.schema import ActionReturn, ActionStatusCode
from .base_action import BaseAction

DEFAULT_DESCRIPTION = """这是一个可以美化二维码图片的API。
当你需要美化二维码图片时，可以使用它。
输入应该是json格式的，示例格式在三个反引号里面
file_path是需要美化的二维码图片路径，可以从之前的回答中查找
```
{"file_path":"qrcode_image_file_path"}
```
"""

url = "http://127.0.0.1:8000/run_diffusion_control"

class QrcodeBeautify(BaseAction):
    """
    Args:
        api_key (str): API KEY to use serper google search API,
            You can create a free API key at https://serper.dev.
        timeout (int): Upper bound of waiting time for a serper request.
        search_type (str): Serper API support ['search', 'images', 'news',
            'places'] types of search, currently we only support 'search'.
        k (int): select first k results in the search results as response.
        description (str): The description of the action. Defaults to
            None.
        name (str, optional): The name of the action. If None, the name will
            be class name. Defaults to None.
        enable (bool, optional): Whether the action is enabled. Defaults to
            True.
        disable_description (str, optional): The description of the action when
            it is disabled. Defaults to None.
    """

    def __init__(self,
                 timeout: int = 10,
                 description: str = DEFAULT_DESCRIPTION,
                 name: Optional[str] = None,
                 enable: bool = True,
                 disable_description: Optional[str] = None) -> None:
        super().__init__(description, name, enable, disable_description)
        self.timeout = timeout


    def __call__(self, query, **kwargs) -> ActionReturn:
        try:
            import json  
        
            # 使用json.loads()来解析JSON字符串  
            prompt = json.loads(query).get("prompt", "1girl, flowers")  
            tool_return = ActionReturn(url=None, args=None, type=self.name)
            if prompt is None:
                tool_return.result = dict(text="没有提供提示词")
                return tool_return
            
            image_path = json.loads(query).get("file_path", None)
            print(image_path)
            if image_path is None:
                tool_return.result = dict(text="没有获得二维码图片路径")
                return tool_return
            type = 'nohide'
            model = 'GhostMix'
            data = {
                "prompt": prompt,
                "type":type,
                "model":model
            }
            print("提示词为", prompt, image_path)
            local_file = Path(image_path)
            content = local_file.read_bytes()
            response = requests.post(url, files={'file': BytesIO(content)}, data=data)
            # 检查响应
            if response.status_code == 200:
                # 获取文件名
                filename = response.headers["Content-Disposition"].split("filename=")[1].strip('\"')  
                print(f"File '{filename}' received successfully.")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    temp_file_path = temp_file.name
                    Image.open(BytesIO(response.content)).save(temp_file_path)
                    tool_return.result = dict(text=f'成功美化图片', image=temp_file_path)
                # temp_file.delete()
                return tool_return
            else:
                # 请求失败
                print("Error:", str(response.status_code), response.text)
                text = '无法连接到服务器，错误信息：' + str(response.status_code) + response.text
                tool_return.result = dict(text=text)
                return tool_return
        
        except Exception as e:
            print(str(e))
            tool_return.result = dict(text=str(e))
            return tool_return
        