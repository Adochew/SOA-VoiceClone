import json
import os

from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO

from utils.audio_utils import preprocess_audio, split_audio_by_sentences, merge_cloned_audio
from utils.oss_utils import upload_to_oss
from utils.transcription import recognize_audio
from utils.voice_util import process_sentences_with_voice_cloning, regenerate_sentence_audio
from utils.subtitle_utils import generate_srt

# 初始化 Flask 应用
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

BASE_URL = 'D:\Adochew Project/pythonProject/Voice'

app.config['UPLOAD_FOLDER'] = BASE_URL + '/uploads'
app.config['REFERENCE_FOLDER'] = BASE_URL + '/reference'
app.config['PROCESSED_FOLDER'] = BASE_URL + '/static/processed'
app.config['JSON_FOLDER'] = BASE_URL + '/static/json'
app.config['SPLIT_FOLDER'] = BASE_URL + '/static/split'
app.config['MERGE_FOLDER'] = BASE_URL + '/static/merge'
app.config['SUBTITLE_FOLDER'] = BASE_URL + '/static/subtitle'

# 全局数据存储
file_info = {}

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REFERENCE_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
os.makedirs(app.config['JSON_FOLDER'], exist_ok=True)
os.makedirs(app.config['SPLIT_FOLDER'], exist_ok=True)
os.makedirs(app.config['MERGE_FOLDER'], exist_ok=True)
os.makedirs(app.config['SUBTITLE_FOLDER'], exist_ok=True)


# 路由：主页（文件上传）
@app.route('/')
def index():
    return render_template('index.html')


# 路由：处理上传文件
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file uploaded", 400
    file = request.files['file']

    # 保存上传文件到本地
    input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(input_filepath)

    # 上传原始音频到 OSS
    original_oss_url = upload_to_oss(input_filepath)

    # 音频预处理（统一为 WAV 格式，16kHz 单声道）
    preprocessed_filepath = preprocess_audio(input_filepath, app.config['PROCESSED_FOLDER'])

    # 上传预处理后的音频到 OSS
    preprocessed_oss_url = upload_to_oss(preprocessed_filepath)

    # 保存文件信息
    file_info["original_audio"] = {
        "local_url": input_filepath,
        "oss_url": original_oss_url
    }
    file_info["preprocessed_audio"] = {
        "local_url": preprocessed_filepath,
        "oss_url": preprocessed_oss_url
    }

    return jsonify({
        "message": "Upload successful and audio preprocessed!",
        "original_audio": file_info["original_audio"],
        "preprocessed_audio": file_info["preprocessed_audio"]
    })


# 路由：识别音频
@app.route('/recognize', methods=['POST'])
def recognize():
    audio_url = file_info.get("preprocessed_audio", {}).get("oss_url")
    if not audio_url:
        return jsonify({"error": "No preprocessed audio URL available"}), 400

    # 语音识别
    transcription_result = recognize_audio(audio_url)

    # 保存识别结果到本地
    json_filename = f"{os.path.basename(audio_url).split('.')[0]}_transcription.json"
    json_filepath = os.path.join(app.config['JSON_FOLDER'], json_filename)
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(transcription_result, f, ensure_ascii=False, indent=4)

    # 上传识别结果 JSON 文件到 OSS
    json_oss_url = upload_to_oss(json_filepath)

    # 保存文件信息
    file_info["transcription"] = {
        "local_url": json_filepath,
        "oss_url": json_oss_url
    }

    return jsonify({
        "transcription": file_info["transcription"],
        "message": "Recognition completed and transcription saved!"
    })


# 路由：切割音频
@app.route('/split_audio', methods=['POST'])
def split_audio():
    # 从全局变量中获取音频和 JSON 文件路径
    preprocessed_audio = file_info.get("preprocessed_audio", {}).get("local_url")
    transcription_json_path = file_info.get("transcription", {}).get("local_url")

    if not preprocessed_audio or not transcription_json_path:
        return jsonify({"error": "Required audio or JSON file is missing"}), 400

    # 加载 JSON 数据
    with open(transcription_json_path, 'r', encoding='utf-8') as f:
        transcription_json = json.load(f)

    # 输出目录
    output_folder = os.path.join(app.config['SPLIT_FOLDER'], 'sentences')
    os.makedirs(output_folder, exist_ok=True)

    # 调用切割函数
    sentence_audio_info = split_audio_by_sentences(preprocessed_audio, transcription_json, output_folder)

    # 保存结果到全局变量
    file_info["sentence_audio"] = sentence_audio_info

    return jsonify({
        "message": "Audio split by sentences successfully!",
        "sentence_audio_info": sentence_audio_info
    })


# 路由：更新句子编辑结果
@app.route('/update_transcription', methods=['POST'])
def update_transcription():
    try:
        # 获取前端传递的数据
        data = request.json
        if not data or "updated_sentences" not in data:
            return jsonify({"error": "Invalid data"}), 400

        updated_sentences = data["updated_sentences"]

        # 检查全局变量是否包含 sentence_audio 信息
        if "sentence_audio" not in file_info:
            return jsonify({"error": "Sentence audio data not found in file_info"}), 400

        # 遍历更新的句子，匹配并更新全局变量中的对应内容
        for updated_sentence in updated_sentences:
            sentence_id = int(updated_sentence.get("sentence_id"))
            new_text = updated_sentence.get("text")

            # 查找匹配的 sentence_id 并更新 text
            for sentence in file_info["sentence_audio"]:
                if sentence["sentence_id"] == sentence_id:
                    sentence["text"] = new_text  # 更新句子文本
                    break

        print(jsonify({
            "message": "Sentence audio information updated successfully!",
            "updated_sentence_audio": file_info["sentence_audio"]
        }))

        # 返回成功信息
        return jsonify({
            "message": "Sentence audio information updated successfully!",
            "updated_sentence_audio": file_info["sentence_audio"]
        })

    except Exception as e:
        # 捕获异常并返回错误信息
        return jsonify({"error": "An error occurred while updating the sentence audio.", "details": str(e)}), 500


@app.route('/upload_reference', methods=['POST'])
def upload_reference():
    try:
        if 'file' not in request.files or 'text' not in request.form:
            return jsonify({"error": "Audio file and text are required"}), 400

        # 获取音频文件和文本信息
        file = request.files['file']
        reference_text = request.form['text']

        # 保存音频文件到本地 reference 文件夹
        reference_audio_path = os.path.join(app.config['REFERENCE_FOLDER'], file.filename)
        file.save(reference_audio_path)

        # 上传音频文件到 OSS
        reference_audio_oss_url = upload_to_oss(reference_audio_path)

        # 保存信息到全局变量
        file_info["reference_audio"] = {
            "local_url": reference_audio_path,
            "oss_url": reference_audio_oss_url,
            "text": reference_text
        }

        # 返回成功信息
        return jsonify({
            "message": "Reference audio and text uploaded successfully!",
            "reference_audio": file_info["reference_audio"]
        })

    except Exception as e:
        return jsonify({"error": "An error occurred while uploading reference audio.", "details": str(e)}), 500


@app.route('/generate_cloned_audio', methods=['POST'])
def generate_cloned_audio():
    # 检查必要的文件信息是否存在
    sentences = file_info.get("sentence_audio")
    reference_audio = file_info.get("reference_audio", {}).get("oss_url")

    if not sentences or not reference_audio:
        return jsonify({"error": "Missing required data (sentences or reference audio)"}), 400

    try:
        # 调用变声处理函数
        output_folder = os.path.join(app.config['SPLIT_FOLDER'], 'cloned_audio')
        cloned_audio_info = process_sentences_with_voice_cloning(sentences, reference_audio, output_folder)

        # 保存变声音频信息到全局变量
        file_info["cloned_audio"] = cloned_audio_info

        return jsonify({
            "message": "Voice cloning completed successfully!",
            "cloned_audio_info": cloned_audio_info
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/regenerate_cloned_audio', methods=['POST'])
def regenerate_cloned_audio():
    """
    重新生成单句变声音频。
    """
    try:
        # 获取请求参数
        data = request.json
        sentence_id = data.get("sentence_id")
        new_text = data.get("text")

        if not sentence_id or not new_text:
            return jsonify({"error": "Missing required parameters (sentence_id or text)"}), 400

        # 检查句子是否存在于全局变量中
        cloned_audio = file_info.get("cloned_audio", [])
        sentence = next((s for s in cloned_audio if s["sentence_id"] == sentence_id), None)
        if not sentence:
            return jsonify({"error": f"Sentence with ID {sentence_id} not found"}), 404

        # 保留其他字段，仅更新 text
        sentence["text"] = new_text

        # 获取参考音频的 URL
        reference_audio_url = file_info.get("reference_audio", {}).get("oss_url")
        if not reference_audio_url:
            return jsonify({"error": "Reference audio URL not found"}), 400

        # 获取原音频的本地文件路径
        output_folder = os.path.join(app.config['SPLIT_FOLDER'], 'cloned_audio')
        output_file = os.path.join(output_folder, f"cloned_sentence_{sentence_id}.mp3")

        # 调用工具方法重新生成音频
        updated_audio = regenerate_sentence_audio(sentence, reference_audio_url, output_file)

        sentence["local_url"] = updated_audio["local_url"]
        sentence["oss_url"] = updated_audio["oss_url"]

        # 找到并更新相应的句子
        for idx, s in enumerate(cloned_audio):
            if s["sentence_id"] == sentence_id:
                cloned_audio[idx] = sentence
                break

        # 确保更新后的 cloned_audio 被写回 file_info
        file_info["cloned_audio"] = cloned_audio

        return jsonify({
            "message": f"Audio for sentence {sentence_id} regenerated successfully!",
            "updated_sentence": sentence,
        })

    except Exception as e:
        return jsonify({"error": "An error occurred while regenerating audio.", "details": str(e)}), 500



@app.route('/merge_cloned_audio', methods=['POST'])
def merge_cloned_audio_route():
    """
    合并 cloned_audio 中的音频文件，并保存到本地和 OSS。
    """
    try:
        # 获取 cloned_audio 信息
        cloned_audio = file_info.get("cloned_audio")
        if not cloned_audio:
            return jsonify({"error": "No cloned audio data found in file_info"}), 400

        # 定义合并后的音频文件路径
        output_file = os.path.join(app.config['MERGE_FOLDER'], 'merged_audio.wav')

        # 调用合并函数
        merged_audio_path = merge_cloned_audio(cloned_audio, output_file)

        if not merged_audio_path:
            return jsonify({"error": "Failed to merge audio files"}), 500

        # 上传合并后的文件到 OSS
        merged_audio_oss_url = upload_to_oss(merged_audio_path)

        # 保存合并音频信息到全局变量
        file_info["merged_audio"] = {
            "local_url": merged_audio_path,
            "oss_url": merged_audio_oss_url
        }

        return jsonify({
            "message": "Cloned audio files merged successfully!",
            "merged_audio": file_info["merged_audio"]
        }), 200

    except Exception as e:
        return jsonify({"error": "An error occurred while merging cloned audio files.", "details": str(e)}), 500


# 路由：生成 SRT 字幕
@app.route('/generate_srt', methods=['POST'])
def generate_srt_route():
    """
    根据音频的句子信息生成 SRT 字幕文件并上传到 OSS。
    """
    try:
        # 获取切割后的句子音频信息
        sentences = file_info.get("sentence_audio")
        if not sentences:
            return jsonify({"error": "No sentence audio data found in file_info"}), 400

        # 生成 SRT 字幕文件
        output_srt_file = os.path.join(app.config['SUBTITLE_FOLDER'], 'generated_subtitles.srt')
        generate_srt(sentences, output_srt_file)

        # 上传字幕文件到 OSS
        srt_oss_url = upload_to_oss(output_srt_file)

        # 保存字幕文件信息到全局变量
        file_info["generated_srt"] = {
            "local_url": output_srt_file,
            "oss_url": srt_oss_url
        }

        return jsonify({
            "message": "SRT subtitles generated successfully!",
            "generated_srt": file_info["generated_srt"]
        }), 200

    except Exception as e:
        return jsonify({"error": "An error occurred while generating SRT subtitles.", "details": str(e)}), 500


# 路由：查看全局 file_info
@app.route('/get_info', methods=['GET'])
def get_info():
    """
    返回当前全局变量 file_info 的内容
    """
    try:
        return jsonify({
            "message": "File info retrieved successfully!",
            "file_info": file_info
        }), 200
    except Exception as e:
        return jsonify({
            "error": "An error occurred while retrieving file info.",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    socketio.run(app, debug=True, host="127.0.0.1", port=5000)
