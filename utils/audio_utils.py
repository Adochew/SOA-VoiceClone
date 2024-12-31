import librosa
import soundfile as sf
from pydub import AudioSegment
import noisereduce as nr  # 降噪库
from utils.oss_utils import upload_to_oss
import os

def preprocess_audio(input_filepath, output_folder):
    """
    处理音频文件：确保统一为 WAV 格式，16kHz 单声道，并进行降噪。
    """
    try:
        # 获取文件名和输出路径
        filename = os.path.splitext(os.path.basename(input_filepath))[0]
        output_filepath = os.path.join(output_folder, f"{filename}_preprocessed.wav")
        temp_filepath = os.path.join(output_folder, f"{filename}_temp.wav")

        print(f"[INFO] Starting audio preprocessing for: {input_filepath}")

        # 检查文件格式，若为 MP3 则转换为临时 WAV 文件
        if input_filepath.lower().endswith('.mp3'):
            print("[INFO] Input file is in MP3 format, converting to WAV...")
            audio = AudioSegment.from_file(input_filepath, format="mp3")
            audio.export(temp_filepath, format="wav")
        else:
            print("[INFO] Input file is in WAV format.")
            temp_filepath = input_filepath  # 如果是 WAV 文件，直接使用原路径

        # 加载音频并重新采样为 16kHz 单声道
        print("[INFO] Loading audio file for resampling and processing...")
        audio, sr = librosa.load(temp_filepath, sr=16000, mono=True)

        # 应用降噪算法
        print("[INFO] Applying noise reduction...")
        reduced_noise = nr.reduce_noise(y=audio, sr=sr)

        # 保存处理后的音频到最终输出路径
        print(f"[INFO] Saving processed audio to: {output_filepath}")
        sf.write(output_filepath, reduced_noise, sr)

        # 如果创建了临时文件，则删除
        if temp_filepath != input_filepath:
            print(f"[INFO] Deleting temporary file: {temp_filepath}")
            os.remove(temp_filepath)

        print("[INFO] Audio preprocessing completed successfully.")
        return output_filepath

    except Exception as e:
        print(f"[ERROR] Error during audio preprocessing: {e}")
        raise

def split_audio_by_sentences(audio_file, transcription_json, output_folder):
    """
    根据句子的时间戳切割音频，并保存本地和上传 OSS。
    :param audio_file: 原始音频文件路径
    :param transcription_json: 识别结果的 JSON 数据
    :param output_folder: 本地切割音频保存的文件夹
    :return: 包含切割音频信息的列表
    """
    # 加载音频文件
    audio = AudioSegment.from_wav(audio_file)

    # 确保输出目录存在
    os.makedirs(output_folder, exist_ok=True)

    sentence_audio_info = []

    # 遍历 JSON 文件中的 sentences
    for sentence in transcription_json.get("transcripts", [])[0].get("sentences", []):
        sentence_id = sentence.get("sentence_id")
        begin_time = sentence.get("begin_time")
        end_time = sentence.get("end_time")
        text = sentence.get("text")

        # 转换时间戳为毫秒（因为 pydub 的切割单位是毫秒）
        start_ms = int(begin_time)
        end_ms = int(end_time)

        # 切割音频
        sliced_audio = audio[start_ms:end_ms]

        # 保存本地文件名
        output_filename = f"sentence_{sentence_id}.wav"
        output_filepath = os.path.join(output_folder, output_filename)

        # 保存到本地
        sliced_audio.export(output_filepath, format="wav")
        print(f"[INFO] Sentence {sentence_id} audio saved to: {output_filepath}")

        # 上传到 OSS
        oss_url = upload_to_oss(output_filepath)
        print(f"[INFO] Sentence {sentence_id} audio uploaded to OSS: {oss_url}")

        # 保存当前句子的音频信息
        sentence_audio_info.append({
            "sentence_id": sentence_id,
            "begin_time": begin_time,
            "end_time": end_time,
            "text": text,
            "local_url": output_filepath,
            "oss_url": oss_url
        })

    return sentence_audio_info


def time_to_milliseconds(time_str):
    return int(time_str)


def merge_cloned_audio(cloned_audio, output_file):
    """
    合并 cloned_audio 中的音频文件，按照时间戳排列，填充空白或加速处理。

    :param cloned_audio: 包含音频信息的列表。
    :param output_file: 合并后音频的输出路径。
    :return: 合并后的音频文件路径。
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    combined_audio = AudioSegment.silent(duration=0)  # 初始化为空音频

    for audio_info in cloned_audio:
        # 获取音频文件的本地路径
        local_url = audio_info.get("local_url")

        if not local_url or not os.path.exists(local_url):
            print(f"[WARNING] 音频文件不存在: {local_url}")
            continue

        try:
            # 加载MP3文件并转换为WAV格式
            audio = AudioSegment.from_mp3(local_url)

            # 生成临时WAV文件路径
            wav_file_path = local_url.replace(".mp3", ".wav")
            audio.export(wav_file_path, format="wav")

            # 加载WAV格式文件
            audio = AudioSegment.from_wav(wav_file_path)

        except Exception as e:
            print(f"[ERROR] 加载音频文件失败: {local_url}. 错误: {e}")
            continue

        # 获取时间戳（毫秒）
        start_ms = time_to_milliseconds(audio_info["begin_time"])
        end_ms = time_to_milliseconds(audio_info["end_time"])

        # 填充空白
        if len(combined_audio) < start_ms:
            silence = AudioSegment.silent(duration=start_ms - len(combined_audio))
            combined_audio += silence

        # 调整到目标时间范围
        duration_ms = len(audio)
        target_duration_ms = end_ms - start_ms

        if target_duration_ms > duration_ms:
            silence = AudioSegment.silent(duration=target_duration_ms - duration_ms)
            adjusted_audio = audio + silence
        elif target_duration_ms < duration_ms:
            adjusted_audio = audio.speedup(playback_speed=duration_ms / target_duration_ms)
            # adjusted_audio = audio[:target_duration_ms]
        else:
            adjusted_audio = audio

        combined_audio += adjusted_audio

    # 导出合并后的音频
    try:
        combined_audio.export(output_file, format="wav")
        print(f"[INFO] 合并完成，输出文件为: {output_file}")
        return output_file
    except Exception as e:
        print(f"[ERROR] 无法导出音频文件: {output_file}. 错误: {e}")
        return None


# 示例调用
if __name__ == "__main__":
    # 示例 `cloned_audio` 数据
    cloned_audio = [
        {
            "begin_time": 0,
            "end_time": 10933,
            "local_url": "D:/Adochew Project/pythonProject/Voice/static/split/cloned_audio/cloned_sentence_1.mp3",
            "oss_url": "https://voice-soa.oss-cn-shenzhen.aliyuncs.com/audio/cloned_sentence_1.mp3",
            "sentence_id": 1,
            "text": "七年前，22岁的王云峰大学毕业回到家乡浙江省湖州市长兴县华西村，成为一名村干部。"
        },
        {
            "begin_time": 10933,
            "end_time": 20140,
            "local_url": "D:/Adochew Project/pythonProject/Voice/static/split/cloned_audio/cloned_sentence_2.mp3",
            "oss_url": "https://voice-soa.oss-cn-shenzhen.aliyuncs.com/audio/cloned_sentence_2.mp3",
            "sentence_id": 2,
            "text": "七年来，他从修复生态环境入手，一步步扎根乡村建设，找到了自己的人生价值。"
        }
    ]

    # 合并音频的输出文件路径
    output_file = "../static/merge/merged_audio.wav"

    # 调用合并函数
    merge_cloned_audio(cloned_audio, output_file)
