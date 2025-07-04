import os
import time
import librosa
import tiktoken
import re
import ast
import json
from openai import OpenAI, AsyncOpenAI
import csv
import jieba
import scipy.stats as stats
import soundfile as sf
import pandas as pd
import numpy as np
from pydub import AudioSegment
import seaborn as sns
import matplotlib.pyplot as plt
import noisereduce as nr
from pydub.silence import split_on_silence
import warnings
import collections
from pathlib import Path
import nltk
from flask import current_app
warnings.filterwarnings('ignore')
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import asyncio
from flask import jsonify
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from openai import OpenAI,AzureOpenAI
from .prompt import style_prompt, sentiment_prompt, patterns_prompt, topics_prompt, conflict_prompt, generate_user_profile_prompt, advantage_prompt
from .prompt import (
    generate_user_profile_prompt, scene_construct, return_prompt,
    generate_family_overview, generate_conversation_analysis, 
    emotion_analysis, generate_reflection_questions, 
    conflict_analysis, behavior_analysis, strategy_generation
)
from .tx_deepseek import Scenery_rebuild, Knowledge_Base
import aiofiles

# 新的DeepSeek API客户端 - v3
client_deepseek_v3 = OpenAI(
    api_key="a306bf91-ca05-442f-b09d-8ebaca556f0a",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

aclient_deepseek_v3 = AsyncOpenAI(
    api_key="a306bf91-ca05-442f-b09d-8ebaca556f0a",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

# 新的DeepSeek API客户端 - r1
client_deepseek_r1 = OpenAI(
    api_key="a306bf91-ca05-442f-b09d-8ebaca556f0a",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    timeout=10
)

aclient_deepseek_r1 = AsyncOpenAI(
    api_key="a306bf91-ca05-442f-b09d-8ebaca556f0a",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    timeout=10
)

DEEPSEEK_CLIENT = OpenAI(
    base_url="https://api.siliconflow.cn/v1",
            api_key=os.environ.get('DEEPSEEK_API_KEY')  # 从环境变量获取更安全
)

AZURE_CLIENT = AzureOpenAI(
azure_endpoint='https://pcg-west-us-3.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview',
api_key=os.environ.get('AZURE_OPENAI_API_KEY'),
api_version='2025-01-01'
)

def get_deepseek_response(system_prompt: str, user_content: str, temperature: float = 0.1, max_retries: int = 3, delay: int = 5) -> str:
    """获取DeepSeek的结构化响应，支持重试机制"""
    attempt = 0
    while attempt < max_retries:
        try:
            completion = client_deepseek_r1.chat.completions.create(
                model="ep-20250213154525-wkfdb",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=temperature,
            )
            
            raw_content = completion.choices[0].message.content
            
            # 清洗可能的非JSON内容
            if raw_content.startswith("```json"):
                return raw_content.split("```json")[1].split("```")[0].strip()
            return raw_content
            
        except Exception as e:
            attempt += 1
            print(f"An error occurred: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            time.sleep(delay)
    
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None

# 这个函数处理单个请求，返回单个结果
async def gpt_prompt_async(prompt, input_data, max_retries=3, delay=5):
    attempt = 0
    input = 'Transcripts of conversations: \n' + str(input_data)
    while attempt < max_retries:
        try:
            start_time =  time.time()
            response = await aclient.chat.completions.create(
                model="ep-20250331105849-cbfg5",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input}
                ],
                temperature=0
            )
            output = response.choices[0].message.content
            if output.startswith('```python\n'):
                output = output.strip('```python\n').strip('```')
                output = eval(output)
            end_time = time.time()
            running_time = end_time - start_time
            print(f"GPT running time: {running_time} seconds")
            return output
        except Exception as e:
            attempt += 1
            print(f"An error occurred: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            await asyncio.sleep(delay)
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None



# Function to prompt GPT for analysis
def gpt_prompt(prompt, input_data, max_retries=3, delay=5):
    attempt = 0
    input = 'Transcripts of conversations: \n' + str(input_data)
    while attempt < max_retries:
        try:
            start_time =  time.time()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input}
                ],
                temperature=0
            )
            output = response.choices[0].message.content
            if output.startswith('```python\n'):
                output = output.strip('```python\n').strip('```')
                output = eval(output)
            end_time = time.time()
            running_time = end_time - start_time
            print(f"GPT running time: {running_time} seconds")
            return output
        except Exception as e:
            attempt += 1
            print(f"An error occurred: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            time.sleep(delay)
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None


def gpt_prompt_without_data(prompt, max_retries=3, delay=5):
    attempt = 0
    while attempt < max_retries:
        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model="o1-mini", 
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            output = response.choices[0].message.content
            if output.startswith('```python\n'):
                output = output.strip('```python\n').strip('```')
                output = eval(output)
            end_time = time.time()
            running_time = end_time - start_time
            print(f"GPT running time: {running_time} seconds")
            return output
        except Exception as e:
            attempt += 1
            print(f"An error occurred: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            time.sleep(delay)
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None

async def async_gpt_prompt_without_data(prompt, max_retries=3, delay=5):
    attempt = 0
    while attempt < max_retries:
        try:
            start_time = time.time()
            response = await aclient.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            output = response.choices[0].message.content
            if output.startswith('```python\n'):
                output = output.strip('```python\n').strip('```')
                output = eval(output)
            end_time = time.time()
            running_time = end_time - start_time
            print(f"GPT running time: {running_time} seconds")
            return output
        except Exception as e:
            attempt += 1
            print(f"An error occurred: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            await asyncio.sleep(delay)
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None

# 异步请求 DeepSeek v3
async def deepseek_v3_prompt_async(prompt, input_data, max_retries=3, delay=5):
    attempt = 0
    input_str = 'Transcripts of conversations: \n' + str(input_data)
    while attempt < max_retries:
        try:
            start_time = time.time()
            # 首先尝试使用智增增客户端
            try:
                zhizengzeng_client = AsyncOpenAI(
                    api_key=os.environ.get('ZHIZENGZENG_API_KEY'),
                    base_url="https://api.zhizengzeng.com/v1"
                )
                response = await zhizengzeng_client.chat.completions.create(
                    model="claude-3-7-sonnet-20250219",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": input_str}
                    ],
                    temperature=0.1
                )
            except Exception as e:
                print(f"智增增客户端请求失败,使用备用客户端: {e}")
                # 如果智增增失败,使用备用DeepSeek客户端
                response = await aclient_deepseek_v3.chat.completions.create(
                    model="ep-20250331105849-cbfg5", 
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": input_str}
                    ],
                    temperature=0.1
                )
            
            output = response.choices[0].message.content
            if output.startswith('```python\n'):
                output = output.strip('```python\n').strip('```')
                output = eval(output)
            end_time = time.time()
            running_time = end_time - start_time
            print(f"API running time: {running_time} seconds")
            return output
        except Exception as e:
            attempt += 1
            print(f"An error occurred: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            await asyncio.sleep(delay)
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None

# 同步请求 DeepSeek v3
def deepseek_v3_prompt(prompt, input_data, max_retries=3, delay=10):
    attempt = 0
    input_str = 'Transcripts of conversations: \n' + str(input_data)
    while attempt < max_retries:
        try:
            start_time = time.time()
            # 增加超时时间为30秒
            client_deepseek_v3.timeout = 30
            response = client_deepseek_v3.chat.completions.create(
                model="ep-20250331105849-cbfg5",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_str}
                ],
                temperature=0.1  # 降低随机性以获得更稳定的结果
            )
            output = response.choices[0].message.content
            if output.startswith('```python\n'):
                output = output.strip('```python\n').strip('```')
                output = eval(output)
            end_time = time.time()
            running_time = end_time - start_time
            print(f"DeepSeek v3 running time: {running_time} seconds")
            return output
        except Exception as e:
            attempt += 1
            print(f"An error occurred in deepseekv3: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            time.sleep(delay)
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None

# 异步请求 DeepSeek r1
async def deepseek_r1_prompt_async(prompt, input_data, max_retries=3, delay=5):
    attempt = 0
    input_str = 'Transcripts of conversations: \n' + str(input_data)
    while attempt < max_retries:
        try:
            start_time = time.time()
            response = await aclient_deepseek_r1.chat.completions.create(
                model="ep-20250213154525-wkfdb",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_str}
                ],
                temperature=0
            )
            output = response.choices[0].message.content
            if output.startswith('```python\n'):
                output = output.strip('```python\n').strip('```')
                output = eval(output)
            end_time = time.time()
            running_time = end_time - start_time
            print(f"DeepSeek r1 running time: {running_time} seconds")
            return output
        except Exception as e:
            attempt += 1
            print(f"An error occurred: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            await asyncio.sleep(delay)
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None

# 同步请求 DeepSeek r1
def deepseek_r1_prompt(prompt, input_data, max_retries=3, delay=5):
    attempt = 0
    # 将system prompt和user prompt合并
    user_prompt = f"{prompt}\n \n{str(input_data)}"
    while attempt < max_retries:
        try:
            start_time = time.time()
            response = client_deepseek_r1.chat.completions.create(
                model="ep-20250213154525-wkfdb",
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6
            )
            output = response.choices[0].message.content
            if output.startswith('```python\n'):
                output = output.strip('```python\n').strip('```')
                output = eval(output)
            end_time = time.time()
            running_time = end_time - start_time
            print(f"DeepSeek r1 running time: {running_time} seconds")
            return output
        except Exception as e:
            attempt += 1
            print(f"An error occurred: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            time.sleep(delay)
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None

# 异步请求 DeepSeek v3 without prompt
async def deepseek_v3_without_prompt_async(input_data, max_retries=5, delay=10):
    attempt = 0
    input_str = 'Transcripts of conversations: \n' + str(input_data)
    while attempt < max_retries:
        try:
            start_time = time.time()
            response = await aclient_deepseek_v3.chat.completions.create(
                model="ep-20250331105849-cbfg5",
                messages=[
                    {"role": "user", "content": input_str}
                ],
                temperature=0
            )
            output = response.choices[0].message.content
            if output.startswith('```python\n'):
                output = output.strip('```python\n').strip('```')
                output = eval(output)
            end_time = time.time()
            running_time = end_time - start_time
            print(f"DeepSeek v3 without prompt running time: {running_time} seconds")
            return output
        except Exception as e:
            attempt += 1
            print(f"An error occurred ds: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            await asyncio.sleep(delay)
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None

# 异步请求 DeepSeek r1 without prompt
async def deepseek_r1_without_prompt_async(input_data, max_retries=3, delay=5):
    attempt = 0
    input_str = 'Transcripts of conversations: \n' + str(input_data)
    while attempt < max_retries:
        try:
            start_time = time.time()
            response = await aclient_deepseek_r1.chat.completions.create(
                model="ep-20250213154525-wkfdb",
                messages=[
                    {"role": "user", "content": input_str}
                ],
                temperature=0
            )
            output = response.choices[0].message.content
            if output.startswith('```python\n'):
                output = output.strip('```python\n').strip('```')
                output = eval(output)
            end_time = time.time()
            running_time = end_time - start_time
            print(f"DeepSeek r1 without prompt running time: {running_time} seconds")
            return output
        except Exception as e:
            attempt += 1
            print(f"An error occurred: {e}")
            print(f"Retrying {attempt}/{max_retries} in {delay} seconds...")
            await asyncio.sleep(delay)
    print(f"Failed to get a valid response after {max_retries} attempts")
    return None

# Function to read the JSON file
def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

# Function to preprocess the data and add word count
def preprocess_data(data):
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Convert start_time and end_time to datetime
    df['start_time'] = pd.to_datetime(df['start_time'], format='%H:%M:%S.%f')
    df['end_time'] = pd.to_datetime(df['end_time'], format='%H:%M:%S.%f')
    
    # Calculate word count for each sentence
    df['word_count'] = df['content'].apply(lambda x: len(list(jieba.cut(x))))
    
    return df

# Function to create the frequency histogram
def plot_word_frequency(df, interval='1T', times=None):
    # Resample the data to aggregate word counts over time intervals
    df = df.set_index('start_time')
    word_counts = df['word_count'].resample(interval).sum().fillna(0)
    
    # Plotting the frequency histogram
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(word_counts.index, word_counts.values, width=pd.to_timedelta(interval), color='lightblue', edgecolor='blue')

    # Add vertical lines for each conversation start and end time and fill between them
    if times is not None:
        for i, (start_time, end_time) in enumerate(times):
            ax.axvline(x=start_time, color='r', linestyle='--', linewidth=0.6, label='Start Time' if i == 0 else "")
            ax.axvline(x=end_time, color='g', linestyle='--', linewidth=0.6, label='End Time' if i == 0 else "")
            ax.fill_betweenx([0, ax.get_ylim()[1]], start_time, end_time, color='blue', alpha=0.2)
    
    # Set labels and title
    ax.set_xlabel('Time')
    ax.set_ylabel('Total Word Count')
    ax.set_title('Word Count Frequency Over Time')
    ax.set_ylim(bottom=0)
    ax.set_xlim([pd.to_datetime('00:00:00', format='%H:%M:%S'), word_counts.index.max()])
    
    # Format the x-axis to show only time
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    fig.autofmt_xdate()

    # Add legend
    ax.legend(loc='upper right')

    plt.show()

# Function to segment conversations
def segment_conversations(df, gap_threshold=timedelta(minutes=1.5)):
    conversations = []
    time_ranges = []
    current_conversation = []
    last_end_time = None
    start_time = None
    
    for index, row in df.iterrows():
        if last_end_time and (row['start_time'] - last_end_time > gap_threshold):
            if current_conversation:
                end_time = current_conversation[-1]['end_time']
                conversations.append(current_conversation)
                time_ranges.append((start_time, end_time))
            current_conversation = []
            start_time = row['start_time']
        elif not current_conversation:
            start_time = row['start_time']
        
        current_conversation.append(row)
        last_end_time = row['end_time']
    
    if current_conversation:
        conversations.append(current_conversation)
        time_ranges.append((start_time, last_end_time))
    
    return conversations, time_ranges

# Function to transform the conversation data to the desired format
def transform_conversation(conversation):
    transformed = []
    for index, row in conversation.iterrows():
        transformed.append({
            'id': row['id'],
            'speaker': row['speaker'],
            'content': row['content']
        })
    return transformed

def transcribe_audio(file_path):
    # 获取转录文件夹路径
    transcripts_folder = current_app.config.get('TRANSCRIPTS_FOLDER', 'transcripts/')
    
    # 获取文件名（不包含扩展名）
    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    
    # 构建转录文件路径
    transcript_filename = f"{base_filename}.json"
    transcript_path = os.path.join(transcripts_folder, transcript_filename)
    
    try:
        # 检查转录文件是否存在
        if os.path.exists(transcript_path):
            with open(transcript_path, 'r', encoding='utf-8') as file:
                transcript = json.load(file)
            current_app.logger.info(f"读取转录文件成功: {transcript_path}")
        else:
            current_app.logger.warning(f"指定的转录文件不存在: {transcript_path}")
            # 如果没有找到指定的转录文件，则查找文件夹中的其他json文件
            json_files = [f for f in os.listdir(transcripts_folder) if f.endswith('.json')]
            if json_files:
                # 使用第一个找到的json文件
                alternative_transcript_path = os.path.join(transcripts_folder, json_files[0])
                with open(alternative_transcript_path, 'r', encoding='utf-8') as file:
                    transcript = json.load(file)
                current_app.logger.info(f"使用替代转录文件: {alternative_transcript_path}")
            else:
                raise FileNotFoundError(f"转录文件夹中没有找到任何json文件: {transcripts_folder}")
        
        # 返回转录结果
        return transcript

    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f"读取转录文件时发生错误: {str(e)}")
        raise e


def analyze_audio(transcript):
    # 此处可以添加调用大模型的代码
    # result_style = style
    # result_sentiment = sentiment
    # result_patterns = patterns
    # result_topics = topic
    #print("Transcript content:", transcript)  # 调试打印
    data = [{'id': d['id'], 'speaker': d['speaker'], 'content': d['content']} for d in transcript]
    result_style = gpt_prompt(style_prompt, data)
    result_sentiment = gpt_prompt(sentiment_prompt, data)
    result_patterns = gpt_prompt(patterns_prompt, data)
    result_topics = gpt_prompt(topics_prompt, data)
    result_confict = gpt_prompt(conflict_prompt, data)
    result_advantage = gpt_prompt(advantage_prompt, data)
    return result_style, result_sentiment, result_patterns, result_topics, result_confict, result_advantage


async def analyze_audio_async(transcript):
    data = [{'id': d['id'], 'speaker': d['speaker'], 'content': d['content']} for d in transcript]

    prompts = [
        (style_prompt, data),
        (sentiment_prompt, data),
        (patterns_prompt, data),
        (topics_prompt, data),
        (conflict_prompt, data),
        (advantage_prompt, data)
    ]

    async def process_prompt(prompt_data):
        prompt, data = prompt_data
        return await deepseek_v3_prompt_async(prompt,data)

    tasks = [process_prompt(prompt_data) for prompt_data in prompts]
    results = await asyncio.gather(*tasks)
    print(results)
    result_style, result_sentiment, result_patterns, result_topics, result_confict, result_advantage = results

    return result_style, result_sentiment, result_patterns, result_topics, result_confict, result_advantage

def generate_intervention_strategy(transcript,docs):
    # 假设其他函数已经定义好了
    result_style, result_sentiment, result_patterns, result_topics, result_confict, result_advantage = analyze_audio(transcript)
    '''
    
    '''
    Scenery = Scenery_rebuild(input_data=str(transcript), system_prompt=return_prompt(1), user_prompt=return_prompt(2))
    scenerios = Scenery.final_handle()
    '''
    场景重建完的结果
    '''

    knowledge = Knowledge_Base(docs=docs, input_data=scenerios)
    a1, a2, a3, a4, a5 = knowledge.result()
    '''
    a1: Suggestions for parents on guiding children in each scenario
    a2: Two inspiring cases retrieved for each scenario
    a3: Original dialogue, without improvement
    a4: Improved dialogue
    a5: Questions to provoke parental reflection: Why does this cause occur?
    '''

    # Construct scene
    topics = result_topics + '\n' + str(scenerios)
    #scene = scene_construct(result_style, result_sentiment, result_patterns, topics, result_confict, result_advantage)
    
    # Generate user profile
    #profile_prompt = generate_user_profile_prompt(scene)
    #user_profile = gpt_prompt_without_data(profile_prompt)

    # 第一部分：家庭教育风格分析
    family_overview_prompt = generate_family_overview(result_style, result_patterns, result_advantage)
    family_overview = gpt_prompt_without_data(family_overview_prompt)

    # 第二部分：沟通分析
    conversation_analysis_prompt = generate_conversation_analysis(a3, a4)
    conversation_analysis = gpt_prompt_without_data(conversation_analysis_prompt)

    # 第三部分：情绪分析
    emotion_analysis_prompt = emotion_analysis(result_sentiment)
    emotion_analysis_result = gpt_prompt_without_data(emotion_analysis_prompt)

    # 第四部分：反思问题
    reflection_questions_prompt = generate_reflection_questions(a5)
    reflection_questions = gpt_prompt_without_data(reflection_questions_prompt)

    # 第五部分：冲突分析
    conflict_analysis_prompt = conflict_analysis(result_confict)
    conflict_analysis_result = gpt_prompt_without_data(conflict_analysis_prompt)

    # 第六部分：行为分析
    behavior_analysis_prompt = behavior_analysis(result_confict, scenerios)
    behavior_analysis_result = gpt_prompt_without_data(behavior_analysis_prompt)

    # 第七部分：策略生成
    strategy_generation_prompt = strategy_generation(result_sentiment,a1, a2)
    strategy_generation_result = gpt_prompt_without_data(strategy_generation_prompt)

    return {
        'family_overview': family_overview,
        'conversation_analysis': conversation_analysis,
        'emotion_analysis': emotion_analysis_result,
        'reflection_questions': reflection_questions,
        'conflict_analysis': conflict_analysis_result,
        'behavior_analysis': behavior_analysis_result,
        'strategy_generation': strategy_generation_result
    }

async def transcribe_audio_async(file_path):
    # 获取转录文件夹路径
    transcripts_folder = current_app.config.get('TRANSCRIPTS_FOLDER', 'transcripts/')
    
    # 获取文件名（不包含扩展名）
    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    
    # 构建转录文件路径
    transcript_filename = f"{base_filename}.json"
    transcript_path = os.path.join(transcripts_folder, transcript_filename)
    
    try:
        # 检查转录文件是否存在
        if os.path.exists(transcript_path):
            async with aiofiles.open(transcript_path, 'r', encoding='utf-8') as file:
                content = await file.read()
                transcript = json.loads(content)
            current_app.logger.info(f"读取转录文件成功: {transcript_path}")
        else:
            current_app.logger.warning(f"指定的转录文件不存在: {transcript_path}")
            # 如果没有找到指定的转录文件，则查找文件夹中的其他json文件
            json_files = [f for f in os.listdir(transcripts_folder) if f.endswith('.json')]
            if json_files:
                # 使用第一个找到的json文件
                alternative_transcript_path = os.path.join(transcripts_folder, json_files[0])
                async with aiofiles.open(alternative_transcript_path, 'r', encoding='utf-8') as file:
                    content = await file.read()
                    transcript = json.loads(content)
                current_app.logger.info(f"使用替代转录文件: {alternative_transcript_path}")
            else:
                raise FileNotFoundError(f"转录文件夹中没有找到任何json文件: {transcripts_folder}")
        
        # 返回转录结果
        return transcript

    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f"读取转录文件时发生错误: {str(e)}")
        raise e

async def generate_intervention_strategy_async(transcript):
    # 假设其他异步函数已经定义好了
    result_style, result_sentiment, result_patterns, result_topics, result_confict, result_advantage = await analyze_audio_async(transcript)
    '''
    教养方式，情绪变化，沟通模式，主题分析，冲突分析，优势劣势分析
    '''
    print("特征提取完毕")
    scenery = Scenery_rebuild(input_data=str(transcript), system_prompt=return_prompt(1), user_prompt=return_prompt(2))
    scenerios = await asyncio.to_thread(scenery.final_handle)
    print("场景重建完毕")
    '''
    场景重建完的结果
    '''
    print("初始化数据库")
    knowledge = Knowledge_Base(docs=None, input_data=scenerios,index_folder_path='./checkpoints/index')
    a1, a2, a3, a4, a5 = await asyncio.to_thread(knowledge.result)
    print("数据库初始化完成")
    '''
    a1: Suggestions for parents on guiding children in each scenario
    a2: Two inspiring cases retrieved for each scenario
    a3: Original dialogue, without improvement
    a4: Improved dialogue
    a5: Questions to provoke parental reflection: Why does this cause occur?
    '''
    
    # Construct scene
    #topics = result_topics + '\n' + str(scenerios)
    #scene = scene_construct(result_style, result_sentiment, result_patterns, topics, result_confict, result_advantage)
    
    # Generate user profile
    #profile_prompt = generate_user_profile_prompt(scene)
    #user_profile = await deepseek_v3_without_prompt_async(profile_prompt)

    # 并行生成所有分析结果
    tasks = [
        deepseek_v3_without_prompt_async(generate_family_overview(result_style, result_patterns, result_advantage)),
        deepseek_v3_without_prompt_async(generate_conversation_analysis(a3, a4)),
        deepseek_v3_without_prompt_async(emotion_analysis(result_sentiment)),
        deepseek_v3_without_prompt_async(generate_reflection_questions(a5)),
        deepseek_v3_without_prompt_async(conflict_analysis(result_confict)),
        deepseek_v3_without_prompt_async(behavior_analysis(result_confict, scenerios)),
        deepseek_v3_without_prompt_async(strategy_generation(result_sentiment, a1, a2))
    ]
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks)
    
    # 解包结果
    family_overview, conversation_analysis, emotion_analysis_result, reflection_questions, \
    conflict_analysis_result, behavior_analysis_result, strategy_generation_result = results

    return {
        'family_overview': family_overview,
        'conversation_analysis': conversation_analysis,
        'emotion_analysis': emotion_analysis_result,
        'reflection_questions': reflection_questions,
        'conflict_analysis': conflict_analysis_result,
        'behavior_analysis': behavior_analysis_result,
        'strategy_generation': strategy_generation_result
    }

# 导入所需的模块



# 定义冲突类型枚举
class ConflictType(str, Enum):
    EC = "期望和目标冲突"
    CC = "沟通和互动方式冲突"
    LMC = "学习过程与方法冲突"
    RC = "规则与控制冲突"
    TMC = "时间与精力管理冲突"
    KC = "知识水平与理解差异冲突"
    FC = "注意力和专注度冲突"

# 定义冲突强度枚举
class SeverityLevel(str, Enum):
    High = "高"
    Medium = "中"
    Low = "低"

# 定义输出结构的Pydantic模型
class ConflictScene(BaseModel):
    scene_id: int
    trigger: str # 用中文描述冲突触发点
    process: str # 用中文描述冲突发展过程
    conflict_type: ConflictType # 冲突类型
    severity: SeverityLevel # 冲突强度等级
    dt: int  # 格式为"YYYYMMDD"

class ConflictAnalysisOutput(BaseModel):
    scenes: List[ConflictScene]

# 定义行为分析类
class ConflictAnalysis:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.prompt_behavior_analysis = """
# 亲子行为分析任务

## 以下是家长辅导孩子写作业过程中常见的亲子冲突分类：

### 1. **期望和目标冲突 (EC)**
- **代码定义**: 家长对孩子的成绩、进步或未来的期望较高，而孩子的实际能力、目标或兴趣与家长的期望不一致，导致双方之间的冲突。家长可能将孩子的表现与他人进行比较，进一步加剧冲突。
- **使用准则**: 当家长对孩子的表现要求过高或与孩子的自我认知产生明显差异时使用。包括家长将孩子与他人 (如同学、兄弟姐妹)进行比较，产生压力。
- **示例**:  
  - 家长："你应该像你的同学那样考满分，这么简单的题目怎么还会错？"  
  - 孩子："我已经尽力了，为什么你总觉得我比别人差？"

### 2. **沟通和互动方式冲突 (CC)**
- **代码定义**: 家长和孩子在作业辅导过程中，因沟通方式不同而产生的冲突。家长可能批评、质疑或贬低孩子，导致孩子感到不被理解或被压迫，沟通障碍加剧。
- **使用准则**: 当家长与孩子在沟通过程中情绪失控、批评或质疑等负面沟通方式导致冲突时使用。需关注家长是否责备或贬低孩子的表现，以及孩子对此产生的抵触情绪。
- **示例**:  
  - 家长："你到底怎么回事？我教你这么多遍了，你还不明白！"  
  - 孩子："我就是不想听你说话了，你每次都这样骂我！"

### 3. **学习过程与方法冲突 (LMC)**
- **代码定义**: 家长和孩子在如何完成作业的方式、方法上存在分歧。家长可能认为孩子的方法效率低，试图让孩子采用自己的方法，而孩子则坚持自己的做法，不愿意接受家长的干预。
- **使用准则**: 当家长试图强迫孩子改变学习方法或直接干预学习方式时使用，尤其是在方法不一致导致争执时。
- **示例**:  
  - 家长："你不能这么学，应该先做完所有题再检查！"  
  - 孩子："我习惯这样，为什么要按照你说的做？"

### 4. **规则与控制冲突 (RC)**
- **代码定义**: 家长为学习设定的规则与孩子的自主性发生冲突。家长可能试图通过设定严格的规则来控制孩子的学习节奏和方式，而孩子则寻求更多的自主权和灵活性。
- **使用准则**: 当冲突涉及家长设定的规则、界限或控制权时使用，如学习时间、完成作业的方式等。特别关注孩子是否表达了对规则的不满或寻求更多自主权。
- **示例**:  
  - 家长："必须在晚饭后马上做作业，你不能再拖延了。"  
  - 孩子："我想再玩一会儿，每次你都要管这么多。"

### 5. **时间与精力管理冲突 (TMC)**
- **代码定义**: 家长和孩子在如何分配学习时间和精力上产生的分歧。家长可能希望孩子按固定时间学习，而孩子则有不同的时间安排，导致冲突。
- **使用准则**: 当冲突围绕学习时间、精力分配或学习节奏的安排时使用。尤其是当孩子对家长设定的时间要求表达不满时。
- **示例**:  
  - 家长："你老是拖到这么晚才做作业，效率太低了。"  
  - 孩子："我习惯晚些时候学，早上我根本学不进去！"

### 6. **知识水平与理解差异冲突 (KC)**
- **代码定义**: 家长和孩子在知识水平或理解能力上的差异导致的冲突。家长掌握了某些知识，无法理解孩子为何感到困难，或在讲解时无法站在孩子的角度思考，导致孩子感到不被理解或被批评。此外，家长对某些学习内容不熟悉，孩子质疑其指导的正确性，进一步引发冲突。
- **使用准则**: 当冲突涉及到知识的掌握程度、家长对孩子学习困境的不理解，或孩子对家长知识水平产生怀疑时使用。特别关注家长是否低估了孩子学习的难度。
- **示例**:  
  - 家长："这道题这么简单，你怎么还搞不明白？"  
  - 孩子："你讲的和老师说的不一样，我听不懂。"

### 7. **注意力和专注度冲突 (FC)**
- **代码定义**: 家长对孩子在学习过程中的专注程度不满，认为孩子分心、不专注或效率低下，试图通过提醒或纠正让孩子集中注意力，而孩子可能因过度干预感到压力，产生对立情绪。
- **使用准则**: 当家长因孩子注意力不集中或不专心学习而引发冲突时使用，特别是家长不断干预孩子的学习状态时。
- **示例**:  
  - 家长："你到底在发什么呆？快点专心做作业！"  
  - 孩子："我没走神，只是在想题怎么做。"

## 冲突强度判断标准

### 强度等级:
1. 高 2. 中 3. 低

### 判断标准:

#### 高
- **语气**: 对话语气极其激烈，常伴有大声呵斥、批评或责骂
- **语言严重程度**: 语言中包含侮辱、贬低或指责的言论
- **持续时间**: 对话持续时间较长，且情绪不断升级
- **肢体语言**(如有描述): 涉及拍桌子或摔东西等激烈动作

**示例**:
- 家长大喊："你怎么这么没用，这都做不好！"
- 孩子大声回应："我已经尽力了！你为什么总是骂我？"

#### 中
- **语气**: 语气较为情绪化但未达到大声呵斥的程度，可能包含强烈的不满和争执
- **语言严重程度**: 语言中包含批评或责备，但无严重侮辱
- **持续时间**: 对话时间适中，有一定争执但未继续升级

**示例**:
- 家长说："你这次又考得不好，真让人失望。"
- 孩子回应："我已经很努力了，下次我会做得更好。"

#### 低
- **语气**: 语气平和或略有不满，但总体可控，可能包含轻微批评或建议
- **语言严重程度**: 语言中不含严重负面词汇，更多是表达失望或给出建议
- **持续时间**: 对话时间较短，冲突程度较轻

**示例**:
- 家长说："这次成绩不太理想，要多加努力。"
- 孩子回应："好的，我知道了。"

## 任务描述
使用音频转写文本，识别家长辅导作业过程中的**亲子冲突**场景。每个场景需描述其触发点、过程、家长和孩子的具体行为、冲突类型和强度等级。

## 注意：单次对话中的冲突数量不固定，可能出现多个冲突。

## 输入格式
输入为字典列表，每个字典代表一段转写文本，包含以下键：
- "id": 对话ID
- 'speaker': 说话者角色(家长、孩子或其他)
- "content": 包含转写文本的字符串
## 输出示例
输出为JSON格式，包含以下字段:

- scene_id: 场景ID，整数类型
- trigger: 用中文描述冲突触发点，字符串类型 
- process: 用中文描述冲突发展过程，字符串类型  
- conflict_type: 冲突类型，字符串类型，如"期望冲突"、"沟通方式冲突"等
- severity: 冲突强度等级，字符串类型，可选值为"High"、"Medium"、"Low"
- dt: 日期时间，整数类型，格式为"YYYYMMDD"
    """

    def analyze_conflict(self, transcripts: List[dict], date: str) -> ConflictAnalysisOutput:
        # 计算输入token数量
        encoding = tiktoken.encoding_for_model("gpt-4o")
        input_text = str(transcripts) + f"日期：{date}"
        input_tokens = len(encoding.encode(input_text))
        prompt_tokens = len(encoding.encode(self.prompt_behavior_analysis))
        total_input_tokens = input_tokens + prompt_tokens
        
        print(f"Input tokens: {input_tokens}")
        print(f"Prompt tokens: {prompt_tokens}")
        print(f"Total input tokens: {total_input_tokens}")
        
        # 构造系统提示词（简化，避免过长）
        system_prompt = (
            "你是一个结构化数据生成器。请根据以下指南分析亲子冲突场景，并生成符合指定格式的JSON输出。"
        )
        output_format = """
    确保输出格式严格符合以下结构：
    {
        "scenes": [
            {
                "scene_id": 整数,
                "trigger": "冲突触发点描述",
                "process": "冲突发展过程描述",
                "conflict_type": "冲突类型",
                "severity": "冲突强度等级",
                "dt": 日期整数
            },
            ...
        ]
    }
    
    注意事项：
    1. conflict_type必须是以下值之一: 期望和目标冲突、沟通和互动方式冲突、学习过程与方法冲突、规则与控制冲突、时间与精力管理冲突、知识水平与理解差异冲突、注意力和专注度冲突
    2. severity必须是以下值之一: 高、中、低
    3. dt字段必须是YYYYMMDD格式的整数
    """
        
        # 使用正确的参数名称，分离提示词
        try:
            # 先传送系统提示词
            response = deepseek_v3_prompt(
                prompt=system_prompt + "\n" + output_format,
                input_data=self.prompt_behavior_analysis + "\n\n" + input_text
            )
            print(response)
            # 检查响应
            if response is None:
                print("API调用失败，无法获取有效响应")
                return ConflictAnalysisOutput(scenes=[])
            
             # 解析并修正JSON响应
            try:
                # 提取JSON内容
                if "```json" in response:
                    json_content = response.split("```json")[1].split("```")[0].strip()
                    raw_data = json.loads(json_content)
                else:
                    raw_data = json.loads(response)
                
                # 如果返回的是列表而不是字典，进行转换
                if isinstance(raw_data, list):
                    raw_data = {"scenes": raw_data}
                
                # 确保所有字段符合要求
                if "scenes" in raw_data:
                    for scene in raw_data["scenes"]:
                        # 确保dt是整数
                        if "dt" in scene and not isinstance(scene["dt"], int):
                            try:
                                scene["dt"] = int(scene["dt"])
                            except:
                                scene["dt"] = int(date)
                        
                        # 检查其他必要字段
                        required_fields = ["scene_id", "trigger", "process", "conflict_type", "severity"]
                        for field in required_fields:
                            if field not in scene:
                                if field == "scene_id":
                                    scene[field] = raw_data["scenes"].index(scene) + 1
                                else:
                                    scene[field] = "未提供" if field in ["trigger", "process"] else "低" if field == "severity" else "规则与控制冲突"
                
                # 验证和返回
                analysis_output = ConflictAnalysisOutput.parse_obj(raw_data)
                return analysis_output
                
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                print(f"原始响应: {response[:200]}...")
                return ConflictAnalysisOutput(scenes=[])
            
            except Exception as e:
                print(f"处理冲突分析结果时发生错误: {e}")
                print(f"原始数据: {raw_data}")
                return ConflictAnalysisOutput(scenes=[])
        except Exception as e:
            print(f"处理冲突分析时发生错误: {e}")
            return ConflictAnalysisOutput(scenes=[])
    

# 定义行为类型枚举
class BehaviorType(str, Enum):
    ENC = "鼓励"
    SP = "有标注表扬"
    GP = "无标注表扬"
    GI = "启发式指导"
    SR = "设定规则"
    SRS = "敏感性回应"
    DI = "非启发式指导"
    IT = "信息教授"
    EC = "纠正错误"
    MON = "监督检查"
    DC = "直接命令"
    IC = "间接命令"
    CB = "批评责备"
    FT = "强迫威胁"
    NI = "忽视冷漠"
    BD = "贬低质疑"
    FD = "沮丧失望"
    II = "急躁不耐"

# 定义冲突强度等级枚举
class SeverityLevel(str, Enum):
    积极 = "积极"
    中性 = "中性"
    消极 = "消极"

# 定义行为场景模型
class BehaviorScene(BaseModel):
    behaviour_id: int
    description: str  # 用中文描述行为
    code: BehaviorType  # 行为种类
    type: SeverityLevel  # 行为类型
    dt: str  # 日期时间，格式为"YYYYMMDD"

# 定义行为分析输出模型
class BehaviorAnalysisOutput(BaseModel):
    scenes: List[BehaviorScene]

# 定义行为分析类
class BehaviorAnalysis:
    def __init__(self):
        self.prompt_behavior_analysis = """
# 任务描述
你是一位家庭教育专家,你的任务是分析家长在辅导作业过程中的具体行为。你需要仔细审阅提供的对话内容,识别和捕捉反映家长行为的对话片段,并使用预定义的行为类别对这些行为进行分类。

# 输出格式
必须严格按照以下JSON格式输出:
{
    "scenes": [
        {
            "behaviour_id": 1,
            "description": "家长行为的详细描述",
            "code": "鼓励",  // 注意：只使用代码名称，不要包含括号和代码缩写
            "type": "积极",  // 必须是：积极、中性、消极三者之一
            "dt": "20241212"
        },
        // 更多场景...
    ]
}

# 行为类别

### 积极行为

#### 1. **鼓励 (ENC)**
- **代码定义**: 家长通过言语或行为积极支持孩子的努力和进步，增强孩子的自信心和学习动力，帮助他们克服困难。
- **使用准则**: 当家长给予孩子正面的支持和鼓励，尤其是在孩子遇到困难时，不论结果如何都表现出积极态度。
- **示例**:  
  - 家长："你已经很努力了，继续加油！我相信你能行！"
  - 家长："别着急，我们一步步来，你一定能学会。"

#### 2. **有标注表扬 (SP)**
- **代码定义**: 家长明确指出孩子的具体行为或成就，并给予称赞，帮助孩子认识到自己的具体进步和优点。
- **使用准则**: 当家长清晰指出孩子的某个具体行为、成就或表现，并给予积极的反馈。
- **示例**:  
  - 家长："你这道加法题算得特别好，完全没出错！"
  - 家长："这次你写字写得特别整齐，保持下去！"

#### 3. **无标注表扬 (GP)**
- **代码定义**: 家长对孩子进行一般性的表扬，但没有明确指出具体的行为或成就。
- **使用准则**: 当家长用泛泛的言辞表扬孩子，而不涉及具体的细节或行为时使用。
- **示例**:  
  - 家长："你真棒，继续努力！"
  - 家长："哇，太厉害了！"

#### 4. **启发式指导 (GI)**
- **代码定义**: 家长通过提问或提供线索，引导孩子独立思考和解决问题，而不是直接给出答案，鼓励孩子探索和思考。
- **使用准则**: 当家长通过问题或线索帮助孩子找到解决方案，而不是直接告诉答案时使用。
- **示例**:  
  - 家长："你觉得这个字母应该加在哪个地方？"
  - 家长："我们用什么办法可以把这道题算对呢？想一想有几种方法。"

#### 5. **设定规则 (SR)**
- **代码定义**: 家长为孩子完成作业设立明确的规则或要求，以帮助孩子建立良好的学习习惯和时间管理能力。
- **使用准则**: 当家长明确设定规则并要求孩子遵守时使用，规则通常与作业顺序、时间或完成标准相关。
- **示例**:  
  - 家长："你要先完成语文作业，然后才能去看动画片。"
  - 家长："今天要在晚饭前把所有作业写完，才能出去玩。"

#### 6. **敏感性回应 (SRS)**
- **代码定义**: 家长对孩子的情感、需求和行为做出及时、恰当且体贴的回应。家长能感知到孩子的情绪并给予情感上的支持。
- **使用准则**: 当家长能够识别孩子的情绪，并给予孩子理解和情感上的安慰或支持时使用。
- **示例**:  
  - 家长："我知道你现在有点困了，我们休息一下再继续，好吗？"
  - 家长："你是不是觉得这道题有点难？没关系，我们一起再看看。"

### 中性行为

#### 7. **非启发式指导 (DI)**
- **代码定义**: 家长直接告诉孩子如何完成任务或解答问题，而没有通过启发性的方式引导孩子思考。
- **使用准则**: 当家长直接给出答案或解决方案，而没有通过问题或线索引导孩子思考时使用。
- **示例**:  
  - 家长："这道题你应该这样做，把4加上6就等于10了。"
  - 家长："直接这样抄写答案，不要多想。"

#### 8. **信息教授 (IT)**
- **代码定义**: 家长通过讲解课文、解释概念等方式向孩子传授新知识或技能，通常是为了帮助孩子理解新的学习内容。
- **使用准则**: 当家长为帮助孩子学习新知识或技能进行系统性的讲解时使用。
- **示例**:  
  - 家长："'树'字的写法是左边是木字旁，右边是'寸'，我们来一起写一遍。"
  - 家长："乘法口诀要这样背，二二得四，二三得六，先记住这些。"

#### 9. **纠正错误 (EC)**
- **代码定义**: 家长指出孩子在作业中的错误，并指导其进行修改或改正。
- **使用准则**: 当家长发现孩子作业中的错误并指导孩子进行纠正时使用。
- **示例**:  
  - 家长："你这个地方少写了一个'木'字旁，再写一次吧。"
  - 家长："这里加法错了，重新算一下，记得列好竖式。"

#### 10. **监督检查 (MON)**
- **代码定义**: 家长定期检查孩子的作业进展或完成情况，确保孩子按时完成任务。
- **使用准则**: 当家长通过检查来跟踪孩子的作业进度或检查作业质量时使用。
- **示例**:  
  - 家长："你已经写了几页了？让我看一下有没有错。"
  - 家长："我来检查一下你今天的拼音作业，看看有没有问题。"

#### 11. **直接命令 (DC)**
- **代码定义**: 家长用明确、直接的语言要求孩子执行某项行为或任务，具有较强的命令性和指令性。
- **使用准则**: 当家长以强制性语气直接要求孩子完成任务时使用。
- **示例**:  
  - 家长："马上去写数学作业，不许再拖延了！"
  - 家长："现在停下玩具，去把拼音抄写完。"

#### 12. **间接命令 (IC)**
- **代码定义**: 家长用较为间接的方式向孩子传达要求，例如暗示或建议，而不是直接下达命令。
- **使用准则**: 当家长通过委婉的提议或暗示引导孩子完成任务时使用。
- **示例**:  
  - 家长："作业写完了吗？是不是该去把它做完了？"
  - 家长："我们先把作业做完再去玩吧，这样就不用担心没时间了。"

### 消极行为

#### 13. **批评责备 (CB)**
- **代码定义**: 家长对孩子的错误或行为表达负面评价，直接指责孩子的不足之处，可能带有贬低性语言。
- **使用准则**: 当家长因孩子的表现不如预期而进行指责或批评时使用。
- **示例**:  
  - 家长："你怎么连这么简单的字都写错了？"
  - 家长："我跟你说了多少次，你怎么还记不住！"

#### 14. **强迫威胁 (FT)**
- **代码定义**: 家长通过施加压力或威胁后果，逼迫孩子服从其要求，以达到预定的行为结果。
- **使用准则**: 当家长用威胁或强迫的方式要求孩子完成任务时使用。
- **示例**:  
  - 家长："如果你不写作业，今天就别想玩积木！"
  - 家长："要是再不写完，我就把你的玩具收走！"

#### 15. **忽视冷漠 (NI)**
- **代码定义**: 家长对孩子的需求或情感表现出无视或冷淡，不给予任何关注或回应。
- **使用准则**: 当家长对孩子的请求、情感或行为表现出无视或冷漠时使用。
- **示例**:  
  - 孩子："妈妈，我不会这道题，可以帮我吗？"  
  - 家长 (没有回应，继续玩手机)。

#### 16. **贬低质疑 (BD)**
- **代码定义**: 家长通过贬低孩子的能力或质疑孩子的表现，直接打击孩子的自信心和积极性。此类言语或行为通常带有不信任或否定的情绪，表现为对孩子能力的怀疑或对其表现的强烈不满。
- **使用准则**: 当家长以贬损的语言或质疑的态度直接否定孩子的能力时使用。这类行为通常表现为不信任孩子的学习能力或对其表现表达强烈不满。
- **示例**:  
  - 家长："你怎么这么笨，连最简单的加法都不会算？"    
  - 家长："就你这成绩，肯定考不上好学校。"  

#### 17. **沮丧失望 (FD)**
- **代码定义**: 家长因孩子的表现不符合期望而表现出失望或沮丧情绪，通常伴有负面情感的表达。
- **使用准则**: 当家长因孩子的学习成绩或进步不如预期而表现出失望情绪时使用。
- **示例**:  
  - 家长："我真没想到你会考这么差，太让我失望了。"
  - 家长："我原本以为你能做得更好，看来是我想多了。"

#### 18. **急躁不耐 (II)**
- **代码定义**: 家长因孩子的表现不如预期而表现出急躁或不耐烦的情绪，可能伴随较为负面的言语或行为。
- **使用准则**: 当家长对孩子的学习速度或表现感到不耐烦或急躁时使用。
- **示例**:  
  - 家长："你怎么这么慢！我都等了半天了！"
  - 家长："怎么还没写完？每次都这么拖拉！"

# 输入格式
输入是一个包含音频片段的字典列表，每个字典包含：
- 'id': 片段的标识符
- 'speaker': 说话者的角色（家长、孩子或其他）
- 'content': 片段的对话内容

# 输出格式
输出为JSON格式，包含以下字段:

- behaviour_id: 行为ID，整数类型
- Description of behavior: 用中文描述行为，字符串类型
- code: 行为代码，字符串类型，如"鼓励 (ENC)"、"启发式指导 (GI)"等
- type: 行为类型，字符串类型，可选值为"积极"、"中性"、"消极"
- dt: 日期时间，字符串类型，格式为"YYYYMMDD"
以下是部分输出示例：
    {
        "scenes": [
            {
        "behaviour_id": 1,
        "Description of behavior": "家长对孩子的数学表现给予了明确的积极反馈。",
        "code": "有标注表扬 (SP)",
        "type": "积极",
        "dt": "20241212"
    },
    {
        "behaviour_id": 2,
        "Description of behavior": "家长通过言语或行为积极支持孩子的努力和进步。",
        "code": "鼓励 (ENC)",
        "type": "积极",
        "dt": "20241212"
    },
    {
        "behaviour_id": 3,
        "Description of behavior": "家长通过提问或提供线索，引导孩子独立思考和解决问题。",
        "code": "启发式指导 (GI)",
        "type": "积极",
        "dt": "20241212"
    },
    {
        "behaviour_id": 4,
        "Description of behavior": "家长为孩子完成作业设立明确的规则或要求。",
        "code": "设定规则 (SR)",
        "type": "中性",
        "dt": "20241212"
    },
    {
        "behaviour_id": 5,
        "Description of behavior": "家长直接告诉孩子如何完成任务或解答问题。",
        "code": "非启发式指导 (DI)",
        "type": "中性",
        "dt": "20241212"
    },
            ... [更多场景，根据输入对话内容细分] ...
        ]
    }
输出应严格按照以下格式返回，用```json```包裹：
    """

    def analyze_behavior(self, transcripts: List[dict], date: str) -> BehaviorAnalysisOutput:
        # 计算输入token数量
        encoding = tiktoken.encoding_for_model("gpt-4o")
        input_text = str(transcripts) + f"日期：{date}"
        input_tokens = len(encoding.encode(input_text))
        prompt_tokens = len(encoding.encode(self.prompt_behavior_analysis))
        total_input_tokens = input_tokens + prompt_tokens
        
        print(f"Input tokens: {input_tokens}")
        print(f"Prompt tokens: {prompt_tokens}")
        print(f"Total input tokens: {total_input_tokens}")
        
        # 构造系统提示词（简化）
        system_prompt = (
            "你是一个结构化数据生成器。请根据以下指南分析家长行为，并生成符合指定格式的JSON输出。"
        )
        
        # 明确指定输出格式
        output_format = """
        确保输出格式严格符合以下结构：
        {
            "scenes": [
                {
                    "behaviour_id": 整数,
                    "description": "行为描述文本",
                    "code": "行为代码",
                    "type": "行为类型",
                    "dt": "日期"
                },
                ...
            ]
        }
        
        注意事项：
        1. code字段必须是以下值之一（不要包含括号中的代码）: 鼓励、有标注表扬、无标注表扬、启发式指导、设定规则、敏感性回应、非启发式指导、信息教授、纠正错误、监督检查、直接命令、间接命令、批评责备、强迫威胁、忽视冷漠、贬低质疑、沮丧失望、急躁不耐
        2. type字段必须是以下值之一: 积极、中性、消极
        3. description字段用于描述家长的具体行为
        """
        
        try:
            response = deepseek_v3_prompt(
                prompt=system_prompt + "\n" + output_format,
                input_data=self.prompt_behavior_analysis + "\n\n" + input_text
            )
            
            # 检查响应
            if response is None:
                print("API调用失败，无法获取有效响应")
                return BehaviorAnalysisOutput(scenes=[])
            
            # 解析并修正JSON响应
            try:
                # 提取JSON内容
                if "```json" in response:
                    json_content = response.split("```json")[1].split("```")[0].strip()
                    raw_data = json.loads(json_content)
                else:
                    raw_data = json.loads(response)
                
                # 如果返回的是列表而不是字典，进行转换
                if isinstance(raw_data, list):
                    raw_data = {"scenes": raw_data}
                
                # 修正字段名称和值
                if "scenes" in raw_data:
                    for scene in raw_data["scenes"]:
                        # 修正description字段
                        if "Description of behavior" in scene and "description" not in scene:
                            scene["description"] = scene.pop("Description of behavior")
                        
                        # 修正code字段（去掉括号部分）
                        if "code" in scene and " (" in scene["code"]:
                            scene["code"] = scene["code"].split(" (")[0]
                        
                        # 确保dt字段存在
                        if "dt" not in scene or not scene["dt"]:
                            scene["dt"] = date
                
                # 验证和返回
                analysis_output = BehaviorAnalysisOutput.parse_obj(raw_data)
                return analysis_output
                
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                print(f"原始响应: {response[:200]}...")
                return BehaviorAnalysisOutput(scenes=[])
                
            except Exception as e:
                print(f"处理行为分析结果时发生错误: {e}")
                print(f"原始数据: {raw_data}")
                return BehaviorAnalysisOutput(scenes=[])
                
        except Exception as e:
            print(f"处理行为分析时发生错误: {e}")
            return BehaviorAnalysisOutput(scenes=[])


'''
def generate_intervent_strategy(scene, user_profile, knowledge):
    intervent_strategy_prompt = f"""
你是一名心理咨询和干预专家，你的任务是根据家庭的内在属性，包括家长和孩子的固有品质、人格特质、教育背景和认知能力，以及一段家长辅导孩子写作业的对话内容，为这个家长提供有效的教育行为干预策略。

家庭的内在属性，包括家长和孩子的固有品质、人格特质、教育背景和认知能力：
{user_profile}

父母在辅导孩子写家庭作业期间的行为情境和对话内容：
{scene}

这是一些相似情景下的解决方案，你制定干预策略的时候可以借鉴它们：
{knowledge}

请你以心理咨询师的身份对家长进行教育策略干预，具体步骤如下：

1. **共情**：首先对家长表示共情，理解他们的付出和心情，你在共情时可以使用更温暖、更个人化的语言，让家长感受到更真实的关怀和支持。
2. **表扬**：挑出家长在本次作业辅导中做得好的三个方面，你的赞扬和支持要根据家长辅导孩子的对话细节落实到实处，不能只是笼统地夸奖家长。
3. **情绪抚慰**：对家长进行情绪抚慰，并举一些和家长处境类似的例子，你举的例子要尽量详细点，从而更好地触动家长。
4. **问题指出**：明确指出家长在辅导过程中的问题，结合家长和孩子的画像以及当前场景提供具体且全面的建议。
5. **再次共情和系统性干预询问**：再次表示共情，并询问家长是否需要系统性干预方案。

你的输出将是一封写给家长的信，内容应详细且直接针对家长。为了增加家长的共鸣感，你的干预策略中应该加入对家长辅导孩子过程中的对话细节的分析，这些分析需依据心理学和教育学理论，做到详尽且完善。
"""

    generate_intervent_strategy = gpt_prompt_without_data(intervent_strategy_prompt)
    return generate_intervent_strategy
'''
