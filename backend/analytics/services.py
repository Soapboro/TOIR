from datetime import date, timedelta

from repair_requests.models import RepairRequest, RequestStatus

_FAILURE_STATUSES = [RequestStatus.COMPLETED, RequestStatus.CLOSED]


def _failure_timestamps(equipment_id):
    """Sorted list of failure datetimes (completed RepairRequests)."""
    return list(
        RepairRequest.objects
        .filter(equipment_id=equipment_id, status__in=_FAILURE_STATUSES)
        .order_by('created_at')
        .values_list('created_at', flat=True)
    )


def calculate_mtbf(equipment_id):
    """Return MTBF in hours, or None when fewer than 2 failure records exist."""
    ts = _failure_timestamps(equipment_id)
    if len(ts) < 2:
        return None
    intervals = [(ts[i + 1] - ts[i]).total_seconds() / 3600 for i in range(len(ts) - 1)]
    return sum(intervals) / len(intervals)


def predict_next_failure(equipment_id):
    """
    Return a prediction dict for the given equipment.
    'predicted_date' is None when fewer than 2 failure records exist.
    """
    ts = _failure_timestamps(equipment_id)
    failure_count = len(ts)

    if failure_count < 2:
        return {
            'predicted_date': None,
            'mtbf_hours': None,
            'last_failure_date': ts[0].date() if ts else None,
            'failure_count': failure_count,
            'days_until_failure': None,
            'reason': 'Недостаточно данных: требуется минимум 2 записи об отказах',
        }

    intervals = [(ts[i + 1] - ts[i]).total_seconds() / 3600 for i in range(failure_count - 1)]
    mtbf_hours = sum(intervals) / len(intervals)
    last_failure = ts[-1]
    predicted_date = (last_failure + timedelta(hours=mtbf_hours)).date()
    days_until = (predicted_date - date.today()).days

    return {
        'predicted_date': predicted_date,
        'mtbf_hours': round(mtbf_hours, 2),
        'last_failure_date': last_failure.date(),
        'failure_count': failure_count,
        'days_until_failure': days_until,
        'reason': None,
    }
