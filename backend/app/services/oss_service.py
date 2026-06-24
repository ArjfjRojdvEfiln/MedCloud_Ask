import oss2
import uuid
from app.core.config import settings


class OSSService:
    """封装阿里云 OSS 文件上传操作"""

    def __init__(self):
        # 用 AccessKey 初始化认证信息
        auth = oss2.Auth(settings.oss_access_key_id, settings.oss_access_key_secret)
        # 初始化 Bucket 操作对象
        self.bucket = oss2.Bucket(auth, f"https://{settings.oss_endpoint}", settings.oss_bucket_name)
        self.bucket_name = settings.oss_bucket_name
        self.endpoint = settings.oss_endpoint

    def upload_file(self, filename: str, file_content: bytes, content_type: str) -> str:
        """
        上传文件到 OSS，返回可访问的公开 URL。

        :param filename: 原始文件名，如 "口腔介绍.pdf"
        :param file_content: 文件二进制内容
        :param content_type: MIME 类型，如 "application/pdf"
        :return: 文件的公开访问 URL
        """
        # 用 uuid 生成唯一文件名，避免同名文件互相覆盖
        # 例如：knowledge/a1b2c3d4-口腔介绍.pdf
        unique_key = f"knowledge/{uuid.uuid4().hex}-{filename}"

        # 上传文件，同时设置 Content-Type，浏览器访问时能正确识别文件类型
        self.bucket.put_object(
            unique_key,
            file_content,
            headers={"Content-Type": content_type},
        )

        # 拼接公开访问 URL
        # 格式：https://{bucket}.{endpoint}/{key}
        oss_url = f"https://{self.bucket_name}.{self.endpoint}/{unique_key}"
        return oss_url


# 全局单例，和 dify_service 保持一致的用法
oss_service = OSSService()