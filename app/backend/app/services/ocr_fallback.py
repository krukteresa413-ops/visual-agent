import os
import time
import logging

from alibabacloud_docmind_api20220711.client import Client
from alibabacloud_docmind_api20220711 import models as M
from alibabacloud_tea_openapi import models as OpenApiModels
from alibabacloud_tea_util import models as UtilModels

logger = logging.getLogger(__name__)

_ENDPOINT = "docmind-api.cn-hangzhou.aliyuncs.com"
_POLL_INTERVAL = 5
_MAX_WAIT = int(os.environ.get("OCR_MAX_WAIT_SECONDS", "120"))


def _build_client() -> Client:
    cfg = OpenApiModels.Config(
        access_key_id=os.environ["ALIBABA_CLOUD_ACCESS_KEY_ID"],
        access_key_secret=os.environ["ALIBABA_CLOUD_ACCESS_KEY_SECRET"],
    )
    cfg.endpoint = _ENDPOINT
    return Client(cfg)


def ocr_pdf(fp: str) -> str:
    """扫描/图片型 PDF 兜底:调用文档解析(大模型版)提取文本。
    成功返回文本;任何失败/超时返回空字符串(交由上游既有空文本逻辑处理)。"""
    try:
        client = _build_client()
        with open(fp, "rb") as f:
            submit = client.submit_doc_parser_job_advance(
                M.SubmitDocParserJobAdvanceRequest(
                    file_url_object=f,
                    file_name=os.path.basename(fp),
                    file_name_extension="pdf",
                ),
                UtilModels.RuntimeOptions(),
            )
        job_id = submit.body.data.id
        logger.info("OCR fallback 触发: job_id=%s file=%s", job_id, os.path.basename(fp))

        deadline = time.time() + _MAX_WAIT
        completed = False
        while time.time() < deadline:
            st = client.query_doc_parser_status(M.QueryDocParserStatusRequest(id=job_id))
            sbody = st.body.to_map()
            data = sbody.get("Data") or {}
            status = data.get("Status", "")
            if status == "success":
                completed = True
                break
            elif status == "Fail" or status == "fail":
                logger.warning("OCR 处理失败: job_id=%s code=%s", job_id, data.get("Code"))
                return ""
            time.sleep(_POLL_INTERVAL)
        if not completed:
            logger.warning("OCR 轮询超时(%ss): job_id=%s", _MAX_WAIT, job_id)
            return ""

        parts = []
        layout_num = 0
        step = 100
        while True:
            res = client.get_doc_parser_result(
                M.GetDocParserResultRequest(id=job_id, layout_num=layout_num, layout_step_size=step)
            )
            data = res.body.to_map().get("Data") or {}
            layouts = data.get("layouts") or []
            if not layouts:
                break
            for lo in layouts:
                parts.append(lo.get("markdownContent") or lo.get("text") or "")
            if len(layouts) < step:
                break
            layout_num += len(layouts)

        text = "\n".join(p for p in parts if p).strip()
        if not text:
            logger.warning("OCR 返回空文本: job_id=%s", job_id)
        return text
    except Exception as e:
        logger.warning("OCR fallback 异常: %s", e)
        return ""
