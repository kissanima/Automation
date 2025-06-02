"""
Post Scheduling with Queue System - FIXED VERSION
Handles timing, persistence, and queued execution of automated posts
"""

import json
import time
import threading
import logging
import random
import queue
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from utils.file_manager import FileManager
from ui.settings_dialog import get_current_settings

class AutomationStatus(Enum):
    ONGOING = "ongoing"
    PAUSED = "paused"
    STOPPED = "stopped"

@dataclass
class ScheduledPost:
    id: str
    template_id: str
    group_urls: List[str]
    frequency_hours: int
    status: AutomationStatus
    next_post_time: float
    last_post_time: Optional[float] = None
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

@dataclass
class PostJob:
    """Represents a post job in the queue"""
    post_id: str
    scheduled_post: ScheduledPost
    template: Dict
    timestamp: float

class PostScheduler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.file_manager = FileManager()
        self.scheduled_posts: Dict[str, ScheduledPost] = {}
        self.facebook_login = None
        self.group_poster = None
        self.is_running = False
        
        # Queue system for sequential posting
        self.post_queue = queue.Queue()
        self.queue_worker_thread = None
        self.queue_lock = threading.Lock()
        self.is_processing = False
        
        self.load_scheduled_posts()
        self.start_queue_worker()
        
    def start_queue_worker(self):
        """Start the queue worker thread"""
        if self.queue_worker_thread is None or not self.queue_worker_thread.is_alive():
            self.queue_worker_thread = threading.Thread(
                target=self._queue_worker,
                daemon=True,
                name="PostQueueWorker"
            )
            self.queue_worker_thread.start()
            self.logger.info("Post queue worker started")
    
    def _queue_worker(self):
        """Worker thread that processes posts one at a time"""
        while True:
            try:
                # Get next job from queue (blocks until available)
                job = self.post_queue.get(timeout=1)
                
                with self.queue_lock:
                    if self.is_processing:
                        # Another job is already processing, put this back and wait
                        self.post_queue.put(job)
                        time.sleep(1)
                        continue
                    
                    self.is_processing = True
                
                try:
                    self.logger.info(f"QUEUE: Processing post job {job.post_id}")
                    self._execute_post_job(job)
                except Exception as e:
                    self.logger.error(f"QUEUE: Error processing job {job.post_id}: {e}")
                finally:
                    with self.queue_lock:
                        self.is_processing = False
                    
                    # Mark job as done
                    self.post_queue.task_done()
                    
                    # Wait between posts to avoid conflicts
                    time.sleep(5)
                
            except queue.Empty:
                # No jobs in queue, continue waiting
                continue
            except Exception as e:
                self.logger.error(f"QUEUE: Worker error: {e}")
                time.sleep(1)
    
    def set_dependencies(self, facebook_login, group_poster):
        """Set dependencies for posting operations"""
        self.facebook_login = facebook_login
        self.group_poster = group_poster
        self.logger.info("Dependencies set for scheduler")
    
    def add_scheduled_post(self, template_id: str, group_urls: List[str], frequency_hours: int, start_immediately: bool = True) -> str:
        """Add a new scheduled post automation"""
        post_id = f"schedule_{int(time.time())}_{len(self.scheduled_posts)}"
        
        # Calculate next post time
        if start_immediately:
            next_post_time = time.time() + 30  # 30 seconds
        else:
            next_post_time = time.time() + (frequency_hours * 3600)
        
        scheduled_post = ScheduledPost(
            id=post_id,
            template_id=template_id,
            group_urls=group_urls,
            frequency_hours=frequency_hours,
            status=AutomationStatus.ONGOING,
            next_post_time=next_post_time
        )
        
        self.scheduled_posts[post_id] = scheduled_post
        self.save_scheduled_posts()
        
        self.logger.info(f"Added scheduled post: {post_id} - Next post at: {datetime.fromtimestamp(next_post_time)}")
        return post_id
    
    def check_scheduled_posts(self):
        """Check and queue any posts that are due"""
        if not self.facebook_login or not self.group_poster:
            self.logger.warning("Dependencies not set, skipping post check")
            return
        
        current_time = time.time()
        due_posts = []
        
        for post_id, scheduled_post in self.scheduled_posts.items():
            if (scheduled_post.status == AutomationStatus.ONGOING and 
                scheduled_post.next_post_time <= current_time):
                
                # CRITICAL: Check if this job is already in the queue
                queue_size = self.post_queue.qsize()
                if queue_size > 0:
                    # Don't add more jobs if queue is busy
                    self.logger.debug(f"Queue busy ({queue_size} jobs), skipping new additions")
                    continue
                
                # CRITICAL: Check if this was recently posted (prevent duplicates)
                if scheduled_post.last_post_time:
                    time_since_last = current_time - scheduled_post.last_post_time
                    if time_since_last < 300:  # Less than 5 minutes ago
                        self.logger.warning(f"Post {post_id} was just executed {time_since_last:.0f}s ago, skipping")
                        continue
                
                due_posts.append((post_id, scheduled_post))
        
        if due_posts:
            self.logger.info(f"Found {len(due_posts)} posts due - adding to queue")
            
            for post_id, scheduled_post in due_posts:
                # Load template
                template = self.file_manager.get_template(scheduled_post.template_id)
                if template:
                    # Create job and add to queue
                    job = PostJob(
                        post_id=post_id,
                        scheduled_post=scheduled_post,
                        template=template,
                        timestamp=current_time
                    )
                    
                    self.post_queue.put(job)
                    self.logger.info(f"QUEUE: Added job {post_id} to queue (queue size: {self.post_queue.qsize()})")
                    
                    # CRITICAL: Update next post time IMMEDIATELY to prevent re-queuing
                    scheduled_post.next_post_time = time.time() + (scheduled_post.frequency_hours * 3600)
                    self.save_scheduled_posts()
                    self.logger.info(f"QUEUE: Pre-updated next post time for {post_id} to prevent duplicates")
                else:
                    self.logger.error(f"Template not found for {post_id}: {scheduled_post.template_id}")

    
    def _execute_post_job(self, job: PostJob):
        """Execute a single post job from the queue with configurable settings"""
        try:
            post_id = job.post_id
            scheduled_post = job.scheduled_post
            template = job.template
            
            # Load current settings for configurable behavior
            try:
                from ui.settings_dialog import get_current_settings
                settings = get_current_settings()
            except ImportError:
                # Fallback to defaults if settings module not available
                settings = {
                    'min_group_delay': 60,
                    'max_group_delay': 120,
                    'retry_delay_minutes': 30,
                    'max_retries': 3,
                    'detailed_logging': False
                }
            
            # Detailed logging if enabled
            if settings.get('detailed_logging', False):
                self.logger.info(f"QUEUE: Executing post {post_id} with settings: "
                            f"group_delays={settings.get('min_group_delay')}-{settings.get('max_group_delay')}s, "
                            f"retry_delay={settings.get('retry_delay_minutes')}min")
            else:
                self.logger.info(f"QUEUE: Executing post {post_id}")
            
            # Check login status
            if not self.facebook_login or not self.facebook_login.is_logged_in:
                retry_delay_seconds = settings.get('retry_delay_minutes', 30) * 60
                self.logger.error(f"QUEUE: Not logged in, rescheduling {post_id} for {settings.get('retry_delay_minutes', 30)} minutes")
                self._reschedule_post(scheduled_post, retry_delay_seconds)
                return
            
            # Verify session
            if not self.facebook_login.is_session_valid():
                retry_delay_seconds = settings.get('retry_delay_minutes', 30) * 60
                self.logger.error(f"QUEUE: Session invalid, rescheduling {post_id} for {settings.get('retry_delay_minutes', 30)} minutes")
                self._reschedule_post(scheduled_post, retry_delay_seconds)
                return
            
            # Post to each group sequentially
            successful_posts = 0
            total_groups = len(scheduled_post.group_urls)
            
            # Get group delay settings
            min_group_delay = settings.get('min_group_delay', 60)
            max_group_delay = settings.get('max_group_delay', 120)
            
            # Validate delay settings
            if min_group_delay > max_group_delay:
                self.logger.warning(f"Invalid delay settings: min({min_group_delay}) > max({max_group_delay}), using defaults")
                min_group_delay, max_group_delay = 60, 120
            
            self.logger.info(f"QUEUE: Posting to {total_groups} groups for {post_id} "
                            f"(delays: {min_group_delay}-{max_group_delay}s between groups)")
            
            for i, group_url in enumerate(scheduled_post.group_urls, 1):
                try:
                    # Detailed logging for each group if enabled
                    if settings.get('detailed_logging', False):
                        self.logger.info(f"QUEUE: Starting post {i}/{total_groups} to {group_url}")
                    else:
                        self.logger.info(f"QUEUE: Posting to group {i}/{total_groups}: {group_url}")
                    
                    # Record start time for this group
                    group_start_time = time.time()
                    
                    # Execute the post
                    success = self.group_poster.post_to_group(group_url, template)
                    
                    # Calculate posting time
                    group_duration = time.time() - group_start_time
                    
                    if success:
                        successful_posts += 1
                        if settings.get('detailed_logging', False):
                            self.logger.info(f"QUEUE: ✅ Group {i}/{total_groups} completed in {group_duration:.1f}s")
                        else:
                            self.logger.info(f"QUEUE: Successfully posted to group {i}/{total_groups}")
                        
                        # Wait between groups using configurable delays
                        if i < total_groups:
                            delay = random.randint(min_group_delay, max_group_delay)
                            
                            if settings.get('detailed_logging', False):
                                remaining_groups = total_groups - i
                                estimated_remaining_time = (delay + 120) * remaining_groups  # Rough estimate
                                self.logger.info(f"QUEUE: Waiting {delay}s before next group "
                                            f"(~{estimated_remaining_time//60}min remaining for {remaining_groups} groups)")
                            else:
                                self.logger.info(f"QUEUE: Waiting {delay} seconds before next group...")
                            
                            time.sleep(delay)
                    else:
                        if settings.get('detailed_logging', False):
                            self.logger.error(f"QUEUE: ❌ Group {i}/{total_groups} failed after {group_duration:.1f}s: {group_url}")
                        else:
                            self.logger.error(f"QUEUE: Failed to post to group {i}/{total_groups}: {group_url}")
                            
                except Exception as e:
                    self.logger.error(f"QUEUE: Error posting to group {group_url}: {e}")
                    
                    # If detailed logging, show more error context
                    if settings.get('detailed_logging', False):
                        import traceback
                        self.logger.debug(f"QUEUE: Full error trace: {traceback.format_exc()}")
            
            # CRITICAL FIX: Update timing IMMEDIATELY after completion
            current_time = time.time()
            scheduled_post.last_post_time = current_time
            
            # Calculate NEXT post time (not immediate)
            next_post_time = current_time + (scheduled_post.frequency_hours * 3600)
            scheduled_post.next_post_time = next_post_time
            
            # SAVE IMMEDIATELY to prevent re-queuing
            self.save_scheduled_posts()
            
            # Enhanced logging for completion
            next_post_datetime = datetime.fromtimestamp(next_post_time)
            if settings.get('detailed_logging', False):
                total_execution_time = current_time - job.timestamp
                self.logger.info(f"QUEUE: ✅ Updated next post time to: {next_post_datetime.strftime('%Y-%m-%d %H:%M:%S')} "
                            f"(total execution: {total_execution_time:.1f}s)")
            else:
                self.logger.info(f"QUEUE: Updated next post time to: {next_post_datetime}")
            
            # Log execution with settings context
            self.log_post_execution(post_id, scheduled_post, successful_posts, total_groups)
            
            # Final status report
            if successful_posts > 0:
                success_rate = (successful_posts / total_groups) * 100
                if settings.get('detailed_logging', False):
                    self.logger.info(f"QUEUE: ✅ Completed {post_id} - {successful_posts}/{total_groups} successful ({success_rate:.1f}% success rate)")
                else:
                    self.logger.info(f"QUEUE: Completed {post_id} - {successful_posts}/{total_groups} successful")
            else:
                # Use longer retry delay for complete failures
                retry_delay_seconds = settings.get('retry_delay_minutes', 30) * 60 * 2  # Double the retry time for complete failure
                self.logger.warning(f"QUEUE: All posts failed for {post_id}, rescheduling for {retry_delay_seconds//60} minutes")
                self._reschedule_post(scheduled_post, retry_delay_seconds)
            
        except Exception as e:
            # Handle settings-aware error recovery
            try:
                from ui.settings_dialog import get_current_settings
                settings = get_current_settings()
                retry_delay_seconds = settings.get('retry_delay_minutes', 30) * 60
            except:
                retry_delay_seconds = 3600  # 1 hour fallback
            
            self.logger.error(f"QUEUE: Critical error executing post job {job.post_id}: {e}")
            
            # Enhanced error logging if detailed logging is enabled
            try:
                if settings.get('detailed_logging', False):
                    import traceback
                    self.logger.error(f"QUEUE: Full error traceback: {traceback.format_exc()}")
            except:
                pass
            
            self._reschedule_post(job.scheduled_post, retry_delay_seconds)


    
    def _reschedule_post(self, scheduled_post: ScheduledPost, delay_seconds: int):
        """Reschedule a failed post"""
        scheduled_post.next_post_time = time.time() + delay_seconds
        self.save_scheduled_posts()
        self.logger.info(f"Rescheduled {scheduled_post.id} for {delay_seconds} seconds from now")
    
    def get_queue_status(self):
        """Get current queue status"""
        return {
            'queue_size': self.post_queue.qsize(),
            'is_processing': self.is_processing,
            'worker_alive': self.queue_worker_thread.is_alive() if self.queue_worker_thread else False
        }
    
    def pause_automation(self, post_id: str) -> bool:
        """Pause an ongoing automation"""
        if post_id in self.scheduled_posts:
            self.scheduled_posts[post_id].status = AutomationStatus.PAUSED
            self.save_scheduled_posts()
            self.logger.info(f"Paused automation: {post_id}")
            return True
        return False
    
    def resume_automation(self, post_id: str) -> bool:
        """Resume a paused automation"""
        if post_id in self.scheduled_posts:
            scheduled_post = self.scheduled_posts[post_id]
            if scheduled_post.status == AutomationStatus.PAUSED:
                scheduled_post.status = AutomationStatus.ONGOING
                if scheduled_post.next_post_time < time.time():
                    scheduled_post.next_post_time = time.time() + (scheduled_post.frequency_hours * 3600)
                self.save_scheduled_posts()
                self.logger.info(f"Resumed automation: {post_id}")
                return True
        return False
    
    def delete_automation(self, post_id: str) -> bool:
        """Delete an automation completely"""
        if post_id in self.scheduled_posts:
            del self.scheduled_posts[post_id]
            self.save_scheduled_posts()
            self.logger.info(f"Deleted automation: {post_id}")
            return True
        return False
    
    def force_execute_post(self, post_id: str):
        """Force execute a specific post immediately"""
        if post_id in self.scheduled_posts:
            scheduled_post = self.scheduled_posts[post_id]
            if scheduled_post.status == AutomationStatus.ONGOING:
                template = self.file_manager.get_template(scheduled_post.template_id)
                if template:
                    job = PostJob(
                        post_id=post_id,
                        scheduled_post=scheduled_post,
                        template=template,
                        timestamp=time.time()
                    )
                    self.post_queue.put(job)
                    self.logger.info(f"Force queued post: {post_id}")
                    return True
        return False
    
    def get_scheduled_posts(self) -> Dict[str, ScheduledPost]:
        """Get all scheduled posts"""
        return self.scheduled_posts.copy()
    
    def log_post_execution(self, post_id: str, scheduled_post: ScheduledPost, successful: int, total: int):
        """Log post execution details"""
        log_entry = {
            'timestamp': time.time(),
            'post_id': post_id,
            'template_id': scheduled_post.template_id,
            'groups_targeted': total,
            'successful_posts': successful,
            'failed_posts': total - successful,
            'next_scheduled': scheduled_post.next_post_time,
            'status': 'success' if successful > 0 else 'failed'
        }
        
        self.file_manager.add_log_entry(log_entry)
    
    def save_scheduled_posts(self):
        """Save scheduled posts to file"""
        try:
            data = {}
            for post_id, scheduled_post in self.scheduled_posts.items():
                post_dict = asdict(scheduled_post)
                post_dict['status'] = scheduled_post.status.value
                data[post_id] = post_dict
            
            self.file_manager.save_automations(data)
            
        except Exception as e:
            self.logger.error(f"Failed to save scheduled posts: {e}")
    
    def load_scheduled_posts(self):
        """Load scheduled posts from file"""
        try:
            data = self.file_manager.load_automations()
            
            for post_id, post_data in data.items():
                post_data['status'] = AutomationStatus(post_data['status'])
                scheduled_post = ScheduledPost(**post_data)
                self.scheduled_posts[post_id] = scheduled_post
            
            self.logger.info(f"Loaded {len(self.scheduled_posts)} scheduled posts")
            
        except Exception as e:
            self.logger.error(f"Failed to load scheduled posts: {e}")
