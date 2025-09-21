"""
Analytics models for PromoWeb Africa.
Handles tracking, reporting, and business intelligence.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSON, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class SearchAnalytic(Base):
    """Track search queries and behavior."""
    
    __tablename__ = "search_analytics"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Search query
    query = Column(String(255), nullable=False, index=True)
    normalized_query = Column(String(255), nullable=True, index=True)  # Cleaned/normalized version
    
    # User context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Search results
    results_count = Column(Integer, default=0, nullable=False)
    clicked_product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    click_position = Column(Integer, nullable=True)  # Position of clicked result
    
    # Filters used
    filters_applied = Column(JSON, nullable=True)  # Category, price range, etc.
    sort_order = Column(String(50), nullable=True)  # Sort criteria used
    
    # Technical details
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    page_number = Column(Integer, default=1, nullable=False)
    
    # Timing
    search_duration_ms = Column(Integer, nullable=True)  # Time to get results
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="search_analytics")
    clicked_product = relationship("Product")
    
    # Indexes
    __table_args__ = (
        Index('idx_search_analytics_query', 'query'),
        Index('idx_search_analytics_user_session', 'user_id', 'session_id'),
        Index('idx_search_analytics_created_at', 'created_at'),
        Index('idx_search_analytics_results', 'results_count'),
    )
    
    def __repr__(self):
        return f"<SearchAnalytic(id={self.id}, query='{self.query}', results={self.results_count})>"
    
    @property
    def had_results(self) -> bool:
        """Check if search returned results."""
        return self.results_count > 0
    
    @property
    def had_click(self) -> bool:
        """Check if user clicked on a result."""
        return self.clicked_product_id is not None
    
    @property
    def click_through_rate(self) -> float:
        """Calculate CTR for this search (0 or 1 for individual search)."""
        return 1.0 if self.had_click else 0.0


class ProductView(Base):
    """Track product page views for analytics."""
    
    __tablename__ = "product_views"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Session context
    session_id = Column(String(255), nullable=True, index=True)
    
    # View context
    referrer = Column(String(500), nullable=True)  # Where user came from
    source = Column(String(100), nullable=True)    # search, category, promotion, etc.
    campaign = Column(String(100), nullable=True)  # Marketing campaign
    
    # Technical details
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    
    # Engagement metrics
    time_on_page_seconds = Column(Integer, nullable=True)
    scroll_depth_percent = Column(Integer, nullable=True)
    
    # Conversion indicators
    added_to_cart = Column(Boolean, default=False, nullable=False)
    purchased = Column(Boolean, default=False, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="product_views")
    user = relationship("User", back_populates="product_views")
    
    # Indexes
    __table_args__ = (
        Index('idx_product_views_product', 'product_id'),
        Index('idx_product_views_user', 'user_id'),
        Index('idx_product_views_session', 'session_id'),
        Index('idx_product_views_created_at', 'created_at'),
        Index('idx_product_views_source', 'source'),
    )
    
    def __repr__(self):
        return f"<ProductView(id={self.id}, product_id={self.product_id}, user_id={self.user_id})>"
    
    @property
    def is_bounce(self) -> bool:
        """Check if this was a bounce (very short time on page)."""
        return self.time_on_page_seconds is not None and self.time_on_page_seconds < 30
    
    @property
    def engagement_level(self) -> str:
        """Get engagement level based on time and scroll."""
        if not self.time_on_page_seconds:
            return "unknown"
        
        if self.time_on_page_seconds < 30:
            return "low"
        elif self.time_on_page_seconds < 120:
            return "medium"
        else:
            return "high"


class CartAbandonmentEvent(Base):
    """Track cart abandonment for recovery campaigns."""
    
    __tablename__ = "cart_abandonment_events"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Cart state at abandonment
    cart_value = Column(Integer, nullable=False)  # Total cart value in XAF
    item_count = Column(Integer, nullable=False)
    
    # Abandonment context
    last_page = Column(String(255), nullable=True)  # Last page before abandonment
    abandonment_stage = Column(String(50), nullable=True)  # cart, checkout, payment
    
    # Recovery efforts
    email_sent = Column(Boolean, default=False, nullable=False)
    email_opened = Column(Boolean, default=False, nullable=False)
    email_clicked = Column(Boolean, default=False, nullable=False)
    recovered = Column(Boolean, default=False, nullable=False)
    recovery_order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    
    # Timestamps
    abandoned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    recovered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    cart = relationship("Cart")
    user = relationship("User")
    recovery_order = relationship("Order")
    
    # Indexes
    __table_args__ = (
        Index('idx_cart_abandonment_user', 'user_id'),
        Index('idx_cart_abandonment_abandoned_at', 'abandoned_at'),
        Index('idx_cart_abandonment_recovered', 'recovered'),
    )
    
    def __repr__(self):
        return f"<CartAbandonmentEvent(id={self.id}, cart_id={self.cart_id}, value={self.cart_value})>"
    
    @property
    def recovery_rate(self) -> float:
        """Get recovery rate (0 or 1 for individual event)."""
        return 1.0 if self.recovered else 0.0
    
    def mark_as_recovered(self, order_id: str) -> None:
        """Mark cart as recovered."""
        self.recovered = True
        self.recovery_order_id = order_id
        self.recovered_at = datetime.utcnow()


class ConversionFunnel(Base):
    """Track user journey through conversion funnel."""
    
    __tablename__ = "conversion_funnels"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=False, index=True)
    
    # Funnel steps (timestamps)
    landed_at = Column(DateTime(timezone=True), nullable=True)       # First page visit
    viewed_product_at = Column(DateTime(timezone=True), nullable=True)  # First product view
    added_to_cart_at = Column(DateTime(timezone=True), nullable=True)   # First add to cart
    started_checkout_at = Column(DateTime(timezone=True), nullable=True) # Checkout started
    completed_order_at = Column(DateTime(timezone=True), nullable=True)  # Order completed
    
    # Traffic source
    source = Column(String(100), nullable=True)     # organic, paid, social, etc.
    medium = Column(String(100), nullable=True)     # search, display, email, etc.
    campaign = Column(String(100), nullable=True)   # Campaign name
    referrer = Column(String(500), nullable=True)   # Referring URL
    
    # Device/browser info
    device_type = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)
    
    # Final outcome
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    conversion_value = Column(Integer, nullable=True)  # Order value if converted
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    order = relationship("Order")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversion_funnel_session', 'session_id'),
        Index('idx_conversion_funnel_user', 'user_id'),
        Index('idx_conversion_funnel_source', 'source', 'medium'),
        Index('idx_conversion_funnel_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ConversionFunnel(id={self.id}, session_id='{self.session_id}')>"
    
    @property
    def converted(self) -> bool:
        """Check if session converted to order."""
        return self.completed_order_at is not None
    
    @property
    def funnel_stage(self) -> str:
        """Get the furthest stage reached."""
        if self.completed_order_at:
            return "converted"
        elif self.started_checkout_at:
            return "checkout"
        elif self.added_to_cart_at:
            return "cart"
        elif self.viewed_product_at:
            return "product"
        elif self.landed_at:
            return "landing"
        return "unknown"
    
    @property
    def time_to_conversion(self) -> Optional[int]:
        """Get time to conversion in seconds."""
        if self.converted and self.landed_at:
            return int((self.completed_order_at - self.landed_at).total_seconds())
        return None


class PerformanceMetric(Base):
    """Store performance metrics and KPIs."""
    
    __tablename__ = "performance_metrics"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric identification
    metric_name = Column(String(100), nullable=False, index=True)
    metric_category = Column(String(50), nullable=False, index=True)  # sales, traffic, conversion, etc.
    
    # Metric value
    value = Column(Integer, nullable=False)  # Use integer for all metrics (store cents, etc.)
    unit = Column(String(20), nullable=False)  # xaf, percent, count, seconds, etc.
    
    # Time period
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Dimensions for filtering
    dimensions = Column(JSON, nullable=True)  # Additional grouping data
    
    # Timestamp
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_performance_metric_name_period', 'metric_name', 'period_type', 'period_start'),
        Index('idx_performance_metric_category', 'metric_category'),
        Index('idx_performance_metric_recorded_at', 'recorded_at'),
    )
    
    def __repr__(self):
        return f"<PerformanceMetric(name='{self.metric_name}', value={self.value}, period='{self.period_type}')>"
    
    @property
    def formatted_value(self) -> str:
        """Get formatted value with unit."""
        if self.unit == 'xaf':
            return f"{self.value:,} XAF"
        elif self.unit == 'percent':
            return f"{self.value/100:.1f}%"
        elif self.unit == 'count':
            return f"{self.value:,}"
        elif self.unit == 'seconds':
            return f"{self.value}s"
        return f"{self.value} {self.unit}"


class ABTest(Base):
    """A/B testing experiments."""
    
    __tablename__ = "ab_tests"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Test identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    hypothesis = Column(Text, nullable=True)
    
    # Test configuration
    variants = Column(JSON, nullable=False)  # List of variant configurations
    traffic_split = Column(JSON, nullable=False)  # Percentage allocation per variant
    
    # Success metrics
    primary_metric = Column(String(100), nullable=False)  # Main KPI to track
    secondary_metrics = Column(JSON, default=list, nullable=False)
    
    # Test status
    status = Column(String(20), default='draft', nullable=False)  # draft, running, paused, completed
    
    # Time period
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    statistical_significance = Column(Boolean, nullable=True)
    confidence_level = Column(Integer, nullable=True)  # 90, 95, 99
    winning_variant = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    participants = relationship("ABTestParticipant", back_populates="ab_test", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ABTest(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if test is currently running."""
        if self.status != 'running':
            return False
        
        now = datetime.utcnow()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        
        return True
    
    @property
    def participant_count(self) -> int:
        """Get total number of participants."""
        return len(self.participants)


class ABTestParticipant(Base):
    """Track A/B test participants."""
    
    __tablename__ = "ab_test_participants"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    ab_test_id = Column(UUID(as_uuid=True), ForeignKey("ab_tests.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Participant details
    session_id = Column(String(255), nullable=True)
    variant_assigned = Column(String(50), nullable=False)
    
    # Conversion tracking
    converted = Column(Boolean, default=False, nullable=False)
    conversion_value = Column(Integer, nullable=True)
    conversion_time = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamp
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    ab_test = relationship("ABTest", back_populates="participants")
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_ab_test_participant_test', 'ab_test_id'),
        Index('idx_ab_test_participant_user', 'user_id'),
        Index('idx_ab_test_participant_variant', 'variant_assigned'),
    )
    
    def __repr__(self):
        return f"<ABTestParticipant(id={self.id}, test_id={self.ab_test_id}, variant='{self.variant_assigned}')>"
    
    def record_conversion(self, value: Optional[int] = None) -> None:
        """Record conversion for this participant."""
        self.converted = True
        self.conversion_value = value
        self.conversion_time = datetime.utcnow()
