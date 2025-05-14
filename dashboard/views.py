from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from cars.models import Car
from customers.models import Customer
from bookings.models import Booking

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def safe_percent_change(self, current, previous):
        if previous == 0:
            if current == 0:
                return 0.0
            else:
                return 100.0
        return round(((current - previous) / previous) * 100, 2)

    def get(self, request):
        today = timezone.localdate()
        week_ago = today - timedelta(days=7)
        two_weeks_ago = today - timedelta(days=14)
        first_day = today.replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # For Total Cars
        today = timezone.localdate()
        week_ago = today - timedelta(days=7)
        two_weeks_ago = today - timedelta(days=14)

        # Cars added in last 7 days
        cars_added_last_7_days = Car.objects.filter(
            is_deleted=False,
            created_at__gte=week_ago,
            created_at__lt=today + timedelta(days=1)
        ).count()

        # Cars added in previous 7 days
        cars_added_prev_7_days = Car.objects.filter(
            is_deleted=False,
            created_at__gte=two_weeks_ago,
            created_at__lt=week_ago
        ).count()

        # Total cars in the system
        total_cars = Car.objects.filter(is_deleted=False).count()

        # Percent change in new cars
        if cars_added_prev_7_days == 0:
            if cars_added_last_7_days == 0:
                total_cars_change = 0.0
            else:
                total_cars_change = 100.0
        else:
            total_cars_change = round(((cars_added_last_7_days - cars_added_prev_7_days) / cars_added_prev_7_days) * 100, 2)

        # Customers added in last 7 days
        customers_added_last_7_days = Customer.objects.filter(
            created_at__gte=week_ago,
            created_at__lt=today + timedelta(days=1)
        ).count()

        # Customers added in previous 7 days
        customers_added_prev_7_days = Customer.objects.filter(
            created_at__gte=two_weeks_ago,
            created_at__lt=week_ago
        ).count()

        total_customers = Customer.objects.count()

        if customers_added_prev_7_days == 0:
            if customers_added_last_7_days == 0:
                total_customers_change = 0.0
            else:
                total_customers_change = 100.0
        else:
            total_customers_change = round(((customers_added_last_7_days - customers_added_prev_7_days) / customers_added_prev_7_days) * 100, 2)

        #Today pickups and returns
        todays_pickup = Booking.objects.filter(start_date=today).count()
        pickup_prev = Booking.objects.filter(start_date=week_ago).count()

        if pickup_prev == 0:
            if todays_pickup == 0:
                pickup_change = 0.0
            else:
                pickup_change = 100.0
        else:
            pickup_change = round(((todays_pickup - pickup_prev) / pickup_prev) * 100, 2)

        todays_return = Booking.objects.filter(end_date=today).count()
        return_prev = Booking.objects.filter(end_date=week_ago).count()

        if return_prev == 0:
            if todays_return == 0:
                return_change = 0.0
            else:
                return_change = 100.0
        else:
            return_change = round(((todays_return - return_prev) / return_prev) * 100, 2)


        # Ongoing Bookings
        ongoing_bookings = Booking.objects.filter(
            start_date__lte=today, end_date__gte=today, booking_status='Active'
        ).count()
        ongoing_bookings_last_week = Booking.objects.filter(
            start_date__lte=week_ago, end_date__gte=week_ago, booking_status='Active'
        ).count()

        if ongoing_bookings_last_week == 0:
            if ongoing_bookings == 0:
                ongoing_change = 0.0
            else:
                ongoing_change = 100.0
        else:
            ongoing_change = round(((ongoing_bookings - ongoing_bookings_last_week) / ongoing_bookings_last_week) * 100, 2)


        # Booking Calendar (bookings per day in current month)
        calendar = []
        for day in range(1, last_day.day + 1):
            date = today.replace(day=day)
            count = Booking.objects.filter(start_date=date).count()
            calendar.append({
                "date": str(date),
                "bookings": count
            })

        # Booking Summary (last 7 days: Booked vs Canceled)
        summary_dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
        summary = []
        for date in summary_dates:
            booked = Booking.objects.filter(start_date=date, booking_status='Active').count()
            canceled = Booking.objects.filter(start_date=date, booking_status='Cancelled').count()
            summary.append({
                "date": str(date),
                "booked": booked,
                "canceled": canceled
            })

        return Response({
            "data": {
                "total_cars": {
                    "count": total_cars,
                    "percent_change": total_cars_change
                },
                "total_customers": {
                    "count": total_customers,
                    "percent_change": total_customers_change
                },
                "todays_pickup": {
                    "count": todays_pickup,
                    "percent_change": pickup_change
                },
                "todays_return": {
                    "count": todays_return,
                    "percent_change": return_change
                },
                "ongoing_bookings": {
                    "count": ongoing_bookings,
                    "percent_change": ongoing_change
                },
                "calendar": calendar,
                "booking_summary": summary
            },
            "message": "Dashboard data fetched successfully",
            "status_code": 200
        })
