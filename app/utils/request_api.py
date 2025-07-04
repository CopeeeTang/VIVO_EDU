# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import json
import os
import time
import urllib
import requests
import pandas as pd
from pydub import AudioSegment
import logging
import tiktoken
from openai import OpenAI
import asyncio
import aiohttp

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 配置常量
LFASR_HOST = 'https://raasr.xfyun.cn/v2/api'
API_UPLOAD = '/upload'
API_GET_RESULT = '/getResult'
ROLE_TYPE = 1


class RequestApi:
    """
    处理与API交互的类，包括上传文件和获取结果。
    """

    def __init__(self, appid, secret_key, upload_file_path):
        self.appid = appid
        self.secret_key = secret_key
        self.upload_file_path = upload_file_path
        self.ts = str(int(time.time()))
        self.signa = self.get_signa()
        logging.debug(f"初始化 RequestApi: appid={appid}, upload_file_path={upload_file_path}")

    def get_signa(self):
        """
        生成签名。
        """
        md5_hash = hashlib.md5((self.appid + self.ts).encode('utf-8')).hexdigest()
        md5_bytes = md5_hash.encode('utf-8')
        signa = hmac.new(self.secret_key.encode('utf-8'), md5_bytes, hashlib.sha1).digest()
        signa_b64 = base64.b64encode(signa).decode('utf-8')
        logging.debug(f"生成签名: {signa_b64}")
        return signa_b64

    def upload(self):
        """
        上传文件到API。
        """
        file_size = os.path.getsize(self.upload_file_path)
        file_name = os.path.basename(self.upload_file_path)

        params = {
            'appId': self.appid,
            'signa': self.signa,
            'ts': self.ts,
            'fileSize': file_size,
            'fileName': file_name,
            'duration': "200",
            'roleType': ROLE_TYPE
        }

        with open(self.upload_file_path, 'rb') as f:
            data = f.read()

        response = requests.post(
            url=f"{LFASR_HOST}{API_UPLOAD}?{urllib.parse.urlencode(params)}",
            headers={"Content-type": "application/json"},
            data=data
        )
        logging.debug(f"上传URL: {response.request.url}")
        logging.debug(f"上传响应: {response.text}")
        return response.json()

    def get_result(self):
        """
        获取转写结果。
        """
        upload_response = self.upload()
        order_id = upload_response['content']['orderId']
        params = {
            'appId': self.appid,
            'signa': self.signa,
            'ts': self.ts,
            'orderId': order_id,
            'resultType': "transfer,predict"
        }

        status = 3  # 初始状态
        while status == 3:
            response = requests.post(
                url=f"{LFASR_HOST}{API_GET_RESULT}?{urllib.parse.urlencode(params)}",
                headers={"Content-type": "application/json"}
            )
            result = response.json()
            status = result['content']['orderInfo']['status']
            logging.debug(f"获取结果状态: {status}")
            if status == 4:
                break
            time.sleep(5)
        return result

def transcribe_file(file_path, api_details):
    """
    转写单个文件并获取结果。
    """
    logging.info(f"开始转写文件: {file_path}")
    api = RequestApi(
        appid=api_details['appid'],
        secret_key=api_details['secret_key'],
        upload_file_path=file_path
    )
    try:
        result = api.get_result()
        logging.debug(f"转写结果: {result}")
        return result
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

def combine_rows(df):
    """
    根据阈值合并相邻的相同说话人内容。
    """
    logging.info("开始合并行")
    MERGE_THRESHOLD = 1  # 秒
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
***Task Description***
Identify the roles of speakers in parent-child conversations during parental homework involvement scenarios using provided audio segments. Due to potential inaccuracies in speaker identification from the audio API, roles must be inferred from chat content. Speakers can be labeled as 'parent', 'child', or 'others'. When only two speakers are identified, they are labeled as 'parent' and 'child'. For cases with more speakers, determine if they share roles or if the recording includes additional speakers. 'Others' may occur when music or learning material audio is detected during homework sessions, resulting in a new speaker recognition.

***Input Format***
A list of dictionaries, where each dictionary represents an audio segment and includes the following keys:

"speaker": String representing the speaker's name
"start_time": String indicating the start time of the segment
"end_time": String indicating the end time of the segment
"content": String containing the segment's content

***Output Format***
A dictionary mapping speaker names to their roles. Must return the dictionary in JSON format.

***Example***
<Input>
[
    {
        "speaker": "Speaker 1",
        "start_time": "00:00:15.620000",
        "end_time": "00:00:25.390000",
        "content": "你能帮帮我解决数学题吗?"
    },
    {
        "speaker": "Speaker 2",
        "start_time": "00:00:26.150000",
        "end_time": "00:00:35.940000",
        "content": "好，什么数学题?"
    },
    {
        "speaker": "Speaker 1",
        "start_time": "00:00:37.520000",
        "end_time": "00:00:48.970000",
        "content": "这个数学题是关于除法算式，我被难住了"
    }
]
</Input>

<Output>
{
    "Speaker 1": "parent",
    "Speaker 2": "child"
}
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

def transcribe_audio(file_path: str, api_details: dict, api_key: str) -> str:
    """
    完整的转写和角色分配流程。
    返回最终的JSON结果。
    """
    logging.info(f"开始转写音频文件: {file_path}")
    # 转写文件
    transcription_result = transcribe_file(file_path, api_details)
    if not transcription_result:
        logging.warning("转写失败，返回空JSON")
        return json.dumps({}, ensure_ascii=False, indent=4)

    # 处理转写结果
    processed_data = process_json(json.loads(transcription_result['content']['orderResult']))
    df = pd.DataFrame(processed_data, columns=['speaker', 'start_time', 'end_time', 'content'])
    combined_df = combine_rows(df)
    combined_df['start_time'] = pd.to_datetime(combined_df['start_time'], format="%H:%M:%S,%f").dt.strftime('%H:%M:%S.%f')
    combined_df['end_time'] = pd.to_datetime(combined_df['end_time'], format="%H:%M:%S,%f").dt.strftime('%H:%M:%S.%f')
    

    # 转换为JSON
    data_json = json.dumps(combined_df.to_dict(orient='records'), ensure_ascii=False)
    
    # 分配角色
    final_json = assign_roles(data_json, api_key)
    logging.info("转写和角色分配完成")
    return final_json

def process_audio(audio_file_path: str) -> dict:
    """
    处理音频文件并返回最终的JSON结果。

    参数:
    audio_file_path (str): 音频文件的路径
    api_details (dict): 包含API详细信息的字典

    返回:
    str: 包含转写和角色分配结果的JSON字符串
    """
    api_details = {
        'appid': "7492a3df",
        'secret_key': "730875415ad62b813b0799bd1ae73c14",
        'api_key': os.environ.get('OPENAI_API_KEY'),
    }
    logging.info(f"开始处理音频文件: {audio_file_path}")
    
    try:
        final_json = transcribe_audio(audio_file_path, api_details, api_details['api_key'])
        logging.info("音频处理完成")
        return final_json
    except Exception as e:
        logging.error(f"处理音频文件时发生错误: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=4)

async def process_audio_async(audio_file_path: str) -> dict:
    """
    异步处理音频文件并返回最终的JSON结果。

    参数:
    audio_file_path (str): 音频文件的路径

    返回:
    dict: 包含转写和角色分配结果的JSON字典
    """
    api_details = {
        'appid': "7492a3df",
        'secret_key': "730875415ad62b813b0799bd1ae73c14" ,
        'api_key': os.environ.get('OPENAI_API_KEY'),
    }
    logging.info(f"开始异步处理音频文件: {audio_file_path}")

    try:
        # 异步转写文件
        transcription_result = await asyncio.get_event_loop().run_in_executor(
            None, transcribe_file, audio_file_path, api_details
        )
        if not transcription_result:
            logging.warning("转写失败，返回空JSON")
            return {}

        # 处理转写结果
        processed_data = process_json(json.loads(transcription_result['content']['orderResult']))
        df = pd.DataFrame(processed_data, columns=['speaker', 'start_time', 'end_time', 'content'])
        combined_df = combine_rows(df)
        combined_df['start_time'] = pd.to_datetime(combined_df['start_time'], format="%H:%M:%S,%f").dt.strftime('%H:%M:%S.%f')
        combined_df['end_time'] = pd.to_datetime(combined_df['end_time'], format="%H:%M:%S,%f").dt.strftime('%H:%M:%S.%f')

        # 转换为JSON
        data_json = json.dumps(combined_df.to_dict(orient='records'), ensure_ascii=False)

        # 分配角色
        final_json = await asyncio.get_event_loop().run_in_executor(
            None, assign_roles, data_json, api_details['api_key']
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




