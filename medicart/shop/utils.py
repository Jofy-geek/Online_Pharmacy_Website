# shop/utils.py
import csv
from django.http import HttpResponse

def export_as_csv(queryset, fields, filename="export.csv"):
    """
    Generic CSV exporter.
    queryset: Django queryset
    fields: list of model fields to include
    filename: downloaded file name
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(fields)

    for obj in queryset:
        row = [getattr(obj, field) for field in fields]
        writer.writerow(row)

    return response
