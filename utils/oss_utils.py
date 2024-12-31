import oss2
import os
from decouple import config

# 设置阿里云 OSS 参数
OSS_ACCESS_KEY_ID = config('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = config('OSS_ACCESS_KEY_SECRET')
OSS_BUCKET_NAME = 'voice-soa'
OSS_ENDPOINT = 'oss-cn-shenzhen.aliyuncs.com'


def upload_to_oss(file_path):
    """
    上传文件到阿里云 OSS。
    :param file_path: 本地文件路径
    :return: 文件在 OSS 上的 URL
    """
    # 创建 OSS 客户端
    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

    # 获取文件的扩展名
    filename = os.path.basename(file_path)
    file_extension = os.path.splitext(filename)[-1]  # 获取文件扩展名，例如 ".mp3"

    # 生成文件在 OSS 上的路径，假设是上传到 "audio" 目录下
    oss_key = f"audio/{filename}"

    # 上传文件
    with open(file_path, 'rb') as file:
        bucket.put_object(oss_key, file)

    # 返回文件的 URL
    return f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{oss_key}"


# 示例调用
if __name__ == '__main__':
    file_path = "path/to/your/local/file.wav"  # 这里需要填写本地文件的路径
    file_url = upload_to_oss(file_path)
    print(f"File uploaded to: {file_url}")
