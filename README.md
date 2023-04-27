# mAIrus

> mAIrus is tool that implement [Chat-GPT](https://openai.com/blog/chatgpt) in Maya.

## How to install

You will need some files that several Illogic tools need. You can get them via this link :
https://github.com/Illogicstudios/common

You also have to specify the path to the ```openai_key``` file that only contains your openai key 
(can be generated here : [API keys](https://platform.openai.com/account/api-keys))
```python
# TODO Put your OpenAI API key here
__PATH_TO_OPENAI_KEY = 'PATH/TO/openai_key'
```

---

## Code generator

<div align="center">
  <span>
    <img src="https://user-images.githubusercontent.com/117286626/229794764-096e3409-ebc2-4f57-90bb-9cad9be7b2ef.png" width=60%>
  </span>
  <p weight="bold">User interface of mAIrus</p>
  <br/>
</div>

You can choose which model of Chat you want to use. Some work better than others for certain tasks.
mAIrus has to generate Maya code in Pymel and with Pyside2 for the user interfaces.
