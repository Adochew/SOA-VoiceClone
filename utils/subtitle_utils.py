import os

def time_to_srt_format(ms):
    """将毫秒转为SRT字幕时间格式（HH:MM:SS,SSS）"""
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    milliseconds = ms % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def generate_srt(cloned_audio, output_srt_file):
    """
    生成SRT字幕文件

    :param cloned_audio: 包含音频信息的列表。
    :param output_srt_file: 输出SRT字幕文件路径。
    """
    with open(output_srt_file, 'w', encoding='utf-8') as srt_file:
        for idx, audio_info in enumerate(cloned_audio, start=1):
            begin_ms = audio_info["begin_time"]
            end_ms = audio_info["end_time"]
            text = audio_info["text"]

            # 转换时间为SRT格式
            start_time = time_to_srt_format(begin_ms)
            end_time = time_to_srt_format(end_ms)

            # 写入SRT文件
            srt_file.write(f"{idx}\n")
            srt_file.write(f"{start_time} --> {end_time}\n")
            srt_file.write(f"{text}\n\n")

    print(f"[INFO] SRT字幕文件已生成: {output_srt_file}")

# 示例调用
if __name__ == "__main__":
    # 示例 `cloned_audio` 数据
    cloned_audio = [
        {
            "begin_time": 0,
            "end_time": 10933,
            "local_url": "D:\\Adochew Project/pythonProject/Voice/static/split\\cloned_audio\\cloned_sentence_1.mp3",
            "oss_url": "https://voice-soa.oss-cn-shenzhen.aliyuncs.com/audio/cloned_sentence_1.mp3",
            "sentence_id": 1,
            "text": "七年前，22岁的王云峰大学毕业回到家乡浙江省湖州市长兴县华西村，成为一名村干部。"
        },
        {
            "begin_time": 10933,
            "end_time": 20140,
            "local_url": "D:\\Adochew Project/pythonProject/Voice/static/split\\cloned_audio\\cloned_sentence_2.mp3",
            "oss_url": "https://voice-soa.oss-cn-shenzhen.aliyuncs.com/audio/cloned_sentence_2.mp3",
            "sentence_id": 2,
            "text": "七年来，他从修复生态环境入手，一步步扎根乡村建设，找到了自己的人生价值。"
        }
    ]

    # 输出SRT字幕文件路径
    output_srt_file = "D:/Adochew Project/pythonProject/Voice/static/subtitle/subtitle.srt"

    # 生成SRT字幕文件
    generate_srt(cloned_audio, output_srt_file)
