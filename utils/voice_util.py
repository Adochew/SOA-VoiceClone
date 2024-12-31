import os

import dashscope
from dashscope.audio.tts_v2 import VoiceEnrollmentService, SpeechSynthesizer, AudioFormat
from decouple import config

from utils.oss_utils import upload_to_oss
import pickle

dashscope.api_key = config('DASHSCOPE_API_KEY')


def process_sentences_with_voice_cloning(sentences, reference_audio_url, output_folder="voice_cloning_output"):
    """
    批量变声处理分割的句子文本，结合参考音频生成变声音频。

    :param sentences: 包含句子文本的列表，每个元素为 {"text": 句子文本, "begin_time": 开始时间戳, "end_time": 结束时间戳}
    :param reference_audio_url: 参考音频的 URL
    :param output_folder: 保存变声音频文件的本地目录
    :return: 包含每个句子变声音频的本地路径和 OSS URL 的列表
    """
    # 声音复刻服务
    target_model = "cosyvoice-v1"
    prefix = reference_audio_url.split("/")[-1].split(".")[0]

    # 创建语音注册服务实例
    service = VoiceEnrollmentService()
    voice_id = service.create_voice(target_model=target_model, prefix=prefix, url=reference_audio_url)
    print(f"Voice ID created: {voice_id}")

    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)

    sentence_audio_info = []

    for i, sentence in enumerate(sentences):
        # 创建语音合成器
        synthesizer = SpeechSynthesizer(model=target_model, voice=voice_id)

        text = sentence["text"]
        print(f"Processing sentence {i + 1}: {text}")

        # 生成音频
        audio = synthesizer.call(text)
        print("Generated audio for:", text)

        # 保存到本地
        output_file = os.path.join(output_folder, f"cloned_sentence_{i + 1}.mp3")
        with open(output_file, "wb") as f:
            pickle.dump(audio, f)
        print(f"Audio saved to {output_file}")

        # 上传到 OSS
        oss_url = upload_to_oss(output_file)
        print(f"Audio uploaded to OSS: {oss_url}")

        # 保存音频信息
        sentence_audio_info.append({
            "sentence_id": i + 1,
            "text": text,
            "begin_time": sentence["begin_time"],
            "end_time": sentence["end_time"],
            "local_url": output_file,
            "oss_url": oss_url
        })

    return sentence_audio_info


def regenerate_sentence_audio(sentence, reference_audio_url, output_file):
    """
    重新生成单句变声音频。
    :param sentence: 包含句子文本和时间信息的字典，如 {"text": 句子文本, "sentence_id": 1}
    :param reference_audio_url: 参考音频的 OSS URL。
    :param output_file: 保存变声音频文件的本地路径。
    :return: 包含音频的本地路径和 OSS URL。
    """
    # 声音复刻服务
    target_model = "cosyvoice-v1"
    prefix = reference_audio_url.split("/")[-1].split(".")[0]

    # 创建语音注册服务实例
    service = VoiceEnrollmentService()
    voice_id = service.create_voice(target_model=target_model, prefix=prefix, url=reference_audio_url)

    # 创建语音合成器
    synthesizer = SpeechSynthesizer(model=target_model, voice=voice_id)

    # 生成音频
    text = sentence["text"]
    print(f"Regenerating audio for sentence {sentence['sentence_id']}: {text}")
    audio = synthesizer.call(text)

    # 保存音频到本地
    with open(output_file, "wb") as f:
        pickle.dump(audio, f)
    print(f"Audio regenerated and saved to {output_file}")

    # 上传到 OSS
    oss_url = upload_to_oss(output_file)
    print(f"Audio re-uploaded to OSS: {oss_url}")

    return {
        "sentence_id": sentence["sentence_id"],
        "text": text,
        "local_url": output_file,
        "oss_url": oss_url,
    }



def test_process_sentences_with_voice_cloning():
    # 模拟分割后的句子列表
    sentences = [
        {"text": "今天天气怎么样？", "begin_time": 0, "end_time": 3000},
        {"text": "你好，世界！", "begin_time": 3000, "end_time": 5000},
        {"text": "这是第三个句子。", "begin_time": 5000, "end_time": 8000}
    ]

    # 模拟参考音频的 OSS URL
    reference_audio_url = "https://voice-soa.oss-cn-shenzhen.aliyuncs.com/audio/Voice.WAV"

    # 定义本地保存变声音频的目录
    output_folder = "./output/cloned_sentences"

    # 调用变声处理函数
    sentence_audio_info = process_sentences_with_voice_cloning(sentences, reference_audio_url, output_folder)

    # 输出处理结果
    for info in sentence_audio_info:
        print("Sentence ID:", info["sentence_id"])
        print("Text:", info["text"])
        print("Begin Time:", info["begin_time"])
        print("End Time:", info["end_time"])
        print("Local URL:", info["local_url"])
        print("OSS URL:", info["oss_url"])
        print("-" * 50)


# 调用测试方法
if __name__ == "__main__":
    test_process_sentences_with_voice_cloning()
