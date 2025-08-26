"""
Notification message templates for auction and bidding system

This module provides standardized notification templates for different
auction scenarios to ensure consistent messaging across the platform.
"""

from typing import Dict, Any
from decimal import Decimal


class AuctionNotificationTemplates:
    """Templates for auction-related notifications"""
    
    @staticmethod
    def winner_automatic_closure(auction_title: str, winning_price: Decimal, 
                                currency: str, volume: Decimal, unit: str, 
                                total_value: Decimal) -> Dict[str, str]:
        """Template for automatic auction closure winner notification"""
        return {
            'title': '🎉 Auction Won! Payment Required',
            'message': (
                f"Congratulations! The auction for {auction_title} has ended and you are the winner! "
                f"Your winning bid: {winning_price} {currency} per {unit} for {volume} {unit}. "
                f"Total amount: {total_value} {currency}. "
                f"Please proceed with payment to secure your purchase."
            )
        }
    
    @staticmethod
    def winner_manual_closure(auction_title: str, winning_price: Decimal, 
                             currency: str, volume: Decimal, unit: str) -> Dict[str, str]:
        """Template for manual admin closure winner notification"""
        return {
            'title': '🎉 Congratulations! You Won the Auction',
            'message': (
                f"Great news! You have won the auction for {auction_title}. "
                f"Your winning bid of {winning_price} {currency} per {unit} for {volume} {unit} "
                f"has been accepted. Please proceed with payment to complete your purchase."
            )
        }
    
    @staticmethod
    def winner_signal_backup(auction_title: str, winning_price: Decimal, 
                            currency: str, volume: Decimal, unit: str, 
                            total_value: Decimal) -> Dict[str, str]:
        """Template for signal-based winner notification (backup)"""
        return {
            'title': '🎉 Congratulations! You Won the Auction',
            'message': (
                f"Great news! You have won the auction for {auction_title}. "
                f"Your winning bid of {winning_price} {currency} per {unit} for {volume} {unit} "
                f"has been accepted. Total amount: {total_value} {currency}. "
                f"Please proceed with payment to complete your purchase."
            )
        }
    
    @staticmethod
    def outbid_notification(auction_title: str, bid_price: Decimal, 
                           currency: str, unit: str) -> Dict[str, str]:
        """Template for outbid notification"""
        return {
            'title': "You've Been Outbid",
            'message': (
                f"Your bid of {bid_price} {currency} per {unit} for {auction_title} "
                f"has been outbid. You can place a higher bid to regain the lead."
            )
        }
    
    @staticmethod
    def auction_ended_lost(auction_title: str, bid_price: Decimal, 
                          currency: str, unit: str) -> Dict[str, str]:
        """Template for auction ended notification (lost)"""
        return {
            'title': "Auction Ended",
            'message': (
                f"The auction for {auction_title} has ended. "
                f"Your bid of {bid_price} {currency} per {unit} was not the winning bid."
            )
        }
    
    @staticmethod
    def reserve_not_met(auction_title: str, highest_bid: Decimal, 
                       reserve_price: Decimal, currency: str) -> Dict[str, str]:
        """Template for reserve price not met notification"""
        return {
            'title': "Auction Ended - Reserve Not Met",
            'message': (
                f"The auction for {auction_title} has ended without a winner. "
                f"The highest bid of {highest_bid} {currency} did not meet the "
                f"reserve price of {reserve_price} {currency}."
            )
        }


class BidNotificationTemplates:
    """Templates for bid-related notifications"""
    
    @staticmethod
    def bid_placed_confirmation(auction_title: str, bid_price: Decimal, 
                               currency: str, volume: Decimal, unit: str) -> Dict[str, str]:
        """Template for bid placement confirmation"""
        return {
            'title': "Bid Placed Successfully",
            'message': (
                f"Your bid of {bid_price} {currency} per {unit} for {volume} {unit} "
                f"has been placed on {auction_title}. You will be notified if you are outbid."
            )
        }
    
    @staticmethod
    def auto_bid_triggered(auction_title: str, new_bid_price: Decimal, 
                          currency: str, volume: Decimal, unit: str) -> Dict[str, str]:
        """Template for auto-bid triggered notification"""
        return {
            'title': "Auto-Bid Activated",
            'message': (
                f"Your auto-bid has been triggered for {auction_title}. "
                f"Your new bid: {new_bid_price} {currency} per {unit} for {volume} {unit}."
            )
        }


def get_auction_notification_metadata(auction_id: int, bid_id: int, 
                                     winning_price: Decimal, volume: Decimal, 
                                     total_value: Decimal, currency: str, 
                                     unit: str, closure_type: str, 
                                     action_type: str) -> Dict[str, Any]:
    """Generate standard metadata for auction notifications"""
    return {
        'auction_id': auction_id,
        'bid_id': bid_id,
        'winning_price': str(winning_price),
        'volume': str(volume),
        'total_value': str(total_value),
        'currency': currency,
        'unit': unit,
        'closure_type': closure_type,
        'action_type': action_type
    }


def get_bid_notification_metadata(auction_id: int, bid_id: int, 
                                 bid_price: Decimal, volume: Decimal, 
                                 currency: str, unit: str, 
                                 action_type: str, **kwargs) -> Dict[str, Any]:
    """Generate standard metadata for bid notifications"""
    metadata = {
        'auction_id': auction_id,
        'bid_id': bid_id,
        'bid_price': str(bid_price),
        'volume': str(volume),
        'currency': currency,
        'unit': unit,
        'action_type': action_type
    }
    
    # Add any additional metadata
    metadata.update(kwargs)
    
    return metadata
