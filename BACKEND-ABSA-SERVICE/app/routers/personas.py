"""
페르소나 분석 및 네트워크 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.db import get_db
from app.services.persona_analyzer import PersonaAnalyzer, PersonaProfile
import logging
from app.security import require_role, get_current_actor, Actor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("/{user_identifier}/analyze")
async def analyze_persona(
    user_identifier: str,
    platform: str = Query(..., description="Platform (reddit, twitter, news_comment, etc.)"),
    depth: int = Query(50, ge=1, le=500, description="Number of posts to analyze"),
    force_refresh: bool = Query(False, description="Force refresh even if cached"),
    db: Session = Depends(get_db)
):
    """
    사용자의 페르소나를 분석합니다.
    작성자의 과거 게시물과 댓글을 추적하여 종합적인 프로필을 생성합니다.
    """
    try:
        analyzer = PersonaAnalyzer(db)
        
        # 페르소나 분석
        profile = await analyzer.analyze_user_persona(
            user_identifier=user_identifier,
            platform=platform,
            depth=depth
        )
        
        return {
            "success": True,
            "profile": profile.to_dict(),
            "analysis_depth": depth,
            "platform": platform
        }
        
    except Exception as e:
        logger.error(f"Error analyzing persona: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# Identity Link Requests (RBAC)
# ---------------------------

@router.post("/identities/links/requests")
async def create_identity_link_request(
    payload: Dict[str, Any],
    actor: Actor = Depends(require_role(["admin", "analyst", "user"])),
    db: Session = Depends(get_db)
):
    """
    신원 링크 요청 생성 (analyst/user/admin)
    Required body: { platform, identifier, canonical_id?, evidence_type?, evidence_ref? }
    """
    try:
        from app.models import IdentityLinkRequest, IdentityAuditLog
        platform = payload.get("platform")
        identifier = payload.get("identifier")
        canonical_id = payload.get("canonical_id")
        evidence_type = payload.get("evidence_type")
        evidence_ref = payload.get("evidence_ref")

        if not platform or not identifier:
            raise HTTPException(status_code=400, detail="platform and identifier are required")

        req = IdentityLinkRequest(
            platform=platform,
            identifier=identifier,
            canonical_id=canonical_id,
            status="pending",
            evidence_type=evidence_type,
            evidence_ref=evidence_ref,
            requester_role=actor.role,
            requester_sub=actor.sub or ""
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        # 감사 로그
        audit = IdentityAuditLog(
            actor_role=actor.role,
            actor_sub=actor.sub or "",
            action="link_request",
            details={"request_id": req.id, "platform": platform, "identifier": identifier}
        )
        db.add(audit)
        db.commit()

        return {"success": True, "request_id": req.id, "status": req.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating identity link request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/identities/links/requests/{request_id}/approve")
async def approve_identity_link_request(
    request_id: int,
    actor: Actor = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    try:
        from app.models import IdentityLinkRequest, IdentityAuditLog
        req = db.query(IdentityLinkRequest).filter(IdentityLinkRequest.id == request_id).first()
        if not req:
            raise HTTPException(status_code=404, detail="request not found")
        if req.status != "pending":
            raise HTTPException(status_code=400, detail="request is not pending")

        req.status = "approved"
        req.decided_at = datetime.utcnow()
        req.decided_by = actor.sub or "admin"
        db.commit()

        audit = IdentityAuditLog(
            actor_role=actor.role,
            actor_sub=actor.sub or "",
            action="approve",
            details={"request_id": req.id, "platform": req.platform, "identifier": req.identifier}
        )
        db.add(audit)
        db.commit()

        return {"success": True, "request_id": req.id, "status": req.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving identity link request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/identities/links/requests/{request_id}/reject")
async def reject_identity_link_request(
    request_id: int,
    actor: Actor = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    try:
        from app.models import IdentityLinkRequest, IdentityAuditLog
        req = db.query(IdentityLinkRequest).filter(IdentityLinkRequest.id == request_id).first()
        if not req:
            raise HTTPException(status_code=404, detail="request not found")
        if req.status != "pending":
            raise HTTPException(status_code=400, detail="request is not pending")

        req.status = "rejected"
        req.decided_at = datetime.utcnow()
        req.decided_by = actor.sub or "admin"
        db.commit()

        audit = IdentityAuditLog(
            actor_role=actor.role,
            actor_sub=actor.sub or "",
            action="reject",
            details={"request_id": req.id, "platform": req.platform, "identifier": req.identifier}
        )
        db.add(audit)
        db.commit()

        return {"success": True, "request_id": req.id, "status": req.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting identity link request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# Persona Recalculation
# ---------------------------

@router.post("/recalculate/{persona_id}")
async def recalculate_persona(
    persona_id: str,
    platform: Optional[str] = Query(None, description="Platform of the persona for recalculation"),
    background_tasks: BackgroundTasks = None,
    actor: Actor = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """
    단일 페르소나 재계산을 스케줄합니다.
    platform이 저장되어 있지 않다면 쿼리 파라미터로 전달해야 합니다.
    """
    try:
        from app.models import UserPersona
        persona = db.query(UserPersona).filter(UserPersona.user_id == persona_id).first()
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")
        if not platform and not persona.platform:
            raise HTTPException(status_code=400, detail="platform is required for recalculation")

        # 백그라운드 재계산
        if background_tasks:
            background_tasks.add_task(
                recalculate_persona_async,
                username=persona.username,
                platform=platform or persona.platform,
                db=db
            )
        else:
            await recalculate_persona_async(username=persona.username, platform=platform or persona.platform, db=db)

        return {"success": True, "message": "Recalculation scheduled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling recalculation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def recalculate_persona_async(username: str, platform: str, db: Session):
    try:
        analyzer = PersonaAnalyzer(db)
        await analyzer.analyze_user_persona(
            user_identifier=username,
            platform=platform,
            depth=50
        )
    except Exception as e:
        logger.error(f"Error in recalculate_persona_async: {str(e)}")

@router.get("/network/{user_id}")
async def get_persona_network(
    user_id: str,
    depth: int = Query(1, ge=1, le=3, description="Network depth level"),
    min_connection_strength: float = Query(0.1, ge=0, le=1, description="Minimum connection strength to include"),
    db: Session = Depends(get_db)
):
    """
    사용자의 페르소나 네트워크를 가져옵니다.
    연결된 사용자들과의 관계를 메시 형태로 반환합니다.
    """
    try:
        from app.models import UserPersona, UserConnection
        
        # 중심 사용자 조회
        central_user = db.query(UserPersona).filter(
            UserPersona.user_id == user_id
        ).first()
        
        if not central_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        nodes = []
        links = []
        visited = set()
        
        # BFS로 네트워크 구축
        queue = [(central_user, 0)]
        visited.add(user_id)
        
        # 중심 노드 추가
        import json
        profile_data = json.loads(central_user.profile_data)
        nodes.append({
            "id": user_id,
            "username": central_user.username,
            "type": "primary",
            "depth": 0,
            "influence": profile_data.get("influence", {}).get("score", 0),
            "dominant_sentiment": profile_data.get("sentiment", {}).get("dominant", "neutral"),
            "post_count": profile_data.get("total_posts", 0) + profile_data.get("total_comments", 0)
        })
        
        while queue and len(queue) > 0:
            current_user, current_depth = queue.pop(0)
            
            if current_depth >= depth:
                continue
            
            # 연결된 사용자들 조회
            connections = db.query(UserConnection).filter(
                (UserConnection.user1_id == current_user.user_id) |
                (UserConnection.user2_id == current_user.user_id)
            ).filter(
                UserConnection.connection_strength >= min_connection_strength
            ).all()
            
            for conn in connections:
                # 연결된 사용자 ID 확인
                other_user_id = conn.user2_id if conn.user1_id == current_user.user_id else conn.user1_id
                
                if other_user_id not in visited:
                    visited.add(other_user_id)
                    
                    # 연결된 사용자 정보 조회
                    other_user = db.query(UserPersona).filter(
                        UserPersona.user_id == other_user_id
                    ).first()
                    
                    if other_user:
                        other_profile = json.loads(other_user.profile_data)
                        
                        # 노드 추가
                        nodes.append({
                            "id": other_user_id,
                            "username": other_user.username,
                            "type": "connected",
                            "depth": current_depth + 1,
                            "influence": other_profile.get("influence", {}).get("score", 0),
                            "dominant_sentiment": other_profile.get("sentiment", {}).get("dominant", "neutral"),
                            "post_count": other_profile.get("total_posts", 0) + other_profile.get("total_comments", 0)
                        })
                        
                        # 다음 레벨 탐색을 위해 큐에 추가
                        if current_depth + 1 < depth:
                            queue.append((other_user, current_depth + 1))
                
                # 링크 추가 (중복 방지)
                link_id = f"{min(current_user.user_id, other_user_id)}-{max(current_user.user_id, other_user_id)}"
                if not any(l.get("id") == link_id for l in links):
                    links.append({
                        "id": link_id,
                        "source": current_user.user_id,
                        "target": other_user_id,
                        "strength": conn.connection_strength,
                        "sentiment": conn.avg_sentiment,
                        "interaction_count": conn.interaction_count,
                        "common_topics": json.loads(conn.common_topics) if conn.common_topics else []
                    })
        
        return {
            "nodes": nodes,
            "links": links,
            "network_stats": {
                "total_nodes": len(nodes),
                "total_links": len(links),
                "max_depth": depth,
                "center_user": user_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting persona network: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{persona_id}/details")
async def get_persona_details(
    persona_id: str,
    include_recent_posts: bool = Query(True, description="Include recent posts"),
    include_connections: bool = Query(True, description="Include connections"),
    db: Session = Depends(get_db)
):
    """
    특정 페르소나의 상세 정보를 가져옵니다.
    """
    try:
        from app.models import UserPersona, Content, Comment, UserActivity
        import json
        
        # 페르소나 조회
        persona = db.query(UserPersona).filter(
            UserPersona.user_id == persona_id
        ).first()
        
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        profile_data = json.loads(persona.profile_data)

        # 평탄화된 필드 구성 (FE 요구사항 대응)
        dominant_sentiment = profile_data.get("sentiment", {}).get("dominant")
        sentiment_distribution = profile_data.get("sentiment", {}).get("distribution", {})
        influence = profile_data.get("influence", {}).get("score", 0)
        engagement_rate = profile_data.get("influence", {}).get("engagement_rate", 0)
        key_topics = profile_data.get("topics", {}).get("key_topics", [])
        topic_weights = profile_data.get("topics", {}).get("weights", {})
        argumentation_style = profile_data.get("language", {}).get("argumentation_style")
        formality_level = profile_data.get("language", {}).get("formality_level")
        total_posts = profile_data.get("total_posts", 0)
        total_comments = profile_data.get("total_comments", 0)
        tracked_sources = profile_data.get("metadata", {}).get("tracked_sources", [])

        # 신선도 계산
        last_calc = persona.last_calculated_at
        stale = False
        staleness_reason = None
        if last_calc:
            # 기본 임계값: 24h
            from app.config import settings
            threshold = timedelta(hours=settings.persona_staleness_hours_default)
            if datetime.utcnow() - last_calc > threshold:
                stale = True
                staleness_reason = "older_than_threshold"
            # 최근 활동 존재 여부
            recent_activity = db.query(UserActivity.id).filter(
                UserActivity.user_identifier == persona.username,
                UserActivity.tracked_at > last_calc
            ).first()
            if recent_activity:
                stale = True
                staleness_reason = "new_activity_since_last_calculation"

        response = {
            "user_id": persona_id,
            "username": persona.username,
            "dominant_sentiment": dominant_sentiment,
            "sentiment_distribution": sentiment_distribution,
            "influence": influence,
            "engagement_rate": engagement_rate,
            "key_topics": key_topics,
            "topic_weights": topic_weights,
            "argumentation_style": argumentation_style,
            "formality_level": formality_level,
            "total_posts": total_posts,
            "total_comments": total_comments,
            "tracked_sources": tracked_sources,
            "last_calculated_at": last_calc.isoformat() if last_calc else None,
            "stale": stale,
            "staleness_reason": staleness_reason,
            "raw_profile": profile_data,
        }
        
        # 최근 게시물 포함
        if include_recent_posts:
            recent_posts = db.query(Content).filter(
                Content.author == persona.username
            ).order_by(Content.created_at.desc()).limit(10).all()
            
            response["recent_posts"] = [
                {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                    "url": post.url,
                    "created_at": post.created_at.isoformat(),
                    "sentiment": post.sentiment_score,
                    "engagement": {
                        "likes": post.likes or 0,
                        "comments": post.comment_count or 0
                    }
                }
                for post in recent_posts
            ]
        
        # 연결 관계 포함
        if include_connections:
            from app.models import UserConnection
            
            connections = db.query(UserConnection).filter(
                (UserConnection.user1_id == persona_id) |
                (UserConnection.user2_id == persona_id)
            ).order_by(UserConnection.connection_strength.desc()).limit(20).all()
            
            response["connections"] = [
                {
                    "connected_user": conn.user2_id if conn.user1_id == persona_id else conn.user1_id,
                    "strength": conn.connection_strength,
                    "sentiment": conn.avg_sentiment,
                    "interaction_count": conn.interaction_count,
                    "common_topics": json.loads(conn.common_topics) if conn.common_topics else [],
                    "last_interaction": conn.last_interaction.isoformat() if conn.last_interaction else None
                }
                for conn in connections
            ]
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting persona details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_identifier}/track")
async def track_user_activity(
    user_identifier: str,
    platform: str,
    content_id: str,
    content_type: str = Query(..., regex="^(post|comment)$"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    사용자의 새로운 활동을 추적하고 페르소나를 업데이트합니다.
    """
    try:
        from app.models import Content, Comment, UserActivity
        
        # 활동 기록 저장
        activity = UserActivity(
            user_identifier=user_identifier,
            platform=platform,
            content_id=content_id,
            content_type=content_type,
            tracked_at=datetime.utcnow()
        )
        db.add(activity)
        db.commit()
        
        # 백그라운드로 페르소나 업데이트
        if background_tasks:
            background_tasks.add_task(
                update_persona_async,
                user_identifier=user_identifier,
                platform=platform,
                db=db
            )
        
        return {
            "success": True,
            "message": "Activity tracked successfully",
            "activity_id": activity.id
        }
        
    except Exception as e:
        logger.error(f"Error tracking user activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending")
async def get_trending_personas(
    time_window: int = Query(24, description="Time window in hours"),
    limit: int = Query(10, ge=1, le=50),
    sentiment_filter: Optional[str] = Query(None, regex="^(positive|negative|neutral)$"),
    db: Session = Depends(get_db)
):
    """
    트렌딩 페르소나들을 가져옵니다 (높은 영향력, 최근 활동 기준).
    """
    try:
        from app.models import UserPersona, UserActivity
        from sqlalchemy import desc, func
        import json
        
        # 시간 필터
        time_threshold = datetime.utcnow() - timedelta(hours=time_window)
        
        # 최근 활동이 있는 사용자들 조회 (서브쿼리 + 매핑)
        active_users_subq = db.query(
            UserActivity.user_identifier.label('user_identifier'),
            func.count(UserActivity.id).label('activity_count')
        ).filter(
            UserActivity.tracked_at >= time_threshold
        ).group_by(
            UserActivity.user_identifier
        ).subquery()

        # 빠르게 조회할 수 있도록 매핑 생성
        activity_rows = db.query(
            active_users_subq.c.user_identifier,
            active_users_subq.c.activity_count
        ).all()
        activity_counts = {r[0]: r[1] for r in activity_rows}

        # 페르소나 조회 및 정렬
        query = db.query(UserPersona).join(
            active_users_subq,
            UserPersona.username == active_users_subq.c.user_identifier
        ).order_by(
            desc(active_users_subq.c.activity_count)
        )

        personas = query.limit(limit).all()
        
        trending = []
        for persona in personas:
            profile = json.loads(persona.profile_data)
            
            # 감정 필터 적용
            if sentiment_filter and profile.get("sentiment", {}).get("dominant") != sentiment_filter:
                continue
            
            trending.append({
                "user_id": persona.user_id,
                "username": persona.username,
                "influence_score": profile.get("influence", {}).get("score", 0),
                "dominant_sentiment": profile.get("sentiment", {}).get("dominant"),
                "key_topics": profile.get("topics", {}).get("key_topics", [])[:5],
                "recent_activity_count": int(activity_counts.get(persona.username, 0) or 0),
                "engagement_rate": profile.get("influence", {}).get("engagement_rate", 0)
            })
        
        return {
            "trending": trending,
            "time_window_hours": time_window,
            "total_count": len(trending)
        }
        
    except Exception as e:
        logger.error(f"Error getting trending personas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def update_persona_async(user_identifier: str, platform: str, db: Session):
    """
    비동기로 페르소나를 업데이트합니다.
    """
    try:
        analyzer = PersonaAnalyzer(db)
        await analyzer.analyze_user_persona(
            user_identifier=user_identifier,
            platform=platform,
            depth=10  # 최근 10개만 빠르게 업데이트
        )
    except Exception as e:
        logger.error(f"Error updating persona: {str(e)}")


@router.post("/connections/update")
async def update_user_connections(
    user1_id: str,
    user2_id: str,
    interaction_type: str = Query(..., regex="^(reply|mention|quote|reaction)$"),
    sentiment: Optional[float] = None,
    topics: List[str] = Query(default=[]),
    db: Session = Depends(get_db)
):
    """
    사용자 간 연결 관계를 업데이트합니다.
    """
    try:
        from app.models import UserConnection
        import json
        
        # 기존 연결 조회 (양방향)
        connection = db.query(UserConnection).filter(
            ((UserConnection.user1_id == user1_id) & (UserConnection.user2_id == user2_id)) |
            ((UserConnection.user1_id == user2_id) & (UserConnection.user2_id == user1_id))
        ).first()
        
        if connection:
            # 업데이트
            connection.interaction_count += 1
            connection.last_interaction = datetime.utcnow()
            
            # 감정 업데이트
            if sentiment is not None:
                sentiments = json.loads(connection.sentiment_history) if connection.sentiment_history else []
                sentiments.append(sentiment)
                connection.sentiment_history = json.dumps(sentiments[-100:])  # 최근 100개만 유지
                connection.avg_sentiment = sum(sentiments[-100:]) / len(sentiments[-100:])
            
            # 주제 업데이트
            if topics:
                existing_topics = json.loads(connection.common_topics) if connection.common_topics else {}
                for topic in topics:
                    existing_topics[topic] = existing_topics.get(topic, 0) + 1
                connection.common_topics = json.dumps(existing_topics)
            
            # 연결 강도 재계산
            connection.connection_strength = min(1.0, connection.interaction_count / 100)
            
        else:
            # 새 연결 생성
            connection = UserConnection(
                user1_id=min(user1_id, user2_id),  # 일관된 순서 유지
                user2_id=max(user1_id, user2_id),
                interaction_count=1,
                connection_strength=0.01,
                avg_sentiment=sentiment or 0,
                sentiment_history=json.dumps([sentiment] if sentiment is not None else []),
                common_topics=json.dumps({topic: 1 for topic in topics}),
                first_interaction=datetime.utcnow(),
                last_interaction=datetime.utcnow()
            )
            db.add(connection)
        
        db.commit()
        
        return {
            "success": True,
            "connection": {
                "user1": connection.user1_id,
                "user2": connection.user2_id,
                "strength": connection.connection_strength,
                "interaction_count": connection.interaction_count,
                "avg_sentiment": connection.avg_sentiment
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating connections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
