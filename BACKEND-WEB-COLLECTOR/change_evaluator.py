"""
AI 기반 변경 중요도 평가 시스템
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import re
import numpy as np
from collections import Counter

from gemini_client_v2 import GeminiClientV2
from prompts.change import IntelligentChangeAnalysisPromptTemplate
from parsers.gemini_parser import GeminiResponseParser

logger = logging.getLogger(__name__)


class ImpactLevel(Enum):
    """영향 수준"""
    CRITICAL = "critical"  # 매우 중요
    HIGH = "high"  # 높음
    MEDIUM = "medium"  # 중간
    LOW = "low"  # 낮음
    MINIMAL = "minimal"  # 최소


class ChangeCategory(Enum):
    """변경 카테고리"""
    POLICY = "policy"  # 정책 변경
    FINANCIAL = "financial"  # 재정 관련
    REGULATORY = "regulatory"  # 규제 변경
    OPERATIONAL = "operational"  # 운영 변경
    INFORMATIONAL = "informational"  # 정보성
    TECHNICAL = "technical"  # 기술적 변경


@dataclass
class EvaluationCriteria:
    """평가 기준"""
    name: str
    weight: float
    threshold: float
    keywords: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    
    def evaluate(self, content: str) -> float:
        """기준별 평가"""
        score = 0.0
        content_lower = content.lower()
        
        # 키워드 매칭
        if self.keywords:
            keyword_matches = sum(
                1 for keyword in self.keywords 
                if keyword.lower() in content_lower
            )
            score += (keyword_matches / len(self.keywords)) * 0.5
        
        # 패턴 매칭
        if self.patterns:
            pattern_matches = sum(
                1 for pattern in self.patterns
                if re.search(pattern, content, re.IGNORECASE)
            )
            score += (pattern_matches / len(self.patterns)) * 0.5
        
        return min(1.0, score) * self.weight


@dataclass
class ImportanceScore:
    """중요도 점수"""
    total_score: float  # 0-100
    impact_level: ImpactLevel
    change_category: ChangeCategory
    confidence: float  # 0-1
    criteria_scores: Dict[str, float]
    ai_insights: Dict[str, Any]
    notification_required: bool
    urgency: str  # immediate/high/medium/low
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "total_score": self.total_score,
            "impact_level": self.impact_level.value,
            "change_category": self.change_category.value,
            "confidence": self.confidence,
            "criteria_scores": self.criteria_scores,
            "ai_insights": self.ai_insights,
            "notification_required": self.notification_required,
            "urgency": self.urgency,
            "summary": self.summary
        }


class PensionDomainEvaluator:
    """연금 도메인 특화 평가기"""
    
    def __init__(self):
        self.critical_keywords = [
            "보험료", "인상", "개혁", "고갈", "재정",
            "수급", "연령", "소득대체율", "기금"
        ]
        
        self.policy_patterns = [
            r"정부.*발표",
            r"개혁.*추진",
            r"법.*개정",
            r"정책.*변경"
        ]
        
        self.financial_patterns = [
            r"\d+%.*인상",
            r"\d+조.*원",
            r"수익률.*\d+",
            r"적자.*\d+"
        ]
    
    def evaluate_pension_relevance(self, content: str) -> float:
        """연금 관련성 평가"""
        score = 0.0
        content_lower = content.lower()
        
        # 핵심 키워드 체크
        critical_found = sum(
            1 for keyword in self.critical_keywords
            if keyword in content_lower
        )
        score += (critical_found / len(self.critical_keywords)) * 0.5
        
        # 정책 패턴 체크
        policy_matches = sum(
            1 for pattern in self.policy_patterns
            if re.search(pattern, content, re.IGNORECASE)
        )
        if policy_matches > 0:
            score += 0.3
        
        # 재정 패턴 체크
        financial_matches = sum(
            1 for pattern in self.financial_patterns
            if re.search(pattern, content, re.IGNORECASE)
        )
        if financial_matches > 0:
            score += 0.2
        
        return min(1.0, score)
    
    def determine_stakeholder_impact(self, content: str) -> Dict[str, str]:
        """이해관계자 영향 분석"""
        impacts = {}
        
        age_groups = {
            "청년": ["20대", "30대", "청년", "젊은"],
            "중년": ["40대", "50대", "중년"],
            "노년": ["60대", "노인", "고령자", "은퇴"]
        }
        
        for group, keywords in age_groups.items():
            if any(keyword in content for keyword in keywords):
                impacts[group] = "직접 영향"
            else:
                impacts[group] = "간접 영향"
        
        # 특수 그룹
        if "자영업" in content:
            impacts["자영업자"] = "직접 영향"
        if "기업" in content or "사업주" in content:
            impacts["기업"] = "직접 영향"
        
        return impacts


class ChangeImportanceEvaluator:
    """
    AI 기반 변경 중요도 평가기
    
    변경사항의 중요도를 다각도로 평가하고 알림 우선순위 결정
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        domain: str = "pension"
    ):
        self.gemini_client = GeminiClientV2(api_key=gemini_api_key) if gemini_api_key else None
        self.change_prompt = IntelligentChangeAnalysisPromptTemplate()
        self.parser = GeminiResponseParser()
        
        # 도메인별 평가기
        self.domain = domain
        if domain == "pension":
            self.domain_evaluator = PensionDomainEvaluator()
        else:
            self.domain_evaluator = None
        
        # 평가 기준 설정
        self.criteria = self._setup_criteria()
        
        # 학습 데이터
        self.evaluation_history: List[Dict[str, Any]] = []
        self.accuracy_metrics = {
            "true_positives": 0,
            "false_positives": 0,
            "true_negatives": 0,
            "false_negatives": 0
        }
        
        self.logger = logger
    
    def _setup_criteria(self) -> List[EvaluationCriteria]:
        """평가 기준 설정"""
        criteria = []
        
        # 정책 변경
        criteria.append(EvaluationCriteria(
            name="policy_change",
            weight=0.25,
            threshold=0.5,
            keywords=["정책", "개혁", "변경", "개정", "시행"],
            patterns=[r"정부.*발표", r"법.*개정"]
        ))
        
        # 재정 영향
        criteria.append(EvaluationCriteria(
            name="financial_impact",
            weight=0.25,
            threshold=0.4,
            keywords=["보험료", "수익률", "재정", "예산", "비용"],
            patterns=[r"\d+%", r"\d+조원", r"\d+억원"]
        ))
        
        # 대중 영향
        criteria.append(EvaluationCriteria(
            name="public_impact",
            weight=0.20,
            threshold=0.3,
            keywords=["국민", "시민", "가입자", "수급자"],
            patterns=[r"전체.*영향", r"모든.*대상"]
        ))
        
        # 긴급성
        criteria.append(EvaluationCriteria(
            name="urgency",
            weight=0.15,
            threshold=0.6,
            keywords=["즉시", "긴급", "시급", "조속히", "당장"],
            patterns=[r"즉시.*시행", r"긴급.*대응"]
        ))
        
        # 규모
        criteria.append(EvaluationCriteria(
            name="scale",
            weight=0.15,
            threshold=0.4,
            keywords=["전면", "대규모", "전체", "모든"],
            patterns=[r"전면.*개편", r"대규모.*변경"]
        ))
        
        return criteria
    
    async def evaluate(
        self,
        before_content: str,
        after_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ImportanceScore:
        """
        변경 중요도 평가
        
        Args:
            before_content: 이전 콘텐츠
            after_content: 현재 콘텐츠
            metadata: 추가 메타데이터
        
        Returns:
            중요도 점수
        """
        # 변경 내용 추출
        changes = self._extract_changes(before_content, after_content)
        
        # 기준별 평가
        criteria_scores = {}
        total_weight = 0.0
        weighted_score = 0.0
        
        for criterion in self.criteria:
            score = criterion.evaluate(changes)
            criteria_scores[criterion.name] = score
            weighted_score += score
            total_weight += criterion.weight
        
        # 도메인별 평가
        domain_score = 0.0
        if self.domain_evaluator:
            domain_score = self.domain_evaluator.evaluate_pension_relevance(changes)
            criteria_scores["domain_relevance"] = domain_score
            weighted_score = weighted_score * 0.7 + domain_score * 0.3
        
        # AI 분석
        ai_insights = {}
        if self.gemini_client:
            ai_insights = await self._ai_analysis(
                before_content[:2000],
                after_content[:2000],
                metadata
            )
        
        # 최종 점수 계산
        base_score = (weighted_score / total_weight) * 100 if total_weight > 0 else 0
        
        # AI 조정
        if ai_insights:
            ai_importance = ai_insights.get("importance_score", base_score / 10)
            if isinstance(ai_importance, (int, float)):
                # AI 점수와 기준 점수의 가중 평균
                final_score = base_score * 0.6 + (ai_importance * 10) * 0.4
            else:
                final_score = base_score
        else:
            final_score = base_score
        
        # 영향 수준 결정
        impact_level = self._determine_impact_level(final_score)
        
        # 카테고리 결정
        change_category = self._determine_category(criteria_scores, ai_insights)
        
        # 알림 필요성 결정
        notification_required = final_score >= 30  # 30점 이상
        
        # 긴급도 결정
        urgency = self._determine_urgency(final_score, criteria_scores)
        
        # 요약 생성
        summary = self._generate_summary(
            changes,
            impact_level,
            change_category,
            ai_insights
        )
        
        # 신뢰도 계산
        confidence = self._calculate_confidence(criteria_scores, ai_insights)
        
        # 결과 생성
        importance_score = ImportanceScore(
            total_score=round(final_score, 2),
            impact_level=impact_level,
            change_category=change_category,
            confidence=confidence,
            criteria_scores=criteria_scores,
            ai_insights=ai_insights,
            notification_required=notification_required,
            urgency=urgency,
            summary=summary
        )
        
        # 히스토리 저장
        self._save_evaluation_history(importance_score, metadata)
        
        return importance_score
    
    def _extract_changes(self, before: str, after: str) -> str:
        """변경 내용 추출"""
        # 간단한 추출: after에서 before에 없는 내용
        before_lines = set(before.splitlines())
        after_lines = set(after.splitlines())
        
        new_lines = after_lines - before_lines
        removed_lines = before_lines - after_lines
        
        changes = []
        if new_lines:
            changes.append("추가된 내용:")
            changes.extend(list(new_lines)[:10])  # 처음 10줄
        
        if removed_lines:
            changes.append("제거된 내용:")
            changes.extend(list(removed_lines)[:10])
        
        return "\n".join(changes)
    
    async def _ai_analysis(
        self,
        before: str,
        after: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """AI 분석"""
        try:
            # 프롬프트 생성
            prompt = self.change_prompt.format_prompt(
                "",
                before=before,
                after=after
            )
            
            # 메타데이터 추가
            if metadata:
                prompt += f"\n\n추가 컨텍스트: {metadata}"
            
            # AI 분석 요청
            response = await self.gemini_client.analyze_content(
                prompt,
                prompt_type='change_analysis'
            )
            
            if response.status == 'success':
                return response.data
            
        except Exception as e:
            self.logger.error(f"AI analysis failed: {e}")
        
        return {}
    
    def _determine_impact_level(self, score: float) -> ImpactLevel:
        """영향 수준 결정"""
        if score >= 80:
            return ImpactLevel.CRITICAL
        elif score >= 60:
            return ImpactLevel.HIGH
        elif score >= 40:
            return ImpactLevel.MEDIUM
        elif score >= 20:
            return ImpactLevel.LOW
        else:
            return ImpactLevel.MINIMAL
    
    def _determine_category(
        self,
        criteria_scores: Dict[str, float],
        ai_insights: Dict[str, Any]
    ) -> ChangeCategory:
        """변경 카테고리 결정"""
        # AI 인사이트 우선
        if ai_insights and "change_type" in ai_insights:
            ai_type = ai_insights["change_type"]
            if "policy" in ai_type.lower():
                return ChangeCategory.POLICY
            elif "financial" in ai_type.lower():
                return ChangeCategory.FINANCIAL
            elif "regulatory" in ai_type.lower():
                return ChangeCategory.REGULATORY
        
        # 기준 점수 기반
        if criteria_scores.get("policy_change", 0) > 0.5:
            return ChangeCategory.POLICY
        elif criteria_scores.get("financial_impact", 0) > 0.5:
            return ChangeCategory.FINANCIAL
        else:
            return ChangeCategory.INFORMATIONAL
    
    def _determine_urgency(
        self,
        score: float,
        criteria_scores: Dict[str, float]
    ) -> str:
        """긴급도 결정"""
        urgency_score = criteria_scores.get("urgency", 0)
        
        if score >= 80 or urgency_score > 0.8:
            return "immediate"
        elif score >= 60 or urgency_score > 0.6:
            return "high"
        elif score >= 40 or urgency_score > 0.4:
            return "medium"
        else:
            return "low"
    
    def _generate_summary(
        self,
        changes: str,
        impact_level: ImpactLevel,
        category: ChangeCategory,
        ai_insights: Dict[str, Any]
    ) -> str:
        """요약 생성"""
        # AI 요약 우선
        if ai_insights and "change_summary" in ai_insights:
            return ai_insights["change_summary"]
        
        # 기본 요약
        summary_parts = []
        
        summary_parts.append(f"{impact_level.value.upper()} 중요도")
        summary_parts.append(f"{category.value} 변경")
        
        # 변경 내용 요약
        lines = changes.splitlines()
        if lines:
            first_change = lines[0][:100]
            summary_parts.append(first_change)
        
        return " - ".join(summary_parts)
    
    def _calculate_confidence(
        self,
        criteria_scores: Dict[str, float],
        ai_insights: Dict[str, Any]
    ) -> float:
        """신뢰도 계산"""
        confidence_factors = []
        
        # 기준 점수 일관성
        scores = list(criteria_scores.values())
        if scores:
            # 표준편차가 낮으면 일관성 높음
            std_dev = np.std(scores)
            consistency = 1.0 - min(1.0, std_dev)
            confidence_factors.append(consistency)
        
        # AI 신뢰도
        if ai_insights and "confidence" in ai_insights:
            ai_confidence = ai_insights["confidence"]
            if isinstance(ai_confidence, (int, float)):
                confidence_factors.append(float(ai_confidence))
        
        # 평균 신뢰도
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        
        return 0.5  # 기본값
    
    def _save_evaluation_history(
        self,
        score: ImportanceScore,
        metadata: Optional[Dict[str, Any]]
    ):
        """평가 히스토리 저장"""
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "score": score.to_dict(),
            "metadata": metadata or {}
        }
        
        self.evaluation_history.append(history_entry)
        
        # 크기 제한
        if len(self.evaluation_history) > 1000:
            self.evaluation_history = self.evaluation_history[-1000:]
    
    def update_accuracy_metrics(
        self,
        predicted_important: bool,
        actual_important: bool
    ):
        """정확도 메트릭 업데이트"""
        if predicted_important and actual_important:
            self.accuracy_metrics["true_positives"] += 1
        elif predicted_important and not actual_important:
            self.accuracy_metrics["false_positives"] += 1
        elif not predicted_important and actual_important:
            self.accuracy_metrics["false_negatives"] += 1
        else:
            self.accuracy_metrics["true_negatives"] += 1
    
    def get_accuracy_report(self) -> Dict[str, Any]:
        """정확도 리포트"""
        tp = self.accuracy_metrics["true_positives"]
        fp = self.accuracy_metrics["false_positives"]
        tn = self.accuracy_metrics["true_negatives"]
        fn = self.accuracy_metrics["false_negatives"]
        
        total = tp + fp + tn + fn
        
        if total == 0:
            return {"message": "No evaluation data"}
        
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "accuracy": round(accuracy, 3),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1_score, 3),
            "total_evaluations": total,
            "confusion_matrix": {
                "true_positives": tp,
                "false_positives": fp,
                "true_negatives": tn,
                "false_negatives": fn
            }
        }
