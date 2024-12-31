import dashscope
import requests
from decouple import config

# 设置 DashScope API key
dashscope.api_key = config('DASHSCOPE_API_KEY')

def recognize_audio(audio_url):
    """
    通过 Paraformer 语音识别模型进行音频转录，并返回转录的 JSON 数据。
    """
    try:
        print("[INFO] Submitting audio transcription task...")
        # 提交音频转录任务
        task_response = dashscope.audio.asr.Transcription.async_call(
            model='paraformer-v2',
            file_urls=[audio_url],
            language_hints=['zh', 'en']  # 设置语种
        )

        # 查询任务的转录结果
        print("[INFO] Waiting for transcription result...")
        transcribe_response = dashscope.audio.asr.Transcription.wait(task=task_response.output.task_id)
        if transcribe_response.status_code == 200:
            print("[INFO] Transcription task succeeded, fetching result JSON...")
            # 获取转录结果的 JSON URL
            transcription_url = transcribe_response.output.results[0]['transcription_url']

            # 下载 JSON 数据
            json_response = requests.get(transcription_url)

            # 检查请求是否成功
            if json_response.status_code == 200:
                print("[INFO] Transcription JSON downloaded successfully.")
                # 返回 JSON 内容
                return json_response.json()
            else:
                print("[ERROR] Failed to download transcription JSON file.")
                # 如果 JSON 文件下载失败，返回错误
                return {"error": "Failed to download transcription JSON file."}
        else:
            print(f"[ERROR] Transcription task failed with status code: {transcribe_response.status_code}")
            # 如果转录任务失败，返回错误
            return {"error": "Unable to process the audio."}

    except Exception as e:
        print(f"[ERROR] An exception occurred: {e}")
        # 返回捕获的异常信息
        return {"error": f"An unexpected error occurred: {str(e)}"}
