# -*- coding: utf-8 -*-
import json
import os
import time
import pandas as pd
from pydub import AudioSegment
import logging
import tiktoken
from openai import OpenAI
import asyncio
import aiohttp
from .vivo_audio_client import create_vivo_audio_client

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def transcribe_file(file_path, api_details=None):
    """
    使用vivo API转写单个文件并获取结果。
    """
    logging.info(f"开始转写文件: {file_path}")
    
    try:
        # 创建vivo音频客户端
        vivo_client = create_vivo_audio_client()
        
        # 获取音频文件类型
        file_extension = os.path.splitext(file_path)[1].lower()
        audio_type_map = {
            '.wav': 'auto',
            '.mp3': 'auto',
            '.m4a': 'auto',
            '.aac': 'auto',
            '.ogg': 'auto',
            '.pcm': 'pcm'
        }
        audio_type = audio_type_map.get(file_extension, 'auto')
        
        # 使用vivo API进行转写
        result = vivo_client.transcribe_file(file_path, audio_type)
        
        # 将vivo结果转换为原有格式
        converted_result = {
            'content': {
                'orderResult': json.dumps(result)
            }
        }
        
        logging.debug(f"转写结果: {converted_result}")
        return converted_result
        
    except Exception as e:
        logging.error(f"转写过程中发生错误: {e}")
        return None

def format_time(ms):
    hours = ms // 3600000
    ms = ms % 3600000
    minutes = ms // 60000
    ms = ms % 60000
    seconds = ms // 1000
    milliseconds = ms % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def process_json(json_data):
    """处理原有的JSON数据格式（保留用于兼容）"""
    logging.info("开始处理JSON数据")
    result = []

    data = json_data

    for lattice_entry in data["lattice"]:
        lattice_data = json.loads(lattice_entry["json_1best"])
        speaker_id = int(lattice_data["st"]["rl"]) - 1  # Adjust for 0-indexed list
        speaker = f"Speaker {speaker_id + 1}"
        start_time = int(lattice_data["st"]["bg"])
        end_time = int(lattice_data["st"]["ed"])
        text = ""
        for segment in lattice_data["st"]["rt"]:
            for word_segment in segment["ws"]:
                for word_candidate in word_segment["cw"]:
                    text += word_candidate["w"]
        result.append([speaker, format_time(start_time), format_time(end_time), text])

    logging.debug(f"处理后的JSON数据: {result}")
    return result

def process_vivo_result(vivo_data):
    """处理vivo API返回的结果格式"""
    logging.info("开始处理vivo转写结果")
    logging.info(f"原始vivo数据结构: {json.dumps(vivo_data, ensure_ascii=False, indent=2)}")
    result = []
    
    try:
        # 检查vivo API返回的不同可能格式
        # 格式1: 包含segments字段
        segments = vivo_data.get('segments', [])
        if segments:
            logging.info(f"找到segments字段，包含{len(segments)}个片段")
            for i, segment in enumerate(segments):
                speaker_id = segment.get('speaker_id', 0)
                speaker = f"Speaker {speaker_id + 1}"
                
                start_time_ms = segment.get('start_time', 0)
                end_time_ms = segment.get('end_time', 0)
                start_time = format_time(start_time_ms)
                end_time = format_time(end_time_ms)
                
                text = segment.get('text', '').strip()
                if text:
                    result.append([speaker, start_time, end_time, text])
            
            logging.info(f"从segments提取到{len(result)}条数据")
            return result
        
        # 格式2: 包含sentences字段
        sentences = vivo_data.get('sentences', [])
        if sentences:
            logging.info(f"找到sentences字段，包含{len(sentences)}个句子")
            for i, sentence in enumerate(sentences):
                speaker_id = sentence.get('speaker_id', 0)
                speaker = f"Speaker {speaker_id + 1}"
                
                start_time_ms = sentence.get('begin_time', sentence.get('start_time', 0))
                end_time_ms = sentence.get('end_time', sentence.get('finish_time', 0))
                start_time = format_time(start_time_ms)
                end_time = format_time(end_time_ms)
                
                text = sentence.get('text', sentence.get('sentence', '')).strip()
                if text:
                    result.append([speaker, start_time, end_time, text])
            
            logging.info(f"从sentences提取到{len(result)}条数据")
            return result
        
        # 格式3: 包含result字段（vivo API格式）
        if 'result' in vivo_data:
            result_data = vivo_data['result']
            logging.info(f"找到result字段: {result_data}")
            
            # 如果result是列表
            if isinstance(result_data, list):
                for i, item in enumerate(result_data):
                    if isinstance(item, dict):
                        # vivo API格式：使用bg、ed、onebest、speaker字段
                        if 'onebest' in item:
                            text = item.get('onebest', '').strip()
                            if text:  # 过滤空文本
                                start_time_ms = item.get('bg', 0)
                                end_time_ms = item.get('ed', 0)
                                start_time = format_time(start_time_ms)
                                end_time = format_time(end_time_ms)
                                
                                # 正确利用speaker字段
                                speaker_id = item.get('speaker', 1)  # 默认为1
                                speaker = f"Speaker {speaker_id}"
                                
                                result.append([speaker, start_time, end_time, text])
                        else:
                            # 通用格式
                            text = item.get('text', item.get('sentence', '')).strip()
                            if text:
                                speaker_id = item.get('speaker', item.get('speaker_id', 1))
                                speaker = f"Speaker {speaker_id}"
                                result.append([speaker, "00:00:00,000", "00:00:00,000", text])
            # 如果result是字符串
            elif isinstance(result_data, str) and result_data.strip():
                result.append([f"Speaker 1", "00:00:00,000", "00:00:00,000", result_data.strip()])
            
            logging.info(f"从result提取到{len(result)}条数据")
            return result
        
        # 格式4: 直接包含text字段
        if 'text' in vivo_data:
            text = vivo_data['text'].strip()
            if text:
                result.append([f"Speaker 1", "00:00:00,000", "00:00:00,000", text])
                logging.info(f"从text字段提取到1条数据")
                return result
        
        # 格式5: lattice格式（兼容旧格式）
        if 'lattice' in vivo_data:
            logging.info("检测到lattice格式，使用旧处理方式")
            return process_json(vivo_data)
        
        # 如果都没有找到，尝试直接解析为文本
        if isinstance(vivo_data, str) and vivo_data.strip():
            result.append([f"Speaker 1", "00:00:00,000", "00:00:00,000", vivo_data.strip()])
            logging.info("将整个数据作为文本处理")
            return result
        
        # 遍历所有键值，查找可能的文本内容
        logging.warning("未识别的数据格式，尝试提取所有文本内容")
        for key, value in vivo_data.items():
            if isinstance(value, str) and value.strip() and len(value) > 10:
                result.append([f"Speaker 1", "00:00:00,000", "00:00:00,000", value.strip()])
                logging.info(f"从字段{key}提取到文本")
        
        if result:
            logging.info(f"通过遍历提取到{len(result)}条数据")
            return result
            
    except Exception as e:
        logging.error(f"处理vivo结果时发生错误: {e}")
    
    logging.warning("无法从vivo数据中提取有效内容")
    return result

def combine_rows(df):
    """
    根据阈值合并相邻的相同说话人内容。
    """
    logging.info("开始合并行")
    MERGE_THRESHOLD = 5  # 增加到5秒，减少过度合并
    combined = []
    df['start_time'] = pd.to_datetime(df['start_time'], format="%H:%M:%S,%f")
    df['end_time'] = pd.to_datetime(df['end_time'], format="%H:%M:%S,%f")
    current_speaker = None
    current_start = None
    current_end = None
    current_content = ""

    for _, row in df.iterrows():
        if current_speaker == row['speaker']:
            time_diff = (row['start_time'] - current_end).total_seconds()
            if time_diff <= MERGE_THRESHOLD:
                # 合并内容并更新结束时间
                current_content += " " + row['content']
                current_end = row['end_time']
            else:
                # 保存当前合并内容并重置
                combined.append({
                    'speaker': current_speaker,
                    'start_time': current_start,
                    'end_time': current_end,
                    'content': current_content
                })
                current_start = row['start_time']
                current_end = row['end_time']
                current_content = row['content']
        else:
            if current_content:
                combined.append({
                    'speaker': current_speaker,
                    'start_time': current_start,
                    'end_time': current_end,
                    'content': current_content
                })
            current_speaker = row['speaker']
            current_start = row['start_time']
            current_end = row['end_time']
            current_content = row['content']

    # 添加最后一条记录
    if current_content:
        combined.append({
            'speaker': current_speaker,
            'start_time': current_start,
            'end_time': current_end,
            'content': current_content
        })

    logging.debug(f"合并后的行数: {len(combined)}")
    return pd.DataFrame(combined)

def load_transcribed_files(progress_file_path: str) -> list:
    """
    加载已转写的文件列表。
    """
    logging.info(f"加载已转写的文件列表: {progress_file_path}")
    try:
        with open(progress_file_path, 'r') as f:
            files = f.read().splitlines()
        logging.debug(f"已加载 {len(files)} 个文件")
        return files
    except FileNotFoundError:
        logging.warning(f"未找到进度文件: {progress_file_path}")
        return []

def transcribe_audio_files(directory: str, results_dir: str, transcribed: list, api_details: dict, progress_file: str):
    """
    遍历目录中的音频文件，进行转写并保存结果。
    """
    logging.info(f"开始转写目录中的音频文件: {directory}")
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if filename not in transcribed:
            logging.info(f"正在转写文件: {filename}")
            audio = AudioSegment.from_file(file_path)
            duration_minutes = len(audio) / (1000 * 60)
            logging.debug(f"文件 {filename} 时长: {duration_minutes:.2f} 分钟")
            result = transcribe_file(file_path, api_details)
            if result:
                save_transcription_result(filename, result, results_dir)
                record_transcribed_file(filename, progress_file)
            else:
                logging.error("由于错误停止。请检查您的API余额。")
                break

def save_transcription_result(filename: str, result: dict, results_dir: str):
    """
    保存转写结果到JSON文件。
    """
    result_file_path = os.path.join(results_dir, f"{os.path.splitext(filename)[0]}.json")
    logging.info(f"保存结果到文件: {result_file_path}")
    with open(result_file_path, 'w', encoding='utf-8') as rf:
        json.dump(result, rf, ensure_ascii=False, indent=4)

def record_transcribed_file(filename: str, progress_file: str):
    """
    记录已完成转写的文件。
    """
    logging.info(f"记录已完成转写的文件: {filename}")
    with open(progress_file, 'a') as f:
        f.write(f"{filename}\n")

def process_transcription_results(input_file: str, csv_path: str, json_path: str):
    """
    处理转写结果，生成CSV和JSON文件。
    """
    logging.info(f"处理转写结果: {input_file}")
    with open(input_file, 'r') as file:
        result = json.load(file)

    data = result['content']['orderResult']
    output = process_json(data)
    df = pd.DataFrame(output, columns=['speaker', 'start_time', 'end_time', 'content'])
    df.to_csv(csv_path, index=False)
    logging.debug(f"保存CSV文件: {csv_path}")

    df = pd.read_csv(csv_path)
    logging.debug(f"数据形状: {df.shape}")
    logging.debug(f"数据头部:\n{df.head(20)}")

    # 合并数据
    combined_df = combine_rows(df)

    combined_df['start_time'] = combined_df['start_time'].dt.strftime('%H:%M:%S.%f')
    combined_df['end_time'] = combined_df['end_time'].dt.strftime('%H:%M:%S.%f')
    logging.debug(f"合并后数据头部:\n{combined_df.head(20)}")

    # 转换为JSON格式并保存
    data_json = combined_df.to_json(orient='records', force_ascii=False)
    parsed_json = json.loads(data_json)
    pretty_json = json.dumps(parsed_json, indent=4, ensure_ascii=False)
    with open(json_path, "w", encoding='utf-8') as outfile:
        outfile.write(pretty_json)
    logging.info(f"保存JSON文件: {json_path}")

def conflict_extraction(data_json: str)->dict:
    return None

def assign_roles(data_json: str, api_key: str) -> dict:
    """
    根据对话内容为讲话者分配角色。
    """
    logging.info("开始分配角色")
    prompt = """
***任务说明***
根据家庭作业辅导场景中的亲子对话内容，为说话者分配角色。需要分析对话内容来推断角色，因为音频API的说话人识别可能不准确。

说话者可以标记为 'parent'（家长）、'child'（孩子）或 'others'（其他）。当只识别到两个说话者时，通常为家长和孩子。

***角色识别指南***
**家长特征：**
- 使用指导性语言："你应该..."、"记住..."、"我们来..."
- 表现出教育责任：检查作业、设定规则、监督学习
- 使用成熟词汇和完整句式
- 表达期望和要求："写完作业"、"认真点"、"时间到了"
- 给出指令和建议
- 表现出关心和督促

**孩子特征：**
- 使用简单直接的语言
- 表达需求或抱怨："我不想..."、"太难了"、"我做不来"
- 回应家长的指令
- 表现出学习中的困惑或抵触
- 使用较为随意的表达方式
- 可能出现撒娇、讨价还价的语气

**Others情况：**
- 学习音频或背景音乐被识别为新说话者
- 明显不是家长或孩子的声音

***输入格式***
包含以下字段的字典列表：
"speaker"：说话者名称（如"Speaker 1"）
"start_time"：开始时间
"end_time"：结束时间  
"content"：对话内容

***输出格式***
必须返回JSON格式的字典，将说话者名称映射到角色。

***示例***
<输入>
[
    {
        "speaker": "Speaker 1",
        "start_time": "00:00:15.620000",
        "end_time": "00:00:25.390000",
        "content": "开始写作业了啊，我不想要这个。"
    },
    {
        "speaker": "Speaker 2", 
        "start_time": "00:00:26.150000",
        "end_time": "00:00:35.940000",
        "content": "快点，你就开机时，我没计时啊，你刚才说一杯开始。"
    },
    {
        "speaker": "Speaker 1",
        "start_time": "00:00:37.520000", 
        "end_time": "00:00:48.970000",
        "content": "我招你啥啦，这是什么啊，别玩别的啦。"
    }
]
</输入>

<输出>
{
    "Speaker 1": "child",
    "Speaker 2": "parent"
}
</输出>

请仔细分析对话内容中的语气、用词、表达方式和互动模式来准确识别角色。
"""

    # 初始化 OpenAI API 客户端
    from openai import OpenAI

    # 尝试使用智增增客户端
    try:
        client = OpenAI(
            api_key=os.environ.get('ZHIZENGZENG_API_KEY'),
            base_url="https://api.zhizengzeng.com/v1"
        )

        # 调用智增增 API 生成输出
        logging.debug(f"调用智增增 API，输入数据: {data_json[:100]}...")
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": data_json},
            ]
        )

        # 从响应中提取生成的输出
        output_roles = response.choices[0].message.content.strip()
        logging.debug(f"智增增 API 响应: {output_roles}")

    except Exception as e:
        logging.warning(f"智增增 API 调用失败,使用备用 API: {str(e)}")
        # 使用备用 API
        client = OpenAI(base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key)
        
        # 调用备用 API 生成输出
        logging.debug(f"调用备用 API，输入数据: {data_json[:100]}...")
        response = client.chat.completions.create(
            model="ep-20250331105849-cbfg5",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": data_json},
            ]
        )
        output_roles = response.choices[0].message.content.strip()
        logging.debug(f"备用 API 响应: {output_roles}")

    try:
        # 提取JSON内容
        json_start = output_roles.find('{')
        json_end = output_roles.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("无法在API响应中找到有效的JSON")
        
        json_content = output_roles[json_start:json_end]
        roles = json.loads(json_content)

        # 将输入的 JSON 字符串解析为 Python 对象
        data = json.loads(data_json)
        
        # 应用角色映射并创建新的列表，添加id索引
        result = []
        for index, item in enumerate(data):
            new_item = {
                'id': index,
                'speaker': roles.get(item['speaker'], 'unknown'),
                'start_time': item['start_time'],
                'end_time': item['end_time'],
                'content': item['content']
            }
            result.append(new_item)

        logging.info("角色分配完成")
        return result
    except Exception as e:
        logging.error(f"角色分配过程中发生错误: {str(e)}")
        raise

# GPT4: cl100k_base; GPT-4o: o200k_base
def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def transcribe_audio(file_path: str) -> dict:
    """
    完整的转写和角色分配流程。
    返回最终的JSON结果。
    """
    logging.info(f"开始转写音频文件: {file_path}")
    
    # 转写文件
    transcription_result = transcribe_file(file_path)
    if not transcription_result:
        logging.warning("转写失败，返回空结果")
        return {}

    # 处理转写结果 - 适配vivo API格式
    try:
        order_result = transcription_result['content']['orderResult']
        if isinstance(order_result, str):
            processed_data = process_vivo_result(json.loads(order_result))
        else:
            processed_data = process_vivo_result(order_result)
    except Exception as e:
        logging.warning(f"处理vivo结果失败，尝试旧格式: {e}")
        processed_data = process_json(json.loads(transcription_result['content']['orderResult']))
    
    # 如果没有处理出数据，返回空结果
    if not processed_data:
        logging.warning("没有处理出有效的转写数据")
        return {}
    
    df = pd.DataFrame(processed_data, columns=['speaker', 'start_time', 'end_time', 'content'])
    combined_df = combine_rows(df)
    combined_df['start_time'] = pd.to_datetime(combined_df['start_time'], format="%H:%M:%S,%f").dt.strftime('%H:%M:%S.%f')
    combined_df['end_time'] = pd.to_datetime(combined_df['end_time'], format="%H:%M:%S,%f").dt.strftime('%H:%M:%S.%f')
    
    # 转换为JSON
    data_json = json.dumps(combined_df.to_dict(orient='records'), ensure_ascii=False)
    
    # 分配角色
    api_key = os.environ.get('OPENAI_API_KEY')
    final_json = assign_roles(data_json, api_key)
    logging.info("转写和角色分配完成")
    return final_json

def process_audio(audio_file_path: str) -> dict:
    """
    处理音频文件并返回最终的JSON结果。

    参数:
    audio_file_path (str): 音频文件的路径

    返回:
    dict: 包含转写和角色分配结果的JSON结果
    """
    logging.info(f"开始处理音频文件: {audio_file_path}")
    
    try:
        final_json = transcribe_audio(audio_file_path)
        logging.info("音频处理完成")
        return final_json
    except Exception as e:
        logging.error(f"处理音频文件时发生错误: {e}")
        return {"error": str(e)}

async def process_audio_async(audio_file_path: str) -> dict:
    """
    异步处理音频文件并返回最终的JSON结果。

    参数:
    audio_file_path (str): 音频文件的路径

    返回:
    dict: 包含转写和角色分配结果的JSON字典
    """
    logging.info(f"开始异步处理音频文件: {audio_file_path}")

    try:
        # 异步转写文件
        transcription_result = await asyncio.get_event_loop().run_in_executor(
            None, transcribe_file, audio_file_path
        )
        if not transcription_result:
            logging.warning("转写失败，返回空JSON")
            return {}

        # 处理转写结果 - 注意vivo API返回的格式可能不同
        try:
            # 尝试解析vivo API的结果
            order_result = transcription_result['content']['orderResult']
            if isinstance(order_result, str):
                processed_data = process_vivo_result(json.loads(order_result))
            else:
                processed_data = process_vivo_result(order_result)
        except Exception as e:
            logging.warning(f"处理vivo结果失败，尝试旧格式: {e}")
            processed_data = process_json(json.loads(transcription_result['content']['orderResult']))
        
        df = pd.DataFrame(processed_data, columns=['speaker', 'start_time', 'end_time', 'content'])
        combined_df = combine_rows(df)
        combined_df['start_time'] = pd.to_datetime(combined_df['start_time'], format="%H:%M:%S,%f").dt.strftime('%H:%M:%S.%f')
        combined_df['end_time'] = pd.to_datetime(combined_df['end_time'], format="%H:%M:%S,%f").dt.strftime('%H:%M:%S.%f')

        # 转换为JSON
        data_json = json.dumps(combined_df.to_dict(orient='records'), ensure_ascii=False)

        # 分配角色
        api_key = os.environ.get('OPENAI_API_KEY')
        final_json = await asyncio.get_event_loop().run_in_executor(
            None, assign_roles, data_json, api_key
        )
        logging.info("异步转写和角色分配完成")
        return final_json
    except Exception as e:
        logging.error(f"异步处理音频文件时发生错误: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    logging.info("程序开始执行")
    
    # 示例使用
    audio_file_path = 'uploads/spli.m4a'
    api_details = {
        'appid': "50017301",
        'secret_key': "154d69165ad6245b3a02f43dd4eb57b5",
        'api_key': os.environ.get('OPENAI_API_KEY')
    }
    result = process_audio(audio_file_path)
    print(result)
    
    logging.info("程序执行结束")




