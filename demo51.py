"""
自助式的数据分析智能体
"""
import json

import openpyxl
import pandas as pd
import streamlit as st
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr


openai_model=ChatOpenAI(
    model = 'openai_model',
    base_url = 'https://api.openai-hk.com/v1',
    api_key = SecretStr('hk-1ui60r10000561983535706b6ea9aaf2457240da4cb00129'),
              )

PROMPT_PREFIX = """你是一位数据分析助手，你的回应内容取决于用户的请求内容，请按照下面的步骤处理用户请求：

1. 思考阶段 (Thought) ：先分析用户请求类型（文字回答/表格/图表），并验证数据类型是否匹配。
2. 行动阶段 (Action) ：根据分析结果选择以下严格对应的格式。
   - 纯文字回答: 
     {"answer": "不超过50个字符的明确答案"}

   - 表格数据：  
     {"table":{"columns":["列名1", "列名2", ...], "data":[["第一行值1", "值2", ...], ["第二行值1", "值2", ...]]}}

   - 柱状图 
     {"bar":{"columns": ["A", "B", "C", ...], "data":[35, 42, 29, ...]}}

   - 折线图 
     {"line":{"columns": ["A", "B", "C", ...], "data": [35, 42, 29, ...]}}

3. 格式校验要求
   - 字符串值必须使用英文双引号
   - 数值类型不得添加引号
   - 确保数组闭合无遗漏

   错误案例：{'columns':['Product', 'Sales'], data:[[A001, 200]]}  
   正确案例：{"columns":["product", "sales"], "data":[["A001", 200]]}

注意：响应数据的"output"中不要有换行符、制表符以及其他格式符号。
"""

def dataframe_agent(df, question):
    """
    创建智能体，提问与回答
    :param df:
    :param question:
    :return:
    """
    agent = create_pandas_dataframe_agent(
        llm=openai_model,
        df=df,
        verbose=True,
        max_iterations=4,
        allow_dangerous_code=True,
        agent_executor_kwargs={
            'handle_parsing_errors': True,
        }
    )
    res = agent.invoke({
        'input': PROMPT_PREFIX + question,
    })
    return json.loads(res['output'])




def generate_chart(data_source, chart_type):
    # 先处理柱状图与折线图数据
    df = pd.DataFrame({
        'x':data_source['columns'],
    'y': data_source['data'],
    }).set_index('x')

    if chart_type == 'bar':
        st.bar_chart(df)
    elif chart_type == 'line':
        st.line_chart(df)

st.title('自助式数据分析')

# 单选按钮 选择待分析文件类型
option = st.radio(
    "请选择待分析文件类型",
    ('Excel', 'CSV', 'JSON', 'SQL'))
file_type = 'xlsx' if option == 'Excel' else 'csv'
#选择上传文件
file = st.file_uploader('选择文件',type=file_type)

# 判断，如果有选择上传文件，则将上传文件中的数据表获取到
if file:
    if file_type == 'xlsx':
       wb = openpyxl.load_workbook( file)

       sheets = wb.sheetnames

       option = st.selectbox('请选择数据表',sheets)

       df = pd.read_excel(file, sheet_name=option)

    else:
        df = pd.read_csv(file)
    with st.expander('数据表'):
        st.dataframe(df)

question = st.text_area('请输入问题描述或可视化要求：',
                        placeholder='请输入问题描述或可视化要求：',
                        )
#按钮
button = st.button('分析')

# 判断点击按钮后，是否有选择文件，是否有输入问题
if button and file and question:
    st.error('请选择文件')
    st.stop()
if button and not question:
    st.error('请输入问题描述')
    st.stop()

# 点击按钮并且有文件与问题后
if button and file and question and 'df' in st.session_state:
    with st.spinner('思考中...'):
        res = dataframe_agent(df=st.session_state['df'], question=question)
    # print(res)
    # st.write(res)
    # 获取到语言模型输出返回的数据后，处理数据
    if 'answer' in res:  # 纯文本数据
        st.write(res['answer'])
    if 'table' in res:  # 表格数据
        st.table(data=pd.DataFrame(
            data=res['table']['data'],
            columns=res['table']['columns'],
        ))
    if 'bar' in res:  # 柱状图
        generate_chart(res['bar'], chart_type='bar')
    if 'line' in res:  # 折线图
        generate_chart(res['line'], chart_type='line')