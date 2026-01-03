"""
Analytics module for tracking and analyzing optimization metrics.
Provides data for the advanced analytics dashboard.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func, and_
from database import db, OptimizationSession, DailyUsage

logger = logging.getLogger(__name__)


class Analytics:
    """Analytics service for collecting and aggregating metrics."""
    
    @staticmethod
    def get_user_analytics(user_id: Optional[int], days: int = 30) -> Dict:
        """
        Get comprehensive analytics for a user.

        Args:
            user_id: User ID (None for anonymous)
            days: Number of days to analyze

        Returns:
            Dictionary with analytics data
        """
        db_session = db.get_session()
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            # Total optimizations
            total_optimizations = db_session.query(OptimizationSession).filter(
                OptimizationSession.user_id == user_id if user_id else True
            ).count()

            # Optimizations in date range
            optimizations_in_range = db_session.query(OptimizationSession).filter(
                and_(
                    OptimizationSession.user_id == user_id if user_id else True,
                    OptimizationSession.created_at >= datetime.combine(start_date, datetime.min.time()),
                    OptimizationSession.created_at <= datetime.combine(end_date, datetime.max.time())
                )
            ).count()

            # Average quality score
            avg_score = db_session.query(
                func.avg(OptimizationSession.quality_score)
            ).filter(
                and_(
                    OptimizationSession.user_id == user_id if user_id else True,
                    OptimizationSession.quality_score.isnot(None)
                )
            ).scalar() or 0

            # Quality score distribution
            score_distribution = db_session.query(
                OptimizationSession.quality_score,
                func.count(OptimizationSession.id)
            ).filter(
                and_(
                    OptimizationSession.user_id == user_id if user_id else True,
                    OptimizationSession.quality_score.isnot(None)
                )
            ).group_by(OptimizationSession.quality_score).all()

            # Prompt type distribution
            type_distribution = db_session.query(
                OptimizationSession.prompt_type,
                func.count(OptimizationSession.id)
            ).filter(
                OptimizationSession.user_id == user_id if user_id else True
            ).group_by(OptimizationSession.prompt_type).all()

            # Daily usage trend
            daily_usage = db_session.query(
                DailyUsage.date,
                DailyUsage.usage_count
            ).filter(
                and_(
                    DailyUsage.user_id == user_id if user_id else True,
                    DailyUsage.date >= start_date,
                    DailyUsage.date <= end_date
                )
            ).order_by(DailyUsage.date).all()

            # Average processing time
            avg_processing_time = db_session.query(
                func.avg(OptimizationSession.processing_time)
            ).filter(
                and_(
                    OptimizationSession.user_id == user_id if user_id else True,
                    OptimizationSession.processing_time.isnot(None)
                )
            ).scalar() or 0

            # Total tokens used
            total_tokens = db_session.query(
                func.sum(OptimizationSession.tokens_used)
            ).filter(
                and_(
                    OptimizationSession.user_id == user_id if user_id else True,
                    OptimizationSession.tokens_used.isnot(None)
                )
            ).scalar() or 0

            return {
                "total_optimizations": total_optimizations,
                "optimizations_in_range": optimizations_in_range,
                "average_quality_score": round(float(avg_score), 2),
                "score_distribution": {str(score): count for score, count in score_distribution},
                "type_distribution": {ptype: count for ptype, count in type_distribution},
                "daily_usage": [{"date": str(du.date), "count": du.usage_count} for du in daily_usage],
                "average_processing_time": round(float(avg_processing_time), 2),
                "total_tokens_used": int(total_tokens),
                "date_range": {
                    "start": str(start_date),
                    "end": str(end_date)
                }
            }
        except Exception as e:
            logger.error(f"Error getting user analytics: {str(e)}")
            return {}
        finally:
            db_session.close()
    
    @staticmethod
    def get_quality_trends(user_id: Optional[int], days: int = 30) -> List[Dict]:
        """
        Get quality score trends over time.

        Args:
            user_id: User ID
            days: Number of days

        Returns:
            List of daily average quality scores
        """
        db_session = db.get_session()
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            trends = db_session.query(
                func.date(OptimizationSession.created_at).label('date'),
                func.avg(OptimizationSession.quality_score).label('avg_score'),
                func.count(OptimizationSession.id).label('count')
            ).filter(
                and_(
                    OptimizationSession.user_id == user_id if user_id else True,
                    OptimizationSession.created_at >= datetime.combine(start_date, datetime.min.time()),
                    OptimizationSession.created_at <= datetime.combine(end_date, datetime.max.time()),
                    OptimizationSession.quality_score.isnot(None)
                )
            ).group_by(func.date(OptimizationSession.created_at)).order_by('date').all()

            return [
                {
                    "date": str(trend.date),
                    "average_score": round(float(trend.avg_score), 2),
                    "count": trend.count
                }
                for trend in trends
            ]
        except Exception as e:
            logger.error(f"Error getting quality trends: {str(e)}")
            return []
        finally:
            db_session.close()

    @staticmethod
    def get_top_prompts(user_id: Optional[int], limit: int = 10) -> List[Dict]:
        """
        Get top performing prompts by quality score.

        Args:
            user_id: User ID
            limit: Number of prompts to return

        Returns:
            List of top prompts
        """
        db_session = db.get_session()
        try:
            top_prompts = db_session.query(OptimizationSession).filter(
                and_(
                    OptimizationSession.user_id == user_id if user_id else True,
                    OptimizationSession.quality_score.isnot(None)
                )
            ).order_by(OptimizationSession.quality_score.desc()).limit(limit).all()

            return [
                {
                    "id": prompt.id,
                    "original_prompt": prompt.original_prompt[:100] + "..." if len(prompt.original_prompt) > 100 else prompt.original_prompt,
                    "quality_score": prompt.quality_score,
                    "prompt_type": prompt.prompt_type,
                    "created_at": prompt.created_at.isoformat()
                }
                for prompt in top_prompts
            ]
        except Exception as e:
            logger.error(f"Error getting top prompts: {str(e)}")
            return []
        finally:
            db_session.close()
    
    @staticmethod
    def log_event(user_id: Optional[int], event_type: str, event_data: Optional[Dict] = None):
        """Log an analytics event."""
        db.log_analytics_event(user_id, event_type, event_data)
