from datetime import date, timedelta
import html
import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from notifications.services.telegram_service import TelegramService
from membership.models import Membership
from payments.models import Payment

logger = logging.getLogger(__name__)


@shared_task
def mark_expired_memberships():
    today = timezone.now().date()

    expired_memberships = Membership.objects.select_related("member", "plan").filter(
        end_date__lt=today,
        status__in=[Membership.Status.ACTIVE, Membership.Status.FROZEN]
    )

    for membership in expired_memberships:
        membership.status = Membership.Status.EXPIRED
        membership.save()

        message = (
            f"<b>Membership Expired</b>\n"
            f"Member: {html.escape(membership.member.get_full_name())}\n"
            f"Email: {html.escape(membership.member.email)}\n"
            f"Plan: {html.escape(membership.plan.name)}\n"
            f"End Date: {membership.end_date}"
        )
        TelegramService.send_message(message)

    return f"Marked {len(expired_memberships)} memberships as expired"


@shared_task
def send_expiration_reminders(days_before=7):
    target_date = timezone.now().date() + timedelta(days=days_before)

    memberships = Membership.objects.select_related("member", "plan").filter(
        end_date=target_date,
        status=Membership.Status.ACTIVE
    )

    count = 0
    for membership in memberships:
        message = (
            f"⏰ <b>Membership Expiring Soon</b>\n"
            f"Member: {html.escape(membership.member.get_full_name())}\n"
            f"Email: {html.escape(membership.member.email)}\n"
            f"Plan: {html.escape(membership.plan.name)}\n"
            f"Expires in: {days_before} day(s)\n"
            f"End Date: {membership.end_date}"
        )
        TelegramService.send_message(message)
        count += 1

    return f"Sent {count} expiration reminders for {days_before} days before"


@shared_task
def auto_renew_memberships():
    today = timezone.now().date()

    expired_auto_renew = Membership.objects.select_related("member", "plan").filter(
        auto_renew=True,
        status=Membership.Status.EXPIRED
    )

    count = 0
    for old_membership in expired_auto_renew:
        has_pending = Payment.objects.filter(
            membership__member=old_membership.member,
            status=Payment.Status.PENDING
        ).exists()

        if has_pending:
            logger.info(f"Skipping auto-renew for user {old_membership.member.email}: pending payment exists.")
            continue

        with transaction.atomic():
            old_membership.auto_renew = False
            old_membership.save()

            new_membership = Membership.objects.create(
                member=old_membership.member,
                plan=old_membership.plan,
                start_date=today,
                end_date=today + timedelta(days=old_membership.plan.duration_days),
                status=Membership.Status.ACTIVE,
                auto_renew=True,
                price_at_purchase=old_membership.plan.price
            )

        message = (
            f"🔄 <b>Auto-Renewal Successful</b>\n"
            f"Member: {html.escape(new_membership.member.get_full_name())}\n"
            f"Email: {html.escape(new_membership.member.email)}\n"
            f"Plan: {html.escape(new_membership.plan.name)}\n"
            f"New End Date: {new_membership.end_date}"
        )
        TelegramService.send_message(message)
        count += 1

    return f"Auto-renewed {count} memberships"


@shared_task
def notify_new_membership(membership_id):
    try:
        membership = Membership.objects.select_related("member", "plan").get(id=membership_id)
        message = (
            f"<b>New Membership Created</b>\n"
            f"Member: {html.escape(membership.member.get_full_name())}\n"
            f"Email: {html.escape(membership.member.email)}\n"
            f"Plan: {html.escape(membership.plan.name)}\n"
            f"Price: ${membership.price_at_purchase}\n"
            f"Start Date: {membership.start_date}\n"
            f"End Date: {membership.end_date}\n"
            f"Auto-Renew: {'Yes' if membership.auto_renew else 'No'}"
        )
        TelegramService.send_message(message)
        return f"Notification sent for membership {membership_id}"

    except Membership.DoesNotExist:
        logger.warning(f"Membership {membership_id} not found for notification")
        return f"Membership {membership_id} not found"


@shared_task
def notify_membership_frozen(membership_id):
    try:
        membership = Membership.objects.select_related("member", "plan").get(id=membership_id)
        message = (
            f"❄️ <b>Membership Frozen</b>\n"
            f"Member: {html.escape(membership.member.get_full_name())}\n"
            f"Email: {html.escape(membership.member.email)}\n"
            f"Plan: {html.escape(membership.plan.name)}\n"
            f"Frozen From: {membership.frozen_from}\n"
            f"Frozen To: {membership.frozen_to}\n"
            f"New End Date: {membership.end_date}"
        )
        TelegramService.send_message(message)
        return f"Freeze notification sent for membership {membership_id}"

    except Membership.DoesNotExist:
        logger.warning(f"Membership {membership_id} not found for freeze notification")
        return f"Membership {membership_id} not found"


@shared_task
def notify_payment_success(payment_id):
    try:
        payment = Payment.objects.select_related(
            "membership__member",
            "membership__plan"
        ).get(id=payment_id)

        membership = payment.membership

        if not membership:
            error_msg = f"❌ Payment {payment_id} is received, but it has no linked membership!"
            logger.error(error_msg)
            return error_msg

        member = membership.member
        plan = membership.plan

        member_name = html.escape(member.get_full_name()) if member else "Unknown Member"
        member_email = html.escape(member.email) if member else "No Email"
        plan_name = html.escape(plan.name) if plan else "Unknown Plan"

        message = (
            f"✅ <b>Payment Successful</b>\n"
            f"Payment ID: {payment.id}\n"
            f"Type: {payment.get_type_display()}\n"
            f"Amount: ${payment.money_to_pay}\n"
            f"Member: {member_name}\n"
            f"Email: {member_email}\n"
            f"Plan: {plan_name}"
        )

        TelegramService.send_message(message)
        logger.info(f"🚀 Payment success notification sent for payment {payment_id}")
        return f"Payment success notification sent for payment {payment_id}"

    except Payment.DoesNotExist:
        logger.warning(f"⚠️ Payment {payment_id} not found")
        return f"Payment {payment_id} not found"
    except Exception as e:
        logger.error(f"❌ Unexpected error in notify_payment_success: {str(e)}")
        raise e
