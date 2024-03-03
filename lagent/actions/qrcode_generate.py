import qrcode
import os
from typing import List, Optional, Tuple, Union


from lagent.schema import ActionReturn, ActionStatusCode
from .base_action import BaseAction

DEFAULT_DESCRIPTION = """一个可以生成二维码图片的API。
当你需要利用用户提供的字符串生成简单的黑白色调的二维码图片时，可以使用它。
输入应该是json格式的，示例格式在三个反引号里面
```
{"message":"user_provided_string"}
```
"""


class QrcodeGenerate(BaseAction):
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
                 timeout: int = 5,
                 description: str = DEFAULT_DESCRIPTION,
                 name: Optional[str] = None,
                 enable: bool = True,
                 disable_description: Optional[str] = None) -> None:
        super().__init__(description, name, enable, disable_description)
        self.timeout = timeout

    def __call__(self, query: str) -> ActionReturn:
        """Return the search response.

        Args:
            query (str): The search content.

        Returns:
            ActionReturn: The action return.
        """
        import json  
        
        # 使用json.loads()来解析JSON字符串  
        message = json.loads(query).get("message", None)  
        tool_return = ActionReturn(url=None, args=None, type=self.name)
        if message is not None:
            status_code, response = self._generate(message)
        else:
            tool_return.result = dict(text="传入的参数不正确")
            tool_return.state = ActionStatusCode.HTTP_ERROR
            return tool_return
        # convert search results to ToolReturn format
        # 生成二维码出错
        if status_code == -1:
            tool_return.errmsg = response
            tool_return.state = ActionStatusCode.HTTP_ERROR
        # 成功生成二维码
        else:
            import tempfile  
            with tempfile.NamedTemporaryFile(delete=False,suffix='.png') as tmp:  
                # 将图片保存到临时文件中  
                response.save(tmp.name)  
                # 关闭文件  
                tmp.close()    
            print(tmp.name)
            tool_return.result = dict(text="已生成二维码,二维码路径为"+tmp.name, image=tmp.name)
            # tool_return.result = dict(img=response)
            tool_return.state = ActionStatusCode.SUCCESS
        return tool_return

    def _generate(self, message,
                **kwargs) -> Tuple[int, Union[dict, str]]:
        """HTTP requests to Serper API.

        Args:
            search_term (str): The search query.
            search_type (str): search type supported by Serper API,
                default to 'search'.

        Returns:
            tuple: the return value is a tuple contains:
                - status_code (int): HTTP status code from Serper API.
                - response (dict): response context with json format.
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(message)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            return 1, img
        except Exception as e:
            return -1, str(e)
        