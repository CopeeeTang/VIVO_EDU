import os
import pickle
from langchain_community.vectorstores import FAISS

import aiofiles
import aiohttp
import os
from langchain_openai import OpenAIEmbeddings,AzureOpenAIEmbeddings,AzureChatOpenAI


def upload_to_storage(file_id, file_name):
    upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads/')
    os.makedirs(upload_folder, exist_ok=True)
    filename = f"{file_id}_{file_name}"
    file_path = os.path.join(upload_folder, filename)
    # 在预签名URL上传的情况下，这里不需要具体实现
    # 如果直接上传到本地，可以返回file_path
    return file_path

def download_from_storage(file_path):
    # 如果文件存储在本地，直接返回路径
    if os.path.exists(file_path):
        return file_path
    else:
        raise FileNotFoundError("文件不存在")
async def download_from_storage_async(file_path):
    # 如果文件存储在本地，直接返回路径
    if os.path.exists(file_path):  # 改用同步的 os.path.exists
        return file_path
    else:
        raise FileNotFoundError("文件不存在")


def delete_from_storage(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file {file_path}: {str(e)}")
        return False
    
async def load_documents_from_storage_async(pdf_storage_path) -> FAISS:
    try:
        async with aiofiles.open(pdf_storage_path, 'rb') as f:
            content = await f.read()
            docs = pickle.loads(content)
        print(f"Loaded documents from Existing path")
        return docs
    except FileNotFoundError:
        print(f"Documents storage file not found.")
        return None
    except Exception as e:
        print(f"Error loading documents: {e}")
        return None

