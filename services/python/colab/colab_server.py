 # -*- coding: utf-8 -*-
"""
Google Colab Sentiment Analysis Server
이 스크립트는 Google Colab 환경에서 실행되도록 설계되었습니다.

실행 방법:
1. Google Colab에서 새 노트북을 엽니다.
2. 이 파일의 내용을 코드 셀에 복사합니다.
3. 런타임 유형을 GPU로 설정하는 것을 권장합니다 (필수는 아님).
4. 실행합니다.

필요한 라이브러리 설치 (Colab 셀에서 실행 시 주석 해제 필요):
!pip install fastapi uvicorn pyngrok transformers torch pydantic nest-asyncio
"""

import os
import sys
import threading
import uvicorn
from fastapi import FastAPI, HTTPException, Header, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pyngrok import ngrok
from transformers import pipeline
import nest_asyncio
import requests
import time

# Colab의 이벤트 루프 문제 해결
nest_asyncio.apply()

# ==========================================
# 설정 및 상수
# ==========================================
API_KEY = "viki-colab-secret"  # 보안을 위한 API 키
PORT = 8000

# ==========================================
# FastAPI 앱 초기화
# ==========================================
app = FastAPI(
    title="Colab Sentiment Analysis API",
    description="Google Colab에서 실행되는 감성 분석 및 ABSA 서버",
    version="1.0.0"
)

# ==========================================
# 모델 로드 (전역 변수)
# ==========================================
print("모델을 로드하는 중입니다... 잠시만 기다려주세요.")

try:
    # 1. 일반 감성 분석 모델 (Sentiment Analysis)
    # distilbert-base-uncased-finetuned-sst-2-english: 빠르고 성능 준수
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )
    print("✅ 감성 분석 모델 로드 완료")

    # 2. 속성 기반 감성 분석 (ABSA)을 위한 Zero-shot Classification 모델
    # facebook/bart-large-mnli: Zero-shot 분류에 강력함
    # 사용법: 텍스트와 함께 "The sentiment for [Aspect] is [Label]" 형태의 가설을 검증
    absa_pipeline = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli"
    )
    print("✅ ABSA(Zero-shot) 모델 로드 완료")

except Exception as e:
    print(f"❌ 모델 로드 중 오류 발생: {e}")
    sys.exit(1)

# ==========================================
# 데이터 모델 (Pydantic)
# ==========================================
class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    label: str
    score: float

class AbsaRequest(BaseModel):
    text: str
    aspects: List[str]

class AspectSentiment(BaseModel):
    aspect: str
    label: str
    score: float

class AbsaResponse(BaseModel):
    results: List[AspectSentiment]


class TrainRequest(BaseModel):
    jobId: str
    taskType: str
    callbackUrl: str
    hyperparameters: Dict[str, Any] = {}
    dataset: Optional[Dict[str, Any]] = None
    datasetUrl: Optional[str, Any] = None

# ==========================================
# 보안 미들웨어 / 의존성
# ==========================================
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

# ==========================================
# API 엔드포인트
# ==========================================

@app.get("/")
def read_root():
    return {"message": "Colab Sentiment Analysis Server is running. Use POST /sentiment or /absa."}

@app.post("/sentiment", response_model=SentimentResponse, dependencies=[Depends(verify_api_key)])
async def analyze_sentiment(request: SentimentRequest):
    """
    단일 텍스트에 대한 감성 분석을 수행합니다.
    """
    try:
        # 텍스트 길이 제한 처리 (모델의 최대 토큰 수 고려, 여기서는 간단히 예외처리)
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        result = sentiment_pipeline(request.text)[0]
        
        # 결과 형식: {'label': 'POSITIVE', 'score': 0.99...}
        return SentimentResponse(
            label=result['label'],
            score=result['score']
        )
    except Exception as e:
        print(f"Error in /sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/absa", response_model=AbsaResponse, dependencies=[Depends(verify_api_key)])
async def analyze_absa(request: AbsaRequest):
    """
    텍스트와 속성(Aspect) 리스트를 받아 각 속성별 감성을 분석합니다.
    Zero-shot classification을 활용하여 구현되었습니다.
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        if not request.aspects:
            raise HTTPException(status_code=400, detail="Aspects list cannot be empty")

        results = []
        candidate_labels = ["positive", "negative", "neutral"]

        for aspect in request.aspects:
            # 가설 템플릿 설정: "The sentiment for {aspect} is {}."
            hypothesis_template = f"The sentiment for {aspect} is {{}}."
            
            # Zero-shot classification 실행
            output = absa_pipeline(
                request.text,
                candidate_labels,
                hypothesis_template=hypothesis_template,
                multi_label=False
            )
            
            # output 형식:
            # {
            #   'sequence': '...',
            #   'labels': ['positive', 'neutral', 'negative'],
            #   'scores': [0.9, 0.05, 0.05]
            # }
            
            top_label = output['labels'][0]
            top_score = output['scores'][0]

            results.append(AspectSentiment(
                aspect=aspect,
                label=top_label.upper(),
                score=top_score
            ))

        return AbsaResponse(results=results)

    except Exception as e:
        print(f"Error in /absa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_training_job(req: TrainRequest):
    """오래 걸리는 학습 작업을 백그라운드에서 실행하고 Java 서버로 콜백을 보냅니다.

    현재는 SENTIMENT 태스크에 대해 HuggingFace Trainer를 사용한
    간단한 파인튜닝 예시를 제공합니다. ABSA 태스크의 경우에는
    향후 확장을 위해 분기만 정의해두었습니다.
    """
    try:
        print(f"[TRAIN] jobId={req.jobId}, taskType={req.taskType} - training started")

        if req.taskType.upper() == "SENTIMENT":
            # ================================
            # 1) 데이터셋 준비 (Light mode 기준)
            # ================================
            from datasets import Dataset
            from transformers import (
                AutoTokenizer,
                AutoModelForSequenceClassification,
                TrainingArguments,
                Trainer,
            )
            import numpy as np
            from sklearn.metrics import accuracy_score, f1_score

            examples = []
            if req.dataset and "examples" in req.dataset:
                examples = req.dataset["examples"]

            if not examples:
                raise ValueError("No training examples provided in dataset.examples")

            texts = [ex["text"] for ex in examples]
            labels = [ex["label"] for ex in examples]

            label2id = {"negative": 0, "neutral": 1, "positive": 2}
            id2label = {v: k for k, v in label2id.items()}

            # 라벨이 사전에 없는 경우 기본 neutral 로 매핑
            encoded_labels = [label2id.get(l, 1) for l in labels]

            ds = Dataset.from_dict({"text": texts, "label": encoded_labels})

            # ================================
            # 2) 토크나이저 / 모델 로드
            # ================================
            base_model_name = req.hyperparameters.get(
                "base_model", "distilbert-base-uncased"
            )
            tokenizer = AutoTokenizer.from_pretrained(base_model_name)
            model = AutoModelForSequenceClassification.from_pretrained(
                base_model_name,
                num_labels=len(label2id),
                id2label=id2label,
                label2id=label2id,
            )

            def preprocess(batch):
                return tokenizer(
                    batch["text"],
                    truncation=True,
                    padding="max_length",
                    max_length=256,
                )

            tokenized = ds.map(preprocess, batched=True)
            split = tokenized.train_test_split(test_size=0.1)
            train_ds = split["train"]
            eval_ds = split["test"]

            # ================================
            # 3) Trainer 설정 및 학습
            # ================================
            output_dir = f"./models/{req.taskType.lower()}/{req.jobId}"
            args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=req.hyperparameters.get("epochs", 3),
                per_device_train_batch_size=req.hyperparameters.get("batch_size", 16),
                per_device_eval_batch_size=32,
                learning_rate=req.hyperparameters.get("learning_rate", 5e-5),
                evaluation_strategy="epoch",
                logging_steps=50,
                save_strategy="epoch",
                load_best_model_at_end=True,
            )

            def compute_metrics(eval_pred):
                logits, labels = eval_pred
                preds = np.argmax(logits, axis=-1)
                return {
                    "accuracy": accuracy_score(labels, preds),
                    "f1": f1_score(labels, preds, average="macro"),
                }

            trainer = Trainer(
                model=model,
                args=args,
                train_dataset=train_ds,
                eval_dataset=eval_ds,
                compute_metrics=compute_metrics,
            )

            trainer.train()
            eval_metrics = trainer.evaluate()

            # ================================
            # 4) 모델 저장 (로컬 경로)
            # ================================
            save_dir = output_dir + "/final"
            os.makedirs(save_dir, exist_ok=True)
            model.save_pretrained(save_dir)
            tokenizer.save_pretrained(save_dir)

            # 실제 환경에서는 save_dir을 GCS/S3 등에 업로드 후 그 경로를 사용
            model_path = f"gs://models/{req.taskType.lower()}/{req.jobId}"
            metrics = {
                "accuracy": float(eval_metrics.get("eval_accuracy", 0.0)),
                "f1": float(eval_metrics.get("eval_f1", 0.0)),
                "loss": float(eval_metrics.get("eval_loss", 0.0)),
            }

        else:
            # ABSA 및 기타 태스크는 현재 시뮬레이션만 제공
            time.sleep(5)
            model_path = f"gs://models/{req.taskType.lower()}/{req.jobId}"
            metrics = {"accuracy": 0.95, "loss": 0.1}

        payload = {
            "jobId": req.jobId,
            "status": "COMPLETED",
            "metrics": metrics,
            "modelPath": model_path,
            "errorMessage": None,
        }
    except Exception as e:
        print(f"[TRAIN] jobId={req.jobId} failed: {e}")
        payload = {
            "jobId": req.jobId,
            "status": "FAILED",
            "metrics": None,
            "modelPath": None,
            "errorMessage": str(e),
        }

    try:
        resp = requests.post(req.callbackUrl, json=payload, timeout=10)
        print(f"[TRAIN] callback to {req.callbackUrl} status={resp.status_code}")
    except Exception as e:
        print(f"[TRAIN] callback failed: {e}")


@app.post("/train", dependencies=[Depends(verify_api_key)])
async def start_training(req: TrainRequest, background_tasks: BackgroundTasks):
    """학습 작업을 시작하고 즉시 응답을 반환합니다."""
    background_tasks.add_task(run_training_job, req)
    return {"jobId": req.jobId, "status": "QUEUED"}

# ==========================================
# 서버 실행
# ==========================================
if __name__ == "__main__":
    # Ngrok 설정
    print("Ngrok 터널을 엽니다...")
    try:
        # 기존 터널이 있다면 닫기 (재실행 시 충돌 방지)
        ngrok.kill()
        
        # 포트 8000을 외부로 노출
        public_url = ngrok.connect(PORT).public_url
        print(f"\n🚀 Server is running!")
        print(f"🌍 Public URL: {public_url}")
        print(f"🔑 API Key: {API_KEY}")
        print(f"📄 Docs: {public_url}/docs\n")
        
        # Uvicorn 서버 실행
        uvicorn.run(app, host="0.0.0.0", port=PORT)
        
    except Exception as e:
        print(f"❌ 서버 실행 중 오류 발생: {e}")