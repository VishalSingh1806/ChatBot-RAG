"""
Scheduler for Automated CPCB Data Updates
Runs data collection and database updates on a schedule
"""

import schedule
import time
from datetime import datetime
import logging
from run_data_update import run_complete_update
import os

# Setup logging
log_dir = "./logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'scheduler.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DataUpdateScheduler:
    def __init__(self, db_path: str = None, collection_name: str = "EPR-Merged"):
        self.db_path = db_path
        self.collection_name = collection_name
        self.last_run = None
        self.run_count = 0

    def job(self):
        """Execute the data update job"""
        logger.info("="*70)
        logger.info(f"🚀 Starting scheduled data update (Run #{self.run_count + 1})")
        logger.info("="*70)

        try:
            success = run_complete_update(
                db_path=self.db_path,
                collection_name=self.collection_name
            )

            if success:
                self.last_run = datetime.now()
                self.run_count += 1
                logger.info(f"✅ Scheduled update completed successfully")
            else:
                logger.error(f"❌ Scheduled update failed")

        except Exception as e:
            logger.error(f"❌ Error during scheduled update: {e}", exc_info=True)

        logger.info(f"⏰ Next run scheduled according to schedule")
        logger.info("="*70 + "\n")

    def run_scheduler(self, schedule_config: str = "daily"):
        """
        Run the scheduler

        Args:
            schedule_config: One of:
                - "hourly" - Every hour
                - "daily" - Once per day at 2 AM
                - "twice-daily" - At 2 AM and 2 PM
                - "weekly" - Every Monday at 2 AM
                - "custom:HH:MM" - Custom time (e.g., "custom:14:30")
        """

        logger.info("="*70)
        logger.info("📅 CPCB Data Update Scheduler Started")
        logger.info("="*70)
        logger.info(f"Schedule: {schedule_config}")
        logger.info(f"Database: {self.db_path or 'default from config'}")
        logger.info(f"Collection: {self.collection_name}")
        logger.info("="*70)

        # Configure schedule
        if schedule_config == "hourly":
            schedule.every().hour.do(self.job)
            logger.info("⏰ Scheduled to run every hour")

        elif schedule_config == "daily":
            schedule.every().day.at("02:00").do(self.job)
            logger.info("⏰ Scheduled to run daily at 2:00 AM")

        elif schedule_config == "twice-daily":
            schedule.every().day.at("02:00").do(self.job)
            schedule.every().day.at("14:00").do(self.job)
            logger.info("⏰ Scheduled to run at 2:00 AM and 2:00 PM daily")

        elif schedule_config == "weekly":
            schedule.every().monday.at("02:00").do(self.job)
            logger.info("⏰ Scheduled to run every Monday at 2:00 AM")

        elif schedule_config.startswith("custom:"):
            time_str = schedule_config.split(":")[1] + ":" + schedule_config.split(":")[2]
            schedule.every().day.at(time_str).do(self.job)
            logger.info(f"⏰ Scheduled to run daily at {time_str}")

        else:
            logger.error(f"❌ Unknown schedule config: {schedule_config}")
            return

        # Run immediately on start
        logger.info("\n🎯 Running initial update immediately...")
        self.job()

        # Keep running
        logger.info("\n👀 Scheduler is now running. Press Ctrl+C to stop.\n")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("\n⚠️  Scheduler stopped by user")
            logger.info(f"📊 Total runs completed: {self.run_count}")
            if self.last_run:
                logger.info(f"⏰ Last successful run: {self.last_run.strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="CPCB Data Update Scheduler")
    parser.add_argument('--db-path', help='ChromaDB path (default: from config)')
    parser.add_argument('--collection', default='EPR-Merged', help='Collection name')
    parser.add_argument(
        '--schedule',
        default='daily',
        help='Schedule: hourly, daily, twice-daily, weekly, or custom:HH:MM'
    )

    args = parser.parse_args()

    scheduler = DataUpdateScheduler(
        db_path=args.db_path,
        collection_name=args.collection
    )

    scheduler.run_scheduler(schedule_config=args.schedule)


if __name__ == "__main__":
    main()
