"""
Django management command to automatically close expired auctions and determine winners.

This command should be run periodically (e.g., via cron job) to:
1. Find auctions that have passed their end date
2. Determine the highest bidder for each auction
3. Mark the winning bid as 'won' and others as 'lost'
4. Update auction status to 'completed'
5. Send notifications to winners

Usage:
    python manage.py close_expired_auctions
    python manage.py close_expired_auctions --dry-run  # Preview without making changes
    python manage.py close_expired_auctions --verbose  # Detailed output
"""

import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Max
from ads.models import Ad
from bids.models import Bid
from bids.services import BidService
from ads.auction_services.auction_completion import AuctionCompletionService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Close expired auctions and determine winners'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview actions without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )
        parser.add_argument(
            '--grace-period',
            type=int,
            default=5,
            help='Grace period in minutes after auction end time (default: 5)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        grace_period = options['grace_period']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting auction closure process (dry_run={dry_run}, grace_period={grace_period}min)'
            )
        )
        
        # Initialize auction completion service
        auction_service = AuctionCompletionService()

        # Find expired auctions
        expired_auctions = auction_service.get_expired_auctions(grace_period)

        if verbose:
            self.stdout.write(f'Found {len(expired_auctions)} expired auctions to process')

        if not expired_auctions:
            self.stdout.write(self.style.SUCCESS('No expired auctions found'))
            return

        processed_count = 0
        successful_count = 0
        failed_count = 0
        
        if not dry_run:
            # Process auctions using the service with notifications
            results = []
            for auction in expired_auctions:
                result = auction_service.close_auction_with_notifications(auction)
                results.append(result)

            # Create batch result format
            batch_result = {
                'total_processed': len(results),
                'successful_count': len([r for r in results if r['success']]),
                'failed_count': len([r for r in results if not r['success']]),
                'results': results
            }

            successful_count = batch_result['successful_count']
            failed_count = batch_result['failed_count']
            processed_count = batch_result['total_processed']

            # Display results
            for result in batch_result['results']:
                if verbose:
                    self.stdout.write(f'\nProcessing auction: {result["auction_title"]} (ID: {result["auction_id"]})')

                    if result['success']:
                        if result['has_winner']:
                            self.stdout.write(
                                self.style.SUCCESS(f'  ✓ Auction completed successfully')
                            )
                            self.stdout.write(f'    Winner: {result["winner_email"]}')
                            self.stdout.write(f'    Winning bid: {result["winning_price"]} {result["currency"]}')
                            self.stdout.write(f'    Volume: {result["winning_volume"]} {result["unit"]}')
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'  ⚠ {result["message"]}')
                            )
                            if 'reserve_price' in result:
                                self.stdout.write(f'    Reserve price: {result["reserve_price"]} {result["currency"]}')
                                self.stdout.write(f'    Highest bid: {result["highest_bid"]} {result["currency"]}')
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ {result["message"]}')
                        )

        else:
            # Dry run - just show what would be processed
            for auction in expired_auctions:
                processed_count += 1
                self.stdout.write(f'\n[DRY RUN] Would process auction: {auction.title} (ID: {auction.id})')
                self.stdout.write(f'  End date: {auction.auction_end_date}')
                
                # Get active bids
                active_bids = auction.bids.filter(
                    status__in=['active', 'winning']
                ).order_by('-bid_price_per_unit', 'created_at')

                if not active_bids.exists():
                    self.stdout.write(f'  [DRY RUN] Would complete auction without winner')
                    successful_count += 1
                else:
                    highest_bid = active_bids.first()
                    self.stdout.write(f'  [DRY RUN] Would close auction')
                    self.stdout.write(f'    Highest bidder: {highest_bid.user.email}')
                    self.stdout.write(f'    Highest bid: {highest_bid.bid_price_per_unit} {auction.currency}')

                    if auction.reserve_price and highest_bid.bid_price_per_unit < auction.reserve_price:
                        self.stdout.write(f'    ⚠ Reserve price not met ({auction.reserve_price} {auction.currency})')

                    successful_count += 1

        # Final summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nAuction closure process completed:'
            )
        )
        self.stdout.write(f'  Total processed: {processed_count}')
        self.stdout.write(f'  Successful: {successful_count}')
        self.stdout.write(f'  Failed: {failed_count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('This was a dry run - no changes were made')
            )
